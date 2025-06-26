import random
import discord
from discord.ext import commands

class RoleplaySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='roleplay', aliases=['rp'])
    async def roleplay_help(self, ctx):
        """Mostra todos os comandos de roleplay disponíveis"""
        embed = discord.Embed(
            title="🎭 Sistema de Roleplay",
            description="Comandos de interação disponíveis:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="💕 Ações Carinhosas",
            value="`!abracar @usuário` - Abraçar alguém\n`!beijar @usuário` - Beijar alguém\n`!cafune @usuário` - Fazer cafuné",
            inline=False
        )
        
        embed.add_field(
            name="🤝 Ações Sociais", 
            value="`!tocaaqui @usuário` - Cumprimentar\n`!dancar @usuário` - Dançar junto",
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Ações de Combate",
            value="`!bofetada @usuário` - Dar uma bofetada\n`!atacar @usuário` - Atacar (com dano aleatório)",
            inline=False
        )
        
        embed.set_footer(text="Mencione um usuário para interagir!")
        await ctx.send(embed=embed)

    @commands.command(name='abracar', aliases=['hug', 'abraço'])
    async def abracar(self, ctx, member: discord.Member = None):
        """Abraça um usuário mencionado"""
        if member is None:
            embed = discord.Embed(
                title="❌ Usuário Necessário",
                description="Você precisa mencionar um usuário para abraçar!\n**Exemplo:** `!abracar @usuário`",
                color=discord.Color.red()
            )
        elif member == ctx.author:
            embed = discord.Embed(
                title="🤗 Auto-Abraço",
                description=f"{ctx.author.mention} se abraçou! Que fofo!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="🤗 Abraço Carinhoso",
                description=f"{ctx.author.mention} abraçou {member.mention} com muito carinho! 💕",
                color=discord.Color.green()
            )
        await ctx.send(embed=embed)

    @commands.command(name='beijar', aliases=['kiss', 'beijo'])
    async def beijar(self, ctx, member: discord.Member = None):
        """Beija um usuário mencionado"""
        if member is None:
            embed = discord.Embed(
                title="❌ Usuário Necessário",
                description="Você precisa mencionar um usuário para beijar!\n**Exemplo:** `!beijar @usuário`",
                color=discord.Color.red()
            )
        elif member == ctx.author:
            embed = discord.Embed(
                title="😘 Auto-Beijo",
                description=f"{ctx.author.mention} beijou o próprio reflexo! Narcisista!",
                color=discord.Color.pink()
            )
        else:
            embed = discord.Embed(
                title="😘 Beijo Apaixonado",
                description=f"{ctx.author.mention} beijou {member.mention} com muito afeto! 💋",
                color=discord.Color.pink()
            )
        await ctx.send(embed=embed)

    @commands.command(name='bofetada', aliases=['slap', 'tapa'])
    async def bofetada(self, ctx, member: discord.Member = None):
        """Dá uma bofetada em um usuário mencionado"""
        if member is None:
            embed = discord.Embed(
                title="❌ Usuário Necessário",
                description="Você precisa mencionar um usuário para dar uma bofetada!\n**Exemplo:** `!bofetada @usuário`",
                color=discord.Color.red()
            )
        elif member == ctx.author:
            embed = discord.Embed(
                title="🤦 Auto-Bofetada",
                description=f"{ctx.author.mention} se deu uma bofetada! Isso deve ter doído...",
                color=discord.Color.dark_red()
            )
        else:
            embed = discord.Embed(
                title="👋 Bofetada Sonora",
                description=f"{ctx.author.mention} deu uma bofetada em {member.mention}! **TAPA!** 💥",
                color=discord.Color.dark_red()
            )
        await ctx.send(embed=embed)

    @commands.command(name='cafune', aliases=['headpat', 'pat'])
    async def cafune(self, ctx, member: discord.Member = None):
        """Faz cafuné em um usuário mencionado"""
        if member is None:
            embed = discord.Embed(
                title="❌ Usuário Necessário",
                description="Você precisa mencionar um usuário para fazer cafuné!\n**Exemplo:** `!cafune @usuário`",
                color=discord.Color.red()
            )
        elif member == ctx.author:
            embed = discord.Embed(
                title="😌 Auto-Cafuné",
                description=f"{ctx.author.mention} fez cafuné em si mesmo! Que relaxante!",
                color=discord.Color.purple()
            )
        else:
            embed = discord.Embed(
                title="😌 Cafuné Relaxante",
                description=f"{ctx.author.mention} fez um cafuné carinhoso em {member.mention}! Que delicadeza! ✨",
                color=discord.Color.purple()
            )
        await ctx.send(embed=embed)

    @commands.command(name='tocaaqui', aliases=['highfive', 'hifive'])
    async def tocaaqui(self, ctx, member: discord.Member = None):
        """Cumprimenta um usuário com toca aqui"""
        if member is None:
            embed = discord.Embed(
                title="❌ Usuário Necessário",
                description="Você precisa mencionar um usuário para o toca aqui!\n**Exemplo:** `!tocaaqui @usuário`",
                color=discord.Color.red()
            )
        elif member == ctx.author:
            embed = discord.Embed(
                title="🙌 Auto-Cumprimento",
                description=f"{ctx.author.mention} bateu palmas sozinho! Estranho, mas ok!",
                color=discord.Color.gold()
            )
        else:
            embed = discord.Embed(
                title="🙌 Toca Aqui!",
                description=f"{ctx.author.mention} cumprimentou {member.mention} com um toca aqui! **High Five!** ⚡",
                color=discord.Color.gold()
            )
        await ctx.send(embed=embed)

    @commands.command(name='atacar', aliases=['attack'])
    async def atacar(self, ctx, member: discord.Member = None):
        """Ataca um usuário mencionado causando dano aleatório"""
        if member is None:
            embed = discord.Embed(
                title="❌ Usuário Necessário",
                description="Você precisa mencionar um usuário para atacar!\n**Exemplo:** `!atacar @usuário`",
                color=discord.Color.red()
            )
        elif member == ctx.author:
            damage = random.randint(1, 50)
            embed = discord.Embed(
                title="⚔️ Auto-Ataque",
                description=f"{ctx.author.mention} se atacou causando **{damage}** pontos de dano! Confusão mental!",
                color=discord.Color.dark_gray()
            )
        else:
            damage = random.randint(1, 100)
            embed = discord.Embed(
                title="⚔️ Ataque Realizado",
                description=f"{ctx.author.mention} atacou {member.mention} causando **{damage}** pontos de dano! 💥",
                color=discord.Color.dark_gray()
            )
        await ctx.send(embed=embed)

    @commands.command(name='dancar', aliases=['dance'])
    async def dancar(self, ctx, member: discord.Member = None):
        """Dança com um usuário mencionado"""
        if member is None:
            embed = discord.Embed(
                title="❌ Usuário Necessário",
                description="Você precisa mencionar um usuário para dançar!\n**Exemplo:** `!dancar @usuário`",
                color=discord.Color.red()
            )
        elif member == ctx.author:
            embed = discord.Embed(
                title="💃 Dança Solo",
                description=f"{ctx.author.mention} dançou sozinho! Show particular!",
                color=discord.Color.magenta()
            )
        else:
            embed = discord.Embed(
                title="💃 Dança em Dupla",
                description=f"{ctx.author.mention} dançou com {member.mention} numa vibe incrível! 🎵✨",
                color=discord.Color.magenta()
            )
        await ctx.send(embed=embed)

    @commands.command(name='helproleplay')
    async def help_roleplay(self, ctx):
        """Mostra ajuda detalhada sobre o sistema de roleplay"""
        embed = discord.Embed(
            title="🎭 Sistema de Roleplay - Ajuda Completa",
            description="Sistema de interações entre usuários do servidor!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 Como Usar",
            value="Use `!comando @usuário` para interagir com outros membros do servidor.",
            inline=False
        )
        
        embed.add_field(
            name="💕 Comandos Carinhosos",
            value="• `!abracar` - Abraça com carinho\n• `!beijar` - Beija com afeto\n• `!cafune` - Faz cafuné relaxante",
            inline=True
        )
        
        embed.add_field(
            name="🤝 Comandos Sociais",
            value="• `!tocaaqui` - Cumprimento amigável\n• `!dancar` - Dança em dupla",
            inline=True
        )
        
        embed.add_field(
            name="⚔️ Comandos de Combate",
            value="• `!bofetada` - Dá uma bofetada\n• `!atacar` - Ataque com dano aleatório (1-100)",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Dicas",
            value="• Você pode usar os comandos em si mesmo\n• Alguns comandos têm aliases (atalhos)\n• Use `!roleplay` para ver lista resumida",
            inline=False
        )
        
        embed.set_footer(text="Divirta-se interagindo com outros membros! 🎉")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleplaySystem(bot))