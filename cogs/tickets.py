import discord
from discord.ext import commands
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

class TicketSystem(commands.Cog):
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
            self.collection = self.db['ticket_config']
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

    @commands.command(name='ticket')
    async def ticket(self, ctx):
        config = await self.get_guild_config(ctx.guild.id)
        canal_comando = config.get('canal_comando')
        categoria_ticket = config.get('categoria_ticket')

        if not canal_comando:
            embed = discord.Embed(
                title="❌ Erro",
                description="Sistema de tickets não configurado. Configure primeiro com um administrador.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if ctx.channel.id != canal_comando:
            canal = self.bot.get_channel(canal_comando)
            embed = discord.Embed(
                title="❌ Erro",
                description=f"Use o comando !ticket apenas no canal {canal.mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if not categoria_ticket:
            embed = discord.Embed(
                title="❌ Erro",
                description="Categoria de tickets não configurada.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        categoria = discord.utils.get(ctx.guild.categories, id=categoria_ticket)
        if not categoria:
            embed = discord.Embed(
                title="❌ Erro",
                description="Categoria de tickets não encontrada.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Verificar se o usuário já tem um ticket aberto
        for channel in categoria.channels:
            if channel.name == f"ticket-{ctx.author.id}":
                embed = discord.Embed(
                    title="❌ Erro",
                    description=f"Você já tem um ticket aberto: {channel.mention}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

        # Criar o canal do ticket
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Adicionar permissões para administradores
        for member in ctx.guild.members:
            if member.guild_permissions.administrator:
                overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await ctx.guild.create_text_channel(
            name=f"ticket-{ctx.author.id}",
            category=categoria,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Ticket Criado",
            description=f"Seu ticket foi criado: {ticket_channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

        # Mensagem de boas-vindas no ticket
        embed_welcome = discord.Embed(
            title="🎫 Novo Ticket",
            description=f"Olá {ctx.author.mention}! Descreva seu problema ou dúvida aqui.\nUm administrador irá ajudá-lo em breve.",
            color=discord.Color.blue()
        )
        embed_welcome.set_footer(text="Para fechar este ticket, um administrador deve usar !fecharticket")
        await ticket_channel.send(embed=embed_welcome)

    @commands.command(name='fecharticket')
    @commands.has_permissions(administrator=True)
    async def fechar_ticket(self, ctx):
        if not ctx.channel.name.startswith('ticket-'):
            embed = discord.Embed(
                title="❌ Erro",
                description="Este comando só pode ser usado em canais de ticket.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🔒 Fechando Ticket",
            description="Este ticket será fechado em 5 segundos...",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

        await asyncio.sleep(5)
        await ctx.channel.delete()

    @commands.command(name='adicionarcategoriaticket')
    @commands.has_permissions(administrator=True)
    async def adicionar_categoria_ticket(self, ctx, categoria_id: int):
        categoria = discord.utils.get(ctx.guild.categories, id=categoria_id)
        if not categoria:
            embed = discord.Embed(
                title="❌ Erro",
                description="Categoria não encontrada. Verifique o ID da categoria.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        success = await self.set_guild_config(ctx.guild.id, 'categoria_ticket', categoria_id)
        
        if success:
            embed = discord.Embed(
                title="✅ Categoria de Ticket Definida",
                description=f"Categoria configurada para: {categoria.name}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar a configuração.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)

    @commands.command(name='canaldecomandoticket')
    @commands.has_permissions(administrator=True)
    async def canal_de_comando_ticket(self, ctx, canal: discord.TextChannel):
        success = await self.set_guild_config(ctx.guild.id, 'canal_comando', canal.id)
        
        if success:
            embed = discord.Embed(
                title="✅ Canal de Comando Definido",
                description=f"Canal de comandos configurado para: {canal.mention}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar a configuração.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)

    @commands.command(name='configticket')
    @commands.has_permissions(administrator=True)
    async def config_ticket(self, ctx):
        config = await self.get_guild_config(ctx.guild.id)
        
        embed = discord.Embed(
            title="⚙️ Configuração de Tickets",
            color=discord.Color.blue()
        )
        
        canal_comando = config.get('canal_comando')
        categoria_ticket = config.get('categoria_ticket')

        embed.add_field(
            name="Canal de Comando",
            value=f"<#{canal_comando}>" if canal_comando else "❌ Não configurado",
            inline=False
        )
        
        if categoria_ticket:
            categoria = discord.utils.get(ctx.guild.categories, id=categoria_ticket)
            categoria_nome = categoria.name if categoria else "Categoria não encontrada"
        else:
            categoria_nome = "❌ Não configurada"
            
        embed.add_field(
            name="Categoria de Tickets",
            value=categoria_nome,
            inline=False
        )

        embed.add_field(
            name="Como usar",
            value="1. Configure o canal de comando com !canaldecomandoticket\n2. Configure a categoria com !adicionarcategoriaticket\n3. Usuários podem usar !ticket no canal configurado",
            inline=False
        )

        await ctx.send(embed=embed)

    async def cog_unload(self):
        """Fecha a conexão com MongoDB quando o cog é descarregado"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB fechada")

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))