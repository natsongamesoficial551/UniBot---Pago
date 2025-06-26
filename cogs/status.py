import discord
from discord.ext import commands, tasks
import asyncio
import random
from datetime import datetime

class StatusSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_list = [
            {"type": "playing", "text": "!ajuda | Central de Comandos"},
            {"type": "listening", "text": "música relaxante"},
            {"type": "playing", "text": "!saldo | Sistema de Economia"},
            {"type": "watching", "text": "você ganhar dinheiro"},
            {"type": "playing", "text": "!trabalhar | Ganhe recompensas"},
            {"type": "listening", "text": "comandos úteis"},
            {"type": "playing", "text": "!crime | Atividades arriscadas"},
            {"type": "watching", "text": "o servidor crescer"},
            {"type": "playing", "text": "!loteria | Tente a sorte"},
            {"type": "streaming", "text": "conteúdo ao vivo"},
            {"type": "playing", "text": "!loja | Compre itens"},
            {"type": "watching", "text": "transações do servidor"},
            {"type": "playing", "text": "!apostar | Jogos de azar"},
            {"type": "listening", "text": "playlist do servidor"},
            {"type": "playing", "text": "Sistema Econômico"},
            {"type": "playing", "text": "!diario | Recompensa diária"},
            {"type": "watching", "text": "você se divertir"},
            {"type": "listening", "text": "suas conquistas"},
            {"type": "playing", "text": "!investir | Multiplique ganhos"},
            {"type": "watching", "text": "atividade do mercado"}
        ]
        
        self.current_status_index = 0
        self.status_interval = 10
        self.status_mode = "random"  # "random" ou "sequential"
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Inicia o sistema de status quando o bot fica online"""
        print(f"📊 Sistema de Status iniciado para {self.bot.user}")
        
        if not self.change_status.is_running():
            self.change_status.start()
    
    @tasks.loop(minutes=10)
    async def change_status(self):
        """Muda status baseado no modo configurado"""
        try:
            if self.status_mode == "random":
                status_info = random.choice(self.status_list)
            else:  # sequential
                status_info = self.status_list[self.current_status_index]
                self.current_status_index = (self.current_status_index + 1) % len(self.status_list)
            
            await self._set_status(status_info)
            print(f"🔄 Status alterado: {status_info['type']} {status_info['text']}")
            
        except Exception as e:
            print(f"❌ Erro ao mudar status: {e}")
    
    async def _set_status(self, status_info):
        """Define o status do bot"""
        if status_info["type"] == "playing":
            activity = discord.Game(name=status_info["text"])
        elif status_info["type"] == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=status_info["text"])
        elif status_info["type"] == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=status_info["text"])
        elif status_info["type"] == "streaming":
            activity = discord.Streaming(name=status_info["text"], url="https://twitch.tv/exemplo")
        else:
            activity = discord.Game(name=status_info["text"])
        
        await self.bot.change_presence(status=discord.Status.online, activity=activity)
    
    @commands.command(name='statusmodo')
    @commands.has_permissions(administrator=True)
    async def set_status_mode(self, ctx, modo: str = None):
        """Altera o modo de mudança de status (random/sequential)"""
        if modo is None:
            embed = discord.Embed(
                title="📊 Modo Atual",
                description=f"Modo atual: **{self.status_mode}**",
                color=0x0099ff
            )
            embed.add_field(
                name="Modos Disponíveis",
                value="• `random` - Status aleatório\n• `sequential` - Status em sequência",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        modo = modo.lower()
        if modo not in ["random", "sequential"]:
            embed = discord.Embed(
                title="❌ Erro",
                description="Modo inválido! Use: `random` ou `sequential`",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        self.status_mode = modo
        if modo == "sequential":
            self.current_status_index = 0
        
        embed = discord.Embed(
            title="⚙️ Modo de Status Alterado",
            description=f"Novo modo: **{modo}**",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='statusintervalo')
    @commands.has_permissions(administrator=True)
    async def set_status_interval(self, ctx, minutos: int):
        """Altera o intervalo de mudança de status"""
        if minutos < 1 or minutos > 1440:
            embed = discord.Embed(
                title="❌ Erro",
                description="O intervalo deve ser entre 1 e 1440 minutos!",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        self.status_interval = minutos
        self.change_status.cancel()
        self.change_status.change_interval(minutes=minutos)
        self.change_status.start()
        
        embed = discord.Embed(
            title="⚙️ Intervalo Alterado",
            description=f"Novo intervalo: **{minutos} minutos**",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='statusmanual')
    @commands.has_permissions(administrator=True)
    async def manual_status_change(self, ctx):
        """Força uma mudança manual de status"""
        try:
            if self.status_mode == "random":
                status_info = random.choice(self.status_list)
            else:
                status_info = self.status_list[self.current_status_index]
                self.current_status_index = (self.current_status_index + 1) % len(self.status_list)
            
            await self._set_status(status_info)
            
            embed = discord.Embed(
                title="🔄 Status Alterado",
                description=f"**{status_info['text']}**",
                color=0x00ff00
            )
            
            type_emoji = {"playing": "🎮", "listening": "🎵", "watching": "👀", "streaming": "📺"}
            embed.add_field(
                name="Tipo",
                value=f"{type_emoji.get(status_info['type'], '🎮')} {status_info['type'].title()}",
                inline=True
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro",
                description=f"Erro ao alterar status: {e}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='listarstatus')
    async def list_status(self, ctx):
        """Mostra todos os status disponíveis"""
        embed = discord.Embed(
            title="📊 Lista de Status",
            description=f"**{len(self.status_list)}** status disponíveis",
            color=0x0099ff
        )
        
        status_text = ""
        for i, status in enumerate(self.status_list, 1):
            emoji = {"playing": "🎮", "listening": "🎵", "watching": "👀", "streaming": "📺"}
            status_text += f"{emoji.get(status['type'], '🎮')} {status['text']}\n"
            
            if i % 10 == 0 or i == len(self.status_list):
                embed.add_field(
                    name=f"Status {i-9 if i >= 10 else 1}-{i}",
                    value=status_text,
                    inline=False
                )
                status_text = ""
        
        embed.add_field(
            name="⚙️ Configuração",
            value=f"**Intervalo:** {self.status_interval}min\n**Modo:** {self.status_mode}",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StatusSystem(bot))