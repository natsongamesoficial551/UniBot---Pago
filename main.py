import os
import discord
from discord.ext import commands
from flask import Flask
import asyncio
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient  # MongoDB

# Carregar variáveis do .env
load_dotenv()

TOKEN = os.getenv("TOKEN")
AUTOPING = os.getenv("AUTOPING")
MONGO_URL = os.getenv("MONGO_URL")  # URL de conexão MongoDB Atlas

# Intents e prefixo
intents = discord.Intents.all()

# Flask App para manter online no Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot está rodando com sucesso! ✅"

# Tarefa de auto-ping a cada 5 minutos
async def auto_ping():
    import aiohttp
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                await session.get(AUTOPING)
                print("[AutoPing] Ping enviado com sucesso.")
        except Exception as e:
            print(f"[AutoPing] Erro ao enviar ping: {e}")
        await asyncio.sleep(300)  # 5 minutos

# Bot customizado com conexão ao Mongo e setup_hook
class CustomBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_client = AsyncIOMotorClient(MONGO_URL, tls=True, tlsAllowInvalidCertificates=True)
        self.db = self.db_client["natanbot"]  # Nome do banco de dados

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"[COG] Carregado: {filename}")
                except Exception as e:
                    print(f"[ERRO] Ao carregar {filename}: {e}")

        self.loop.create_task(auto_ping())

# Instância do bot
bot = CustomBot(command_prefix="!", intents=intents)

# Iniciar Flask + Bot
if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    asyncio.run(bot.start(TOKEN))
