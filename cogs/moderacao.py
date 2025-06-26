import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import os
from motor.motor_asyncio import AsyncIOMotorClient

class ModerationSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.mod_data = None
        self.mod_config = None
        self._connection_ready = False
        self.bot.loop.create_task(self.init_database())
        self.check_mutes.start()

    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada!")
                return
            
            print("🔄 Conectando ao MongoDB...")
            self.client = AsyncIOMotorClient(mongo_uri)
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.mod_data = self.db['moderation_data']
            self.mod_config = self.db['moderation_config']
            self._connection_ready = True
            
            # Criar índices
            await self.mod_data.create_index("guild_id")
            await self.mod_config.create_index("guild_id")
            
            print("✅ Conectado ao MongoDB!")
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante conexão ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def get_guild_data(self, guild_id):
        """Obtém dados de moderação"""
        if not await self.ensure_connection():
            return {'guild_id': str(guild_id), 'warnings': {}, 'mutes': {}, 'logs': []}
        
        guild_id = str(guild_id)
        data = await self.mod_data.find_one({"guild_id": guild_id})
        
        if not data:
            default_data = {'guild_id': guild_id, 'warnings': {}, 'mutes': {}, 'logs': []}
            await self.mod_data.insert_one(default_data)
            return default_data
        return data

    async def save_guild_data(self, guild_id, data):
        """Salva dados de moderação"""
        if not await self.ensure_connection():
            return False
        
        guild_id = str(guild_id)
        data['guild_id'] = guild_id
        await self.mod_data.replace_one({"guild_id": guild_id}, data, upsert=True)
        return True

    async def get_guild_config(self, guild_id):
        """Obtém configurações do servidor"""
        if not await self.ensure_connection():
            return {'guild_id': str(guild_id), 'mute_role_id': None, 'log_channel_id': None, 'max_warnings': 3, 'auto_punish': True}
        
        guild_id = str(guild_id)
        config = await self.mod_config.find_one({"guild_id": guild_id})
        
        if not config:
            default_config = {'guild_id': guild_id, 'mute_role_id': None, 'log_channel_id': None, 'max_warnings': 3, 'auto_punish': True}
            await self.mod_config.insert_one(default_config)
            return default_config
        return config

    async def save_guild_config(self, guild_id, config):
        """Salva configurações"""
        if not await self.ensure_connection():
            return False
        
        guild_id = str(guild_id)
        config['guild_id'] = guild_id
        await self.mod_config.replace_one({"guild_id": guild_id}, config, upsert=True)
        return True

    async def log_action(self, guild, action, moderator, target, reason=None, duration=None):
        config = await self.get_guild_config(guild.id)
        guild_data = await self.get_guild_data(guild.id)
        
        log_entry = {
            'action': action,
            'moderator_id': moderator.id,
            'target_id': target.id,
            'reason': reason,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        guild_data['logs'].append(log_entry)
        await self.save_guild_data(guild.id, guild_data)
        
        if config['log_channel_id']:
            channel = guild.get_channel(config['log_channel_id'])
            if channel:
                embed = discord.Embed(title=f"🔨 {action.upper()}", color=discord.Color.orange())
                embed.add_field(name="Moderador", value=moderator.mention, inline=True)
                embed.add_field(name="Usuário", value=target.mention, inline=True)
                if reason:
                    embed.add_field(name="Motivo", value=reason, inline=False)
                if duration:
                    embed.add_field(name="Duração", value=duration, inline=True)
                embed.timestamp = datetime.now()
                try:
                    await channel.send(embed=embed)
                except:
                    pass

    @commands.command(name='aviso')
    @commands.has_permissions(administrator=True)
    async def warn_user(self, ctx, member: discord.Member, *, reason="Não especificado"):
        guild_data = await self.get_guild_data(ctx.guild.id)
        config = await self.get_guild_config(ctx.guild.id)
        
        user_id = str(member.id)
        if user_id not in guild_data['warnings']:
            guild_data['warnings'][user_id] = []
        
        warning = {
            'reason': reason,
            'moderator': ctx.author.id,
            'timestamp': datetime.now().isoformat()
        }
        
        guild_data['warnings'][user_id].append(warning)
        warning_count = len(guild_data['warnings'][user_id])
        await self.save_guild_data(ctx.guild.id, guild_data)
        
        embed = discord.Embed(
            title="⚠️ Aviso Aplicado",
            description=f"{member.mention} recebeu um aviso!",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Motivo", value=reason, inline=False)
        embed.add_field(name="Avisos Totais", value=f"{warning_count}/{config['max_warnings']}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, "warn", ctx.author, member, reason)
        
        # Auto punição
        if config['auto_punish'] and warning_count >= config['max_warnings']:
            try:
                mute_role = await self.get_mute_role(ctx.guild)
                if mute_role:
                    await member.add_roles(mute_role)
                    
                    mute_key = f"{ctx.guild.id}_{member.id}"
                    guild_data['mutes'][mute_key] = {
                        'expires': (datetime.now() + timedelta(hours=1)).isoformat(),
                        'reason': f"Auto-mute por {config['max_warnings']} avisos"
                    }
                    await self.save_guild_data(ctx.guild.id, guild_data)
                    
                    embed = discord.Embed(
                        title="🔇 Auto-Mute Aplicado",
                        description=f"{member.mention} foi mutado por atingir {config['max_warnings']} avisos!",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
            except:
                pass

        # DM para o usuário
        try:
            dm_embed = discord.Embed(
                title="⚠️ Você recebeu um aviso",
                description=f"**Servidor:** {ctx.guild.name}\n**Motivo:** {reason}",
                color=discord.Color.yellow()
            )
            await member.send(embed=dm_embed)
        except:
            pass

    @commands.command(name='removeraviso')
    @commands.has_permissions(administrator=True)
    async def remove_warning(self, ctx, member: discord.Member, index: int = None):
        guild_data = await self.get_guild_data(ctx.guild.id)
        user_id = str(member.id)
        
        if user_id not in guild_data['warnings'] or not guild_data['warnings'][user_id]:
            embed = discord.Embed(
                title="❌ Erro",
                description=f"{member.mention} não possui avisos!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if index is None:
            removed_warning = guild_data['warnings'][user_id].pop()
        else:
            if index < 1 or index > len(guild_data['warnings'][user_id]):
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Número do aviso inválido!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            removed_warning = guild_data['warnings'][user_id].pop(index - 1)
        
        await self.save_guild_data(ctx.guild.id, guild_data)
        
        embed = discord.Embed(
            title="✅ Aviso Removido",
            description=f"Aviso removido de {member.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Motivo Removido", value=removed_warning['reason'], inline=False)
        embed.add_field(name="Avisos Restantes", value=len(guild_data['warnings'][user_id]), inline=True)
        
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, "unwarn", ctx.author, member)

    @commands.command(name='avisos')
    @commands.has_permissions(administrator=True)
    async def list_warnings(self, ctx, member: discord.Member = None):
        guild_data = await self.get_guild_data(ctx.guild.id)
        
        if member:
            user_id = str(member.id)
            if user_id not in guild_data['warnings'] or not guild_data['warnings'][user_id]:
                embed = discord.Embed(
                    title="📋 Avisos",
                    description=f"{member.mention} não possui avisos!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"📋 Avisos de {member.display_name}",
                color=discord.Color.orange()
            )
            
            for i, warning in enumerate(guild_data['warnings'][user_id], 1):
                moderator = self.bot.get_user(warning['moderator'])
                mod_name = moderator.name if moderator else "Desconhecido"
                date = datetime.fromisoformat(warning['timestamp']).strftime("%d/%m/%Y %H:%M")
                
                embed.add_field(
                    name=f"Aviso #{i}",
                    value=f"**Motivo:** {warning['reason']}\n**Moderador:** {mod_name}\n**Data:** {date}",
                    inline=False
                )
            
            embed.set_thumbnail(url=member.display_avatar.url)
        else:
            all_warnings = []
            for user_id, warnings in guild_data['warnings'].items():
                if warnings:
                    user = ctx.guild.get_member(int(user_id))
                    if user:
                        all_warnings.append((user, len(warnings)))
            
            if not all_warnings:
                embed = discord.Embed(
                    title="📋 Avisos do Servidor",
                    description="Nenhum aviso encontrado!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            
            all_warnings.sort(key=lambda x: x[1], reverse=True)
            
            embed = discord.Embed(
                title="📋 Avisos do Servidor",
                color=discord.Color.orange()
            )
            
            warning_text = ""
            for user, count in all_warnings[:10]:
                warning_text += f"{user.mention}: **{count}** avisos\n"
            
            embed.description = warning_text
        
        await ctx.send(embed=embed)

    async def get_mute_role(self, guild):
        config = await self.get_guild_config(guild.id)
        if config['mute_role_id']:
            return guild.get_role(config['mute_role_id'])
        
        mute_role = discord.utils.get(guild.roles, name="Mutado")
        if not mute_role:
            try:
                mute_role = await guild.create_role(
                    name="Mutado",
                    color=discord.Color.dark_gray(),
                    permissions=discord.Permissions(send_messages=False, speak=False)
                )
                
                for channel in guild.channels:
                    try:
                        await channel.set_permissions(mute_role, send_messages=False, speak=False)
                    except:
                        pass
                
                config['mute_role_id'] = mute_role.id
                await self.save_guild_config(guild.id, config)
            except:
                return None
        
        return mute_role

    @commands.command(name='mutar')
    @commands.has_permissions(administrator=True)
    async def mute_user(self, ctx, member: discord.Member, tempo="30m", *, reason="Não especificado"):
        mute_role = await self.get_mute_role(ctx.guild)
        if not mute_role:
            embed = discord.Embed(title="❌ Erro", description="Erro ao criar cargo de mute!", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        
        duration = self.parse_duration(tempo)
        if not duration:
            embed = discord.Embed(title="❌ Erro", description="Formato inválido! Use: 30s, 5m, 2h, 1d", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        
        try:
            await member.add_roles(mute_role)
            
            guild_data = await self.get_guild_data(ctx.guild.id)
            mute_key = f"{ctx.guild.id}_{member.id}"
            guild_data['mutes'][mute_key] = {
                'expires': (datetime.now() + duration).isoformat(),
                'reason': reason
            }
            await self.save_guild_data(ctx.guild.id, guild_data)
            
            embed = discord.Embed(title="🔇 Usuário Mutado", description=f"{member.mention} foi mutado!", color=discord.Color.red())
            embed.add_field(name="Duração", value=tempo, inline=True)
            embed.add_field(name="Motivo", value=reason, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "mute", ctx.author, member, reason, tempo)
            
            try:
                dm_embed = discord.Embed(
                    title="🔇 Você foi mutado",
                    description=f"**Servidor:** {ctx.guild.name}\n**Duração:** {tempo}\n**Motivo:** {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=dm_embed)
            except:
                pass
                
        except discord.Forbidden:
            embed = discord.Embed(title="❌ Erro", description="Sem permissão para mutar!", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='desmutar')
    @commands.has_permissions(administrator=True)
    async def unmute_user(self, ctx, member: discord.Member):
        mute_role = await self.get_mute_role(ctx.guild)
        if not mute_role or mute_role not in member.roles:
            embed = discord.Embed(title="❌ Erro", description=f"{member.mention} não está mutado!", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        
        try:
            await member.remove_roles(mute_role)
            
            guild_data = await self.get_guild_data(ctx.guild.id)
            mute_key = f"{ctx.guild.id}_{member.id}"
            if mute_key in guild_data['mutes']:
                del guild_data['mutes'][mute_key]
                await self.save_guild_data(ctx.guild.id, guild_data)
            
            embed = discord.Embed(title="🔊 Usuário Desmutado", description=f"{member.mention} foi desmutado!", color=discord.Color.green())
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "unmute", ctx.author, member)
            
        except discord.Forbidden:
            embed = discord.Embed(title="❌ Erro", description="Sem permissão para desmutar!", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='banir')
    @commands.has_permissions(administrator=True)
    async def ban_user(self, ctx, member: discord.Member, *, reason="Não especificado"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(title="❌ Erro", description="Você não pode banir este usuário!", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        
        try:
            try:
                dm_embed = discord.Embed(
                    title="🔨 Você foi banido",
                    description=f"**Servidor:** {ctx.guild.name}\n**Motivo:** {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=dm_embed)
            except:
                pass
            
            await member.ban(reason=reason)
            
            embed = discord.Embed(title="🔨 Usuário Banido", description=f"{member.mention} foi banido!", color=discord.Color.red())
            embed.add_field(name="Motivo", value=reason, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "ban", ctx.author, member, reason)
            
        except discord.Forbidden:
            embed = discord.Embed(title="❌ Erro", description="Sem permissão para banir!", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='expulsar')
    @commands.has_permissions(administrator=True)
    async def kick_user(self, ctx, member: discord.Member, *, reason="Não especificado"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(title="❌ Erro", description="Você não pode expulsar este usuário!", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        
        try:
            try:
                dm_embed = discord.Embed(
                    title="👢 Você foi expulso",
                    description=f"**Servidor:** {ctx.guild.name}\n**Motivo:** {reason}",
                    color=discord.Color.orange()
                )
                await member.send(embed=dm_embed)
            except:
                pass
            
            await member.kick(reason=reason)
            
            embed = discord.Embed(title="👢 Usuário Expulso", description=f"{member.mention} foi expulso!", color=discord.Color.orange())
            embed.add_field(name="Motivo", value=reason, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "kick", ctx.author, member, reason)
            
        except discord.Forbidden:
            embed = discord.Embed(title="❌ Erro", description="Sem permissão para expulsar!", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='limparmensagem', aliases=['clear', 'purge'])
    @commands.has_permissions(administrator=True)
    async def clear_messages(self, ctx, amount: int = 10):
        if amount <= 0 or amount > 100:
            embed = discord.Embed(title="❌ Erro", description="Quantidade deve ser entre 1 e 100!", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)
            
            embed = discord.Embed(title="🧹 Mensagens Limpas", description=f"**{len(deleted) - 1}** mensagens deletadas!", color=discord.Color.green())
            
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
            
        except discord.Forbidden:
            embed = discord.Embed(title="❌ Erro", description="Sem permissão para deletar mensagens!", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='configmod')
    @commands.has_permissions(administrator=True)
    async def config_moderation(self, ctx):
        config = await self.get_guild_config(ctx.guild.id)
        guild_data = await self.get_guild_data(ctx.guild.id)
        
        embed = discord.Embed(title="⚙️ Configurações de Moderação", color=discord.Color.blue())
        
        mute_role = await self.get_mute_role(ctx.guild)
        mute_text = mute_role.mention if mute_role else "❌ Não configurado"
        embed.add_field(name="🔇 Cargo de Mute", value=mute_text, inline=True)
        
        log_channel = ctx.guild.get_channel(config['log_channel_id']) if config['log_channel_id'] else None
        log_text = log_channel.mention if log_channel else "❌ Não configurado"
        embed.add_field(name="📋 Canal de Logs", value=log_text, inline=True)
        
        embed.add_field(name="⚠️ Max Avisos", value=config['max_warnings'], inline=True)
        embed.add_field(name="🤖 Auto Punir", value="✅ Ativo" if config['auto_punish'] else "❌ Inativo", inline=True)
        
        total_warnings = sum(len(warnings) for warnings in guild_data['warnings'].values())
        active_mutes = len(guild_data['mutes'])
        
        embed.add_field(name="📊 Avisos Totais", value=total_warnings, inline=True)
        embed.add_field(name="🔇 Mutes Ativos", value=active_mutes, inline=True)
        
        embed.add_field(
            name="📝 Comandos",
            value="`!aviso` `!removeraviso` `!avisos` `!mutar` `!desmutar` `!banir` `!expulsar` `!limparmensagem`",
            inline=False
        )
        
        await ctx.send(embed=embed)

    def parse_duration(self, duration_str):
        """Converte string de duração em timedelta"""
        try:
            unit = duration_str[-1].lower()
            value = int(duration_str[:-1])
            
            if unit == 's':
                return timedelta(seconds=value)
            elif unit == 'm':
                return timedelta(minutes=value)
            elif unit == 'h':
                return timedelta(hours=value)
            elif unit == 'd':
                return timedelta(days=value)
        except:
            pass
        return None

    @tasks.loop(minutes=1)
    async def check_mutes(self):
        """Verifica mutes expirados"""
        for guild in self.bot.guilds:
            guild_data = await self.get_guild_data(guild.id)
            expired_mutes = []
            
            for mute_key, mute_data in guild_data['mutes'].items():
                expire_time = datetime.fromisoformat(mute_data['expires'])
                if datetime.now() >= expire_time:
                    expired_mutes.append(mute_key)
                    
                    try:
                        user_id = int(mute_key.split('_')[1])
                        member = guild.get_member(user_id)
                        mute_role = await self.get_mute_role(guild)
                        
                        if member and mute_role and mute_role in member.roles:
                            await member.remove_roles(mute_role)
                    except:
                        pass
            
            for mute_key in expired_mutes:
                del guild_data['mutes'][mute_key]
            
            if expired_mutes:
                await self.save_guild_data(guild.id, guild_data)

    @check_mutes.before_loop
    async def before_check_mutes(self):
        await self.bot.wait_until_ready()

    @warn_user.error
    @mute_user.error
    @ban_user.error
    @kick_user.error
    @clear_messages.error
    async def mod_error_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title="❌ Sem Permissão", description="Você precisa ser **Administrador**!", color=discord.Color.red())
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="❌ Erro", description="Usuário não encontrado!", color=discord.Color.red())
            await ctx.send(embed=embed)

    async def cog_unload(self):
        """Fecha conexão MongoDB quando o cog é removido"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB fechada")

async def setup(bot):
    await bot.add_cog(ModerationSystem(bot))