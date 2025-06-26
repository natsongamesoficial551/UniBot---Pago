import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = os.getenv("MONGO_URI")

class Sugestoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(MONGO_URI)["sugestoes_bot"]
        
    async def get_config(self, guild_id):
        """Pega a configuração do servidor"""
        config = await self.db.config.find_one({"guild_id": str(guild_id)})
        return config
    
    @commands.command(name="config_sugestoes")
    @commands.has_permissions(manage_guild=True)
    async def config_sugestoes(self, ctx, canal: discord.TextChannel = None):
        """Define o canal de sugestões do servidor"""
        if canal is None:
            canal = ctx.channel
            
        await self.db.config.update_one(
            {"guild_id": str(ctx.guild.id)},
            {"$set": {
                "guild_id": str(ctx.guild.id),
                "canal_sugestoes": canal.id,
                "canal_nome": canal.name
            }},
            upsert=True
        )
        
        embed = discord.Embed(
            title="⚙️ Configuração Atualizada",
            description=f"Canal de sugestões definido como {canal.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="sugerir")
    async def sugerir(self, ctx, *, sugestao):
        """Enviar uma nova sugestão"""
        if len(sugestao) > 1000:
            return await ctx.send("❌ Sugestão muito longa! Máximo 1000 caracteres.")
            
        config = await self.get_config(ctx.guild.id)
        
        if not config:
            return await ctx.send("❌ Canal de sugestões não configurado! Use `config_sugestoes` primeiro.")
            
        canal = self.bot.get_channel(config["canal_sugestoes"])
        if not canal:
            return await ctx.send("❌ Canal de sugestões não encontrado!")
            
        # Verifica se já não enviou sugestão recentemente (cooldown)
        ultima = await self.db.sugestoes.find_one({
            "guild_id": str(ctx.guild.id),
            "user_id": str(ctx.author.id)
        }, sort=[("_id", -1)])
        
        embed = discord.Embed(
            title="📢 Nova Sugestão",
            description=sugestao,
            color=discord.Color.blue()
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"ID: {ctx.author.id}")
        
        try:
            mensagem = await canal.send(embed=embed)
            await mensagem.add_reaction("👍")
            await mensagem.add_reaction("👎")
            
            await self.db.sugestoes.insert_one({
                "guild_id": str(ctx.guild.id),
                "user_id": str(ctx.author.id),
                "user": str(ctx.author),
                "mensagem": sugestao,
                "mensagem_id": mensagem.id,
                "canal_id": canal.id,
                "status": "pendente"
            })
            
            await ctx.send("✅ Sugestão enviada com sucesso!")
            await ctx.message.delete()
            
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para enviar mensagens no canal de sugestões!")
    
    @commands.command(name="ver_sugestoes")
    async def ver_sugestoes(self, ctx, usuario: discord.Member = None):
        """Ver sugestões do servidor ou de um usuário específico"""
        filtro = {"guild_id": str(ctx.guild.id)}
        if usuario:
            filtro["user_id"] = str(usuario.id)
            
        sugestoes = self.db.sugestoes.find(filtro).sort("_id", -1).limit(10)
        
        embed = discord.Embed(
            title=f"📬 Últimas Sugestões{f' de {usuario.display_name}' if usuario else ''}",
            color=discord.Color.blurple()
        )
        
        count = 0
        async for s in sugestoes:
            count += 1
            status_emoji = {"pendente": "⏳", "aprovada": "✅", "rejeitada": "❌"}.get(s.get("status", "pendente"), "⏳")
            embed.add_field(
                name=f"{status_emoji} {s['user'][:20]}...",
                value=s["mensagem"][:100] + ("..." if len(s["mensagem"]) > 100 else ""),
                inline=False
            )
            
        if count == 0:
            embed.description = "Nenhuma sugestão encontrada."
            
        await ctx.send(embed=embed)
    
    @commands.command(name="aprovar")
    @commands.has_permissions(manage_messages=True)
    async def aprovar(self, ctx, mensagem_id: int):
        """Aprovar uma sugestão pelo ID da mensagem"""
        sugestao = await self.db.sugestoes.find_one({
            "guild_id": str(ctx.guild.id),
            "mensagem_id": mensagem_id
        })
        
        if not sugestao:
            return await ctx.send("❌ Sugestão não encontrada!")
            
        await self.db.sugestoes.update_one(
            {"_id": sugestao["_id"]},
            {"$set": {"status": "aprovada"}}
        )
        
        # Atualiza a mensagem original
        try:
            canal = self.bot.get_channel(sugestao["canal_id"])
            mensagem = await canal.fetch_message(mensagem_id)
            
            embed = mensagem.embeds[0]
            embed.color = discord.Color.green()
            embed.title = "✅ Sugestão Aprovada"
            
            await mensagem.edit(embed=embed)
            await ctx.send("✅ Sugestão aprovada!")
            
        except:
            await ctx.send("✅ Sugestão marcada como aprovada, mas não foi possível atualizar a mensagem.")
    
    @commands.command(name="rejeitar")
    @commands.has_permissions(manage_messages=True)
    async def rejeitar(self, ctx, mensagem_id: int, *, motivo="Sem motivo especificado"):
        """Rejeitar uma sugestão pelo ID da mensagem"""
        sugestao = await self.db.sugestoes.find_one({
            "guild_id": str(ctx.guild.id),
            "mensagem_id": mensagem_id
        })
        
        if not sugestao:
            return await ctx.send("❌ Sugestão não encontrada!")
            
        await self.db.sugestoes.update_one(
            {"_id": sugestao["_id"]},
            {"$set": {"status": "rejeitada", "motivo": motivo}}
        )
        
        # Atualiza a mensagem original
        try:
            canal = self.bot.get_channel(sugestao["canal_id"])
            mensagem = await canal.fetch_message(mensagem_id)
            
            embed = mensagem.embeds[0]
            embed.color = discord.Color.red()
            embed.title = "❌ Sugestão Rejeitada"
            if len(motivo) <= 100:
                embed.add_field(name="Motivo", value=motivo, inline=False)
            
            await mensagem.edit(embed=embed)
            await ctx.send("❌ Sugestão rejeitada!")
            
        except:
            await ctx.send("❌ Sugestão marcada como rejeitada, mas não foi possível atualizar a mensagem.")
    
    @commands.command(name="stats_sugestoes")
    async def stats_sugestoes(self, ctx):
        """Estatísticas das sugestões do servidor"""
        pipeline = [
            {"$match": {"guild_id": str(ctx.guild.id)}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        stats = {}
        async for result in self.db.sugestoes.aggregate(pipeline):
            stats[result["_id"]] = result["count"]
        
        total = sum(stats.values())
        
        embed = discord.Embed(
            title="📊 Estatísticas de Sugestões",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="📝 Total", value=str(total), inline=True)
        embed.add_field(name="⏳ Pendentes", value=str(stats.get("pendente", 0)), inline=True)
        embed.add_field(name="✅ Aprovadas", value=str(stats.get("aprovada", 0)), inline=True)
        embed.add_field(name="❌ Rejeitadas", value=str(stats.get("rejeitada", 0)), inline=True)
        
        if total > 0:
            aprovacao = (stats.get("aprovada", 0) / total) * 100
            embed.add_field(name="📈 Taxa de Aprovação", value=f"{aprovacao:.1f}%", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="limpar_sugestoes")
    @commands.has_permissions(administrator=True)
    async def limpar_sugestoes(self, ctx):
        """Limpar todas as sugestões do servidor (CUIDADO!)"""
        embed = discord.Embed(
            title="⚠️ Confirmação Necessária",
            description="Tem certeza que quer limpar TODAS as sugestões? Digite `confirmar` em 30s",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "confirmar"
        
        try:
            await self.bot.wait_for('message', check=check, timeout=30.0)
            result = await self.db.sugestoes.delete_many({"guild_id": str(ctx.guild.id)})
            await ctx.send(f"🗑️ {result.deleted_count} sugestões foram removidas!")
        except:
            await ctx.send("❌ Operação cancelada.")
    
    @commands.command(name="help_sugestoes")
    async def help_sugestoes(self, ctx):
        """Mostra todos os comandos de sugestões"""
        embed = discord.Embed(
            title="📋 Comandos de Sugestões",
            color=discord.Color.blue()
        )
        
        comandos = [
            ("config_sugestoes [#canal]", "Define canal de sugestões (Admin)"),
            ("sugerir <texto>", "Enviar nova sugestão"),
            ("ver_sugestoes [@user]", "Ver sugestões do servidor/usuário"),
            ("aprovar <id>", "Aprovar sugestão (Mod)"),
            ("rejeitar <id> [motivo]", "Rejeitar sugestão (Mod)"),
            ("stats_sugestoes", "Ver estatísticas"),
            ("limpar_sugestoes", "Limpar todas (Admin)"),
            ("help_sugestoes", "Mostra esta ajuda")
        ]
        
        for cmd, desc in comandos:
            embed.add_field(name=f"`{cmd}`", value=desc, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Sugestoes(bot))