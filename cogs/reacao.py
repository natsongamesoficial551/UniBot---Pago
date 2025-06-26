import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

class RoleManager(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.mongo_client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
        self.db = self.mongo_client.discord_bot
        self.collection = self.db.cargos_reacao

    @discord.ui.button(label='⚙️ Gerenciar Cargos', style=discord.ButtonStyle.secondary, custom_id='manage_roles')
    async def manage_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ Você não tem permissão para gerenciar cargos.", ephemeral=True)
        
        modal = RoleConfigModal(self.bot, interaction.message.id)
        await interaction.response.send_modal(modal)

class RoleConfigModal(discord.ui.Modal, title='Configurar Cargo por Reação'):
    def __init__(self, bot, message_id):
        super().__init__()
        self.bot = bot
        self.message_id = message_id
        self.mongo_client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
        self.db = self.mongo_client.discord_bot
        self.collection = self.db.cargos_reacao

    emoji = discord.ui.TextInput(
        label='Emoji',
        placeholder='Digite o emoji (ex: 🎯, ⚡, 🔥)',
        required=True,
        max_length=10
    )
    
    role_name = discord.ui.TextInput(
        label='Nome do Cargo',
        placeholder='Digite o nome exato do cargo',
        required=True,
        max_length=100
    )
    
    description = discord.ui.TextInput(
        label='Descrição do Cargo',
        placeholder='Breve descrição do que este cargo representa',
        required=False,
        max_length=150,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=self.role_name.value)
        
        if not role:
            return await interaction.response.send_message(f"❌ Cargo `{self.role_name.value}` não encontrado!", ephemeral=True)
        
        try:
            message = await interaction.channel.fetch_message(self.message_id)
            await message.add_reaction(self.emoji.value)
            
            # Salvar no banco
            await self.collection.update_one(
                {"message_id": self.message_id},
                {
                    "$set": {
                        f"reactions.{self.emoji.value}": {
                            "role_id": role.id,
                            "role_name": role.name,
                            "description": self.description.value or f"Cargo {role.name}"
                        },
                        "guild_id": guild.id
                    }
                },
                upsert=True
            )
            
            # Atualizar embed
            await self.update_embed(message)
            
            embed = discord.Embed(
                title="✅ Configuração Salva",
                description=f"{self.emoji.value} **{role.name}**\n{self.description.value or 'Sem descrição'}",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message("❌ Erro ao configurar reação", ephemeral=True)

    async def update_embed(self, message):
        data = await self.collection.find_one({"message_id": message.id})
        if not data:
            return
            
        reactions = data.get("reactions", {})
        
        embed = discord.Embed(
            title="🎭 Painel de Cargos",
            description="**Reaja para receber/remover cargos:**",
            color=0x5865f2
        )
        
        if reactions:
            roles_text = ""
            for emoji, role_data in reactions.items():
                if isinstance(role_data, dict):
                    desc = role_data.get("description", "")
                    roles_text += f"{emoji} **{role_data['role_name']}**\n{desc}\n\n"
                else:
                    # Compatibilidade com formato antigo
                    guild = message.guild
                    role = guild.get_role(role_data)
                    if role:
                        roles_text += f"{emoji} **{role.name}**\n\n"
            
            embed.add_field(name="📋 Cargos Disponíveis", value=roles_text or "Nenhum cargo configurado", inline=False)
        else:
            embed.add_field(name="📋 Cargos Disponíveis", value="*Use o botão abaixo para configurar*", inline=False)
        
        embed.set_footer(text="💡 Clique no botão para gerenciar • Sistema automático")
        
        view = RoleManager(None, message.guild.id)
        await message.edit(embed=embed, view=view)

class CargosReacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
        self.db = self.mongo_client.discord_bot
        self.collection = self.db.cargos_reacao
        self.config_collection = self.db.config_cargos
        print("✅ Sistema Profissional de Cargos carregado")

    async def get_config(self, guild_id):
        config = await self.config_collection.find_one({"guild_id": guild_id})
        return config or {}

    async def update_config(self, guild_id, data):
        await self.config_collection.update_one(
            {"guild_id": guild_id}, 
            {"$set": data}, 
            upsert=True
        )

    @commands.group(name="roles", invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def roles_group(self, ctx):
        embed = discord.Embed(
            title="🎭 Sistema Profissional de Cargos",
            description="**Comandos disponíveis:**",
            color=0x5865f2
        )
        embed.add_field(
            name="📚 Configuração",
            value="`!roles setup <#canal>` - Configurar sistema\n`!roles panel` - Criar painel interativo\n`!roles remove <msg_id> <emoji>` - Remover cargo",
            inline=False
        )
        embed.add_field(
            name="💡 Como usar",
            value="1. Configure o canal com `!roles setup`\n2. Crie o painel com `!roles panel`\n3. Use o botão para adicionar cargos\n4. Usuários reagem para receber cargos",
            inline=False
        )
        embed.set_footer(text="Sistema automatizado • Interface moderna")
        await ctx.send(embed=embed)

    @roles_group.command(name="setup")
    @commands.has_permissions(manage_roles=True)
    async def setup_system(self, ctx, canal: discord.TextChannel):
        await self.update_config(ctx.guild.id, {"canal_painel": canal.id})
        
        embed = discord.Embed(
            title="✅ Sistema Configurado",
            description=f"**Canal configurado:** {canal.mention}\n\nUse `!roles panel` para criar o painel interativo.",
            color=0x00ff00
        )
        embed.set_footer(text="Próximo passo: criar painel")
        await ctx.send(embed=embed)

    @roles_group.command(name="panel")
    @commands.has_permissions(manage_roles=True)
    async def create_panel(self, ctx):
        config = await self.get_config(ctx.guild.id)
        canal_id = config.get("canal_painel")
        
        if not canal_id:
            embed = discord.Embed(
                title="❌ Configuração Necessária",
                description="Configure o canal primeiro:\n`!roles setup <#canal>`",
                color=0xff0000
            )
            return await ctx.send(embed=embed)
        
        canal = self.bot.get_channel(canal_id)
        
        embed = discord.Embed(
            title="🎭 Painel de Cargos",
            description="**Reaja para receber/remover cargos:**",
            color=0x5865f2
        )
        embed.add_field(
            name="📋 Cargos Disponíveis", 
            value="*Use o botão abaixo para configurar*", 
            inline=False
        )
        embed.set_footer(text="💡 Clique no botão para gerenciar • Sistema automático")
        
        view = RoleManager(self.bot, ctx.guild.id)
        msg = await canal.send(embed=embed, view=view)
        
        embed_success = discord.Embed(
            title="✅ Painel Criado",
            description=f"**Canal:** {canal.mention}\n**ID:** `{msg.id}`\n\n*Use o botão no painel para adicionar cargos*",
            color=0x00ff00
        )
        embed_success.set_footer(text="Painel pronto para uso")
        await ctx.send(embed=embed_success)

    @roles_group.command(name="remove")
    @commands.has_permissions(manage_roles=True)
    async def remove_role_reaction(self, ctx, msg_id: int, emoji: str):
        result = await self.collection.update_one(
            {"message_id": msg_id},
            {"$unset": {f"reactions.{emoji}": ""}}
        )
        
        if result.modified_count:
            try:
                config = await self.get_config(ctx.guild.id)
                canal = self.bot.get_channel(config.get("canal_painel"))
                message = await canal.fetch_message(msg_id)
                
                modal = RoleConfigModal(self.bot, msg_id)
                await modal.update_embed(message)
                
                embed = discord.Embed(
                    title="✅ Cargo Removido",
                    description=f"Emoji {emoji} removido do painel",
                    color=0x00ff00
                )
            except:
                embed = discord.Embed(
                    title="✅ Cargo Removido",
                    description=f"Emoji {emoji} removido (painel pode precisar de atualização manual)",
                    color=0x00ff00
                )
        else:
            embed = discord.Embed(
                title="❌ Não Encontrado",
                description="Reação não encontrada no sistema",
                color=0xff0000
            )
        
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member and payload.member.bot:
            return
            
        data = await self.collection.find_one({"message_id": payload.message_id})
        if not data or str(payload.emoji) not in data.get("reactions", {}):
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        reaction_data = data["reactions"][str(payload.emoji)]
        
        if isinstance(reaction_data, dict):
            role_id = reaction_data["role_id"]
        else:
            role_id = reaction_data
            
        role = guild.get_role(role_id)
        
        if role and role not in payload.member.roles:
            await payload.member.add_roles(role, reason="Sistema de cargos por reação")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        data = await self.collection.find_one({"message_id": payload.message_id})
        if not data or str(payload.emoji) not in data.get("reactions", {}):
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        
        if not member:
            return
            
        reaction_data = data["reactions"][str(payload.emoji)]
        
        if isinstance(reaction_data, dict):
            role_id = reaction_data["role_id"]
        else:
            role_id = reaction_data
            
        role = guild.get_role(role_id)
        
        if role and role in member.roles:
            await member.remove_roles(role, reason="Sistema de cargos por reação")

async def setup(bot):
    await bot.add_cog(CargosReacao(bot))
    print("✅ Sistema Profissional de Cargos ativado")