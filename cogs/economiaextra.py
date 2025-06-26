import discord
from discord.ext import commands
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
from datetime import datetime, timedelta

class EconomySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.collection = None
        self._connection_ready = False
        self.bot.loop.create_task(self.init_database())

    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada nas variáveis de ambiente!")
                return
            
            print("🔄 Conectando ao MongoDB (Economy)...")
            self.client = AsyncIOMotorClient(mongo_uri)
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.collection = self.db['economy_data']
            self._connection_ready = True
            
            print("✅ Conectado ao MongoDB (Economy) com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB (Economy): {e}")
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
                
            data = await self.collection.find_one({"user_id": str(user_id), "guild_id": str(guild_id)})
            return data if data else {}
            
        except Exception as e:
            print(f"❌ Erro ao buscar dados do usuário: {e}")
            return {}

    async def update_user_data(self, user_id, guild_id, update_data):
        """Atualiza dados do usuário no MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
            
            await self.collection.update_one(
                {"user_id": str(user_id), "guild_id": str(guild_id)},
                {"$set": update_data},
                upsert=True
            )
            return True
                
        except Exception as e:
            print(f"❌ Erro ao atualizar dados do usuário: {e}")
            return False



    @commands.command(name='presentear')
    async def presentear(self, ctx, membro: discord.Member, quantia: int):
        """Presenteia outro membro com dinheiro"""
        if membro == ctx.author:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Você não pode presentear a si mesmo!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if quantia <= 0:
            embed = discord.Embed(
                title="❌ Quantia Inválida",
                description="A quantia deve ser maior que zero!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Busca dados de ambos usuários
        sender_data = await self.get_user_data(ctx.author.id, ctx.guild.id)
        receiver_data = await self.get_user_data(membro.id, ctx.guild.id)

        sender_balance = sender_data.get('saldo', 0)
        
        if sender_balance < quantia:
            embed = discord.Embed(
                title="❌ Saldo Insuficiente",
                description=f"Você tem apenas R$ {sender_balance:,}!\nQuantia solicitada: R$ {quantia:,}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Realiza a transferência
        new_sender_balance = sender_balance - quantia
        new_receiver_balance = receiver_data.get('saldo', 0) + quantia

        sender_success = await self.update_user_data(ctx.author.id, ctx.guild.id, {'saldo': new_sender_balance})
        receiver_success = await self.update_user_data(membro.id, ctx.guild.id, {'saldo': new_receiver_balance})

        if sender_success and receiver_success:
            embed = discord.Embed(
                title="🎁 Presente Enviado!",
                description=f"**{ctx.author.mention}** presenteou **{membro.mention}** com R$ {quantia:,}!",
                color=discord.Color.green()
            )
            embed.add_field(name="💰 Seu Saldo", value=f"R$ {new_sender_balance:,}", inline=True)
            embed.add_field(name="🎯 Saldo do Presenteado", value=f"R$ {new_receiver_balance:,}", inline=True)
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível processar o presente.",
                color=discord.Color.red()
            )

        await ctx.send(embed=embed)

    @commands.command(name='transferir')
    async def transferir(self, ctx, membro: discord.Member, quantia: int):
        """Transfere dinheiro para outro membro"""
        if membro == ctx.author:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Você não pode transferir dinheiro para si mesmo!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if quantia <= 0:
            embed = discord.Embed(
                title="❌ Quantia Inválida",
                description="A quantia deve ser maior que zero!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Taxa de transferência (2%)
        taxa = max(1, int(quantia * 0.02))
        total_necessario = quantia + taxa

        sender_data = await self.get_user_data(ctx.author.id, ctx.guild.id)
        receiver_data = await self.get_user_data(membro.id, ctx.guild.id)

        sender_balance = sender_data.get('saldo', 0)
        
        if sender_balance < total_necessario:
            embed = discord.Embed(
                title="❌ Saldo Insuficiente",
                description=f"Você precisa de R$ {total_necessario:,}!\n(R$ {quantia:,} + R$ {taxa:,} de taxa)\nSeu saldo: R$ {sender_balance:,}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Realiza a transferência
        new_sender_balance = sender_balance - total_necessario
        new_receiver_balance = receiver_data.get('saldo', 0) + quantia

        sender_success = await self.update_user_data(ctx.author.id, ctx.guild.id, {'saldo': new_sender_balance})
        receiver_success = await self.update_user_data(membro.id, ctx.guild.id, {'saldo': new_receiver_balance})

        if sender_success and receiver_success:
            embed = discord.Embed(
                title="💸 Transferência Realizada!",
                description=f"**{ctx.author.mention}** transferiu R$ {quantia:,} para **{membro.mention}**",
                color=discord.Color.green()
            )
            embed.add_field(name="💰 Seu Saldo", value=f"R$ {new_sender_balance:,}", inline=True)
            embed.add_field(name="🎯 Saldo do Destinatário", value=f"R$ {new_receiver_balance:,}", inline=True)
            embed.add_field(name="📊 Taxa Cobrada", value=f"R$ {taxa:,} (2%)", inline=True)
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível processar a transferência.",
                color=discord.Color.red()
            )

        await ctx.send(embed=embed)



    async def cog_unload(self):
        """Fecha a conexão com MongoDB quando o cog é descarregado"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB (Economy) fechada")

async def setup(bot):
    await bot.add_cog(EconomySystem(bot))