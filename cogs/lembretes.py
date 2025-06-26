import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

class Lembretes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lembretes_ativos = {}
        print("✅ Cog Lembretes carregado com sucesso")

    @commands.command(name="lembrete")
    async def lembrete(self, ctx, tempo: int, *, mensagem):
        """Define um lembrete que será enviado após X minutos"""
        
        # Validações básicas
        if tempo <= 0:
            await ctx.send("⚠️ O tempo deve ser maior que 0 minutos!")
            return
        
        if tempo > 10080:  # 7 dias em minutos
            await ctx.send("⚠️ O tempo máximo é de 7 dias (10080 minutos)!")
            return

        # Calcula quando o lembrete deve ser executado
        agora = datetime.datetime.now()
        tempo_execucao = agora + datetime.timedelta(minutes=tempo)
        
        # Cria um ID único para o lembrete
        lembrete_id = f"{ctx.author.id}_{int(agora.timestamp())}"
        
        # Armazena o lembrete
        self.lembretes_ativos[lembrete_id] = {
            'user_id': ctx.author.id,
            'channel_id': ctx.channel.id,
            'mensagem': mensagem,
            'tempo_execucao': tempo_execucao,
            'task': None
        }
        
        # Cria e inicia a task do lembrete
        task = asyncio.create_task(self._executar_lembrete_task(lembrete_id, tempo * 60))
        self.lembretes_ativos[lembrete_id]['task'] = task
        
        # Confirma que o lembrete foi criado
        embed = discord.Embed(
            title="⏳ Lembrete Definido",
            description=f"**Mensagem:** {mensagem}",
            color=0x00ff00
        )
        embed.add_field(
            name="⏰ Será executado em:",
            value=tempo_execucao.strftime('%d/%m/%Y às %H:%M:%S'),
            inline=False
        )
        embed.add_field(
            name="🕐 Tempo restante:",
            value=f"{tempo} minutos",
            inline=False
        )
        
        await ctx.send(embed=embed)
        print(f"📝 Lembrete criado: {lembrete_id} - {mensagem}")

    async def _executar_lembrete_task(self, lembrete_id, segundos):
        """Task que aguarda e executa o lembrete"""
        try:
            # Aguarda o tempo especificado
            await asyncio.sleep(segundos)
            
            # Verifica se o lembrete ainda existe (não foi cancelado)
            if lembrete_id not in self.lembretes_ativos:
                return
            
            lembrete = self.lembretes_ativos[lembrete_id]
            
            # Busca o usuário
            user = self.bot.get_user(lembrete['user_id'])
            if not user:
                user = await self.bot.fetch_user(lembrete['user_id'])
            
            mensagem = f"⏰ **Lembrete:** {lembrete['mensagem']}"
            
            # Tenta enviar por DM primeiro
            try:
                await user.send(mensagem)
                print(f"✅ Lembrete enviado por DM: {lembrete_id}")
            except discord.Forbidden:
                # Se falhar, envia no canal original
                channel = self.bot.get_channel(lembrete['channel_id'])
                if channel:
                    await channel.send(f"{user.mention} {mensagem}")
                    print(f"✅ Lembrete enviado no canal: {lembrete_id}")
            
            # Remove o lembrete da lista de ativos
            del self.lembretes_ativos[lembrete_id]
            
        except asyncio.CancelledError:
            print(f"❌ Lembrete cancelado: {lembrete_id}")
        except Exception as e:
            print(f"❌ Erro ao executar lembrete {lembrete_id}: {e}")
            # Remove o lembrete mesmo em caso de erro
            if lembrete_id in self.lembretes_ativos:
                del self.lembretes_ativos[lembrete_id]

    @commands.command(name="meuslembretes")
    async def meuslembretes(self, ctx):
        """Lista todos os lembretes ativos do usuário"""
        lembretes_usuario = []
        
        for lembrete_id, lembrete in self.lembretes_ativos.items():
            if lembrete['user_id'] == ctx.author.id:
                lembretes_usuario.append((lembrete_id, lembrete))
        
        if not lembretes_usuario:
            await ctx.send("📭 Você não tem lembretes ativos.")
            return
        
        embed = discord.Embed(
            title="📌 Seus Lembretes Ativos",
            color=0x0099ff
        )
        
        for i, (lembrete_id, lembrete) in enumerate(lembretes_usuario[:5], 1):
            mensagem = lembrete['mensagem']
            tempo_execucao = lembrete['tempo_execucao']
            
            # Limita o tamanho da mensagem
            if len(mensagem) > 50:
                mensagem = mensagem[:50] + "..."
            
            embed.add_field(
                name=f"#{i}",
                value=f"**{mensagem}**\n🕐 {tempo_execucao.strftime('%d/%m/%Y às %H:%M:%S')}",
                inline=False
            )
        
        if len(lembretes_usuario) > 5:
            embed.set_footer(text=f"Mostrando 5 de {len(lembretes_usuario)} lembretes ativos")
        
        await ctx.send(embed=embed)

    @commands.command(name="cancelarlembrete")
    async def cancelar_lembrete(self, ctx, numero: int = None):
        """Cancela um lembrete específico"""
        if numero is None:
            await ctx.send("⚠️ Uso: `!cancelarlembrete <número>`\nUse `!meuslembretes` para ver os números.")
            return
        
        lembretes_usuario = []
        for lembrete_id, lembrete in self.lembretes_ativos.items():
            if lembrete['user_id'] == ctx.author.id:
                lembretes_usuario.append((lembrete_id, lembrete))
        
        if not lembretes_usuario or numero < 1 or numero > len(lembretes_usuario):
            await ctx.send("❌ Número de lembrete inválido. Use `!meuslembretes` para ver seus lembretes.")
            return
        
        lembrete_id, lembrete = lembretes_usuario[numero - 1]
        
        # Cancela a task
        if lembrete['task']:
            lembrete['task'].cancel()
        
        # Remove da lista
        del self.lembretes_ativos[lembrete_id]
        
        await ctx.send(f"✅ Lembrete #{numero} cancelado com sucesso!")

    @commands.command(name="limparlembretes")
    async def limpar_lembretes(self, ctx):
        """Cancela todos os lembretes do usuário"""
        cancelados = 0
        
        # Cria uma lista dos IDs para evitar modificar durante iteração
        ids_para_remover = []
        
        for lembrete_id, lembrete in self.lembretes_ativos.items():
            if lembrete['user_id'] == ctx.author.id:
                ids_para_remover.append(lembrete_id)
        
        # Cancela e remove cada lembrete
        for lembrete_id in ids_para_remover:
            lembrete = self.lembretes_ativos[lembrete_id]
            if lembrete['task']:
                lembrete['task'].cancel()
            del self.lembretes_ativos[lembrete_id]
            cancelados += 1
        
        if cancelados > 0:
            await ctx.send(f"✅ {cancelados} lembrete(s) cancelado(s) com sucesso!")
        else:
            await ctx.send("📭 Você não tinha lembretes ativos para cancelar.")

    def cog_unload(self):
        """Cancela todas as tasks quando o cog é descarregado"""
        print("🔄 Descarregando cog Lembretes...")
        for lembrete in self.lembretes_ativos.values():
            if lembrete['task']:
                lembrete['task'].cancel()
        self.lembretes_ativos.clear()


async def setup(bot):
    await bot.add_cog(Lembretes(bot))
    print("✅ Cog Lembretes adicionado ao bot")

# Bot principal (para teste direto)
if __name__ == "__main__":
    print("🚀 Iniciando bot...")
    
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f'🤖 Bot conectado como {bot.user}')
        await setup(bot)
    
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠️ Argumento obrigatório faltando: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("⚠️ Argumento inválido. Verifique o formato do comando.")
        else:
            print(f"Erro não tratado: {error}")
            await ctx.send("❌ Ocorreu um erro inesperado.")
    
    # Executa o bot
    discord_token = os.getenv('DISCORD_TOKEN')
    if discord_token:
        print("🔑 Token encontrado, iniciando bot...")
        bot.run(discord_token)
    else:
        print("❌ DISCORD_TOKEN não encontrado no arquivo .env")
        print("📝 Crie um arquivo .env com: DISCORD_TOKEN=seu_token_aqui")