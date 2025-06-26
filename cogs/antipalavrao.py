import discord
from discord.ext import commands
import json
import os
import re
from motor.motor_asyncio import AsyncIOMotorClient

class Antipalavrao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "palavroes.json"  # Backup fallback
        
        # MongoDB connection
        self.client = None
        self.db = None
        self.collection = None
        self._connection_ready = False
        
        # In-memory data
        self.palavroes = []
        self.configuracoes = {
            'ativo': True,
            'deletar_mensagem': True,
            'avisar_usuario': True
        }
        
        # Initialize MongoDB connection
        self.bot.loop.create_task(self.init_database())
    
    async def init_database(self):
        """Initialize MongoDB connection"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada nas variáveis de ambiente!")
                self.load_data()
                return
            
            print("🔄 Conectando ao MongoDB...")
            self.client = AsyncIOMotorClient(mongo_uri)
            
            # Test connection
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.collection = self.db['antipalavrao']
            self._connection_ready = True
            
            print("✅ Conectado ao MongoDB com sucesso!")
            await self.load_data_from_mongodb()
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB: {e}")
            print("🔄 Usando arquivo JSON como fallback...")
            self._connection_ready = False
            self.load_data()

    async def ensure_connection(self):
        """Ensure MongoDB connection is active"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def get_guild_palavroes(self, guild_id):
        """Get guild specific words from MongoDB"""
        try:
            if not await self.ensure_connection():
                return self.palavroes
                
            doc = await self.collection.find_one({"guild_id": str(guild_id)})
            if doc and 'palavroes' in doc:
                return doc['palavroes']
            return self.palavroes
            
        except Exception as e:
            print(f"❌ Erro ao buscar palavrões: {e}")
            return self.palavroes

    async def save_guild_palavroes(self, guild_id, palavroes_list):
        """Save guild specific words to MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
            
            await self.collection.update_one(
                {"guild_id": str(guild_id)},
                {"$set": {"palavroes": palavroes_list}},
                upsert=True
            )
            return True
                
        except Exception as e:
            print(f"❌ Erro ao salvar palavrões: {e}")
            return False

    async def get_guild_config(self, guild_id):
        """Get guild configuration from MongoDB"""
        try:
            if not await self.ensure_connection():
                return {}
                
            config = await self.collection.find_one({"guild_id": str(guild_id)})
            return config.get('config', {}) if config else {}
            
        except Exception as e:
            print(f"❌ Erro ao buscar configuração: {e}")
            return {}

    async def set_guild_config(self, guild_id, key, value):
        """Set guild configuration in MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
            
            guild_id = str(guild_id)
            
            await self.collection.update_one(
                {"guild_id": guild_id},
                {"$set": {f"config.{key}": value}},
                upsert=True
            )
            
            return True
                
        except Exception as e:
            print(f"❌ Erro ao salvar configuração: {e}")
            return False
    
    async def load_data_from_mongodb(self):
        """Load data from MongoDB"""
        try:
            # Load global config
            config_doc = await self.collection.find_one({"type": "global_config"})
            if config_doc:
                self.configuracoes = config_doc.get('configuracoes', {
                    'ativo': True,
                    'deletar_mensagem': True,
                    'avisar_usuario': True
                })
            
            # Load global word list
            palavroes_doc = await self.collection.find_one({"type": "global_palavroes"})
            if palavroes_doc:
                self.palavroes = palavroes_doc.get('lista', [])
            
            print(f"📊 Carregados {len(self.palavroes)} palavrões do MongoDB")
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados do MongoDB: {e}")
            self.load_data()
    
    async def save_data_to_mongodb(self):
        """Save data to MongoDB"""
        try:
            if not await self.ensure_connection():
                self.save_data()
                return
            
            # Save global config
            await self.collection.replace_one(
                {"type": "global_config"},
                {
                    "type": "global_config",
                    "configuracoes": self.configuracoes
                },
                upsert=True
            )
            
            # Save global word list
            await self.collection.replace_one(
                {"type": "global_palavroes"},
                {
                    "type": "global_palavroes",
                    "lista": self.palavroes
                },
                upsert=True
            )
            
        except Exception as e:
            print(f"❌ Erro ao salvar no MongoDB: {e}")
            self.save_data()
    
    def load_data(self):
        """Load data from JSON file fallback"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.palavroes = data.get('palavroes', [])
                self.configuracoes = data.get('configuracoes', {
                    'ativo': True,
                    'deletar_mensagem': True,
                    'avisar_usuario': True
                })
        else:
            self.palavroes = []
            self.configuracoes = {
                'ativo': True,
                'deletar_mensagem': True,
                'avisar_usuario': True
            }
            self.save_data()
    
    def save_data(self):
        """Save data to JSON file fallback"""
        data = {
            'palavroes': self.palavroes,
            'configuracoes': self.configuracoes
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @commands.command(name='adicionarpalavrao', aliases=['addword'])
    @commands.has_permissions(manage_messages=True)
    async def adicionar_palavrao(self, ctx, *, palavra):
        """Add a word to the profanity list"""
        palavra = palavra.lower().strip()
        
        if not palavra:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar uma palavra.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        guild_palavroes = await self.get_guild_palavroes(ctx.guild.id)
        
        if palavra in guild_palavroes:
            embed = discord.Embed(
                title="⚠️ Palavra Já Existe",
                description=f"A palavra `{palavra}` já está na lista de palavrões.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        guild_palavroes.append(palavra)
        await self.save_guild_palavroes(ctx.guild.id, guild_palavroes)
        
        # Update global list if not there
        if palavra not in self.palavroes:
            self.palavroes.append(palavra)
            await self.save_data_to_mongodb()
        
        embed = discord.Embed(
            title="🚫 Palavra Adicionada",
            description=f"A palavra `{palavra}` foi adicionada à lista de palavrões.",
            color=0x00ff7f
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='removerpalavrao', aliases=['rmword'])
    @commands.has_permissions(manage_messages=True)
    async def remover_palavrao(self, ctx, *, palavra):
        """Remove a word from the profanity list"""
        palavra = palavra.lower().strip()
        
        if not palavra:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar uma palavra.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        guild_palavroes = await self.get_guild_palavroes(ctx.guild.id)
        
        if palavra not in guild_palavroes:
            embed = discord.Embed(
                title="❓ Palavra Não Encontrada",
                description=f"A palavra `{palavra}` não está na lista de palavrões.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        guild_palavroes.remove(palavra)
        await self.save_guild_palavroes(ctx.guild.id, guild_palavroes)
        
        embed = discord.Embed(
            title="✅ Palavra Removida",
            description=f"A palavra `{palavra}` foi removida da lista de palavrões.",
            color=0x00ff7f
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='palavroes', aliases=['listwords'])
    @commands.has_permissions(manage_messages=True)
    async def listar_palavroes(self, ctx):
        """List all registered profanity words"""
        guild_palavroes = await self.get_guild_palavroes(ctx.guild.id)
        
        if not guild_palavroes:
            embed = discord.Embed(
                title="📝 Lista de Palavrões",
                description="Nenhuma palavra cadastrada ainda.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Organize in pages if too many words
        palavras_por_pagina = 20
        total_paginas = (len(guild_palavroes) + palavras_por_pagina - 1) // palavras_por_pagina
        
        # First page
        pagina_atual = 1
        inicio = 0
        fim = min(palavras_por_pagina, len(guild_palavroes))
        
        palavras_formatadas = []
        for i, palavra in enumerate(guild_palavroes[inicio:fim], 1):
            palavras_formatadas.append(f"`{i + inicio}.` {palavra}")
        
        embed = discord.Embed(
            title="🚫 Lista de Palavrões",
            description="\n".join(palavras_formatadas),
            color=0xff6666
        )
        
        if total_paginas > 1:
            embed.set_footer(text=f"Página {pagina_atual}/{total_paginas} • Total: {len(guild_palavroes)} palavras")
        else:
            embed.set_footer(text=f"Total: {len(guild_palavroes)} palavras")
        
        status = "🟢 Ativo" if self.configuracoes['ativo'] else "🔴 Inativo"
        embed.add_field(name="Status", value=status, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='togglefiltro', aliases=['toggle'])
    @commands.has_permissions(manage_messages=True)
    async def toggle_filtro(self, ctx):
        """Toggle profanity filter on/off"""
        self.configuracoes['ativo'] = not self.configuracoes['ativo']
        await self.save_data_to_mongodb()
        
        status = "ativado" if self.configuracoes['ativo'] else "desativado"
        cor = 0x00ff7f if self.configuracoes['ativo'] else 0xff6666
        emoji = "🟢" if self.configuracoes['ativo'] else "🔴"
        
        embed = discord.Embed(
            title=f"{emoji} Filtro {status.capitalize()}",
            description=f"O filtro de palavrões foi **{status}**.",
            color=cor
        )
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Monitor messages for profanity"""
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return
        
        # Check if filter is active
        if not self.configuracoes.get('ativo', True):
            return
        
        # Ignore members with manage messages permission
        if message.author.guild_permissions.manage_messages:
            return
        
        # Get guild specific words
        guild_palavroes = await self.get_guild_palavroes(message.guild.id)
        
        # Check if message contains profanity
        conteudo = message.content.lower()
        palavrao_encontrado = None
        
        for palavrao in guild_palavroes:
            # Use regex to find word as complete word
            padrao = r'\b' + re.escape(palavrao) + r'\b'
            if re.search(padrao, conteudo):
                palavrao_encontrado = palavrao
                break
        
        if palavrao_encontrado:
            # Delete message if configured
            if self.configuracoes.get('deletar_mensagem', True):
                try:
                    await message.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass
            
            # Warn user if configured
            if self.configuracoes.get('avisar_usuario', True):
                embed = discord.Embed(
                    title="⚠️ Linguagem Inadequada",
                    description=f"{message.author.mention}, por favor mantenha um linguajar adequado no servidor.",
                    color=0xffaa00
                )
                embed.set_footer(text="Esta mensagem será removida em 10 segundos")
                
                try:
                    aviso = await message.channel.send(embed=embed)
                    await aviso.delete(delay=10)
                except discord.Forbidden:
                    pass
    
    @adicionar_palavrao.error
    @remover_palavrao.error
    @listar_palavroes.error
    @toggle_filtro.error
    async def comando_error(self, ctx, error):
        """Handle permission errors"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão **Gerenciar Mensagens** para usar este comando.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
    
    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB fechada")

async def setup(bot):
    await bot.add_cog(Antipalavrao(bot))