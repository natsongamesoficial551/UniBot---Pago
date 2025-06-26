import discord
from discord.ext import commands
import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Adiciona o load_dotenv aqui
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Se não tiver python-dotenv instalado, ignora

class AdvancedLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.config_collection = None
        self.logs_collection = None
        self._connection_ready = False
        # Inicializa a conexão com MongoDB
        self.bot.loop.create_task(self.init_database())

    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            # URL de conexão do MongoDB (vem de variável de ambiente)
            mongo_uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
            
            if not mongo_uri:
                print("❌ MONGO_URI ou MONGODB_URI não encontrada nas variáveis de ambiente!")
                return
            
            print("🔄 Conectando ao MongoDB (Logs System)...")
            self.client = AsyncIOMotorClient(mongo_uri)
            
            # Testa a conexão
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.config_collection = self.db['logs_config']
            self.logs_collection = self.db['logs_history']
            self._connection_ready = True
            
            print("✅ Conectado ao MongoDB (Logs System) com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB (Logs): {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def cog_unload(self):
        """Fecha a conexão com o MongoDB quando o cog é descarregado"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB (Logs) fechada")
    
    async def get_log_channel(self, guild_id):
        """Obtém o canal de logs configurado para o servidor"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível")
                return None
                
            config = await self.config_collection.find_one({"guild_id": str(guild_id)})
            return config.get('log_channel') if config else None
        except Exception as e:
            print(f"❌ Erro ao buscar canal de log: {e}")
            return None
    
    async def save_log_config(self, guild_id, channel_id):
        """Salva a configuração do canal de logs"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível")
                return False
            
            await self.config_collection.update_one(
                {"guild_id": str(guild_id)},
                {"$set": {
                    "log_channel": channel_id, 
                    "updated_at": datetime.datetime.utcnow()
                }},
                upsert=True
            )
            print(f"✅ Canal de logs salvo: {channel_id} para guild {guild_id}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar configuração de log: {e}")
            return False
    
    async def save_log_entry(self, guild_id, log_type, data):
        """Salva uma entrada de log no histórico"""
        try:
            if not await self.ensure_connection():
                return False
                
            log_entry = {
                "guild_id": str(guild_id),
                "log_type": log_type,
                "timestamp": datetime.datetime.utcnow(),
                "data": data
            }
            await self.logs_collection.insert_one(log_entry)
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar entrada de log: {e}")
            return False
    
    async def send_log(self, guild, embed, log_type=None, log_data=None):
        """Envia o log para o canal configurado"""
        channel_id = await self.get_log_channel(guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(embed=embed)
                    # Salva o log no MongoDB
                    if log_type and log_data:
                        await self.save_log_entry(guild.id, log_type, log_data)
                except discord.Forbidden:
                    print(f"❌ Sem permissão para enviar logs no canal {channel.name}")
                except discord.NotFound:
                    print(f"❌ Canal de logs não encontrado: {channel_id}")
                except Exception as e:
                    print(f"❌ Erro ao enviar log: {e}")
    
    @commands.command(name='canaldelogs')
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Define o canal para receber os logs do servidor"""
        success = await self.save_log_config(ctx.guild.id, channel.id)
        
        if success:
            embed = discord.Embed(
                title="✅ Canal de Logs Configurado",
                description=f"Canal de logs definido para {channel.mention}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar a configuração. Verifique a conexão com o banco de dados.",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='testelog')
    @commands.has_permissions(administrator=True)
    async def test_log(self, ctx):
        """Comando para testar se os logs estão funcionando"""
        embed = discord.Embed(
            title="🧪 Teste de Log",
            description="Este é um teste do sistema de logs.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Testado por", value=ctx.author.mention, inline=True)
        
        log_data = {
            "tester_id": ctx.author.id,
            "tester_name": str(ctx.author),
            "channel_id": ctx.channel.id,
            "channel_name": ctx.channel.name
        }
        
        await self.send_log(ctx.guild, embed, "test_log", log_data)
        await ctx.send("✅ Teste de log enviado!")

    @commands.command(name='statusdblogs')
    @commands.has_permissions(administrator=True)
    async def status_db_logs(self, ctx):
        """Verifica o status da conexão com o banco de dados para logs"""
        if self._connection_ready:
            try:
                # Testa a conexão fazendo um ping
                await self.client.admin.command('ping')
                embed = discord.Embed(
                    title="✅ Banco de Dados Conectado (Logs)",
                    description="A conexão com o MongoDB está funcionando corretamente.",
                    color=discord.Color.green()
                )
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Erro na Conexão (Logs)",
                    description=f"Erro ao testar conexão: {str(e)}",
                    color=discord.Color.red()
                )
                self._connection_ready = False
        else:
            embed = discord.Embed(
                title="❌ Banco de Dados Desconectado (Logs)",
                description="A conexão com o MongoDB não está disponível. Tentando reconectar...",
                color=discord.Color.red()
            )
            # Tenta reconectar
            await self.init_database()
            
        await ctx.send(embed=embed)
    
    # LOGS DE MENSAGENS
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return
        
        embed = discord.Embed(
            title="🗑️ Mensagem Deletada",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Autor", value=f"{message.author} ({message.author.id})", inline=True)
        embed.add_field(name="Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="Conteúdo", value=message.content[:1000] or "Sem conteúdo de texto", inline=False)
        if message.attachments:
            embed.add_field(name="Anexos", value=f"{len(message.attachments)} arquivo(s)", inline=True)
        
        # Verifica se o avatar existe antes de usar
        avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
        embed.set_author(name=message.author.display_name, icon_url=avatar_url)
        
        log_data = {
            "author_id": message.author.id,
            "author_name": str(message.author),
            "channel_id": message.channel.id,
            "channel_name": message.channel.name,
            "content": message.content,
            "attachments_count": len(message.attachments) if message.attachments else 0,
            "message_id": message.id
        }
        
        await self.send_log(message.guild, embed, "message_delete", log_data)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        
        embed = discord.Embed(
            title="✏️ Mensagem Editada",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Autor", value=f"{before.author} ({before.author.id})", inline=True)
        embed.add_field(name="Canal", value=before.channel.mention, inline=True)
        embed.add_field(name="Antes", value=before.content[:500] or "Sem conteúdo", inline=False)
        embed.add_field(name="Depois", value=after.content[:500] or "Sem conteúdo", inline=False)
        
        avatar_url = before.author.avatar.url if before.author.avatar else before.author.default_avatar.url
        embed.set_author(name=before.author.display_name, icon_url=avatar_url)
        
        log_data = {
            "author_id": before.author.id,
            "author_name": str(before.author),
            "channel_id": before.channel.id,
            "channel_name": before.channel.name,
            "content_before": before.content,
            "content_after": after.content,
            "message_id": before.id
        }
        
        await self.send_log(before.guild, embed, "message_edit", log_data)
    
    # LOGS DE MEMBROS
    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(
            title="📥 Membro Entrou",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Membro", value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="Conta Criada", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Total de Membros", value=member.guild.member_count, inline=True)
        
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_author(name=member.display_name, icon_url=avatar_url)
        
        log_data = {
            "member_id": member.id,
            "member_name": str(member),
            "account_created": member.created_at,
            "total_members": member.guild.member_count
        }
        
        await self.send_log(member.guild, embed, "member_join", log_data)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(
            title="📤 Membro Saiu",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Membro", value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="Entrou em", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Desconhecido", inline=True)
        embed.add_field(name="Total de Membros", value=member.guild.member_count, inline=True)
        if member.roles[1:]:
            roles = ", ".join([role.name for role in member.roles[1:]])
            embed.add_field(name="Cargos", value=roles[:1000], inline=False)
        
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_author(name=member.display_name, icon_url=avatar_url)
        
        log_data = {
            "member_id": member.id,
            "member_name": str(member),
            "joined_at": member.joined_at,
            "roles": [role.name for role in member.roles[1:]],
            "total_members": member.guild.member_count
        }
        
        await self.send_log(member.guild, embed, "member_remove", log_data)
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(
            title="🔨 Membro Banido",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Usuário", value=f"{user} ({user.id})", inline=True)
        
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        embed.set_author(name=user.display_name, icon_url=avatar_url)
        
        log_data = {
            "user_id": user.id,
            "user_name": str(user),
            "moderator": None,
            "reason": None
        }
        
        # Tenta pegar o motivo do ban
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                if entry.target.id == user.id:
                    embed.add_field(name="Moderador", value=entry.user, inline=True)
                    log_data["moderator"] = str(entry.user)
                    log_data["moderator_id"] = entry.user.id
                    if entry.reason:
                        embed.add_field(name="Motivo", value=entry.reason, inline=False)
                        log_data["reason"] = entry.reason
                    break
        except discord.Forbidden:
            embed.add_field(name="Moderador", value="Sem permissão para ver audit logs", inline=True)
        except Exception as e:
            print(f"❌ Erro ao buscar audit logs: {e}")
        
        await self.send_log(guild, embed, "member_ban", log_data)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(
            title="🔓 Membro Desbanido",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Usuário", value=f"{user} ({user.id})", inline=True)
        
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        embed.set_author(name=user.display_name, icon_url=avatar_url)
        
        log_data = {
            "user_id": user.id,
            "user_name": str(user),
            "moderator": None,
            "reason": None
        }
        
        # Tenta pegar quem desbaniu
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=1):
                if entry.target.id == user.id:
                    embed.add_field(name="Moderador", value=entry.user, inline=True)
                    log_data["moderator"] = str(entry.user)
                    log_data["moderator_id"] = entry.user.id
                    if entry.reason:
                        embed.add_field(name="Motivo", value=entry.reason, inline=False)
                        log_data["reason"] = entry.reason
                    break
        except discord.Forbidden:
            embed.add_field(name="Moderador", value="Sem permissão para ver audit logs", inline=True)
        except Exception as e:
            print(f"❌ Erro ao buscar audit logs: {e}")
        
        await self.send_log(guild, embed, "member_unban", log_data)
    
    # LOGS DE CARGOS
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            if added_roles or removed_roles:
                embed = discord.Embed(
                    title="👑 Cargos Alterados",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.utcnow()
                )
                embed.add_field(name="Membro", value=f"{after} ({after.id})", inline=True)
                
                if added_roles:
                    embed.add_field(name="Cargos Adicionados", value=", ".join([role.mention for role in added_roles]), inline=False)
                if removed_roles:
                    embed.add_field(name="Cargos Removidos", value=", ".join([role.mention for role in removed_roles]), inline=False)
                
                avatar_url = after.avatar.url if after.avatar else after.default_avatar.url
                embed.set_author(name=after.display_name, icon_url=avatar_url)
                
                log_data = {
                    "member_id": after.id,
                    "member_name": str(after),
                    "added_roles": [{"id": role.id, "name": role.name} for role in added_roles],
                    "removed_roles": [{"id": role.id, "name": role.name} for role in removed_roles]
                }
                
                await self.send_log(after.guild, embed, "role_update", log_data)
        
        # Mudança de nickname
        if before.nick != after.nick:
            embed = discord.Embed(
                title="📝 Apelido Alterado",
                color=discord.Color.purple(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Membro", value=f"{after} ({after.id})", inline=True)
            embed.add_field(name="Antes", value=before.nick or before.name, inline=True)
            embed.add_field(name="Depois", value=after.nick or after.name, inline=True)
            
            avatar_url = after.avatar.url if after.avatar else after.default_avatar.url
            embed.set_author(name=after.display_name, icon_url=avatar_url)
            
            log_data = {
                "member_id": after.id,
                "member_name": str(after),
                "nick_before": before.nick,
                "nick_after": after.nick
            }
            
            await self.send_log(after.guild, embed, "nickname_update", log_data)
    
    # LOGS DE CANAIS
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(
            title="➕ Canal Criado",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Canal", value=f"{channel.mention} ({channel.id})", inline=True)
        embed.add_field(name="Tipo", value=str(channel.type).title(), inline=True)
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="Categoria", value=channel.category.name, inline=True)
        
        log_data = {
            "channel_id": channel.id,
            "channel_name": channel.name,
            "channel_type": str(channel.type),
            "category": channel.category.name if hasattr(channel, 'category') and channel.category else None
        }
        
        await self.send_log(channel.guild, embed, "channel_create", log_data)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(
            title="🗑️ Canal Deletado",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Canal", value=f"#{channel.name} ({channel.id})", inline=True)
        embed.add_field(name="Tipo", value=str(channel.type).title(), inline=True)
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="Categoria", value=channel.category.name, inline=True)
        
        log_data = {
            "channel_id": channel.id,
            "channel_name": channel.name,
            "channel_type": str(channel.type),
            "category": channel.category.name if hasattr(channel, 'category') and channel.category else None
        }
        
        await self.send_log(channel.guild, embed, "channel_delete", log_data)
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Nome:** {before.name} → {after.name}")
        if hasattr(before, 'topic') and before.topic != after.topic:
            changes.append(f"**Tópico:** {before.topic or 'Nenhum'} → {after.topic or 'Nenhum'}")
        if hasattr(before, 'category') and before.category != after.category:
            before_cat = before.category.name if before.category else "Sem categoria"
            after_cat = after.category.name if after.category else "Sem categoria"
            changes.append(f"**Categoria:** {before_cat} → {after_cat}")
        
        if changes:
            embed = discord.Embed(
                title="🔧 Canal Atualizado",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Canal", value=after.mention, inline=True)
            embed.add_field(name="Alterações", value="\n".join(changes), inline=False)
            
            log_data = {
                "channel_id": after.id,
                "channel_name_before": before.name,
                "channel_name_after": after.name,
                "topic_before": getattr(before, 'topic', None),
                "topic_after": getattr(after, 'topic', None),
                "category_before": before.category.name if hasattr(before, 'category') and before.category else None,
                "category_after": after.category.name if hasattr(after, 'category') and after.category else None
            }
            
            await self.send_log(after.guild, embed, "channel_update", log_data)
    
    # LOGS DE SERVIDOR
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Nome:** {before.name} → {after.name}")
        if before.icon != after.icon:
            changes.append("**Ícone:** Alterado")
        if before.owner != after.owner:
            changes.append(f"**Dono:** {before.owner} → {after.owner}")
        
        if changes:
            embed = discord.Embed(
                title="🏠 Servidor Atualizado",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Alterações", value="\n".join(changes), inline=False)
            
            log_data = {
                "name_before": before.name,
                "name_after": after.name,
                "icon_changed": before.icon != after.icon,
                "owner_before": str(before.owner),
                "owner_after": str(after.owner)
            }
            
            await self.send_log(after, embed, "guild_update", log_data)
    
    # LOGS DE CONVITES
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        embed = discord.Embed(
            title="🔗 Convite Criado",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Código", value=invite.code, inline=True)
        embed.add_field(name="Canal", value=invite.channel.mention, inline=True)
        embed.add_field(name="Criado por", value=invite.inviter, inline=True)
        embed.add_field(name="Usos Máximos", value=invite.max_uses or "Ilimitado", inline=True)
        
        if invite.max_age and invite.max_age > 0:
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=invite.max_age)
            embed.add_field(name="Expira em", value=f"<t:{int(expires_at.timestamp())}:R>", inline=True)
        else:
            embed.add_field(name="Expira em", value="Nunca", inline=True)
        
        log_data = {
            "invite_code": invite.code,
            "channel_id": invite.channel.id,
            "channel_name": invite.channel.name,
            "inviter_id": invite.inviter.id if invite.inviter else None,
            "inviter_name": str(invite.inviter) if invite.inviter else None,
            "max_uses": invite.max_uses,
            "max_age": invite.max_age
        }
        
        await self.send_log(invite.guild, embed, "invite_create", log_data)
    
    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        embed = discord.Embed(
            title="🗑️ Convite Deletado",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Código", value=invite.code, inline=True)
        embed.add_field(name="Canal", value=invite.channel.mention, inline=True)
        
        log_data = {
            "invite_code": invite.code,
            "channel_id": invite.channel.id,
            "channel_name": invite.channel.name
        }
        
        await self.send_log(invite.guild, embed, "invite_delete", log_data)

    @commands.command(name='helplogs')
    async def help_logs(self, ctx):
        """Mostra ajuda sobre os comandos do sistema de logs"""
        embed = discord.Embed(
            title="📋 Sistema de Logs - Ajuda",
            description="Lista de comandos e eventos monitorados:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🔧 Comandos de Configuração",
            value="`!canaldelogs #canal` - Define o canal para logs\n`!testelog` - Testa o sistema de logs\n`!statusdblogs` - Verifica conexão com BD",
            inline=False
        )
        
        embed.add_field(
            name="💬 Logs de Mensagens",
            value="• Mensagens deletadas\n• Mensagens editadas",
            inline=True
        )
        
        embed.add_field(
            name="👥 Logs de Membros",
            value="• Entrada de membros\n• Saída de membros\n• Membros banidos/desbanidos\n• Mudanças de cargos\n• Mudanças de apelido",
            inline=True
        )
        
        embed.add_field(
            name="🏗️ Logs de Servidor",
            value="• Canais criados/deletados/editados\n• Configurações do servidor\n• Convites criados/deletados",
            inline=True
        )
        
        embed.set_footer(text="Todos os logs são salvos no banco de dados para consulta posterior")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedLogs(bot))