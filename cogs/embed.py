import discord
from discord.ext import commands

class AutoEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Cog AutoEmbed carregado com sucesso")

    @commands.command(name="embed")
    async def embed(self, ctx, *, mensagem: str):
        """Transforma sua mensagem em um embed estilizado"""
        if not mensagem.strip():
            await ctx.send("⚠️ Você precisa digitar uma mensagem para o embed.")
            return

        embed = discord.Embed(
            title="📢 Mensagem em destaque",
            description=mensagem,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Enviado por {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoEmbed(bot))
    print("✅ Cog AutoEmbed adicionado ao bot")
