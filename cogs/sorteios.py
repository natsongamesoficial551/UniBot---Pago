import discord
from discord.ext import commands
import os
import random
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

class Sorteio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.sorteios_collection = None
        self.configuracoes_collection = None
        self._connection_ready = False
        # Inicializa a conexão com MongoDB
        self.bot.loop.create_task(self.init_database())
    
    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            # URL de conexão do MongoDB (vem de variável de ambiente)
            mongo_uri = os.getenv("MONGO_URI") or os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
            
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada nas variáveis de ambiente!")
                return
            
            print("🔄 Conectando ao MongoDB (Sorteios)...")
            self.client = AsyncIOMotorClient(mongo_uri)
            
            # Testa a conexão
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.sorteios_collection = self.db['sorteios']
            self.configuracoes_collection = self.db['configuracoes']
            self._connection_ready = True
            
            print("✅ Conectado ao MongoDB (Sorteios) com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB (Sorteios): {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready
    
    async def get_sorteio(self, guild_id):
        """Busca sorteio do servidor no MongoDB"""
        try:
            if not await self.ensure_connection():
                return None
            return await self.sorteios_collection.find_one({'guild_id': str(guild_id)})
        except Exception as e:
            print(f"❌ Erro ao buscar sorteio: {e}")
            return None
    
    async def save_sorteio(self, guild_id, data):
        """Salva ou atualiza sorteio no MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
            data['guild_id'] = str(guild_id)
            await self.sorteios_collection.replace_one(
                {'guild_id': str(guild_id)}, 
                data, 
                upsert=True
            )
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar sorteio: {e}")
            return False
    
    async def delete_sorteio(self, guild_id):
        """Remove sorteio do MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
            await self.sorteios_collection.delete_one({'guild_id': str(guild_id)})
            return True
        except Exception as e:
            print(f"❌ Erro ao deletar sorteio: {e}")
            return False
    
    async def get_configuracao(self, guild_id):
        """Busca configuração do servidor no MongoDB"""
        try:
            if not await self.ensure_connection():
                return {}
            config = await self.configuracoes_collection.find_one({'guild_id': str(guild_id)})
            return config if config else {}
        except Exception as e:
            print(f"❌ Erro ao buscar configuração: {e}")
            return {}
    
    async def save_configuracao(self, guild_id, data):
        """Salva ou atualiza configuração no MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
            data['guild_id'] = str(guild_id)
            await self.configuracoes_collection.replace_one(
                {'guild_id': str(guild_id)}, 
                data, 
                upsert=True
            )
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar configuração: {e}")
            return False
    
    @commands.command(name='comecarsorteio', aliases=['startgw'])
    @commands.has_permissions(administrator=True)
    async def comecar_sorteio(self, ctx, *, premio):
        """Inicia um novo sorteio"""
        guild_id = str(ctx.guild.id)
        
        if not premio:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar um prêmio.\n**Uso:** `!comecarsorteio <prêmio>`",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Verifica se já existe um sorteio ativo
        sorteio_ativo = await self.get_sorteio(guild_id)
        if sorteio_ativo and sorteio_ativo.get('ativo'):
            embed = discord.Embed(
                title="⚠️ Sorteio Já Ativo",
                description="Já existe um sorteio em andamento.\nUse `!encerrarsorteio` para encerrar antes de começar outro.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Verifica se os canais estão configurados
        configs = await self.get_configuracao(guild_id)
        canal_sorteio_id = configs.get('canal_sorteio')
        canal_comando_id = configs.get('canal_comando')
        
        if not canal_sorteio_id:
            embed = discord.Embed(
                title="❌ Canal Não Configurado",
                description="Configure o canal do sorteio primeiro:\n`!canaldosorteio #canal`",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Verifica se está no canal correto
        if canal_comando_id and ctx.channel.id != canal_comando_id:
            canal_comando = self.bot.get_channel(canal_comando_id)
            embed = discord.Embed(
                title="❌ Canal Incorreto",
                description=f"Use este comando no canal {canal_comando.mention if canal_comando else 'configurado'}.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Cria o sorteio
        sorteio_data = {
            'premio': premio,
            'ativo': True,
            'participantes': [],
            'criador': ctx.author.display_name,
            'criador_id': ctx.author.id,
            'data_inicio': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
        # Envia mensagem no canal do sorteio
        canal_sorteio = self.bot.get_channel(canal_sorteio_id)
        if canal_sorteio:
            embed = discord.Embed(
                title="🎉 SORTEIO INICIADO!",
                description=f"**Prêmio:** {premio}\n\nReaja com 🎁 para participar!",
                color=0x00ff7f
            )
            embed.set_footer(text=f"Iniciado por {ctx.author.display_name}")
            
            msg = await canal_sorteio.send(embed=embed)
            await msg.add_reaction('🎁')
            
            # Salva ID da mensagem
            sorteio_data['mensagem_id'] = msg.id
        
        await self.save_sorteio(guild_id, sorteio_data)
        
        # Confirmação no canal de comando
        embed = discord.Embed(
            title="✅ Sorteio Iniciado",
            description=f"Sorteio do prêmio **{premio}** foi iniciado!",
            color=0x00ff7f
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='vencedor', aliases=['winner'])
    @commands.has_permissions(administrator=True)
    async def sortear_vencedor(self, ctx):
        """Sorteia um vencedor do sorteio ativo"""
        guild_id = str(ctx.guild.id)
        
        sorteio = await self.get_sorteio(guild_id)
        if not sorteio or not sorteio.get('ativo'):
            embed = discord.Embed(
                title="❌ Nenhum Sorteio Ativo",
                description="Não há sorteio em andamento.\nUse `!comecarsorteio <prêmio>` para iniciar um.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Verifica canal de comando
        configs = await self.get_configuracao(guild_id)
        canal_comando_id = configs.get('canal_comando')
        
        if canal_comando_id and ctx.channel.id != canal_comando_id:
            canal_comando = self.bot.get_channel(canal_comando_id)
            embed = discord.Embed(
                title="❌ Canal Incorreto",
                description=f"Use este comando no canal {canal_comando.mention if canal_comando else 'configurado'}.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Pega participantes da reação
        canal_sorteio_id = configs.get('canal_sorteio')
        canal_sorteio = self.bot.get_channel(canal_sorteio_id)
        
        if not canal_sorteio:
            embed = discord.Embed(
                title="❌ Canal do Sorteio Não Encontrado",
                description="O canal do sorteio foi removido ou não encontrado.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        try:
            msg_id = sorteio.get('mensagem_id')
            if msg_id:
                msg = await canal_sorteio.fetch_message(msg_id)
                participantes = []
                
                for reaction in msg.reactions:
                    if str(reaction.emoji) == '🎁':
                        async for user in reaction.users():
                            if not user.bot:
                                participantes.append(user)
                        break
            else:
                participantes = []
        except:
            participantes = []
        
        if not participantes:
            embed = discord.Embed(
                title="❌ Sem Participantes",
                description="Nenhum participante encontrado no sorteio.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Sorteia vencedor
        vencedor = random.choice(participantes)
        premio = sorteio['premio']
        
        # Anuncia no canal do sorteio
        embed_vencedor = discord.Embed(
            title="🎊 TEMOS UM VENCEDOR!",
            description=f"🎉 Parabéns {vencedor.mention}!\n\n**Prêmio:** {premio}",
            color=0xffd700
        )
        embed_vencedor.set_footer(text=f"Sorteado entre {len(participantes)} participantes")
        
        await canal_sorteio.send(embed=embed_vencedor)
        
        # Confirmação no canal de comando
        embed = discord.Embed(
            title="🎊 Vencedor Sorteado",
            description=f"**Vencedor:** {vencedor.display_name}\n**Participantes:** {len(participantes)}",
            color=0xffd700
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='encerrarsorteio', aliases=['endgw'])
    @commands.has_permissions(administrator=True)
    async def encerrar_sorteio(self, ctx):
        """Encerra o sorteio ativo"""
        guild_id = str(ctx.guild.id)
        
        sorteio = await self.get_sorteio(guild_id)
        if not sorteio or not sorteio.get('ativo'):
            embed = discord.Embed(
                title="❌ Nenhum Sorteio Ativo",
                description="Não há sorteio em andamento para encerrar.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Verifica canal de comando
        configs = await self.get_configuracao(guild_id)
        canal_comando_id = configs.get('canal_comando')
        
        if canal_comando_id and ctx.channel.id != canal_comando_id:
            canal_comando = self.bot.get_channel(canal_comando_id)
            embed = discord.Embed(
                title="❌ Canal Incorreto",
                description=f"Use este comando no canal {canal_comando.mention if canal_comando else 'configurado'}.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Encerra o sorteio
        premio = sorteio['premio']
        sorteio['ativo'] = False
        await self.save_sorteio(guild_id, sorteio)
        
        # Anuncia encerramento no canal do sorteio
        configs = await self.get_configuracao(guild_id)
        canal_sorteio_id = configs.get('canal_sorteio')
        canal_sorteio = self.bot.get_channel(canal_sorteio_id)
        
        if canal_sorteio:
            embed_encerrado = discord.Embed(
                title="🔒 Sorteio Encerrado",
                description=f"O sorteio do prêmio **{premio}** foi encerrado.",
                color=0xff6666
            )
            await canal_sorteio.send(embed=embed_encerrado)
        
        # Confirmação
        embed = discord.Embed(
            title="✅ Sorteio Encerrado",
            description=f"O sorteio do prêmio **{premio}** foi encerrado com sucesso.",
            color=0x00ff7f
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='canaldecomando', aliases=['cmdchannel'])
    @commands.has_permissions(administrator=True)
    async def canal_comando(self, ctx, canal: discord.TextChannel):
        """Define o canal onde os comandos de sorteio podem ser usados"""
        guild_id = str(ctx.guild.id)
        
        configs = await self.get_configuracao(guild_id)
        configs['canal_comando'] = canal.id
        success = await self.save_configuracao(guild_id, configs)
        
        if success:
            embed = discord.Embed(
                title="✅ Canal de Comando Definido",
                description=f"Os comandos de sorteio agora só podem ser usados em {canal.mention}",
                color=0x00ff7f
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar a configuração. Verifique a conexão com o banco de dados.",
                color=0xff4444
            )
        await ctx.send(embed=embed)
    
    @commands.command(name='canaldosorteio', aliases=['gwchannel'])
    @commands.has_permissions(administrator=True)
    async def canal_sorteio(self, ctx, canal: discord.TextChannel):
        """Define o canal onde os sorteios serão realizados"""
        guild_id = str(ctx.guild.id)
        
        configs = await self.get_configuracao(guild_id)
        configs['canal_sorteio'] = canal.id
        success = await self.save_configuracao(guild_id, configs)
        
        if success:
            embed = discord.Embed(
                title="✅ Canal do Sorteio Definido",
                description=f"Os sorteios serão realizados em {canal.mention}",
                color=0x00ff7f
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar a configuração. Verifique a conexão com o banco de dados.",
                color=0xff4444
            )
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Trata erros de permissão"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa ser **Administrador** para usar este comando.",
                color=0xff4444
            )
            await ctx.send(embed=embed)

    async def cog_unload(self):
        """Fecha a conexão com MongoDB quando o cog é descarregado"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB (Sorteios) fechada")

async def setup(bot):
    await bot.add_cog(Sorteio(bot))