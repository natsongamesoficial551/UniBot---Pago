import discord
from discord.ext import commands
import psutil
import platform
import datetime
import time
import asyncio

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command(name='botinfo', aliases=['bot'])
    async def mostrar_botinfo(self, ctx):
        """Mostra informações detalhadas sobre o bot"""
        try:
            uptime = time.time() - self.start_time
            uptime_str = str(datetime.timedelta(seconds=int(uptime)))

            # Calcular estatísticas com verificação de segurança
            total_members = sum(guild.member_count or 0 for guild in self.bot.guilds)
            total_channels = sum(len(guild.channels) for guild in self.bot.guilds)

            # Sistema com tratamento de erro
            try:
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                memory_usage = f"{memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB ({memory.percent:.1f}%)"
            except:
                cpu_usage = "N/A"
                memory_usage = "N/A"

            embed = discord.Embed(
                title="🤖 Informações do Bot",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )

            # Avatar com fallback
            if self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)

            embed.add_field(name="📊 Estatísticas", value=(
                f"**Servidores:** {len(self.bot.guilds):,}\n"
                f"**Usuários:** {total_members:,}\n"
                f"**Canais:** {total_channels:,}\n"
                f"**Comandos:** {len(self.bot.commands)}"
            ), inline=True)

            embed.add_field(name="💻 Sistema", value=(
                f"**CPU:** {cpu_usage}%\n"
                f"**RAM:** {memory_usage}\n"
                f"**Python:** {platform.python_version()}\n"
                f"**Discord.py:** {discord.__version__}"
            ), inline=True)

            embed.add_field(name="⏰ Informações", value=(
                f"**Uptime:** {uptime_str}\n"
                f"**Ping:** {round(self.bot.latency * 1000)}ms\n"
                f"**ID:** {self.bot.user.id}\n"
                f"**Criado:** <t:{int(self.bot.user.created_at.timestamp())}:R>"
            ), inline=True)

            # Footer com fallback
            author_avatar = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            embed.set_footer(text="Desenvolvido com ❤️", icon_url=author_avatar)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao buscar informações do bot: {str(e)}")

    @commands.command(name='userinfo', aliases=['user', 'ui'])
    async def mostrar_userinfo(self, ctx, user: discord.Member = None):
        """Mostra informações detalhadas sobre um usuário"""
        try:
            if user is None:
                user = ctx.author

            # Verificar se o usuário ainda está no servidor
            if not isinstance(user, discord.Member):
                await ctx.send("❌ Usuário não encontrado no servidor.")
                return

            # Calcular tempo no servidor com verificação
            if user.joined_at:
                joined_days = (datetime.datetime.utcnow() - user.joined_at.replace(tzinfo=None)).days
            else:
                joined_days = 0

            # Calcular tempo de criação da conta
            created_days = (datetime.datetime.utcnow() - user.created_at.replace(tzinfo=None)).days

            # Status do usuário
            status_emoji = {
                discord.Status.online: "🟢",
                discord.Status.idle: "🟡",
                discord.Status.dnd: "🔴",
                discord.Status.offline: "⚫"
            }

            embed = discord.Embed(
                title=f"👤 Informações do Usuário",
                color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )

            # Avatar com fallback
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            embed.set_thumbnail(url=avatar_url)

            # Nome de usuário com verificação para discriminator
            user_tag = f"{user.name}#{user.discriminator}" if user.discriminator != "0" else f"{user.name}"

            embed.add_field(name="🏷️ Usuário", value=(
                f"**Nome:** {user.display_name}\n"
                f"**Tag:** {user_tag}\n"
                f"**ID:** {user.id}\n"
                f"**Status:** {status_emoji.get(user.status, '❓')} {str(user.status).title()}"
            ), inline=True)

            joined_text = f"<t:{int(user.joined_at.timestamp())}:R>" if user.joined_at else "Desconhecido"
            embed.add_field(name="📅 Datas", value=(
                f"**Conta criada:** <t:{int(user.created_at.timestamp())}:R>\n"
                f"**Entrou no servidor:** {joined_text}\n"
                f"**Dias no servidor:** {joined_days}"
            ), inline=True)

            # Cargos do usuário com limite e verificação
            roles = [role.mention for role in user.roles[1:] if role.name != "@everyone"]
            if roles:
                roles_str = ", ".join(roles[:10])
                if len(roles) > 10:
                    roles_str += f" e mais {len(roles) - 10} cargos..."
            else:
                roles_str = "Nenhum"

            embed.add_field(name=f"🎭 Cargos ({len(user.roles) - 1})", value=roles_str, inline=False)

            # Permissões importantes
            perms = user.guild_permissions
            important_perms = []
            if perms.administrator:
                important_perms.append("Administrador")
            if perms.manage_guild:
                important_perms.append("Gerenciar Servidor")
            if perms.manage_roles:
                important_perms.append("Gerenciar Cargos")
            if perms.ban_members:
                important_perms.append("Banir Membros")
            if perms.kick_members:
                important_perms.append("Expulsar Membros")
            if perms.manage_messages:
                important_perms.append("Gerenciar Mensagens")

            if important_perms:
                embed.add_field(name="🔐 Permissões Importantes", value=", ".join(important_perms), inline=False)

            # Footer com fallback
            author_avatar = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=author_avatar)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao buscar informações do usuário: {str(e)}")

    @commands.command(name='serverinfo', aliases=['server', 'si'])
    async def mostrar_serverinfo(self, ctx):
        """Mostra informações detalhadas sobre o servidor"""
        try:
            guild = ctx.guild

            # Contadores de membros com verificação
            total_members = guild.member_count or 0
            if guild.chunked:
                humans = sum(1 for member in guild.members if not member.bot)
                bots = total_members - humans
                online = sum(1 for member in guild.members if member.status != discord.Status.offline)
            else:
                # Se o guild não está chunked, usar aproximações
                humans = total_members
                bots = 0
                online = 0

            # Contadores de canais
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)

            # Nível de verificação
            verification_levels = {
                discord.VerificationLevel.none: "Nenhuma",
                discord.VerificationLevel.low: "Baixa",
                discord.VerificationLevel.medium: "Média",
                discord.VerificationLevel.high: "Alta",
                discord.VerificationLevel.highest: "Muito Alta"
            }

            embed = discord.Embed(
                title=f"🏰 {guild.name}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )

            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)

            embed.add_field(name="📊 Membros", value=(
                f"**Total:** {total_members:,}\n"
                f"**Humanos:** {humans:,}\n"
                f"**Bots:** {bots:,}\n"
                f"**Online:** {online:,}"
            ), inline=True)

            embed.add_field(name="📢 Canais", value=(
                f"**Texto:** {text_channels}\n"
                f"**Voz:** {voice_channels}\n"
                f"**Categorias:** {categories}\n"
                f"**Total:** {len(guild.channels)}"
            ), inline=True)

            owner_mention = guild.owner.mention if guild.owner else 'Desconhecido'
            embed.add_field(name="ℹ️ Informações", value=(
                f"**ID:** {guild.id}\n"
                f"**Dono:** {owner_mention}\n"
                f"**Criado:** <t:{int(guild.created_at.timestamp())}:R>\n"
                f"**Cargos:** {len(guild.roles)}"
            ), inline=True)

            # Boost info com verificação
            boost_count = guild.premium_subscription_count or 0
            embed.add_field(name="🔒 Segurança", value=(
                f"**Verificação:** {verification_levels.get(guild.verification_level, 'Desconhecida')}\n"
                f"**Boost:** Nível {guild.premium_tier}\n"
                f"**Boosts:** {boost_count}\n"
                f"**Emojis:** {len(guild.emojis)}/{guild.emoji_limit}"
            ), inline=True)

            # Recursos do servidor
            features = []
            feature_map = {
                "COMMUNITY": "Comunidade",
                "VERIFIED": "Verificado",
                "PARTNERED": "Parceiro",
                "VANITY_URL": "URL Personalizada",
                "DISCOVERABLE": "Descobrível",
                "FEATURABLE": "Destacável",
                "INVITE_SPLASH": "Splash de Convite",
                "VIP_REGIONS": "Regiões VIP",
                "BANNER": "Banner",
                "ANIMATED_ICON": "Ícone Animado"
            }

            for feature in guild.features:
                if feature in feature_map:
                    features.append(feature_map[feature])

            if features:
                embed.add_field(name="✨ Recursos", value=", ".join(features), inline=False)

            # Footer com fallback
            author_avatar = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=author_avatar)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao buscar informações do servidor: {str(e)}")

    @commands.command(name='ping')
    async def mostrar_ping(self, ctx):
        """Mostra a latência do bot"""
        try:
            start_time = time.time()
            message = await ctx.send("🏓 Calculando ping...")
            end_time = time.time()

            api_latency = round(self.bot.latency * 1000)
            msg_latency = round((end_time - start_time) * 1000)

            # Determinando status baseado na latência
            if api_latency < 100:
                emoji, status, color = "🟢", "Excelente", discord.Color.green()
            elif api_latency < 200:
                emoji, status, color = "🟡", "Bom", discord.Color.yellow()
            elif api_latency < 300:
                emoji, status, color = "🟠", "Médio", discord.Color.orange()
            else:
                emoji, status, color = "🔴", "Ruim", discord.Color.red()

            embed = discord.Embed(
                title="🏓 Pong!",
                color=color,
                timestamp=datetime.datetime.utcnow()
            )

            embed.add_field(name="📱 Latência da API", value=f"{emoji} {api_latency}ms", inline=True)
            embed.add_field(name="💬 Latência da Mensagem", value=f"⚡ {msg_latency}ms", inline=True)
            embed.add_field(name="📊 Status", value=status, inline=True)

            await message.edit(content=None, embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao calcular ping: {str(e)}")

    @commands.command(name='avatar2', aliases=['av2'])
    async def mostrar_avatar(self, ctx, user: discord.Member = None):
        """Mostra o avatar de um usuário"""
        try:
            if user is None:
                user = ctx.author

            embed = discord.Embed(
                title=f"🖼️ Avatar de {user.display_name}",
                color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )

            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            embed.set_image(url=avatar_url)

            # Links com diferentes formatos
            if user.avatar:
                embed.add_field(name="🔗 Links", value=(
                    f"[PNG]({avatar_url}?format=png&size=1024) | "
                    f"[JPG]({avatar_url}?format=jpg&size=1024) | "
                    f"[WEBP]({avatar_url}?format=webp&size=1024)"
                ), inline=False)

            # Footer com fallback
            author_avatar = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=author_avatar)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao buscar avatar: {str(e)}")

    @commands.command(name='banner')
    async def mostrar_banner(self, ctx, user: discord.Member = None):
        """Mostra o banner de um usuário"""
        try:
            if user is None:
                user = ctx.author

            # Buscar informações completas do usuário
            try:
                user_info = await self.bot.fetch_user(user.id)
            except:
                user_info = user

            embed = discord.Embed(
                title=f"🎨 Banner de {user.display_name}",
                color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )

            if hasattr(user_info, 'banner') and user_info.banner:
                embed.set_image(url=user_info.banner.url)
                embed.add_field(name="🔗 Links", value=(
                    f"[PNG]({user_info.banner.url}?format=png&size=1024) | "
                    f"[JPG]({user_info.banner.url}?format=jpg&size=1024) | "
                    f"[WEBP]({user_info.banner.url}?format=webp&size=1024)"
                ), inline=False)
            else:
                embed.description = "❌ Este usuário não possui um banner personalizado."

            # Footer com fallback
            author_avatar = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=author_avatar)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao buscar banner: {str(e)}")

    @commands.command(name='invite', aliases=['convite'])
    async def mostrar_convite(self, ctx):
        """Gera um link de convite para o bot"""
        try:
            permissions = discord.Permissions(administrator=True)
            invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)

            embed = discord.Embed(
                title="🔗 Convide o Bot!",
                description=f"[Clique aqui para me adicionar ao seu servidor!]({invite_url})",
                color=discord.Color.blurple(),
                timestamp=datetime.datetime.utcnow()
            )
            
            if self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)
            
            embed.add_field(name="🔐 Permissões", value=(
                "O link inclui permissões de **Administrador** para funcionamento completo.\n"
                "Você pode ajustar as permissões durante a adição se preferir."
            ), inline=False)

            embed.set_footer(text="Obrigado por usar nosso bot! ❤️")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao gerar convite: {str(e)}")

    @commands.command(name='uptime')
    async def mostrar_uptime(self, ctx):
        """Mostra há quanto tempo o bot está online"""
        try:
            uptime = time.time() - self.start_time
            uptime_str = str(datetime.timedelta(seconds=int(uptime)))

            # Calcular componentes do uptime
            days = int(uptime // 86400)
            hours = int((uptime % 86400) // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)

            embed = discord.Embed(
                title="⏰ Tempo Online",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )

            embed.add_field(name="📊 Uptime Total", value=f"**{uptime_str}**", inline=False)
            
            embed.add_field(name="📅 Dias", value=f"{days:,}", inline=True)
            embed.add_field(name="🕐 Horas", value=f"{hours:,}", inline=True)
            embed.add_field(name="⏱️ Minutos", value=f"{minutes:,}", inline=True)

            embed.add_field(name="🚀 Iniciado em", value=f"<t:{int(self.start_time)}:F>", inline=False)

            embed.set_footer(text="Bot funcionando perfeitamente! ✅")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao calcular uptime: {str(e)}")

    @commands.command(name='membercount', aliases=['membros'])
    async def contar_membros(self, ctx):
        """Mostra estatísticas detalhadas dos membros do servidor"""
        try:
            guild = ctx.guild

            total = guild.member_count or 0
            
            # Verificar se o guild está chunked para estatísticas precisas
            if guild.chunked:
                humans = sum(1 for member in guild.members if not member.bot)
                bots = total - humans
                online = sum(1 for member in guild.members if member.status != discord.Status.offline)

                # Status detalhados
                status_counts = {
                    'online': sum(1 for m in guild.members if m.status == discord.Status.online),
                    'idle': sum(1 for m in guild.members if m.status == discord.Status.idle),
                    'dnd': sum(1 for m in guild.members if m.status == discord.Status.dnd),
                    'offline': sum(1 for m in guild.members if m.status == discord.Status.offline)
                }
            else:
                # Aproximações se não chunked
                await ctx.send("⚠️ Carregando membros do servidor... Isso pode levar alguns segundos.")
                try:
                    async for member in guild.fetch_members(limit=None):
                        pass
                    # Tentar novamente após fetch
                    humans = sum(1 for member in guild.members if not member.bot)
                    bots = total - humans
                    online = sum(1 for member in guild.members if member.status != discord.Status.offline)
                    status_counts = {
                        'online': sum(1 for m in guild.members if m.status == discord.Status.online),
                        'idle': sum(1 for m in guild.members if m.status == discord.Status.idle),
                        'dnd': sum(1 for m in guild.members if m.status == discord.Status.dnd),
                        'offline': sum(1 for m in guild.members if m.status == discord.Status.offline)
                    }
                except:
                    humans, bots, online = total, 0, 0
                    status_counts = {'online': 0, 'idle': 0, 'dnd': 0, 'offline': total}

            embed = discord.Embed(
                title="👥 Contador de Membros",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )

            embed.add_field(name="📊 Geral", value=(
                f"**Total:** {total:,}\n"
                f"**Humanos:** {humans:,}\n"
                f"**Bots:** {bots:,}"
            ), inline=True)

            embed.add_field(name="🔄 Status", value=(
                f"🟢 **Online:** {status_counts['online']:,}\n"
                f"🟡 **Ausente:** {status_counts['idle']:,}\n"
                f"🔴 **Ocupado:** {status_counts['dnd']:,}\n"
                f"⚫ **Offline:** {status_counts['offline']:,}"
            ), inline=True)

            # Estatísticas com verificação de divisão por zero
            if total > 0:
                online_percent = round((online/total)*100, 1)
                offline_percent = round(((total-online)/total)*100, 1)
                human_percent = round((humans/total)*100, 1)
                bot_percent = round((bots/total)*100, 1)
            else:
                online_percent = offline_percent = human_percent = bot_percent = 0

            embed.add_field(name="📈 Estatísticas", value=(
                f"**Online:** {online:,} ({online_percent}%)\n"
                f"**Offline:** {total - online:,} ({offline_percent}%)\n"
                f"**Humanos:** {human_percent}%\n"
                f"**Bots:** {bot_percent}%"
            ), inline=True)

            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)

            embed.set_footer(text=f"Servidor: {guild.name}", icon_url=guild.icon.url if guild.icon else None)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao contar membros: {str(e)}")

    # Comando adicional para limpeza de cache
    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def reload_cog(self, ctx):
        """Recarrega a cog (apenas para o dono do bot)"""
        try:
            await self.bot.reload_extension('utilities')
            await ctx.send("✅ Cog recarregada com sucesso!")
        except Exception as e:
            await ctx.send(f"❌ Erro ao recarregar cog: {str(e)}")

async def setup(bot):
    await bot.add_cog(Utilities(bot))