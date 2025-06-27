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
        
        # Bilingual content - Portuguese and English
        self.content = {
            'pt': {
                'jokes': [
                    "Por que os passarinhos voam para o sul? Porque é muito longe para ir andando! 🐦",
                    "O que a impressora falou para a outra impressora? Essa folha é sua ou é impressão minha? 🖨️",
                    "Por que o livro de matemática estava triste? Porque tinha muitos problemas! 📚",
                    "O que o pato disse para a pata? Vem quá! 🦆",
                    "Por que os peixes não jogam tênis? Porque eles têm medo da rede! 🐟",
                    "O que o café falou para o açúcar? Você adoça a minha vida! ☕",
                    "Por que a vaca foi para o espaço? Para ver a Via Láctea! 🐄",
                    "O que o Batman falou para o Robin antes de entrar no Batmóvel? Robin, vamos! 🦇"
                ],
                'motivational': [
                    "Você é mais forte do que imagina! 💪",
                    "Cada dia é uma nova oportunidade! ✨",
                    "Acredite em você mesmo! 🌟",
                    "O sucesso é a soma de pequenos esforços! 🎯",
                    "Seja a mudança que você quer ver no mundo! 🌍",
                    "Grandes coisas começam com pequenos passos! 👣",
                    "Você tem tudo o que precisa dentro de você! 💎",
                    "Hoje é um ótimo dia para começar algo novo! 🌅"
                ],
                'facts': [
                    "Os polvos têm três corações! 🐙",
                    "Uma barata pode viver por semanas sem cabeça! 🪳",
                    "Os golfinhos têm nomes para uns aos outros! 🐬",
                    "O coração de uma baleia azul é do tamanho de um carro! 🐋",
                    "As abelhas podem reconhecer rostos humanos! 🐝",
                    "Um raio é mais quente que a superfície do Sol! ⚡",
                    "Os flamingos são naturalmente brancos - ficam rosa pela comida! 🦩",
                    "Uma lesma pode dormir por até 3 anos! 🐌"
                ],
                'questions': [
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
                ],
                'moods': [
                    ("😄", "Muito Alegre", "O servidor está radiante hoje!"),
                    ("😊", "Feliz", "Clima positivo por aqui!"),
                    ("😐", "Neutro", "Tudo tranquilo no servidor."),
                    ("😴", "Sonolento", "Parece que todos estão com sono..."),
                    ("🤔", "Pensativo", "Pessoal está refletindo hoje."),
                    ("🎉", "Festivo", "Hora de comemorar!")
                ],
                'rps_options': {'pedra': '🪨', 'papel': '📄', 'tesoura': '✂️'},
                'coin_results': ["Cara", "Coroa"],
                'coin_emojis': {"Cara": "🟡", "Coroa": "⚪"},
                'eightball_responses': [
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
            },
            'en': {
                'jokes': [
                    "Why don't scientists trust atoms? Because they make up everything! ⚛️",
                    "What do you call a fake noodle? An impasta! 🍝",
                    "Why did the math book look so sad? Because it had too many problems! 📚",
                    "What do you call a duck that gets all A's? A wise quacker! 🦆",
                    "Why don't fish play tennis? Because they're afraid of the net! 🐟",
                    "What did the coffee say to the sugar? You make my life sweet! ☕",
                    "Why did the cow go to space? To see the Milky Way! 🐄",
                    "What's Batman's favorite part of a joke? The punchline! 🦇"
                ],
                'motivational': [
                    "You are stronger than you think! 💪",
                    "Every day is a new opportunity! ✨",
                    "Believe in yourself! 🌟",
                    "Success is the sum of small efforts! 🎯",
                    "Be the change you want to see in the world! 🌍",
                    "Great things start with small steps! 👣",
                    "You have everything you need inside you! 💎",
                    "Today is a great day to start something new! 🌅"
                ],
                'facts': [
                    "Octopuses have three hearts! 🐙",
                    "A cockroach can live for weeks without its head! 🪳",
                    "Dolphins have names for each other! 🐬",
                    "A blue whale's heart is the size of a car! 🐋",
                    "Bees can recognize human faces! 🐝",
                    "Lightning is hotter than the surface of the Sun! ⚡",
                    "Flamingos are naturally white - they turn pink from their diet! 🦩",
                    "A snail can sleep for up to 3 years! 🐌"
                ],
                'questions': [
                    "If you could have any superpower, what would it be?",
                    "What's your favorite food?",
                    "If you could travel anywhere, where would you go?",
                    "What's your favorite movie?",
                    "If you could meet anyone, who would it be?",
                    "What's your favorite color and why?",
                    "If you could learn any skill, what would it be?",
                    "What's your favorite animal?",
                    "If you could change one thing in the world, what would it be?",
                    "What's your favorite song right now?"
                ],
                'moods': [
                    ("😄", "Very Happy", "The server is glowing today!"),
                    ("😊", "Happy", "Positive vibes around here!"),
                    ("😐", "Neutral", "Everything's calm in the server."),
                    ("😴", "Sleepy", "Looks like everyone's feeling drowsy..."),
                    ("🤔", "Thoughtful", "People are reflecting today."),
                    ("🎉", "Festive", "Time to celebrate!")
                ],
                'rps_options': {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'},
                'coin_results': ["Heads", "Tails"],
                'coin_emojis': {"Heads": "🟡", "Tails": "⚪"},
                'eightball_responses': [
                    "Yes, definitely!", "It is certain!", "Without a doubt!",
                    "Yes, absolutely!", "You may rely on it!",
                    "As I see it, yes!", "Most likely!",
                    "Good outlook!", "Yes!", "Signs point to yes!",
                    "Reply hazy, try again!", "Ask again later!",
                    "Better not tell you now!", "Cannot predict now!",
                    "Concentrate and ask again!", "Don't count on it!",
                    "My reply is no!", "My sources say no!",
                    "Outlook not so good!", "Very doubtful!"
                ]
            }
        }
        
        # Language detection keywords
        self.portuguese_keywords = [
            'sim', 'não', 'obrigado', 'obrigada', 'por favor', 'desculpa',
            'oi', 'olá', 'tchau', 'bom dia', 'boa tarde', 'boa noite'
        ]

        # Initialize MongoDB connection
        if self.bot.loop.is_running():
            asyncio.create_task(self.init_database())
        else:
            self.bot.loop.create_task(self.init_database())

    async def init_database(self):
        """Initialize MongoDB connection"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            
            if not mongo_uri:
                print("⚠️ MONGO_URI not found - system will work without database")
                self._connection_ready = False
                return
            
            print("🔄 Connecting to MongoDB (Fun System)...")
            self.client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.collection = self.db['fun_config']
            self._connection_ready = True
            
            print("✅ Fun System connected to MongoDB!")
            
        except Exception as e:
            print(f"⚠️ MongoDB unavailable (Fun): {e}")
            print("ℹ️ System will work without data persistence")
            self._connection_ready = False

    async def ensure_connection(self):
        """Ensure MongoDB connection is active"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def detect_language(self, ctx, text=""):
        """Detect user's preferred language"""
        try:
            if await self.ensure_connection():
                # Check saved preference
                user_data = await self.collection.find_one({
                    "user_id": str(ctx.author.id),
                    "guild_id": str(ctx.guild.id)
                })
                if user_data and 'language' in user_data:
                    return user_data['language']
            
            # Auto-detect from message content
            text_lower = text.lower()
            portuguese_count = sum(1 for word in self.portuguese_keywords if word in text_lower)
            
            if portuguese_count > 0:
                return 'pt'
            else:
                return 'en'
                
        except Exception:
            return 'en'  # Default to English

    async def get_content(self, ctx, category, text=""):
        """Get content in appropriate language"""
        lang = await self.detect_language(ctx, text)
        return self.content[lang][category], lang

    async def save_language_preference(self, user_id, guild_id, language):
        """Save user's language preference"""
        try:
            if await self.ensure_connection():
                await self.collection.update_one(
                    {"user_id": str(user_id), "guild_id": str(guild_id)},
                    {"$set": {"language": language}},
                    upsert=True
                )
        except Exception as e:
            print(f"❌ Error saving language preference: {e}")

    @commands.command(name='setlang', aliases=['idioma'])
    async def set_language(self, ctx, lang: str = None):
        """Set your preferred language (en/pt)"""
        if not lang or lang.lower() not in ['en', 'pt', 'english', 'portuguese', 'inglês', 'português']:
            embed = discord.Embed(
                title="🌐 Language / Idioma",
                description="**English:** Use `!setlang en` or `!setlang english`\n**Português:** Use `!setlang pt` ou `!setlang português`",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        # Normalize language codes
        if lang.lower() in ['en', 'english', 'inglês']:
            lang_code = 'en'
            msg = "✅ Language set to English!"
        else:
            lang_code = 'pt'
            msg = "✅ Idioma definido como Português!"
        
        await self.save_language_preference(ctx.author.id, ctx.guild.id, lang_code)
        
        embed = discord.Embed(
            title="🌐 Language Set / Idioma Definido",
            description=msg,
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='piada', aliases=['joke'])
    async def joke(self, ctx):
        """Tell a random joke / Conta uma piada aleatória"""
        try:
            jokes, lang = await self.get_content(ctx, 'jokes')
            joke = random.choice(jokes)
            
            title = "😂 Joke of the Day" if lang == 'en' else "😂 Piada do Dia"
            footer_text = f"Requested by {ctx.author.display_name}" if lang == 'en' else f"Pedido por {ctx.author.display_name}"
            
            embed = discord.Embed(
                title=title,
                description=joke,
                color=discord.Color.gold()
            )
            embed.set_footer(text=footer_text)
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Error telling joke: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao contar piada: {e}"
            await ctx.send(error_msg)

    @commands.command(name='motivar', aliases=['motivate'])
    async def motivate(self, ctx, member: discord.Member = None):
        """Send a motivational phrase / Envia uma frase motivacional"""
        try:
            target = member or ctx.author
            phrases, lang = await self.get_content(ctx, 'motivational')
            phrase = random.choice(phrases)
            
            title = "🌟 Motivation" if lang == 'en' else "🌟 Motivação"
            
            embed = discord.Embed(
                title=title,
                description=f"{target.mention}, {phrase}",
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Error motivating: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao motivar: {e}"
            await ctx.send(error_msg)

    @commands.command(name='curiosidade', aliases=['fact'])
    async def fact(self, ctx):
        """Share an interesting fact / Compartilha uma curiosidade interessante"""
        try:
            facts, lang = await self.get_content(ctx, 'facts')
            fact = random.choice(facts)
            
            title = "🤔 Did You Know?" if lang == 'en' else "🤔 Você Sabia?"
            
            embed = discord.Embed(
                title=title,
                description=fact,
                color=discord.Color.teal()
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Error sharing fact: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao compartilhar curiosidade: {e}"
            await ctx.send(error_msg)

    @commands.command(name='dado', aliases=['dice'])
    async def dice(self, ctx, sides: int = 6):
        """Roll a dice with specified number of sides / Rola um dado com número especificado de lados"""
        try:
            lang = await self.detect_language(ctx)
            
            if sides < 2 or sides > 100:
                title = "❌ Error" if lang == 'en' else "❌ Erro"
                desc = "The dice must have between 2 and 100 sides!" if lang == 'en' else "O dado deve ter entre 2 e 100 lados!"
                
                embed = discord.Embed(title=title, description=desc, color=discord.Color.red())
                await ctx.send(embed=embed)
                return
            
            result = random.randint(1, sides)
            
            title = "🎲 Dice Result" if lang == 'en' else "🎲 Resultado do Dado"
            desc = f"{sides}-sided dice: **{result}**" if lang == 'en' else f"Dado de {sides} lados: **{result}**"
            footer = f"Rolled by {ctx.author.display_name}" if lang == 'en' else f"Jogado por {ctx.author.display_name}"
            
            embed = discord.Embed(title=title, description=desc, color=discord.Color.blue())
            embed.set_footer(text=footer)
            
            await ctx.send(embed=embed)
        except ValueError:
            error_msg = "❌ Please provide a valid number for dice sides!" if await self.detect_language(ctx) == 'en' else "❌ Por favor, forneça um número válido para os lados do dado!"
            await ctx.send(error_msg)
        except Exception as e:
            error_msg = f"❌ Error rolling dice: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao rolar dado: {e}"
            await ctx.send(error_msg)

    @commands.command(name='moeda', aliases=['coin'])
    async def coin(self, ctx):
        """Flip a coin / Joga uma moeda"""
        try:
            coin_results, lang = await self.get_content(ctx, 'coin_results')
            coin_emojis, _ = await self.get_content(ctx, 'coin_emojis')
            
            result = random.choice(coin_results)
            emoji = coin_emojis[result]
            
            title = "🪙 Heads or Tails" if lang == 'en' else "🪙 Cara ou Coroa"
            
            embed = discord.Embed(
                title=title,
                description=f"{emoji} **{result}**!",
                color=discord.Color.orange()
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Error flipping coin: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao jogar moeda: {e}"
            await ctx.send(error_msg)

    @commands.command(name='8ball')
    async def eight_ball(self, ctx, *, question=None):
        """Ask the magic 8-ball a question / Faz uma pergunta para a bola 8"""
        try:
            lang = await self.detect_language(ctx, question or "")
            
            if not question:
                error_msg = "❌ You need to ask a question! Example: `!8ball Will it rain today?`" if lang == 'en' else "❌ Você precisa fazer uma pergunta! Exemplo: `!8ball Vai chover hoje?`"
                await ctx.send(error_msg)
                return
            
            responses, _ = await self.get_content(ctx, 'eightball_responses')
            response = random.choice(responses)
            
            title = "🎱 Magic 8-Ball" if lang == 'en' else "🎱 Bola 8 Mágica"
            question_label = "Question:" if lang == 'en' else "Pergunta:"
            answer_label = "Answer:" if lang == 'en' else "Resposta:"
            footer = f"Asked by {ctx.author.display_name}" if lang == 'en' else f"Perguntado por {ctx.author.display_name}"
            
            embed = discord.Embed(title=title, color=discord.Color.dark_blue())
            embed.add_field(name=question_label, value=question, inline=False)
            embed.add_field(name=answer_label, value=response, inline=False)
            embed.set_footer(text=footer)
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ 8-ball error: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro na bola 8: {e}"
            await ctx.send(error_msg)

    @commands.command(name='avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        """Show a user's avatar / Mostra o avatar de um usuário"""
        try:
            target = member or ctx.author
            lang = await self.detect_language(ctx)
            
            title = f"🖼️ {target.display_name}'s Avatar" if lang == 'en' else f"🖼️ Avatar de {target.display_name}"
            link_text = "Direct link:" if lang == 'en' else "Link direto:"
            
            embed = discord.Embed(title=title, color=discord.Color.blurple())
            embed.set_image(url=target.display_avatar.url)
            embed.add_field(
                name=link_text,
                value=f"[Click here]({target.display_avatar.url})" if lang == 'en' else f"[Clique aqui]({target.display_avatar.url})",
                inline=False
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Error showing avatar: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao mostrar avatar: {e}"
            await ctx.send(error_msg)

    @commands.command(name='escolher', aliases=['choose'])
    async def choose(self, ctx, *, options=None):
        """Choose a random option from provided list / Escolhe uma opção aleatória entre as fornecidas"""
        try:
            lang = await self.detect_language(ctx, options or "")
            
            if not options:
                error_msg = "❌ Provide options separated by comma! Example: `!choose pizza, burger, sushi`" if lang == 'en' else "❌ Forneça opções separadas por vírgula! Exemplo: `!escolher pizza, hambúrguer, sushi`"
                await ctx.send(error_msg)
                return
            
            option_list = [option.strip() for option in options.split(',') if option.strip()]
            
            if len(option_list) < 2:
                title = "❌ Error" if lang == 'en' else "❌ Erro"
                desc = "Provide at least 2 options separated by comma!" if lang == 'en' else "Forneça ao menos 2 opções separadas por vírgula!"
                
                embed = discord.Embed(title=title, description=desc, color=discord.Color.red())
                await ctx.send(embed=embed)
                return
            
            choice = random.choice(option_list)
            
            title = "🎯 Random Choice" if lang == 'en' else "🎯 Escolha Aleatória"
            desc = f"I choose: **{choice}**" if lang == 'en' else f"Eu escolho: **{choice}**"
            options_label = "Available options:" if lang == 'en' else "Opções disponíveis:"
            
            embed = discord.Embed(title=title, description=desc, color=discord.Color.green())
            embed.add_field(name=options_label, value=", ".join(option_list), inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Error choosing: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao escolher: {e}"
            await ctx.send(error_msg)

    @commands.command(name='rps', aliases=['jokenpo'])
    async def rock_paper_scissors(self, ctx, choice: str = None):
        """Play rock, paper, scissors / Joga pedra, papel ou tesoura"""
        try:
            lang = await self.detect_language(ctx, choice or "")
            rps_options, _ = await self.get_content(ctx, 'rps_options')
            
            if not choice:
                if lang == 'en':
                    error_msg = "❌ Choose between: rock, paper or scissors! Example: `!rps rock`"
                else:
                    error_msg = "❌ Escolha entre: pedra, papel ou tesoura! Exemplo: `!rps pedra`"
                await ctx.send(error_msg)
                return
            
            choice = choice.lower()
            
            # Handle both languages
            choice_map = {
                'rock': 'rock', 'pedra': 'rock' if lang == 'en' else 'pedra',
                'paper': 'paper', 'papel': 'paper' if lang == 'en' else 'papel',
                'scissors': 'scissors', 'tesoura': 'scissors' if lang == 'en' else 'tesoura'
            }
            
            if choice not in choice_map:
                title = "❌ Invalid Option" if lang == 'en' else "❌ Opção Inválida"
                desc = "Choose between: rock, paper or scissors" if lang == 'en' else "Escolha entre: pedra, papel ou tesoura"
                
                embed = discord.Embed(title=title, description=desc, color=discord.Color.red())
                await ctx.send(embed=embed)
                return
            
            normalized_choice = choice_map[choice]
            bot_choice = random.choice(list(rps_options.keys()))
            
            # Determine winner
            if normalized_choice == bot_choice:
                result = "It's a tie!" if lang == 'en' else "Empate!"
                color = discord.Color.orange()
            elif (normalized_choice in ['rock', 'pedra'] and bot_choice in ['scissors', 'tesoura']) or \
                 (normalized_choice in ['paper', 'papel'] and bot_choice in ['rock', 'pedra']) or \
                 (normalized_choice in ['scissors', 'tesoura'] and bot_choice in ['paper', 'papel']):
                result = "You won!" if lang == 'en' else "Você ganhou!"
                color = discord.Color.green()
            else:
                result = "I won!" if lang == 'en' else "Eu ganhei!"
                color = discord.Color.red()
            
            title = "🎮 Rock, Paper, Scissors" if lang == 'en' else "🎮 Pedra, Papel, Tesoura"
            your_choice_label = "Your choice:" if lang == 'en' else "Sua escolha:"
            my_choice_label = "My choice:" if lang == 'en' else "Minha escolha:"
            
            embed = discord.Embed(title=title, description=f"**{result}**", color=color)
            embed.add_field(
                name=your_choice_label,
                value=f"{rps_options[normalized_choice]} {normalized_choice.title()}",
                inline=True
            )
            embed.add_field(
                name=my_choice_label,
                value=f"{rps_options[bot_choice]} {bot_choice.title()}",
                inline=True
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Game error: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro no jogo: {e}"
            await ctx.send(error_msg)

    @commands.command(name='love', aliases=['amor'])
    async def love_calculator(self, ctx, person1: discord.Member = None, person2: discord.Member = None):
        """Calculate love compatibility between two people / Calcula a compatibilidade amorosa entre duas pessoas"""
        try:
            lang = await self.detect_language(ctx)
            
            if not person1 or not person2:
                error_msg = "❌ Mention two people! Example: `!love @user1 @user2`" if lang == 'en' else "❌ Mencione duas pessoas! Exemplo: `!love @user1 @user2`"
                await ctx.send(error_msg)
                return
            
            # Generate consistent but random number based on user IDs
            seed = abs(hash(f"{person1.id}{person2.id}")) % 101
            
            if seed < 30:
                emoji = "💔"
                description = "Maybe not the perfect match..." if lang == 'en' else "Talvez não seja o match perfeito..."
            elif seed < 60:
                emoji = "💛"
                description = "There's potential here!" if lang == 'en' else "Há potencial aqui!"
            elif seed < 80:
                emoji = "💕"
                description = "What a cute combination!" if lang == 'en' else "Que combinação fofa!"
            else:
                emoji = "💖"
                description = "Perfect match!" if lang == 'en' else "Match perfeito!"
            
            title = "💘 Love Calculator" if lang == 'en' else "💘 Calculadora do Amor"
            compatibility_label = "Compatibility:" if lang == 'en' else "Compatibilidade:"
            verdict_label = "Verdict:" if lang == 'en' else "Veredicto:"
            
            embed = discord.Embed(
                title=title,
                description=f"{person1.mention} + {person2.mention}",
                color=discord.Color.magenta()
            )
            embed.add_field(name=compatibility_label, value=f"{emoji} **{seed}%**", inline=False)
            embed.add_field(name=verdict_label, value=description, inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Love calculator error: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro na calculadora do amor: {e}"
            await ctx.send(error_msg)

    @commands.command(name='clima', aliases=['mood'])
    async def server_mood(self, ctx):
        """Check server mood/climate / Verifica o clima/humor do servidor"""
        try:
            moods, lang = await self.get_content(ctx, 'moods')
            emoji, mood, description = random.choice(moods)
            
            title = "🌡️ Server Mood" if lang == 'en' else "🌡️ Clima do Servidor"
            online_label = "Members Online:" if lang == 'en' else "Membros Online:"
            total_label = "Total Members:" if lang == 'en' else "Total de Membros:"
            
            embed = discord.Embed(
                title=title,
                description=f"{emoji} **{mood}**\n{description}",
                color=discord.Color.blue()
            )
            embed.add_field(
                name=online_label,
                value=len([m for m in ctx.guild.members if m.status != discord.Status.offline]),
                inline=True
            )
            embed.add_field(
                name=total_label,
                value=ctx.guild.member_count,
                inline=True
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Error checking mood: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao verificar clima: {e}"
            await ctx.send(error_msg)

    @commands.command(name='pergunta', aliases=['question'])
    async def random_question(self, ctx):
        """Ask a random question to liven up the conversation / Faz uma pergunta aleatória para animar a conversa"""
        try:
            questions, lang = await self.get_content(ctx, 'questions')
            question = random.choice(questions)
            
            title = "❓ Random Question" if lang == 'en' else "❓ Pergunta Aleatória"
            footer = "Answer and keep the conversation alive!" if lang == 'en' else "Responda e mantenha a conversa viva!"
            
            embed = discord.Embed(
                title=title,
                description=question,
                color=discord.Color.purple()
            )
            embed.set_footer(text=footer)
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Error asking question: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao fazer pergunta: {e}"
            await ctx.send(error_msg)

    @commands.command(name='helpfun', aliases=['ajudafun', 'funhelp'])
    async def help_fun(self, ctx):
        """Show all available fun commands / Mostra todos os comandos de diversão disponíveis"""
        try:
            lang = await self.detect_language(ctx)
            
            if lang == 'en':
                embed = discord.Embed(
                    title="🎮 Fun System - Commands",
                    description="Complete list of commands to have fun!",
                    color=0x7289DA
                )
                
                embed.add_field(
                    name="🌐 Language",
                    value="`!setlang <en/pt>` - Set preferred language",
                    inline=False
                )
                
                embed.add_field(
                    name="😂 Humor & Entertainment",
                    value="`!joke` - Tell a joke\n`!fact` - Share interesting fact\n`!question` - Random question",
                    inline=False
                )
                
                embed.add_field(
                    name="🎲 Games & Random",
                    value="`!dice [sides]` - Roll a dice\n`!coin` - Heads or tails\n`!rps <option>` - Rock, paper, scissors\n`!choose <options>` - Choose between options",
                    inline=False
                )
                
                embed.add_field(
                    name="🔮 Social Fun",
                    value="`!8ball <question>` - Magic 8-ball\n`!love @user1 @user2` - Love calculator\n`!motivate [@user]` - Motivational phrase",
                    inline=False
                )
                
                embed.add_field(
                    name="👤 Profile & Server",
                    value="`!avatar [@user]` - Show avatar\n`!mood` - Server mood",
                    inline=False
                )
                
                embed.set_footer(text="Use commands to liven up your server! 🎉")
                
            else:  # Portuguese
                embed = discord.Embed(
                    title="🎮 Sistema de Diversão - Comandos",
                    description="Lista completa de comandos para se divertir!",
                    color=0x7289DA
                )
                
                embed.add_field(
                    name="🌐 Idioma",
                    value="`!setlang <en/pt>` - Definir idioma preferido",
                    inline=False
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
            error_msg = f"❌ Error showing help: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao mostrar ajuda: {e}"
            await ctx.send(error_msg)

    @commands.command(name='ping')
    async def ping_fun(self, ctx):
        """Check bot responsiveness / Verifica responsividade do bot"""
        try:
            lang = await self.detect_language(ctx)
            latency = round(self.bot.latency * 1000)
            
            if lang == 'en':
                title = "🏓 Pong!"
                desc = f"Bot latency: **{latency}ms**"
                status_text = "Status: Online and ready for fun! 🎉"
            else:
                title = "🏓 Pong!"
                desc = f"Latência do bot: **{latency}ms**"
                status_text = "Status: Online e pronto para diversão! 🎉"
            
            embed = discord.Embed(
                title=title,
                description=desc,
                color=discord.Color.green()
            )
            embed.add_field(name="ℹ️", value=status_text, inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Ping error: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro no ping: {e}"
            await ctx.send(error_msg)

    @commands.command(name='random', aliases=['aleatorio'])
    async def random_number(self, ctx, min_num: int = 1, max_num: int = 100):
        """Generate a random number within range / Gera um número aleatório dentro do intervalo"""
        try:
            lang = await self.detect_language(ctx)
            
            if min_num >= max_num:
                if lang == 'en':
                    error_msg = "❌ Minimum number must be less than maximum!"
                else:
                    error_msg = "❌ O número mínimo deve ser menor que o máximo!"
                await ctx.send(error_msg)
                return
            
            if abs(max_num - min_num) > 1000000:
                if lang == 'en':
                    error_msg = "❌ Range too large! Maximum difference is 1,000,000"
                else:
                    error_msg = "❌ Intervalo muito grande! Diferença máxima é 1.000.000"
                await ctx.send(error_msg)
                return
            
            result = random.randint(min_num, max_num)
            
            if lang == 'en':
                title = "🎲 Random Number"
                desc = f"Between {min_num} and {max_num}: **{result}**"
            else:
                title = "🎲 Número Aleatório"
                desc = f"Entre {min_num} e {max_num}: **{result}**"
            
            embed = discord.Embed(
                title=title,
                description=desc,
                color=discord.Color.blue()
            )
            
            await ctx.send(embed=embed)
        except ValueError:
            error_msg = "❌ Please provide valid numbers!" if await self.detect_language(ctx) == 'en' else "❌ Por favor, forneça números válidos!"
            await ctx.send(error_msg)
        except Exception as e:
            error_msg = f"❌ Error generating number: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao gerar número: {e}"
            await ctx.send(error_msg)

    @commands.command(name='stats', aliases=['estatisticas'])
    async def fun_stats(self, ctx):
        """Show fun system statistics / Mostra estatísticas do sistema de diversão"""
        try:
            lang = await self.detect_language(ctx)
            
            # Get server info
            total_members = ctx.guild.member_count
            online_members = len([m for m in ctx.guild.members if m.status != discord.Status.offline])
            bot_members = len([m for m in ctx.guild.members if m.bot])
            text_channels = len(ctx.guild.text_channels)
            voice_channels = len(ctx.guild.voice_channels)
            
            if lang == 'en':
                title = "📊 Fun System Statistics"
                server_info = "Server Information"
                system_info = "System Information"
                db_status = "✅ Connected" if self._connection_ready else "⚠️ Disconnected"
                
            else:
                title = "📊 Estatísticas do Sistema de Diversão"
                server_info = "Informações do Servidor"
                system_info = "Informações do Sistema"
                db_status = "✅ Conectado" if self._connection_ready else "⚠️ Desconectado"
            
            embed = discord.Embed(title=title, color=discord.Color.gold())
            
            # Server stats
            server_stats = f"""
👥 **Total:** {total_members}
🟢 **Online:** {online_members}
🤖 **Bots:** {bot_members}
💬 **Text Channels:** {text_channels}
🔊 **Voice Channels:** {voice_channels}
            """.strip()
            
            embed.add_field(name=f"🏠 {server_info}", value=server_stats, inline=True)
            
            # System stats
            system_stats = f"""
🗄️ **Database:** {db_status}
🎭 **Jokes:** {len(self.content['pt']['jokes'])}
💪 **Motivational:** {len(self.content['pt']['motivational'])}
🤔 **Facts:** {len(self.content['pt']['facts'])}
❓ **Questions:** {len(self.content['pt']['questions'])}
            """.strip()
            
            embed.add_field(name=f"⚙️ {system_info}", value=system_stats, inline=True)
            
            embed.set_footer(text=f"🌍 Languages: English & Português")
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"❌ Error showing stats: {e}" if await self.detect_language(ctx) == 'en' else f"❌ Erro ao mostrar estatísticas: {e}"
            await ctx.send(error_msg)

    async def cog_unload(self):
        """Close MongoDB connection when cog is unloaded / Fecha a conexão com MongoDB quando o cog é descarregado"""
        if self.client:
            self.client.close()
            print("🔌 Fun System MongoDB connection closed")

# Function to load the cog / Função para carregar o cog
async def setup(bot):
    await bot.add_cog(FunSystem(bot))