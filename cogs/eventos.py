import discord
from discord.ext import commands
import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = os.getenv("MONGO_URI")

class Eventos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(MONGO_URI)["eventos_bot"]

    async def get_config(self, guild_id):
        """Retorna configuração do servidor"""
        config = await self.db.config.find_one({"guild_id": str(guild_id)})
        return config or {}

    async def check_event_channel(self, ctx):
        """Verifica se o comando está sendo usado no canal correto"""
        config = await self.get_config(ctx.guild.id)
        event_channel = config.get("event_channel")
        
        if event_channel and str(ctx.channel.id) != event_channel:
            channel = self.bot.get_channel(int(event_channel))
            if channel:
                await ctx.send(f"⚠️ Use comandos de eventos apenas em {channel.mention}")
                return False
        return True

    @commands.command(name="configcanal")
    @commands.has_permissions(administrator=True)
    async def configcanal(self, ctx, canal: discord.TextChannel = None):
        """Define o canal para usar comandos de eventos"""
        if not canal:
            canal = ctx.channel
        
        await self.db.config.update_one(
            {"guild_id": str(ctx.guild.id)},
            {"$set": {"event_channel": str(canal.id)}},
            upsert=True
        )
        
        embed = discord.Embed(
            title="⚙️ Configuração Atualizada",
            description=f"Canal de comandos de eventos definido para {canal.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="configaviso")
    @commands.has_permissions(administrator=True)
    async def configaviso(self, ctx, canal: discord.TextChannel = None):
        """Define o canal para avisos de eventos"""
        if not canal:
            canal = ctx.channel
        
        await self.db.config.update_one(
            {"guild_id": str(ctx.guild.id)},
            {"$set": {"announce_channel": str(canal.id)}},
            upsert=True
        )
        
        embed = discord.Embed(
            title="📢 Configuração Atualizada",
            description=f"Canal de avisos de eventos definido para {canal.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="criarevento")
    @commands.has_permissions(manage_events=True)
    async def criarevento(self, ctx, data, hora, *, descricao):
        """Cria um novo evento"""
        if not await self.check_event_channel(ctx):
            return

        try:
            # Validar formato de data e hora
            datetime.datetime.strptime(f"{data} {hora}", "%d/%m/%Y %H:%M")
        except ValueError:
            embed = discord.Embed(
                title="❌ Formato Inválido",
                description="Use o formato: `dd/mm/aaaa` para data e `HH:MM` para hora",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        evento_id = str(int(datetime.datetime.now().timestamp()))
        
        await self.db.eventos.insert_one({
            "_id": evento_id,
            "guild_id": str(ctx.guild.id),
            "data": data,
            "hora": hora,
            "descricao": descricao,
            "criador": str(ctx.author.id),
            "criado_em": datetime.datetime.utcnow()
        })

        embed = discord.Embed(
            title="📅 Evento Criado",
            description=f"**Data:** {data}\n **Hora:** {hora}\n**Descrição:** {descricao}",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="ID do Evento", value=f"`{evento_id}`", inline=True)
        embed.set_footer(text=f"Criado por {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)
        
        # Anunciar no canal de avisos se configurado
        config = await self.get_config(ctx.guild.id)
        announce_channel_id = config.get("announce_channel")
        if announce_channel_id:
            announce_channel = self.bot.get_channel(int(announce_channel_id))
            if announce_channel:
                announce_embed = discord.Embed(
                    title="🎉 Novo Evento Agendado!",
                    description=f"**{descricao}**\n\n📅 **Data:** {data}\n🕐 **Hora:** {hora}",
                    color=discord.Color.blue()
                )
                announce_embed.set_footer(text="Não perca!")
                await announce_channel.send(embed=announce_embed)

    @commands.command(name="eventos")
    async def eventos(self, ctx):
        """Lista todos os eventos do servidor"""
        if not await self.check_event_channel(ctx):
            return

        eventos = self.db.eventos.find({"guild_id": str(ctx.guild.id)}).sort("data", 1)
        embed = discord.Embed(
            title="📅 Eventos Agendados",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        
        count = 0
        async for evento in eventos:
            if count >= 25:  # Limite do Discord para fields
                break
            
            embed.add_field(
                name=f"📅 {evento['data']} às {evento['hora']}",
                value=f"**{evento['descricao']}**\nID: `{evento['_id']}`",
                inline=False
            )
            count += 1

        if count == 0:
            embed.description = "Nenhum evento agendado no momento."
        else:
            embed.set_footer(text=f"Total: {count} evento(s)")

        await ctx.send(embed=embed)

    @commands.command(name="removerevento")
    @commands.has_permissions(manage_events=True)
    async def removerevento(self, ctx, evento_id):
        """Remove um evento pelo ID"""
        if not await self.check_event_channel(ctx):
            return

        evento = await self.db.eventos.find_one({"_id": evento_id, "guild_id": str(ctx.guild.id)})
        
        if not evento:
            embed = discord.Embed(
                title="❌ Evento Não Encontrado",
                description="Verifique se o ID está correto e tente novamente.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        await self.db.eventos.delete_one({"_id": evento_id, "guild_id": str(ctx.guild.id)})
        
        embed = discord.Embed(
            title="✅ Evento Removido",
            description=f"**Evento:** {evento['descricao']}\n**Data:** {evento['data']} às {evento['hora']}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="detalhesevento")
    async def detalhesevento(self, ctx, evento_id):
        """Mostra detalhes de um evento específico"""
        if not await self.check_event_channel(ctx):
            return

        evento = await self.db.eventos.find_one({"_id": evento_id, "guild_id": str(ctx.guild.id)})
        
        if not evento:
            embed = discord.Embed(
                title="❌ Evento Não Encontrado",
                description="Verifique se o ID está correto.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        criador = self.bot.get_user(int(evento['criador']))
        criador_name = criador.display_name if criador else "Usuário não encontrado"

        embed = discord.Embed(
            title="📋 Detalhes do Evento",
            description=evento['descricao'],
            color=discord.Color.blue(),
            timestamp=evento.get('criado_em', datetime.datetime.utcnow())
        )
        embed.add_field(name="📅 Data", value=evento['data'], inline=True)
        embed.add_field(name="🕐 Hora", value=evento['hora'], inline=True)
        embed.add_field(name="🆔 ID", value=f"`{evento['_id']}`", inline=True)
        embed.set_footer(text=f"Criado por {criador_name}")
        
        await ctx.send(embed=embed)

    @commands.command(name="configstatus")
    @commands.has_permissions(administrator=True)
    async def configstatus(self, ctx):
        """Mostra as configurações atuais do servidor"""
        config = await self.get_config(ctx.guild.id)
        
        embed = discord.Embed(
            title="⚙️ Configurações do Servidor",
            color=discord.Color.blue()
        )
        
        event_channel_id = config.get("event_channel")
        announce_channel_id = config.get("announce_channel")
        
        event_channel = self.bot.get_channel(int(event_channel_id)) if event_channel_id else None
        announce_channel = self.bot.get_channel(int(announce_channel_id)) if announce_channel_id else None
        
        embed.add_field(
            name="📝 Canal de Comandos",
            value=event_channel.mention if event_channel else "Não configurado",
            inline=False
        )
        embed.add_field(
            name="📢 Canal de Avisos",
            value=announce_channel.mention if announce_channel else "Não configurado",
            inline=False
        )
        
        total_eventos = await self.db.eventos.count_documents({"guild_id": str(ctx.guild.id)})
        embed.add_field(name="📊 Total de Eventos", value=str(total_eventos), inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="limparevento")
    @commands.has_permissions(administrator=True)
    async def limparevento(self, ctx):
        """Remove todos os eventos do servidor"""
        if not await self.check_event_channel(ctx):
            return

        total = await self.db.eventos.count_documents({"guild_id": str(ctx.guild.id)})
        
        if total == 0:
            embed = discord.Embed(
                title="ℹ️ Nenhum Evento",
                description="Não há eventos para remover.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        # Confirmação
        confirm_embed = discord.Embed(
            title="⚠️ Confirmação Necessária",
            description=f"Você tem certeza que deseja remover **{total}** evento(s)?\nDigite `confirmar` em 30 segundos para continuar.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=confirm_embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'confirmar'

        try:
            await self.bot.wait_for('message', check=check, timeout=30)
            
            await self.db.eventos.delete_many({"guild_id": str(ctx.guild.id)})
            
            embed = discord.Embed(
                title="✅ Eventos Removidos",
                description=f"Todos os {total} evento(s) foram removidos com sucesso.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except:
            embed = discord.Embed(
                title="⏰ Tempo Esgotado",
                description="Operação cancelada por inatividade.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Eventos(bot))