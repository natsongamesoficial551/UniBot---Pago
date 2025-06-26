import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta
import asyncio
import calendar
from motor.motor_asyncio import AsyncIOMotorClient
import random

class Aniversario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.collection = None
        self.config_collection = None
        self._connection_ready = False
        # Inicializa a conexão com MongoDB
        self.bot.loop.create_task(self.init_database())
        # Inicia a task de verificação de aniversários
        self.check_birthdays.start()

    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            # URL de conexão do MongoDB (vem de variável de ambiente)
            mongo_uri = os.getenv("MONGO_URI")
            
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada nas variáveis de ambiente!")
                return
            
            print("🔄 Conectando ao MongoDB (Aniversários)...")
            self.client = AsyncIOMotorClient(mongo_uri)
            
            # Testa a conexão
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.collection = self.db['aniversarios']
            self.config_collection = self.db['birthday_config']
            self._connection_ready = True
            
            print("✅ Conectado ao MongoDB (Aniversários) com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB (Aniversários): {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    def validate_date(self, day, month):
        """Valida se a data é válida considerando anos bissextos"""
        try:
            # Verifica se o mês é válido
            if not (1 <= month <= 12):
                return False
            
            # Verifica se o dia é válido para o mês
            # Usa um ano bissexto para validar 29/02
            max_day = calendar.monthrange(2024, month)[1]
            if not (1 <= day <= max_day):
                return False
            
            return True
        except:
            return False

    async def save_birthday(self, user_id, name, date, day, month, guild_id):
        """Salva aniversário no MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
                
            await self.collection.update_one(
                {'user_id': user_id, 'guild_id': guild_id},
                {
                    '$set': {
                        'user_id': user_id,
                        'guild_id': guild_id,
                        'name': name,
                        'date': date,
                        'day': day,
                        'month': month,
                        'updated_at': datetime.utcnow()
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar aniversário: {e}")
            return False

    async def get_birthday(self, user_id, guild_id):
        """Busca aniversário específico no MongoDB"""
        try:
            if not await self.ensure_connection():
                return None
            return await self.collection.find_one({'user_id': user_id, 'guild_id': guild_id})
        except Exception as e:
            print(f"❌ Erro ao buscar aniversário: {e}")
            return None

    async def get_all_birthdays(self, guild_id):
        """Busca todos os aniversários do servidor no MongoDB"""
        try:
            if not await self.ensure_connection():
                return []
            cursor = self.collection.find({'guild_id': guild_id})
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"❌ Erro ao buscar aniversários: {e}")
            return []

    async def delete_birthday(self, user_id, guild_id):
        """Remove aniversário do MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
            result = await self.collection.delete_one({'user_id': user_id, 'guild_id': guild_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Erro ao deletar aniversário: {e}")
            return False

    async def get_birthday_channel(self, guild_id):
        """Busca o canal configurado para aniversários"""
        try:
            if not await self.ensure_connection():
                return None
            config = await self.config_collection.find_one({'guild_id': guild_id})
            return config.get('channel_id') if config else None
        except Exception as e:
            print(f"❌ Erro ao buscar canal de aniversários: {e}")
            return None

    async def set_birthday_channel(self, guild_id, channel_id):
        """Define o canal para envio de mensagens de aniversário"""
        try:
            if not await self.ensure_connection():
                return False
            await self.config_collection.update_one(
                {'guild_id': guild_id},
                {
                    '$set': {
                        'guild_id': guild_id,
                        'channel_id': channel_id,
                        'updated_at': datetime.utcnow()
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar canal de aniversários: {e}")
            return False

    def get_birthday_messages(self):
        """Retorna mensagens aleatórias de parabéns"""
        messages = [
            "🎉 Parabéns, {nome}! Que este novo ano de vida seja repleto de alegrias e conquistas! 🎂",
            "🎈 Feliz aniversário, {nome}! Desejamos um dia especial e um ano maravilhoso pela frente! 🎊",
            "🎂 Hoje é dia de festa! Parabéns, {nome}! Que todos os seus sonhos se realizem! ✨",
            "🎁 {nome}, chegou o seu dia especial! Parabéns e muitas felicidades! 🌟",
            "🎉 Um brinde à vida de {nome}! Feliz aniversário e que venham muitos anos de saúde e felicidade! 🥳",
            "🎂 {nome}, que este aniversário marque o início de um ano incrível! Parabéns! 🌈",
            "🎊 Celebrando a vida de {nome}! Parabéns e que este novo ciclo seja abençoado! 🎈",
            "✨ {nome}, hoje é seu dia de brilhar ainda mais! Feliz aniversário! 🎉",
            "🎁 Parabéns, {nome}! Que a felicidade seja sua companheira em todos os momentos! 🎂",
            "🌟 {nome}, desejamos que este aniversário seja o início de 365 dias maravilhosos! 🎉"
        ]
        return random.choice(messages)

    @tasks.loop(hours=24)
    async def check_birthdays(self):
        """Task que verifica aniversários diariamente"""
        try:
            hoje = datetime.now()
            print(f"🔍 Verificando aniversários para {hoje.strftime('%d/%m/%Y')}...")
            
            # Busca todos os servidores que o bot está
            for guild in self.bot.guilds:
                guild_id = str(guild.id)
                
                # Busca canal configurado para aniversários
                channel_id = await self.get_birthday_channel(guild_id)
                if not channel_id:
                    continue
                
                channel = guild.get_channel(int(channel_id))
                if not channel:
                    continue
                
                # Busca aniversariantes de hoje
                birthdays = await self.get_all_birthdays(guild_id)
                aniversariantes_hoje = []
                
                for data in birthdays:
                    if data['day'] == hoje.day and data['month'] == hoje.month:
                        member = guild.get_member(int(data['user_id']))
                        if member:
                            aniversariantes_hoje.append(member)
                
                # Envia mensagens para cada aniversariante
                for member in aniversariantes_hoje:
                    try:
                        message = self.get_birthday_messages().format(nome=member.mention)
                        
                        embed = discord.Embed(
                            title="🎉 FELIZ ANIVERSÁRIO! 🎉",
                            description=message,
                            color=0xFF69B4
                        )
                        embed.set_thumbnail(url=member.display_avatar.url)
                        embed.set_footer(text=f"🎂 Aniversário de {member.display_name}")
                        
                        await channel.send(embed=embed)
                        print(f"🎂 Mensagem de aniversário enviada para {member.display_name} em {guild.name}")
                        
                        # Pequena pausa entre mensagens
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        print(f"❌ Erro ao enviar mensagem de aniversário para {member.display_name}: {e}")
                
        except Exception as e:
            print(f"❌ Erro na verificação de aniversários: {e}")

    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        """Aguarda o bot estar pronto antes de iniciar a task"""
        await self.bot.wait_until_ready()
        
        # Calcula quando executar pela primeira vez (próximas 9:00)
        now = datetime.now()
        target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        
        if now >= target_time:
            target_time += timedelta(days=1)
        
        wait_seconds = (target_time - now).total_seconds()
        print(f"⏰ Próxima verificação de aniversários: {target_time.strftime('%d/%m/%Y às %H:%M')}")
        await asyncio.sleep(wait_seconds)

    @commands.command(name='configurarcanal', aliases=['setbdchannel'])
    @commands.has_permissions(administrator=True)
    async def configurar_canal(self, ctx, channel: discord.TextChannel = None):
        """Configura o canal para envio automático de mensagens de aniversário"""
        if channel is None:
            channel = ctx.channel
        
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)
        
        success = await self.set_birthday_channel(guild_id, channel_id)
        
        if success:
            embed = discord.Embed(
                title="✅ Canal Configurado",
                description=f"Canal {channel.mention} configurado para receber mensagens automáticas de aniversário!\n\n"
                           f"🤖 **Como funciona:**\n"
                           f"• O bot verifica aniversários diariamente às 9:00\n"
                           f"• Mensagens automáticas serão enviadas neste canal\n"
                           f"• Cada aniversariante receberá uma mensagem personalizada",
                color=0x00ff7f
            )
            embed.set_footer(text=f"Configurado por {ctx.author.display_name}")
        else:
            embed = discord.Embed(
                title="❌ Erro de Configuração",
                description="Não foi possível salvar a configuração. Verifique a conexão com o banco de dados.",
                color=0xff4444
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='testeaniversario', aliases=['testbd'])
    @commands.has_permissions(administrator=True)
    async def teste_aniversario(self, ctx):
        """Testa o sistema de mensagens automáticas (apenas admins)"""
        guild_id = str(ctx.guild.id)
        channel_id = await self.get_birthday_channel(guild_id)
        
        if not channel_id:
            embed = discord.Embed(
                title="❌ Canal Não Configurado",
                description="Configure primeiro um canal com `!configurarcanal #canal`",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        channel = ctx.guild.get_channel(int(channel_id))
        if not channel:
            embed = discord.Embed(
                title="❌ Canal Não Encontrado",
                description="O canal configurado não foi encontrado. Configure novamente.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Envia mensagem de teste
        message = self.get_birthday_messages().format(nome=ctx.author.mention)
        
        embed = discord.Embed(
            title="🧪 TESTE - FELIZ ANIVERSÁRIO! 🎉",
            description=f"{message}\n\n⚠️ **Esta é uma mensagem de teste**",
            color=0xFFD700
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"🎂 Teste realizado por {ctx.author.display_name}")
        
        await channel.send(embed=embed)
        
        # Confirma o teste
        embed_confirm = discord.Embed(
            title="✅ Teste Realizado",
            description=f"Mensagem de teste enviada em {channel.mention}!",
            color=0x00ff7f
        )
        await ctx.send(embed=embed_confirm)

    @commands.command(name='statuscanal', aliases=['bdchannelinfo'])
    async def status_canal(self, ctx):
        """Mostra informações sobre o canal de aniversários configurado"""
        guild_id = str(ctx.guild.id)
        channel_id = await self.get_birthday_channel(guild_id)
        
        if not channel_id:
            embed = discord.Embed(
                title="📋 Status do Canal de Aniversários",
                description="❌ **Nenhum canal configurado**\n\n"
                           "Para configurar um canal, use:\n"
                           "`!configurarcanal #canal`",
                color=0xffaa00
            )
        else:
            channel = ctx.guild.get_channel(int(channel_id))
            if channel:
                embed = discord.Embed(
                    title="📋 Status do Canal de Aniversários",
                    description=f"✅ **Canal configurado:** {channel.mention}\n\n"
                               f"🤖 **Funcionamento:**\n"
                               f"• Verificação diária às 9:00\n"
                               f"• Mensagens automáticas para aniversariantes\n"
                               f"• Próxima verificação: {self.check_birthdays.next_iteration.strftime('%d/%m/%Y às %H:%M') if self.check_birthdays.next_iteration else 'Carregando...'}",
                    color=0x00ff7f
                )
            else:
                embed = discord.Embed(
                    title="📋 Status do Canal de Aniversários",
                    description="⚠️ **Canal configurado mas não encontrado**\n\n"
                               "O canal pode ter sido deletado.\n"
                               "Configure novamente com `!configurarcanal #canal`",
                    color=0xffaa00
                )
        
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.command(name='adicionardata', aliases=['addbd'])
    async def adicionar_aniversario(self, ctx, data: str, membro: discord.Member = None):
        """Adiciona uma data de aniversário. Formato: DD/MM"""
        if membro is None:
            membro = ctx.author
        
        # Verifica se o usuário tem permissão para adicionar aniversário de outros
        if membro != ctx.author and not ctx.author.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Apenas administradores podem adicionar aniversários de outros membros.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Valida formato DD/MM
            if '/' not in data or data.count('/') != 1:
                raise ValueError("Formato inválido")
            
            day_str, month_str = data.split('/')
            day, month = int(day_str), int(month_str)
            
            # Valida a data
            if not self.validate_date(day, month):
                raise ValueError("Data inválida")
            
            user_id = str(membro.id)
            guild_id = str(ctx.guild.id)
            success = await self.save_birthday(user_id, membro.display_name, data, day, month, guild_id)
            
            if success:
                embed = discord.Embed(
                    title="🎂 Aniversário Adicionado",
                    description=f"Data de aniversário de **{membro.display_name}** salva: **{data}**\n\n"
                               f"🤖 **Lembrete:** Se o canal de mensagens automáticas estiver configurado, "
                               f"{membro.display_name} receberá parabéns automáticos no dia do aniversário!",
                    color=0x00ff7f
                )
                embed.set_footer(text=f"Adicionado por {ctx.author.display_name}")
            else:
                embed = discord.Embed(
                    title="❌ Erro de Conexão",
                    description="Não foi possível salvar. Verifique a conexão com o banco de dados.",
                    color=0xff4444
                )
            await ctx.send(embed=embed)
            
        except (ValueError, IndexError) as e:
            embed = discord.Embed(
                title="❌ Formato Inválido",
                description="Use o formato **DD/MM** (ex: 15/03)\n\n**Exemplos válidos:**\n• 01/01\n• 15/03\n• 29/02\n• 31/12",
                color=0xff4444
            )
            await ctx.send(embed=embed)

    @commands.command(name='aniversariantes', aliases=['bds'])
    async def listar_aniversariantes(self, ctx):
        """Lista todos os aniversariantes do servidor"""
        guild_id = str(ctx.guild.id)
        birthdays = await self.get_all_birthdays(guild_id)
        
        if not birthdays:
            embed = discord.Embed(
                title="📅 Aniversariantes",
                description="Nenhum aniversário cadastrado ainda.\n\nUse `!adicionardata DD/MM` para cadastrar seu aniversário!",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Ordena por mês e dia
        sorted_birthdays = sorted(
            birthdays,
            key=lambda x: (x['month'], x['day'])
        )
        
        # Agrupa por mês
        months = {}
        for data in sorted_birthdays:
            member = ctx.guild.get_member(int(data['user_id']))
            if member:  # Só mostra se o membro ainda está no servidor
                month_name = calendar.month_name[data['month']]
                if month_name not in months:
                    months[month_name] = []
                months[month_name].append(f"🎉 **{data['name']}** - {data['date']}")
        
        if not months:
            embed = discord.Embed(
                title="📅 Aniversariantes",
                description="Nenhum membro ativo encontrado com aniversário cadastrado.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Cria embed com os aniversariantes agrupados por mês
        description = ""
        for month, members in months.items():
            description += f"\n**{month}**\n"
            description += "\n".join(members) + "\n"
        
        embed = discord.Embed(
            title="🎂 Lista de Aniversariantes",
            description=description.strip(),
            color=0x9966ff
        )
        embed.set_footer(text=f"Total: {len([m for members in months.values() for m in members])} aniversariantes")
        await ctx.send(embed=embed)

    @commands.command(name='meuaniversario', aliases=['mybd'])
    async def meu_aniversario(self, ctx):
        """Mostra seu aniversário cadastrado"""
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        birthday = await self.get_birthday(user_id, guild_id)
        
        if birthday:
            data = birthday['date']
            
            # Calcula próximo aniversário
            hoje = datetime.now()
            try:
                proximo = datetime(hoje.year, birthday['month'], birthday['day'])
                if proximo < hoje:
                    proximo = datetime(hoje.year + 1, birthday['month'], birthday['day'])
                
                dias_restantes = (proximo - hoje).days
                
                if dias_restantes == 0:
                    status = "🎉 **HOJE É SEU ANIVERSÁRIO!** 🎉"
                elif dias_restantes == 1:
                    status = "🎂 Seu aniversário é **amanhã**!"
                else:
                    status = f"🗓️ Faltam **{dias_restantes} dias** para seu aniversário"
                
            except ValueError:
                status = "📅 Aniversário cadastrado"
            
            embed = discord.Embed(
                title="🎂 Seu Aniversário",
                description=f"Sua data cadastrada: **{data}**\n\n{status}",
                color=0x00aaff
            )
        else:
            embed = discord.Embed(
                title="❓ Aniversário Não Encontrado",
                description="Você ainda não cadastrou seu aniversário!\n\nUse `!adicionardata DD/MM` para cadastrar.",
                color=0xffaa00
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='removeraniversario', aliases=['rmbd'])
    async def remover_aniversario(self, ctx, membro: discord.Member = None):
        """Remove um aniversário (próprio ou de outro membro se for admin)"""
        if membro is None:
            membro = ctx.author
        elif membro != ctx.author and not ctx.author.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Apenas administradores podem remover aniversários de outros membros.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        user_id = str(membro.id)
        guild_id = str(ctx.guild.id)
        removed = await self.delete_birthday(user_id, guild_id)
        
        if removed:
            embed = discord.Embed(
                title="🗑️ Aniversário Removido",
                description=f"Aniversário de **{membro.display_name}** foi removido com sucesso.",
                color=0xff6666
            )
            embed.set_footer(text=f"Removido por {ctx.author.display_name}")
        else:
            embed = discord.Embed(
                title="❓ Não Encontrado",
                description=f"**{membro.display_name}** não tem aniversário cadastrado neste servidor.",
                color=0xffaa00
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='proximosaniversarios', aliases=['nextbds'])
    async def proximos_aniversarios(self, ctx, dias: int = 30):
        """Mostra os próximos aniversários (padrão: próximos 30 dias)"""
        if dias < 1 or dias > 365:
            embed = discord.Embed(
                title="❌ Valor Inválido",
                description="O número de dias deve estar entre 1 e 365.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        guild_id = str(ctx.guild.id)
        birthdays = await self.get_all_birthdays(guild_id)
        
        if not birthdays:
            embed = discord.Embed(
                title="📅 Próximos Aniversários",
                description="Nenhum aniversário cadastrado neste servidor.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        hoje = datetime.now()
        proximos = []
        
        for data in birthdays:
            # Calcula próximo aniversário
            try:
                aniversario = datetime(hoje.year, data['month'], data['day'])
                if aniversario < hoje:
                    aniversario = datetime(hoje.year + 1, data['month'], data['day'])
                
                dias_restantes = (aniversario - hoje).days
                if dias_restantes <= dias:
                    member = ctx.guild.get_member(int(data['user_id']))
                    if member:
                        proximos.append((dias_restantes, data['name'], data['date']))
            except ValueError:
                continue  # Data inválida (ex: 29/02 em ano não bissexto)
        
        if not proximos:
            embed = discord.Embed(
                title=f"📅 Próximos Aniversários ({dias} dias)",
                description=f"Nenhum aniversário nos próximos {dias} dias.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Ordena por dias restantes
        proximos.sort(key=lambda x: x[0])
        
        description = ""
        for dias_restantes, nome, data in proximos:
            if dias_restantes == 0:
                description += f"🎉 **{nome}** - **HOJE!** ({data})\n"
            elif dias_restantes == 1:
                description += f"🎂 **{nome}** - **amanhã** ({data})\n"
            else:
                description += f"🗓️ **{nome}** - em **{dias_restantes} dias** ({data})\n"
        
        embed = discord.Embed(
            title=f"📅 Próximos Aniversários ({dias} dias)",
            description=description,
            color=0x00ff7f
        )
        embed.set_footer(text=f"Total: {len(proximos)} aniversários encontrados")
        await ctx.send(embed=embed)

    @commands.command(name='aniversariohoje', aliases=['bdtoday'])
    async def aniversario_hoje(self, ctx):
        """Mostra quem faz aniversário hoje"""
        guild_id = str(ctx.guild.id)
        birthdays = await self.get_all_birthdays(guild_id)
        
        hoje = datetime.now()
        aniversariantes_hoje = []
        
        for data in birthdays:
            if data['day'] == hoje.day and data['month'] == hoje.month:
                member = ctx.guild.get_member(int(data['user_id']))
                if member:
                    aniversariantes_hoje.append(data['name'])
        
        if aniversariantes_hoje:
            nomes = ", ".join([f"**{nome}**" for nome in aniversariantes_hoje])
            embed = discord.Embed(
                title="🎉 Aniversariantes de Hoje!",
                description=f"Parabéns para: {nomes}!\n\nDesejamos um feliz aniversário! 🎂🎈",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="📅 Aniversariantes de Hoje",
                description="Ninguém faz aniversário hoje.",
                color=0xffaa00
            )
        
        await ctx.send(embed=embed)

    async def cog_unload(self):
        """Fecha a conexão com MongoDB quando o cog é descarregado"""
        self.check_birthdays.cancel()
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB (Aniversários) fechada")

async def setup(bot):
    await bot.add_cog(Aniversario(bot))