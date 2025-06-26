import discord
from discord.ext import commands
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import random
import json
from datetime import datetime, timedelta
import aiohttp

class FunSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.collection = None
        self._connection_ready = False
        
        # Listas para comandos de diversão
        self.piadas = [
            "Por que os passarinhos voam para o sul? Porque é muito longe para ir andando! 🐦",
            "O que a impressora falou para a outra impressora? Essa folha é sua ou é impressão minha? 🖨️",
            "Por que o livro de matemática estava triste? Porque tinha muitos problemas! 📚",
            "O que o pato disse para a pata? Vem quá! 🦆",
            "Por que os peixes não jogam tênis? Porque eles têm medo da rede! 🐟"
        ]
        
        self.frases_motivacionais = [
            "Você é mais forte do que imagina! 💪",
            "Cada dia é uma nova oportunidade! ✨",
            "Acredite em você mesmo! 🌟",
            "O sucesso é a soma de pequenos esforços! 🎯",
            "Seja a mudança que você quer ver no mundo! 🌍"
        ]
        
        self.curiosidades = [
            "Os polvos têm três corações! 🐙",
            "Uma barata pode viver por semanas sem cabeça! 🪳",
            "Os golfinhos têm nomes para uns aos outros! 🐬",
            "O coração de uma baleia azul é do tamanho de um carro! 🐋",
            "As abelhas podem reconhecer rostos humanos! 🐝"
        ]

        # Inicializa a conexão com MongoDB de forma segura
        if self.bot.loop.is_running():
            asyncio.create_task(self.init_database())
        else:
            self.bot.loop.create_task(self.init_database())

    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            
            if not mongo_uri:
                print("⚠️ MONGO_URI não encontrada - sistema funcionará sem banco de dados")
                self._connection_ready = False
                return
            
            print("🔄 Conectando ao MongoDB (Fun System)...")
            self.client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Testa a conexão
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.collection = self.db['fun_config']
            self._connection_ready = True
            
            print("✅ Fun System conectado ao MongoDB!")
            
        except Exception as e:
            print(f"⚠️ MongoDB indisponível (Fun): {e}")
            print("ℹ️ Sistema funcionará sem persistência de dados")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def get_user_data(self, user_id, guild_id):
        """Obtém dados do usuário do MongoDB"""
        try:
            if not await self.ensure_connection():
                return {}
                
            data = await self.collection.find_one({
                "user_id": str(user_id),
                "guild_id": str(guild_id)
            })
            return data.get('data', {}) if data else {}
            
        except Exception as e:
            print(f"❌ Erro ao buscar dados do usuário: {e}")
            return {}

    async def update_user_data(self, user_id, guild_id, key, value):
        """Atualiza dados do usuário no MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
            
            await self.collection.update_one(
                {"user_id": str(user_id), "guild_id": str(guild_id)},
                {"$set": {f"data.{key}": value}},
                upsert=True
            )
            return True
                
        except Exception as e:
            print(f"❌ Erro ao atualizar dados: {e}")
            return False

    @commands.command(name='piada')
    async def piada(self, ctx):
        """Conta uma piada aleatória"""
        try:
            piada = random.choice(self.piadas)
            
            embed = discord.Embed(
                title="😂 Piada do Dia",
                description=piada,
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"Pedido por {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao contar piada: {e}")

    @commands.command(name='motivar')
    async def motivar(self, ctx, member: discord.Member = None):
        """Envia uma frase motivacional"""
        try:
            target = member or ctx.author
            frase = random.choice(self.frases_motivacionais)
            
            embed = discord.Embed(
                title="🌟 Motivação",
                description=f"{target.mention}, {frase}",
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao motivar: {e}")

    @commands.command(name='curiosidade')
    async def curiosidade(self, ctx):
        """Compartilha uma curiosidade interessante"""
        try:
            curiosidade = random.choice(self.curiosidades)
            
            embed = discord.Embed(
                title="🤔 Você Sabia?",
                description=curiosidade,
                color=discord.Color.teal()
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao compartilhar curiosidade: {e}")

    @commands.command(name='dado')
    async def dado(self, ctx, lados: int = 6):
        """Rola um dado com número especificado de lados"""
        try:
            if lados < 2 or lados > 100:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="O dado deve ter entre 2 e 100 lados!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            resultado = random.randint(1, lados)
            
            embed = discord.Embed(
                title="🎲 Resultado do Dado",
                description=f"Dado de {lados} lados: **{resultado}**",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Jogado por {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send("❌ Por favor, forneça um número válido para os lados do dado!")
        except Exception as e:
            await ctx.send(f"❌ Erro ao rolar dado: {e}")

    @commands.command(name='moeda')
    async def moeda(self, ctx):
        """Joga uma moeda"""
        try:
            resultado = random.choice(["Cara", "Coroa"])
            emoji = "🟡" if resultado == "Cara" else "⚪"
            
            embed = discord.Embed(
                title="🪙 Cara ou Coroa",
                description=f"{emoji} **{resultado}**!",
                color=discord.Color.orange()
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao jogar moeda: {e}")

    @commands.command(name='8ball')
    async def eight_ball(self, ctx, *, pergunta=None):
        """Faz uma pergunta para a bola 8"""
        try:
            if not pergunta:
                await ctx.send("❌ Você precisa fazer uma pergunta! Exemplo: `!8ball Vai chover hoje?`")
                return
                
            respostas = [
                "Sim, definitivamente!", "É certo!", "Sem dúvida!",
                "Sim, sem dúvida!", "Você pode contar com isso!",
                "Como eu vejo, sim!", "Provavelmente sim!",
                "Perspectiva boa!", "Sim!", "Os sinais apontam que sim!",
                "Resposta nebulosa, tente novamente!", "Pergunte novamente mais tarde!",
                "Melhor não te dizer agora!", "Não é possível prever agora!",
                "Concentre-se e pergunte novamente!", "Não conte com isso!",
                "Minha resposta é não!", "Minhas fontes dizem não!",
                "Perspectiva não muito boa!", "Muito duvidoso!"
            ]
            
            resposta = random.choice(respostas)
            
            embed = discord.Embed(
                title="🎱 Bola 8 Mágica",
                color=discord.Color.dark_blue()
            )
            embed.add_field(name="Pergunta:", value=pergunta, inline=False)
            embed.add_field(name="Resposta:", value=resposta, inline=False)
            embed.set_footer(text=f"Perguntado por {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro na bola 8: {e}")

    @commands.command(name='avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        """Mostra o avatar de um usuário"""
        try:
            target = member or ctx.author
            
            embed = discord.Embed(
                title=f"🖼️ Avatar de {target.display_name}",
                color=discord.Color.blurple()
            )
            embed.set_image(url=target.display_avatar.url)
            embed.add_field(
                name="Link direto:",
                value=f"[Clique aqui]({target.display_avatar.url})",
                inline=False
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao mostrar avatar: {e}")

    @commands.command(name='escolher')
    async def escolher(self, ctx, *, opcoes=None):
        """Escolhe uma opção aleatória entre as fornecidas (separadas por vírgula)"""
        try:
            if not opcoes:
                await ctx.send("❌ Forneça opções separadas por vírgula! Exemplo: `!escolher pizza, hambúrguer, sushi`")
                return
                
            lista_opcoes = [opcao.strip() for opcao in opcoes.split(',') if opcao.strip()]
            
            if len(lista_opcoes) < 2:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Forneça ao menos 2 opções separadas por vírgula!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            escolha = random.choice(lista_opcoes)
            
            embed = discord.Embed(
                title="🎯 Escolha Aleatória",
                description=f"Eu escolho: **{escolha}**",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Opções disponíveis:",
                value=", ".join(lista_opcoes),
                inline=False
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao escolher: {e}")

    @commands.command(name='rps')
    async def rock_paper_scissors(self, ctx, escolha: str = None):
        """Joga pedra, papel ou tesoura"""
        try:
            if not escolha:
                await ctx.send("❌ Escolha entre: pedra, papel ou tesoura! Exemplo: `!rps pedra`")
                return
                
            opcoes = {'pedra': '🪨', 'papel': '📄', 'tesoura': '✂️'}
            escolha = escolha.lower()
            
            if escolha not in opcoes:
                embed = discord.Embed(
                    title="❌ Opção Inválida",
                    description="Escolha entre: pedra, papel ou tesoura",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            bot_escolha = random.choice(list(opcoes.keys()))
            
            # Determinar vencedor
            if escolha == bot_escolha:
                resultado = "Empate!"
                cor = discord.Color.orange()
            elif (escolha == 'pedra' and bot_escolha == 'tesoura') or \
                 (escolha == 'papel' and bot_escolha == 'pedra') or \
                 (escolha == 'tesoura' and bot_escolha == 'papel'):
                resultado = "Você ganhou!"
                cor = discord.Color.green()
            else:
                resultado = "Eu ganhei!"
                cor = discord.Color.red()
            
            embed = discord.Embed(
                title="🎮 Pedra, Papel, Tesoura",
                description=f"**{resultado}**",
                color=cor
            )
            embed.add_field(
                name="Sua escolha:",
                value=f"{opcoes[escolha]} {escolha.title()}",
                inline=True
            )
            embed.add_field(
                name="Minha escolha:",
                value=f"{opcoes[bot_escolha]} {bot_escolha.title()}",
                inline=True
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro no jogo: {e}")

    @commands.command(name='love')
    async def love_calculator(self, ctx, pessoa1: discord.Member = None, pessoa2: discord.Member = None):
        """Calcula a compatibilidade amorosa entre duas pessoas"""
        try:
            if not pessoa1 or not pessoa2:
                await ctx.send("❌ Mencione duas pessoas! Exemplo: `!love @user1 @user2`")
                return
                
            # Usar IDs para gerar um número "consistente" mas aleatório
            seed = abs(hash(f"{pessoa1.id}{pessoa2.id}")) % 101
            
            if seed < 30:
                emoji = "💔"
                descricao = "Talvez não seja o match perfeito..."
            elif seed < 60:
                emoji = "💛"
                descricao = "Há potencial aqui!"
            elif seed < 80:
                emoji = "💕"
                descricao = "Que combinação fofa!"
            else:
                emoji = "💖"
                descricao = "Match perfeito!"
            
            embed = discord.Embed(
                title="💘 Calculadora do Amor",
                description=f"{pessoa1.mention} + {pessoa2.mention}",
                color=discord.Color.magenta()
            )
            embed.add_field(
                name="Compatibilidade:",
                value=f"{emoji} **{seed}%**",
                inline=False
            )
            embed.add_field(
                name="Veredicto:",
                value=descricao,
                inline=False
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro na calculadora do amor: {e}")

    @commands.command(name='clima')
    async def clima_humor(self, ctx):
        """Verifica o clima/humor do servidor"""
        try:
            humores = [
                ("😄", "Muito Alegre", "O servidor está radiante hoje!"),
                ("😊", "Feliz", "Clima positivo por aqui!"),
                ("😐", "Neutro", "Tudo tranquilo no servidor."),
                ("😴", "Sonolento", "Parece que todos estão com sono..."),
                ("🤔", "Pensativo", "Pessoal está refletindo hoje."),
                ("🎉", "Festivo", "Hora de comemorar!")
            ]
            
            emoji, humor, descricao = random.choice(humores)
            
            embed = discord.Embed(
                title="🌡️ Clima do Servidor",
                description=f"{emoji} **{humor}**\n{descricao}",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Membros Online:",
                value=len([m for m in ctx.guild.members if m.status != discord.Status.offline]),
                inline=True
            )
            embed.add_field(
                name="Total de Membros:",
                value=ctx.guild.member_count,
                inline=True
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao verificar clima: {e}")

    @commands.command(name='pergunta')
    async def pergunta_aleatoria(self, ctx):
        """Faz uma pergunta aleatória para animar a conversa"""
        try:
            perguntas = [
                "Se você pudesse ter qualquer superpoder, qual seria?",
                "Qual é sua comida favorita?",
                "Se você pudesse viajar para qualquer lugar, onde iria?",
                "Qual é seu filme favorito?",
                "Se você pudesse encontrar qualquer pessoa, quem seria?",
                "Qual é sua cor favorita e por quê?",
                "Se você pudesse aprender qualquer habilidade, qual seria?",
                "Qual é seu animal favorito?",
                "Se você pudesse mudar uma coisa no mundo, o que seria?",
                "Qual é sua música favorita no momento?"
            ]
            
            pergunta = random.choice(perguntas)
            
            embed = discord.Embed(
                title="❓ Pergunta Aleatória",
                description=pergunta,
                color=discord.Color.purple()
            )
            embed.set_footer(text="Responda e mantenha a conversa viva!")
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao fazer pergunta: {e}")

    @commands.command(name='helpfun', aliases=['ajudafun'])
    async def help_fun(self, ctx):
        """Mostra todos os comandos de diversão disponíveis"""
        try:
            embed = discord.Embed(
                title="🎮 Sistema de Diversão - Comandos",
                description="Lista completa de comandos para se divertir!",
                color=0x7289DA  # Discord blurple
            )
            
            embed.add_field(
                name="😂 Humor & Entretenimento",
                value="`!piada` - Conta uma piada\n`!curiosidade` - Compartilha curiosidade\n`!pergunta` - Pergunta aleatória",
                inline=False
            )
            
            embed.add_field(
                name="🎲 Jogos & Sorteios",
                value="`!dado [lados]` - Rola um dado\n`!moeda` - Cara ou coroa\n`!rps <opção>` - Pedra, papel, tesoura\n`!escolher <opções>` - Escolhe entre opções",
                inline=False
            )
            
            embed.add_field(
                name="🔮 Diversão Social",
                value="`!8ball <pergunta>` - Bola 8 mágica\n`!love @user1 @user2` - Calculadora do amor\n`!motivar [@usuário]` - Frase motivacional",
                inline=False
            )
            
            embed.add_field(
                name="👤 Perfil & Servidor",
                value="`!avatar [@usuário]` - Mostra avatar\n`!clima` - Clima do servidor",
                inline=False
            )
            
            embed.set_footer(text="Use os comandos para animar seu servidor! 🎉")
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao mostrar ajuda: {e}")

    async def cog_unload(self):
        """Fecha a conexão com MongoDB quando o cog é descarregado"""
        if self.client:
            self.client.close()
            print("🔌 Conexão Fun System com MongoDB fechada")

# Função para carregar o cog
async def setup(bot):
    await bot.add_cog(FunSystem(bot))