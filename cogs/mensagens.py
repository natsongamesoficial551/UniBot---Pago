import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

class Mensagens(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "mensagens_automaticas.json"
        self.client = None
        self.db = None
        self.collection = None
        self._connection_ready = False
        self.mensagens = {}
        self.tarefas_ativas = {}
        
        # Inicializa a conexão com MongoDB
        self.bot.loop.create_task(self.init_database())
        self.load_data()
    
    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada nas variáveis de ambiente!")
                return
            
            print("🔄 Conectando ao MongoDB...")
            self.client = AsyncIOMotorClient(mongo_uri)
            
            # Testa a conexão
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.collection = self.db['mensagens_automaticas']
            self._connection_ready = True
            
            print("✅ MongoDB conectado - Sistema de Mensagens!")
            
            # Carrega dados do MongoDB após conexão
            await self.load_from_mongodb()
            self.iniciar_tarefas()
            
        except Exception as e:
            print(f"❌ Erro ao conectar MongoDB: {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready
    
    def load_data(self):
        """Carrega dados do arquivo JSON (fallback)"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.mensagens = json.load(f)
        else:
            self.mensagens = {}
            self.save_data()
    
    def save_data(self):
        """Salva dados no arquivo JSON (fallback)"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.mensagens, f, indent=2, ensure_ascii=False)

    async def load_from_mongodb(self):
        """Carrega todas as mensagens do MongoDB"""
        try:
            if not await self.ensure_connection():
                return
                
            cursor = self.collection.find({})
            async for documento in cursor:
                nome = documento['_id']
                documento.pop('_id')
                self.mensagens[nome] = documento
                
        except Exception as e:
            print(f"❌ Erro ao carregar do MongoDB: {e}")

    async def save_to_mongodb(self, nome, dados):
        """Salva ou atualiza uma mensagem no MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
                
            documento = {
                '_id': nome,
                'mensagem': dados['mensagem'],
                'intervalo': dados['intervalo'],
                'canal_id': dados['canal_id'],
                'canal_nome': dados['canal_nome'],
                'autor': dados['autor'],
                'autor_id': dados['autor_id'],
                'data_criacao': dados['data_criacao'],
                'ativo': dados['ativo'],
                'envios': dados['envios']
            }
            
            await self.collection.replace_one(
                {'_id': nome}, 
                documento, 
                upsert=True
            )
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar no MongoDB: {e}")
            return False

    async def delete_from_mongodb(self, nome):
        """Remove uma mensagem do MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
                
            await self.collection.delete_one({'_id': nome})
            return True
            
        except Exception as e:
            print(f"❌ Erro ao deletar do MongoDB: {e}")
            return False

    async def update_envios_mongodb(self, nome, envios):
        """Atualiza apenas o contador de envios no MongoDB"""
        try:
            if not await self.ensure_connection():
                return
                
            await self.collection.update_one(
                {'_id': nome},
                {'$set': {'envios': envios}}
            )
            
        except Exception as e:
            print(f"❌ Erro ao atualizar envios: {e}")
    
    def iniciar_tarefas(self):
        """Inicia todas as tarefas automáticas salvas"""
        for nome, dados in self.mensagens.items():
            if dados.get('ativo', True):
                self.criar_tarefa(nome, dados)
    
    def criar_tarefa(self, nome, dados):
        """Cria uma tarefa automática para enviar mensagens"""
        async def enviar_mensagem_automatica():
            while True:
                try:
                    await asyncio.sleep(dados['intervalo'] * 3600)
                    
                    if nome not in self.mensagens or not self.mensagens[nome].get('ativo', True):
                        break
                    
                    canal = self.bot.get_channel(dados['canal_id'])
                    if canal:
                        await canal.send(dados['mensagem'])
                        
                        self.mensagens[nome]['envios'] = self.mensagens[nome].get('envios', 0) + 1
                        self.save_data()
                        
                        await self.update_envios_mongodb(nome, self.mensagens[nome]['envios'])
                
                except Exception as e:
                    print(f"❌ Erro mensagem automática '{nome}': {e}")
                    break
        
        tarefa = asyncio.create_task(enviar_mensagem_automatica())
        self.tarefas_ativas[nome] = tarefa
    
    def parar_tarefa(self, nome):
        """Para uma tarefa específica"""
        if nome in self.tarefas_ativas:
            self.tarefas_ativas[nome].cancel()
            del self.tarefas_ativas[nome]
    
    @commands.command(name='adicionarmensagem', aliases=['addmsg'])
    @commands.has_permissions(manage_messages=True)
    async def adicionar_mensagem(self, ctx, horas: float, *, mensagem):
        """Adiciona uma mensagem automática. Uso: !adicionarmensagem <horas> <mensagem>"""
        
        if horas <= 0:
            embed = discord.Embed(
                title="❌ Erro",
                description="O intervalo deve ser maior que 0 horas.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        if not mensagem or len(mensagem.strip()) == 0:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar uma mensagem.\n**Uso:** `!adicionarmensagem <horas> <mensagem>`",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        nome = f"msg_{int(datetime.now().timestamp())}"
        
        dados_mensagem = {
            'mensagem': mensagem,
            'intervalo': horas,
            'canal_id': ctx.channel.id,
            'canal_nome': ctx.channel.name,
            'autor': ctx.author.display_name,
            'autor_id': ctx.author.id,
            'data_criacao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'ativo': True,
            'envios': 0
        }
        
        self.mensagens[nome] = dados_mensagem
        self.save_data()
        
        # Salva no MongoDB
        success = await self.save_to_mongodb(nome, dados_mensagem)
        
        # Inicia a tarefa
        self.criar_tarefa(nome, dados_mensagem)
        
        embed = discord.Embed(
            title="✅ Mensagem Automática Adicionada",
            description=f"Mensagem será enviada a cada **{horas}h** no canal {ctx.channel.mention}",
            color=0x00ff7f
        )
        embed.add_field(name="📝 Mensagem", value=mensagem[:200] + "..." if len(mensagem) > 200 else mensagem, inline=False)
        embed.add_field(name="⏰ Intervalo", value=f"{horas} horas", inline=True)
        embed.add_field(name="📍 Canal", value=ctx.channel.mention, inline=True)
        
        if not success:
            embed.add_field(name="⚠️ Aviso", value="Mensagem salva localmente, mas falha ao salvar no banco de dados", inline=False)
            
        await ctx.send(embed=embed)
    
    @commands.command(name='removermensagem', aliases=['rmmsg'])
    @commands.has_permissions(manage_messages=True)
    async def remover_mensagem(self, ctx, *, mensagem_busca):
        """Remove uma mensagem automática pela mensagem ou parte dela"""
        
        if not mensagem_busca:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar a mensagem ou parte dela para remover.\n**Uso:** `!removermensagem <mensagem>`",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        mensagem_encontrada = None
        nome_encontrado = None
        
        for nome, dados in self.mensagens.items():
            if mensagem_busca.lower() in dados['mensagem'].lower():
                mensagem_encontrada = dados
                nome_encontrado = nome
                break
        
        if not mensagem_encontrada:
            embed = discord.Embed(
                title="❓ Mensagem Não Encontrada",
                description=f"Não foi encontrada nenhuma mensagem contendo: `{mensagem_busca}`\nUse `!mensagens` para ver todas as mensagens.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        self.parar_tarefa(nome_encontrado)
        del self.mensagens[nome_encontrado]
        self.save_data()
        
        success = await self.delete_from_mongodb(nome_encontrado)
        
        embed = discord.Embed(
            title="🗑️ Mensagem Removida",
            description="A mensagem automática foi removida com sucesso.",
            color=0xff6666
        )
        embed.add_field(name="📝 Mensagem Removida", value=mensagem_encontrada['mensagem'][:200] + "..." if len(mensagem_encontrada['mensagem']) > 200 else mensagem_encontrada['mensagem'], inline=False)
        embed.add_field(name="⏰ Intervalo", value=f"{mensagem_encontrada['intervalo']}h", inline=True)
        embed.add_field(name="📊 Envios", value=str(mensagem_encontrada['envios']), inline=True)
        
        if not success:
            embed.add_field(name="⚠️ Aviso", value="Removida localmente, mas falha ao remover do banco de dados", inline=False)
            
        await ctx.send(embed=embed)
    
    @commands.command(name='mensagens', aliases=['listmsg'])
    async def listar_mensagens(self, ctx):
        """Lista todas as mensagens automáticas ativas"""
        if not self.mensagens:
            embed = discord.Embed(
                title="📝 Mensagens Automáticas",
                description="Nenhuma mensagem automática cadastrada ainda.\nUse `!adicionarmensagem <horas> <mensagem>` para adicionar uma.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        mensagens_ativas = {nome: dados for nome, dados in self.mensagens.items() if dados.get('ativo', True)}
        
        if not mensagens_ativas:
            embed = discord.Embed(
                title="📝 Mensagens Automáticas",
                description="Nenhuma mensagem automática ativa no momento.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        lista_mensagens = []
        for nome, dados in mensagens_ativas.items():
            canal = self.bot.get_channel(dados['canal_id'])
            canal_nome = canal.mention if canal else f"#{dados['canal_nome']} (canal removido)"
            
            preview = dados['mensagem'][:80] + "..." if len(dados['mensagem']) > 80 else dados['mensagem']
            lista_mensagens.append(f"📌 **{preview}**")
            lista_mensagens.append(f"   └ ⏰ A cada {dados['intervalo']}h | 📍 {canal_nome} | 📊 {dados['envios']} envios")
            lista_mensagens.append("")
        
        if lista_mensagens:
            lista_mensagens.pop()
        
        embed = discord.Embed(
            title="📝 Mensagens Automáticas Ativas",
            description="\n".join(lista_mensagens),
            color=0x9966ff
        )
        embed.set_footer(text=f"Total: {len(mensagens_ativas)} mensagens ativas")
        await ctx.send(embed=embed)
    
    @commands.command(name='testmensagem', aliases=['testmsg'])
    @commands.has_permissions(manage_messages=True)
    async def testar_mensagem(self, ctx, *, mensagem_busca):
        """Testa uma mensagem automática enviando ela imediatamente"""
        
        if not mensagem_busca:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar a mensagem ou parte dela para testar.\n**Uso:** `!testmensagem <mensagem>`",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        mensagem_encontrada = None
        
        for nome, dados in self.mensagens.items():
            if mensagem_busca.lower() in dados['mensagem'].lower():
                mensagem_encontrada = dados
                break
        
        if not mensagem_encontrada:
            embed = discord.Embed(
                title="❓ Mensagem Não Encontrada",
                description=f"Não foi encontrada nenhuma mensagem contendo: `{mensagem_busca}`\nUse `!mensagens` para ver todas as mensagens.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        embed_teste = discord.Embed(
            title="🧪 Teste de Mensagem Automática",
            description="Esta é uma prévia da mensagem automática:",
            color=0x00aaff
        )
        await ctx.send(embed=embed_teste)
        
        await ctx.send(mensagem_encontrada['mensagem'])
        
        embed_confirmacao = discord.Embed(
            title="✅ Teste Realizado",
            description=f"A mensagem foi testada com sucesso!\n**Intervalo configurado:** {mensagem_encontrada['intervalo']}h",
            color=0x00ff7f
        )
        await ctx.send(embed=embed_confirmacao)
    
    @commands.command(name='statusmsg')
    @commands.has_permissions(manage_messages=True)
    async def status_msg(self, ctx):
        """Verifica o status da conexão com o banco de dados"""
        if self._connection_ready:
            try:
                await self.client.admin.command('ping')
                embed = discord.Embed(
                    title="✅ Banco de Dados Conectado",
                    description="A conexão com o MongoDB está funcionando corretamente.",
                    color=discord.Color.green()
                )
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Erro na Conexão",
                    description=f"Erro ao testar conexão: {str(e)}",
                    color=discord.Color.red()
                )
                self._connection_ready = False
        else:
            embed = discord.Embed(
                title="❌ Banco de Dados Desconectado",
                description="A conexão com o MongoDB não está disponível. Tentando reconectar...",
                color=discord.Color.red()
            )
            await self.init_database()
            
        await ctx.send(embed=embed)
    
    @adicionar_mensagem.error
    @remover_mensagem.error
    @testar_mensagem.error
    async def comando_error(self, ctx, error):
        """Trata erros de permissão e conversão"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão **Gerenciar Mensagens** para usar este comando.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Formato Inválido",
                description="O número de horas deve ser um número válido (ex: 3, 2.5, 0.5).",
                color=0xff4444
            )
            await ctx.send(embed=embed)
    
    async def cog_unload(self):
        """Para todas as tarefas quando o cog é descarregado"""
        for tarefa in self.tarefas_ativas.values():
            tarefa.cancel()
        
        if self.client:
            self.client.close()
            print("🔌 Conexão MongoDB fechada - Sistema de Mensagens")

async def setup(bot):
    await bot.add_cog(Mensagens(bot))