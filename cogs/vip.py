import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VIPSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.vip_collection = None
        self.config_collection = None
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
            
            print("🔄 Conectando ao MongoDB (VIP System)...")
            self.client = AsyncIOMotorClient(mongo_uri)
            
            # Testa a conexão
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.vip_collection = self.db['vip_data']
            self.config_collection = self.db['vip_config']
            self._connection_ready = True
            
            print("✅ VIP System conectado ao MongoDB com sucesso!")
            
            # Cria índices para melhor performance
            await self.create_indexes()
            
            # Inicia loop de verificação
            if not self.check_vip_expiry.is_running():
                self.check_vip_expiry.start()
            
        except Exception as e:
            print(f"❌ Erro ao conectar VIP System com MongoDB: {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def create_indexes(self):
        """Cria índices para melhor performance"""
        try:
            # Índice para busca rápida de VIPs por usuário e servidor
            await self.vip_collection.create_index([
                ("user_id", 1),
                ("guild_id", 1)
            ])
            
            # Índice para busca por data de expiração
            await self.vip_collection.create_index([
                ("expiry", 1)
            ])
            
            # Índice para configurações por servidor
            await self.config_collection.create_index([
                ("guild_id", 1)
            ])
            
            print("📊 Índices VIP MongoDB criados com sucesso!")
        except Exception as e:
            print(f"📊 Erro ao criar índices VIP: {e}")

    async def get_vip_data(self, user_id, guild_id):
        """Obtém dados VIP de um usuário do MongoDB"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível")
                return None
                
            return await self.vip_collection.find_one({
                "user_id": str(user_id),
                "guild_id": str(guild_id)
            })
            
        except Exception as e:
            print(f"❌ Erro ao buscar dados VIP: {e}")
            return None

    async def save_vip_data(self, user_id, guild_id, expiry, added_by):
        """Salva dados VIP de um usuário no MongoDB"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível")
                return False
            
            user_id = str(user_id)
            guild_id = str(guild_id)
            
            data = {
                "user_id": user_id,
                "guild_id": guild_id,
                "expiry": expiry,
                "added_by": str(added_by),
                "added_at": datetime.now()
            }
            
            # Usa upsert para criar ou atualizar
            result = await self.vip_collection.replace_one(
                {"user_id": user_id, "guild_id": guild_id},
                data,
                upsert=True
            )
            
            print(f"✅ VIP salvo: User {user_id} - Guild {guild_id}")
            return True
                
        except Exception as e:
            print(f"❌ Erro ao salvar dados VIP: {e}")
            return False

    async def remove_vip_data(self, user_id, guild_id):
        """Remove dados VIP de um usuário do MongoDB"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível")
                return False
            
            result = await self.vip_collection.delete_one({
                "user_id": str(user_id),
                "guild_id": str(guild_id)
            })
            
            if result.deleted_count > 0:
                print(f"✅ VIP removido: User {user_id} - Guild {guild_id}")
                return True
            else:
                print(f"⚠️ VIP não encontrado para remoção: User {user_id} - Guild {guild_id}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao remover dados VIP: {e}")
            return False

    async def get_vip_config(self, guild_id):
        """Obtém configurações VIP do servidor do MongoDB"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível")
                return self.get_default_config(guild_id)
                
            config = await self.config_collection.find_one({"guild_id": str(guild_id)})
            
            if not config:
                # Configuração padrão
                default_config = self.get_default_config(guild_id)
                await self.save_vip_config(guild_id, default_config)
                print(f"📋 Configuração VIP padrão criada para Guild {guild_id}")
                return default_config
                
            return config
            
        except Exception as e:
            print(f"❌ Erro ao buscar configuração VIP: {e}")
            return self.get_default_config(guild_id)

    def get_default_config(self, guild_id):
        """Retorna configuração padrão"""
        return {
            "guild_id": str(guild_id),
            "multipliers": {
                "xp": 2.0,
                "coins": 1.5,
                "daily": 2.0
            },
            "created_at": datetime.now()
        }

    async def save_vip_config(self, guild_id, config_data):
        """Salva configurações VIP do servidor no MongoDB"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível")
                return False
            
            guild_id = str(guild_id)
            config_data["guild_id"] = guild_id
            config_data["updated_at"] = datetime.now()
            
            # Usa upsert para criar ou atualizar
            result = await self.config_collection.replace_one(
                {"guild_id": guild_id},
                config_data,
                upsert=True
            )
            
            print(f"✅ Configuração VIP salva para Guild {guild_id}")
            return True
                
        except Exception as e:
            print(f"❌ Erro ao salvar configuração VIP: {e}")
            return False

    async def get_vip_role(self, guild):
        """Obtém o cargo VIP configurado para o servidor"""
        config = await self.get_vip_config(guild.id)
        if 'vip_role_id' in config:
            role_id = config['vip_role_id']
            return guild.get_role(role_id)
        return None

    async def is_vip(self, user_id, guild_id):
        """Verifica se um usuário é VIP"""
        vip_data = await self.get_vip_data(user_id, guild_id)
        if vip_data:
            expiry_date = vip_data['expiry']
            return datetime.now() < expiry_date
        return False

    async def get_vip_multiplier(self, guild_id, type_bonus="xp"):
        """Obtém multiplicador VIP para XP, economia, etc."""
        config = await self.get_vip_config(guild_id)
        multipliers = config.get('multipliers', {})
        return multipliers.get(type_bonus, 1.0)

    @commands.command(name='statusdbvip')
    @commands.has_permissions(administrator=True)
    async def status_db_vip(self, ctx):
        """Verifica o status da conexão com o banco de dados"""
        if self._connection_ready:
            try:
                # Testa a conexão fazendo um ping
                await self.client.admin.command('ping')
                
                # Testa operações básicas
                await self.vip_collection.find_one({})
                await self.config_collection.find_one({})
                
                embed = discord.Embed(
                    title="✅ Banco de Dados VIP Conectado",
                    description="A conexão com o MongoDB está funcionando corretamente.",
                    color=discord.Color.green()
                )
                
                # Verifica VIPs ativos
                vip_count = await self.vip_collection.count_documents({
                    "guild_id": str(ctx.guild.id),
                    "expiry": {"$gt": datetime.now()}
                })
                
                embed.add_field(
                    name="📊 Estatísticas",
                    value=f"VIPs ativos: {vip_count}",
                    inline=False
                )
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Erro na Conexão VIP",
                    description=f"Erro ao testar conexão: {str(e)}",
                    color=discord.Color.red()
                )
                self._connection_ready = False
        else:
            embed = discord.Embed(
                title="❌ Banco de Dados VIP Desconectado",
                description="A conexão com o MongoDB não está disponível. Tentando reconectar...",
                color=discord.Color.red()
            )
            # Tenta reconectar
            await self.init_database()
            
        await ctx.send(embed=embed)

    @commands.command(name='vip')
    @commands.has_permissions(administrator=True)
    async def add_vip(self, ctx, member: discord.Member, dias: int):
        """Adiciona VIP a um usuário por X dias"""
        if dias <= 0:
            embed = discord.Embed(
                title="❌ Erro",
                description="O número de dias deve ser maior que 0!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Calcula data de expiração
        expiry_date = datetime.now() + timedelta(days=dias)
        
        # Salva dados do VIP no MongoDB
        success = await self.save_vip_data(member.id, ctx.guild.id, expiry_date, ctx.author.id)
        
        if not success:
            embed = discord.Embed(
                title="❌ Erro",
                description="Falha ao salvar VIP no banco de dados!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Adiciona cargo VIP se configurado
        vip_role = await self.get_vip_role(ctx.guild)
        if vip_role:
            try:
                await member.add_roles(vip_role)
            except discord.Forbidden:
                pass

        embed = discord.Embed(
            title="✅ VIP Adicionado",
            description=f"{member.mention} agora é VIP por **{dias} dias**!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Expira em", value=expiry_date.strftime("%d/%m/%Y às %H:%M"), inline=True)
        embed.add_field(name="💾 Banco", value="Salvo com sucesso!", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name='removervip')
    @commands.has_permissions(administrator=True)
    async def remove_vip(self, ctx, member: discord.Member):
        """Remove VIP de um usuário"""
        vip_data = await self.get_vip_data(member.id, ctx.guild.id)
        
        if not vip_data:
            embed = discord.Embed(
                title="❌ Erro",
                description=f"{member.mention} não é VIP!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Remove dados do VIP do MongoDB
        success = await self.remove_vip_data(member.id, ctx.guild.id)
        
        if not success:
            embed = discord.Embed(
                title="❌ Erro",
                description="Falha ao remover VIP do banco de dados!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Remove cargo VIP se configurado
        vip_role = await self.get_vip_role(ctx.guild)
        if vip_role and vip_role in member.roles:
            try:
                await member.remove_roles(vip_role)
            except discord.Forbidden:
                pass

        embed = discord.Embed(
            title="✅ VIP Removido",
            description=f"VIP removido de {member.mention}!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='cargovip')
    @commands.has_permissions(administrator=True)
    async def set_vip_role(self, ctx, role: discord.Role):
        """Define o cargo VIP do servidor"""
        # Atualiza configuração no MongoDB
        config = await self.get_vip_config(ctx.guild.id)
        config['vip_role_id'] = role.id
        success = await self.save_vip_config(ctx.guild.id, config)

        if success:
            embed = discord.Embed(
                title="✅ Cargo VIP Definido",
                description=f"Cargo VIP definido como: {role.mention}",
                color=discord.Color.gold()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Falha ao salvar configuração no banco!",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='configvip')
    @commands.has_permissions(administrator=True)
    async def config_vip(self, ctx):
        """Mostra configurações VIP atuais"""
        config = await self.get_vip_config(ctx.guild.id)
        vip_role = await self.get_vip_role(ctx.guild)
        
        embed = discord.Embed(
            title="⚙️ Configurações VIP",
            description="Configurações atuais do sistema VIP",
            color=discord.Color.gold()
        )
        
        # Status da conexão
        status_emoji = "✅" if self._connection_ready else "❌"
        embed.add_field(
            name="💾 Banco de Dados",
            value=f"{status_emoji} {'Conectado' if self._connection_ready else 'Desconectado'}",
            inline=True
        )
        
        # Cargo VIP
        role_text = vip_role.mention if vip_role else "❌ Não configurado"
        embed.add_field(name="🎭 Cargo VIP", value=role_text, inline=True)
        
        # Multiplicadores
        multipliers = config.get('multipliers', {})
        xp_mult = multipliers.get('xp', 1.0)
        coins_mult = multipliers.get('coins', 1.0)
        daily_mult = multipliers.get('daily', 1.0)
        
        embed.add_field(
            name="📈 Multiplicadores",
            value=f"**XP:** {xp_mult}x\n**Moedas:** {coins_mult}x\n**Daily:** {daily_mult}x",
            inline=True
        )
        
        # VIPs ativos
        try:
            active_vips = await self.vip_collection.count_documents({
                "guild_id": str(ctx.guild.id),
                "expiry": {"$gt": datetime.now()}
            })
        except:
            active_vips = "Erro"
        
        embed.add_field(name="👑 VIPs Ativos", value=str(active_vips), inline=True)
        
        # Como usar
        embed.add_field(
            name="📝 Comandos Disponíveis",
            value="`!cargovip @cargo` - Definir cargo VIP\n"
                  "`!vip @user <dias>` - Adicionar VIP\n"
                  "`!removervip @user` - Remover VIP\n"
                  "`!statusdbvip` - Testar banco de dados",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='listvip')
    @commands.has_permissions(administrator=True)
    async def list_vip(self, ctx):
        """Lista todos os VIPs ativos do servidor"""
        try:
            # Busca VIPs ativos no MongoDB
            cursor = self.vip_collection.find({
                "guild_id": str(ctx.guild.id),
                "expiry": {"$gt": datetime.now()}
            }).limit(10)
            
            active_vips = []
            async for vip_data in cursor:
                user = self.bot.get_user(int(vip_data['user_id']))
                if user:
                    days_left = (vip_data['expiry'] - datetime.now()).days
                    active_vips.append(f"{user.mention} - **{days_left} dias**")
            
            if not active_vips:
                embed = discord.Embed(
                    title="👑 Lista VIP",
                    description="Nenhum VIP ativo no servidor.",
                    color=discord.Color.gold()
                )
            else:
                vip_list = "\n".join(active_vips)
                embed = discord.Embed(
                    title="👑 Lista VIP",
                    description=vip_list,
                    color=discord.Color.gold()
                )
                
                total_vips = await self.vip_collection.count_documents({
                    "guild_id": str(ctx.guild.id),
                    "expiry": {"$gt": datetime.now()}
                })
                
                if total_vips > 10:
                    embed.set_footer(text=f"Mostrando 10 de {total_vips} VIPs")
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro",
                description="Erro ao buscar VIPs no banco de dados!",
                color=discord.Color.red()
            )
            print(f"❌ Erro ao listar VIPs: {e}")
        
        await ctx.send(embed=embed)

    @commands.command(name='checkvip')
    async def check_vip(self, ctx, member: discord.Member = None):
        """Verifica status VIP de um usuário"""
        if not member:
            member = ctx.author
            
        vip_data = await self.get_vip_data(member.id, ctx.guild.id)
        
        if vip_data and datetime.now() < vip_data['expiry']:
            expiry = vip_data['expiry']
            days_left = (expiry - datetime.now()).days
            hours_left = (expiry - datetime.now()).seconds // 3600
            
            embed = discord.Embed(
                title="👑 Status VIP",
                description=f"{member.mention} é **VIP**!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Expira em", value=f"{days_left} dias e {hours_left} horas", inline=True)
            embed.add_field(name="Data de expiração", value=expiry.strftime("%d/%m/%Y às %H:%M"), inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
        else:
            embed = discord.Embed(
                title="❌ Status VIP",
                description=f"{member.mention} não é VIP.",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

    @tasks.loop(hours=1)
    async def check_vip_expiry(self):
        """Verifica VIPs expirados a cada hora"""
        try:
            if not self._connection_ready:
                return
                
            # Busca VIPs expirados no MongoDB
            expired_vips = []
            cursor = self.vip_collection.find({
                "expiry": {"$lte": datetime.now()}
            })
            
            async for vip_data in cursor:
                expired_vips.append(vip_data)
                
                # Remove cargo VIP se possível
                try:
                    guild = self.bot.get_guild(int(vip_data['guild_id']))
                    if guild:
                        member = guild.get_member(int(vip_data['user_id']))
                        vip_role = await self.get_vip_role(guild)
                        
                        if member and vip_role and vip_role in member.roles:
                            await member.remove_roles(vip_role)
                            print(f"Cargo VIP removido de {member.name} (expirado)")
                except:
                    pass  # Ignora erros de permissão
            
            # Remove VIPs expirados do MongoDB
            if expired_vips:
                result = await self.vip_collection.delete_many({
                    "expiry": {"$lte": datetime.now()}
                })
                print(f"Removidos {result.deleted_count} VIPs expirados")
                
        except Exception as e:
            print(f"❌ Erro ao verificar VIPs expirados: {e}")

    @check_vip_expiry.before_loop
    async def before_check_vip_expiry(self):
        await self.bot.wait_until_ready()

    # Métodos auxiliares para outros sistemas usarem
    async def apply_vip_bonus_xp(self, user_id, guild_id, base_xp):
        """Aplica bônus VIP no XP"""
        if await self.is_vip(user_id, guild_id):
            multiplier = await self.get_vip_multiplier(guild_id, "xp")
            return int(base_xp * multiplier)
        return base_xp

    async def apply_vip_bonus_coins(self, user_id, guild_id, base_coins):
        """Aplica bônus VIP nas moedas"""
        if await self.is_vip(user_id, guild_id):
            multiplier = await self.get_vip_multiplier(guild_id, "coins")
            return int(base_coins * multiplier)
        return base_coins

    async def apply_vip_bonus_daily(self, user_id, guild_id, base_daily):
        """Aplica bônus VIP no daily"""
        if await self.is_vip(user_id, guild_id):
            multiplier = await self.get_vip_multiplier(guild_id, "daily")
            return int(base_daily * multiplier)
        return base_daily

    # Error handlers
    @add_vip.error
    @remove_vip.error
    @set_vip_role.error
    @config_vip.error
    @status_db_vip.error
    async def vip_error_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa ser **Administrador** para usar este comando!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="❌ Erro",
                description="Usuário não encontrado!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Erro",
                description="Argumentos inválidos! Verifique o comando.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    async def cog_unload(self):
        """Cleanup quando o cog é descarregado"""
        if self.check_vip_expiry.is_running():
            self.check_vip_expiry.cancel()
        
        if self.client:
            self.client.close()
            print("🔌 Conexão VIP System com MongoDB fechada")

async def setup(bot):
    await bot.add_cog(VIPSystem(bot))