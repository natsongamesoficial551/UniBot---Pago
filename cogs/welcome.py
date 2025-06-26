import discord
from discord.ext import commands
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.collection = None
        self._connection_ready = False
        # Inicializa a conexão com MongoDB
        self.bot.loop.create_task(self.init_database())

    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            # URL de conexão do MongoDB (vem de variável de ambiente)
            mongo_uri = os.getenv("MONGO_URI")
            
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada nas variáveis de ambiente!")
                return
            
            print("🔄 Conectando ao MongoDB...")
            self.client = AsyncIOMotorClient(mongo_uri)
            
            # Testa a conexão
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.collection = self.db['welcome_config']
            self._connection_ready = True
            
            print("✅ Conectado ao MongoDB com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB: {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def get_guild_config(self, guild_id):
        """Obtém a configuração de um servidor específico do MongoDB"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível")
                return {}
                
            config = await self.collection.find_one({"guild_id": str(guild_id)})
            return config.get('config', {}) if config else {}
            
        except Exception as e:
            print(f"❌ Erro ao buscar configuração: {e}")
            return {}

    async def set_guild_config(self, guild_id, key, value):
        """Define uma configuração para um servidor específico no MongoDB"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível")
                return False
            
            guild_id = str(guild_id)
            
            # Usa upsert para criar ou atualizar
            await self.collection.update_one(
                {"guild_id": guild_id},
                {"$set": {f"config.{key}": value}},
                upsert=True
            )
            
            print(f"✅ Configuração salva: {key} = {value} para guild {guild_id}")
            return True
                
        except Exception as e:
            print(f"❌ Erro ao salvar configuração: {e}")
            return False

    @commands.command(name='canalconfig')
    @commands.has_permissions(administrator=True)
    async def canal_config(self, ctx, canal: discord.TextChannel):
        """Define o canal onde os comandos de configuração podem ser usados"""
        success = await self.set_guild_config(ctx.guild.id, 'canal_config', canal.id)
        
        if success:
            embed = discord.Embed(
                title="✅ Canal de Configuração Definido",
                description=f"Canal configurado para: {canal.mention}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar a configuração. Verifique a conexão com o banco de dados.",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

    async def check_config_channel(self, ctx):
        """Verifica se o comando está sendo usado no canal correto"""
        config = await self.get_guild_config(ctx.guild.id)
        canal_config = config.get('canal_config')
        
        if not canal_config:
            embed = discord.Embed(
                title="❌ Canal de Configuração Não Definido",
                description="Primeiro defina um canal de configuração com `!canalconfig #canal`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False
            
        if ctx.channel.id != canal_config:
            canal = self.bot.get_channel(canal_config)
            canal_mention = canal.mention if canal else f"<#{canal_config}>"
            embed = discord.Embed(
                title="❌ Canal Incorreto",
                description=f"Use este comando apenas no canal configurado: {canal_mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False
            
        return True

    @commands.command(name='canalentrada')
    @commands.has_permissions(administrator=True)
    async def canal_entrada(self, ctx, canal: discord.TextChannel):
        """Define o canal para mensagens de boas-vindas"""
        if not await self.check_config_channel(ctx):
            return

        success = await self.set_guild_config(ctx.guild.id, 'canal_entrada', canal.id)
        
        if success:
            embed = discord.Embed(
                title="✅ Canal de Entrada Definido",
                description=f"Canal de entrada configurado para: {canal.mention}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar a configuração.",
                color=discord.Color.red()
            )
            
        await ctx.send(embed=embed)

    @commands.command(name='canalsaida')
    @commands.has_permissions(administrator=True)
    async def canal_saida(self, ctx, canal: discord.TextChannel):
        """Define o canal para mensagens de despedida"""
        if not await self.check_config_channel(ctx):
            return

        success = await self.set_guild_config(ctx.guild.id, 'canal_saida', canal.id)
        
        if success:
            embed = discord.Embed(
                title="✅ Canal de Saída Definido",
                description=f"Canal de saída configurado para: {canal.mention}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar a configuração.",
                color=discord.Color.red()
            )
            
        await ctx.send(embed=embed)

    @commands.command(name='msgentrada')
    @commands.has_permissions(administrator=True)
    async def msg_entrada(self, ctx, *, mensagem):
        """Define a mensagem de boas-vindas
        
        Variáveis disponíveis:
        {user} - Menciona o usuário
        {server} - Nome do servidor
        {count} - Número de membros
        """
        if not await self.check_config_channel(ctx):
            return

        success = await self.set_guild_config(ctx.guild.id, 'msg_entrada', mensagem)
        
        if success:
            embed = discord.Embed(
                title="✅ Mensagem de Entrada Definida",
                description=f"**Mensagem:** {mensagem}\n\n**Variáveis disponíveis:**\n`{user}` - Menciona o usuário\n`{server}` - Nome do servidor\n`{count}` - Número de membros",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar a configuração.",
                color=discord.Color.red()
            )
            
        await ctx.send(embed=embed)

    @commands.command(name='msgsaida')
    @commands.has_permissions(administrator=True)
    async def msg_saida(self, ctx, *, mensagem):
        """Define a mensagem de despedida
        
        Variáveis disponíveis:
        {user} - Nome do usuário
        {server} - Nome do servidor
        {count} - Número de membros
        """
        if not await self.check_config_channel(ctx):
            return

        success = await self.set_guild_config(ctx.guild.id, 'msg_saida', mensagem)
        
        if success:
            embed = discord.Embed(
                title="✅ Mensagem de Saída Definida",
                description=f"**Mensagem:** {mensagem}\n\n**Variáveis disponíveis:**\n`{user}` - Nome do usuário\n`{server}` - Nome do servidor\n`{count}` - Número de membros",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar a configuração.",
                color=discord.Color.red()
            )
            
        await ctx.send(embed=embed)

    @commands.command(name='configmsg')
    @commands.has_permissions(administrator=True)
    async def config_msg(self, ctx):
        """Mostra a configuração atual das mensagens"""
        if not await self.check_config_channel(ctx):
            return

        config = await self.get_guild_config(ctx.guild.id)
        
        embed = discord.Embed(
            title="⚙️ Configuração das Mensagens",
            color=discord.Color.blue()
        )
        
        canal_entrada = config.get('canal_entrada')
        canal_saida = config.get('canal_saida')
        msg_entrada = config.get('msg_entrada', 'Não configurada')
        msg_saida = config.get('msg_saida', 'Não configurada')

        embed.add_field(
            name="📥 Canal de Entrada",
            value=f"<#{canal_entrada}>" if canal_entrada else "❌ Não configurado",
            inline=False
        )
        embed.add_field(
            name="📤 Canal de Saída",
            value=f"<#{canal_saida}>" if canal_saida else "❌ Não configurado",
            inline=False
        )
        embed.add_field(
            name="💬 Mensagem de Entrada",
            value=msg_entrada if msg_entrada != 'Não configurada' else "❌ Não configurada",
            inline=False
        )
        embed.add_field(
            name="👋 Mensagem de Saída",
            value=msg_saida if msg_saida != 'Não configurada' else "❌ Não configurada",
            inline=False
        )

        embed.set_footer(text="Use !testentrada e !testsaida para testar as configurações")
        await ctx.send(embed=embed)

    @commands.command(name='testentrada')
    @commands.has_permissions(administrator=True)
    async def test_entrada(self, ctx):
        """Testa a mensagem de boas-vindas"""
        if not await self.check_config_channel(ctx):
            return

        config = await self.get_guild_config(ctx.guild.id)
        canal_entrada = config.get('canal_entrada')
        msg_entrada = config.get('msg_entrada')

        if not canal_entrada or not msg_entrada:
            embed = discord.Embed(
                title="❌ Configuração Incompleta",
                description="Configure o canal de entrada e a mensagem primeiro usando:\n`!canalentrada #canal`\n`!msgentrada sua mensagem aqui`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        canal = self.bot.get_channel(canal_entrada)
        if not canal:
            embed = discord.Embed(
                title="❌ Canal Não Encontrado",
                description="O canal configurado não foi encontrado. Configure novamente com `!canalentrada`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Formatar mensagem com as variáveis
        mensagem_formatada = self.format_message(msg_entrada, ctx.author, ctx.guild)

        embed = discord.Embed(
            title="🎉 Bem-vindo(a)!",
            description=mensagem_formatada,
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Esta é uma mensagem de teste")
        
        try:
            await canal.send(embed=embed)
            embed_test = discord.Embed(
                title="✅ Teste Realizado",
                description=f"Mensagem de entrada enviada em {canal.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed_test)
        except discord.Forbidden:
            embed_error = discord.Embed(
                title="❌ Erro de Permissão",
                description=f"Não tenho permissão para enviar mensagens em {canal.mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed_error)

    @commands.command(name='testsaida')
    @commands.has_permissions(administrator=True)
    async def test_saida(self, ctx):
        """Testa a mensagem de despedida"""
        if not await self.check_config_channel(ctx):
            return

        config = await self.get_guild_config(ctx.guild.id)
        canal_saida = config.get('canal_saida')
        msg_saida = config.get('msg_saida')

        if not canal_saida or not msg_saida:
            embed = discord.Embed(
                title="❌ Configuração Incompleta",
                description="Configure o canal de saída e a mensagem primeiro usando:\n`!canalsaida #canal`\n`!msgsaida sua mensagem aqui`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        canal = self.bot.get_channel(canal_saida)
        if not canal:
            embed = discord.Embed(
                title="❌ Canal Não Encontrado",
                description="O canal configurado não foi encontrado. Configure novamente com `!canalsaida`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Formatar mensagem com as variáveis (para saída usamos str(member) ao invés de mention)
        mensagem_formatada = msg_saida.replace('{user}', str(ctx.author))
        mensagem_formatada = mensagem_formatada.replace('{server}', ctx.guild.name)
        mensagem_formatada = mensagem_formatada.replace('{count}', str(ctx.guild.member_count))

        embed = discord.Embed(
            title="👋 Até logo!",
            description=mensagem_formatada,
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Esta é uma mensagem de teste")
        
        try:
            await canal.send(embed=embed)
            embed_test = discord.Embed(
                title="✅ Teste Realizado",
                description=f"Mensagem de saída enviada em {canal.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed_test)
        except discord.Forbidden:
            embed_error = discord.Embed(
                title="❌ Erro de Permissão",
                description=f"Não tenho permissão para enviar mensagens em {canal.mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed_error)

    def format_message(self, message, member, guild):
        """Formata a mensagem substituindo as variáveis"""
        if isinstance(member, discord.Member):
            user_reference = member.mention
        else:
            user_reference = str(member)
        
        formatted = message.replace('{user}', user_reference)
        formatted = formatted.replace('{server}', guild.name)
        formatted = formatted.replace('{count}', str(guild.member_count))
        return formatted

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Evento disparado quando um membro entra no servidor"""
        try:
            config = await self.get_guild_config(member.guild.id)
            canal_entrada = config.get('canal_entrada')
            msg_entrada = config.get('msg_entrada')

            if canal_entrada and msg_entrada:
                canal = self.bot.get_channel(canal_entrada)
                if canal:
                    mensagem_formatada = self.format_message(msg_entrada, member, member.guild)

                    embed = discord.Embed(
                        title="🎉 Bem-vindo(a)!",
                        description=mensagem_formatada,
                        color=discord.Color.green()
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.timestamp = discord.utils.utcnow()
                    
                    try:
                        await canal.send(embed=embed)
                    except discord.Forbidden:
                        print(f"❌ Sem permissão para enviar mensagem de entrada no canal {canal.name} (ID: {canal.id})")
                    except Exception as e:
                        print(f"❌ Erro ao enviar mensagem de entrada: {e}")
        except Exception as e:
            print(f"❌ Erro no evento on_member_join: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Evento disparado quando um membro sai do servidor"""
        try:
            config = await self.get_guild_config(member.guild.id)
            canal_saida = config.get('canal_saida')
            msg_saida = config.get('msg_saida')

            if canal_saida and msg_saida:
                canal = self.bot.get_channel(canal_saida)
                if canal:
                    # Para saída, usamos str(member) em vez de mention
                    mensagem_formatada = msg_saida.replace('{user}', str(member))
                    mensagem_formatada = mensagem_formatada.replace('{server}', member.guild.name)
                    mensagem_formatada = mensagem_formatada.replace('{count}', str(member.guild.member_count))

                    embed = discord.Embed(
                        title="👋 Até logo!",
                        description=mensagem_formatada,
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.timestamp = discord.utils.utcnow()
                    
                    try:
                        await canal.send(embed=embed)
                    except discord.Forbidden:
                        print(f"❌ Sem permissão para enviar mensagem de saída no canal {canal.name} (ID: {canal.id})")
                    except Exception as e:
                        print(f"❌ Erro ao enviar mensagem de saída: {e}")
        except Exception as e:
            print(f"❌ Erro no evento on_member_remove: {e}")

    @commands.command(name='helpwelcome')
    async def help_welcome(self, ctx):
        """Mostra ajuda sobre os comandos do sistema de boas-vindas"""
        embed = discord.Embed(
            title="🤖 Sistema de Boas-vindas - Ajuda",
            description="Lista de comandos disponíveis:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🔧 Configuração Inicial",
            value="`!canalconfig #canal` - Define o canal para configurações",
            inline=False
        )
        
        embed.add_field(
            name="📥 Configurar Entrada",
            value="`!canalentrada #canal` - Canal para boas-vindas\n`!msgentrada mensagem` - Mensagem de boas-vindas",
            inline=False
        )
        
        embed.add_field(
            name="📤 Configurar Saída",
            value="`!canalsaida #canal` - Canal para despedidas\n`!msgsaida mensagem` - Mensagem de despedida",
            inline=False
        )
        
        embed.add_field(
            name="📋 Verificar e Testar",
            value="`!configmsg` - Ver configurações\n`!testentrada` - Testar boas-vindas\n`!testsaida` - Testar despedida",
            inline=False
        )
        
        embed.add_field(
            name="📝 Variáveis Disponíveis",
            value="`{user}` - Usuário (mention na entrada, nome na saída)\n`{server}` - Nome do servidor\n`{count}` - Número de membros",
            inline=False
        )
        
        embed.set_footer(text="Todos os comandos (exceto !helpwelcome) requerem permissão de Administrador")
        await ctx.send(embed=embed)

    @commands.command(name='statusdb')
    @commands.has_permissions(administrator=True)
    async def status_db(self, ctx):
        """Verifica o status da conexão com o banco de dados"""
        if self._connection_ready:
            try:
                # Testa a conexão fazendo um ping
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
            # Tenta reconectar
            await self.init_database()
            
        await ctx.send(embed=embed)

    async def cog_unload(self):
        """Fecha a conexão com MongoDB quando o cog é descarregado"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB fechada")

async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))