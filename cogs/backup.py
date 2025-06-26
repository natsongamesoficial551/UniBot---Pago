import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import asyncio
from datetime import datetime
import zipfile
import io

MONGO_URI = os.getenv("MONGO_URI")

class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(MONGO_URI)["backup_bot"]
    
    async def create_full_backup(self, guild, save_to_db=True):
        """Cria backup completo do servidor"""
        backup_data = {
            "_id": str(guild.id),
            "guild_name": guild.name,
            "backup_date": datetime.now().isoformat(),
            "channels": [],
            "roles": [],
            "categories": [],
            "configs": {}
        }
        
        # Backup de categorias
        for category in guild.categories:
            backup_data["categories"].append({
                "name": category.name,
                "position": category.position,
                "overwrites": {str(k.id): dict(v) for k, v in category.overwrites.items()}
            })
        
        # Backup de canais
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                backup_data["channels"].append({
                    "name": channel.name,
                    "type": "text",
                    "topic": channel.topic,
                    "position": channel.position,
                    "category": channel.category.name if channel.category else None,
                    "slowmode": channel.slowmode_delay,
                    "nsfw": channel.nsfw,
                    "overwrites": {str(k.id): dict(v) for k, v in channel.overwrites.items()}
                })
            elif isinstance(channel, discord.VoiceChannel):
                backup_data["channels"].append({
                    "name": channel.name,
                    "type": "voice",
                    "position": channel.position,
                    "category": channel.category.name if channel.category else None,
                    "bitrate": channel.bitrate,
                    "user_limit": channel.user_limit,
                    "overwrites": {str(k.id): dict(v) for k, v in channel.overwrites.items()}
                })
        
        # Backup de cargos
        for role in guild.roles:
            if role != guild.default_role:
                backup_data["roles"].append({
                    "name": role.name,
                    "color": role.color.value,
                    "permissions": role.permissions.value,
                    "position": role.position,
                    "hoist": role.hoist,
                    "mentionable": role.mentionable
                })
        
        # Buscar configs personalizadas do bot
        existing_configs = await self.db.configs.find_one({"_id": str(guild.id)})
        if existing_configs:
            # Remove campos de sistema para pegar apenas as configs personalizadas
            custom_configs = {k: v for k, v in existing_configs.items() 
                            if k not in ["_id", "guild_name", "backup_date", "channels", "roles", "categories"]}
            backup_data["configs"] = custom_configs
        
        # SALVAR NO MONGODB
        if save_to_db:
            try:
                # Salvar backup completo na collection 'backups'
                await self.db.backups.update_one(
                    {"_id": str(guild.id)},
                    {"$set": backup_data},
                    upsert=True
                )
                
                # Manter também na collection 'configs' para compatibilidade
                await self.db.configs.update_one(
                    {"_id": str(guild.id)},
                    {"$set": backup_data},
                    upsert=True
                )
                
                print(f"✅ Backup salvo no MongoDB para guild {guild.id}")
            except Exception as e:
                print(f"❌ Erro ao salvar no MongoDB: {e}")
                raise e
        
        return backup_data
    
    @commands.command(name="backup", aliases=["bkp"])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def backup(self, ctx, tipo="completo"):
        """
        Cria backup do servidor
        Uso: !backup [completo|configs]
        """
        embed = discord.Embed(title="🔄 Criando backup...", color=0x3498db)
        msg = await ctx.send(embed=embed)
        
        try:
            if tipo.lower() == "configs":
                # Backup apenas das configs
                configs = await self.db.configs.find_one({"_id": str(ctx.guild.id)})
                if not configs:
                    embed = discord.Embed(title="❌ Erro", description="Nenhuma configuração encontrada.", color=0xe74c3c)
                    return await msg.edit(embed=embed)
                
                # Criar dados de backup apenas com configs
                backup_data = {
                    "_id": str(ctx.guild.id),
                    "guild_name": ctx.guild.name,
                    "backup_date": datetime.now().isoformat(),
                    "type": "configs_only",
                    "configs": configs
                }
                
                # Salvar no MongoDB
                await self.db.backups.update_one(
                    {"_id": str(ctx.guild.id)},
                    {"$set": backup_data},
                    upsert=True
                )
                
                filename = f"backup_configs_{ctx.guild.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
            else:
                # Backup completo - AGORA SALVA NO MONGODB
                backup_data = await self.create_full_backup(ctx.guild, save_to_db=True)
                filename = f"backup_completo_{ctx.guild.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            # Criar ZIP se arquivo muito grande
            file_size = os.path.getsize(filename)
            if file_size > 8 * 1024 * 1024:  # 8MB
                zip_filename = filename.replace('.json', '.zip')
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(filename, os.path.basename(filename))
                os.remove(filename)
                filename = zip_filename
            
            embed = discord.Embed(
                title="✅ Backup criado com sucesso!",
                description=f"Tipo: {tipo.title()}\nArquivo: `{filename}`\n✅ **Salvo no MongoDB**",
                color=0x2ecc71,
                timestamp=datetime.now()
            )
            
            await msg.edit(embed=embed)
            await ctx.send(file=discord.File(filename))
            os.remove(filename)
            
        except Exception as e:
            embed = discord.Embed(title="❌ Erro ao criar backup", description=f"```{str(e)}```", color=0xe74c3c)
            await msg.edit(embed=embed)
    
    @commands.command(name="restaurar", aliases=["restore"])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 600, commands.BucketType.guild)
    async def restaurar(self, ctx, modo="configs"):
        """
        Restaura backup do servidor
        Uso: !restaurar [configs|canais|cargos|completo]
        """
        if not ctx.message.attachments:
            embed = discord.Embed(
                title="❌ Arquivo necessário",
                description="Envie um arquivo JSON/ZIP de backup junto com o comando.",
                color=0xe74c3c
            )
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(title="🔄 Restaurando backup...", color=0x3498db)
        msg = await ctx.send(embed=embed)
        
        try:
            arquivo = await ctx.message.attachments[0].read()
            
            # Verificar se é ZIP
            if ctx.message.attachments[0].filename.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(arquivo)) as zipf:
                    json_files = [f for f in zipf.namelist() if f.endswith('.json')]
                    if json_files:
                        arquivo = zipf.read(json_files[0])
            
            dados = json.loads(arquivo)
            
            if modo == "configs":
                # Restaurar apenas configs
                configs_data = dados.get("configs", dados)
                await self.db.configs.update_one(
                    {"_id": str(ctx.guild.id)}, 
                    {"$set": configs_data}, 
                    upsert=True
                )
                
                embed = discord.Embed(title="✅ Configurações restauradas!", color=0x2ecc71)
                
            elif modo == "canais" and "channels" in dados:
                # Restaurar canais
                created = 0
                for channel_data in dados["channels"]:
                    if not discord.utils.get(ctx.guild.channels, name=channel_data["name"]):
                        if channel_data["type"] == "text":
                            await ctx.guild.create_text_channel(
                                name=channel_data["name"],
                                topic=channel_data.get("topic"),
                                slowmode_delay=channel_data.get("slowmode", 0)
                            )
                        elif channel_data["type"] == "voice":
                            await ctx.guild.create_voice_channel(
                                name=channel_data["name"],
                                bitrate=channel_data.get("bitrate", 64000),
                                user_limit=channel_data.get("user_limit", 0)
                            )
                        created += 1
                        await asyncio.sleep(1)  # Rate limit
                
                embed = discord.Embed(
                    title="✅ Canais restaurados!",
                    description=f"{created} canais criados.",
                    color=0x2ecc71
                )
                
            elif modo == "cargos" and "roles" in dados:
                # Restaurar cargos
                created = 0
                for role_data in dados["roles"]:
                    if not discord.utils.get(ctx.guild.roles, name=role_data["name"]):
                        await ctx.guild.create_role(
                            name=role_data["name"],
                            color=discord.Color(role_data.get("color", 0)),
                            permissions=discord.Permissions(role_data.get("permissions", 0)),
                            hoist=role_data.get("hoist", False),
                            mentionable=role_data.get("mentionable", False)
                        )
                        created += 1
                        await asyncio.sleep(1)
                
                embed = discord.Embed(
                    title="✅ Cargos restaurados!",
                    description=f"{created} cargos criados.",
                    color=0x2ecc71
                )
                
            elif modo == "completo":
                # Restaurar tudo
                total_restored = 0
                
                # Restaurar configs
                if "configs" in dados:
                    await self.db.configs.update_one(
                        {"_id": str(ctx.guild.id)}, 
                        {"$set": dados["configs"]}, 
                        upsert=True
                    )
                    total_restored += 1
                
                # Restaurar canais
                if "channels" in dados:
                    for channel_data in dados["channels"]:
                        if not discord.utils.get(ctx.guild.channels, name=channel_data["name"]):
                            if channel_data["type"] == "text":
                                await ctx.guild.create_text_channel(name=channel_data["name"])
                            elif channel_data["type"] == "voice":
                                await ctx.guild.create_voice_channel(name=channel_data["name"])
                            total_restored += 1
                            await asyncio.sleep(1)
                
                # Restaurar cargos
                if "roles" in dados:
                    for role_data in dados["roles"]:
                        if not discord.utils.get(ctx.guild.roles, name=role_data["name"]):
                            await ctx.guild.create_role(name=role_data["name"])
                            total_restored += 1
                            await asyncio.sleep(1)
                
                embed = discord.Embed(
                    title="✅ Backup completo restaurado!",
                    description=f"{total_restored} itens restaurados.",
                    color=0x2ecc71
                )
            
            else:
                embed = discord.Embed(
                    title="❌ Modo inválido",
                    description="Use: configs, canais, cargos ou completo",
                    color=0xe74c3c
                )
            
            await msg.edit(embed=embed)
            
        except json.JSONDecodeError:
            embed = discord.Embed(title="❌ Arquivo JSON inválido", color=0xe74c3c)
            await msg.edit(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="❌ Erro na restauração", description=f"```{str(e)}```", color=0xe74c3c)
            await msg.edit(embed=embed)
    
    @commands.command(name="verbackup", aliases=["showbackup", "vbkp"])
    async def verbackup(self, ctx, modo="resumo"):
        """
        Mostra backup salvo
        Uso: !verbackup [resumo|completo]
        """
        # Buscar primeiro na collection 'backups', depois na 'configs'
        backup = await self.db.backups.find_one({"_id": str(ctx.guild.id)})
        if not backup:
            backup = await self.db.configs.find_one({"_id": str(ctx.guild.id)})
        
        if not backup:
            embed = discord.Embed(
                title="❌ Nenhum backup encontrado",
                description="Use `!backup` para criar um backup primeiro.",
                color=0xe74c3c
            )
            return await ctx.send(embed=embed)
        
        if modo == "completo":
            # Mostrar backup completo (limitado)
            backup_str = json.dumps(backup, indent=2, ensure_ascii=False)
            if len(backup_str) > 1900:
                backup_str = backup_str[:1900] + "...\n[TRUNCADO]"
            
            embed = discord.Embed(
                title="🔎 Backup Completo",
                description=f"```json\n{backup_str}```",
                color=0x3498db
            )
        else:
            # Mostrar resumo
            embed = discord.Embed(title="🔎 Resumo do Backup", color=0x3498db)
            
            if "backup_date" in backup:
                embed.add_field(name="📅 Data", value=backup["backup_date"][:19], inline=True)
            
            if "channels" in backup:
                embed.add_field(name="📝 Canais", value=len(backup["channels"]), inline=True)
            
            if "roles" in backup:
                embed.add_field(name="🎭 Cargos", value=len(backup["roles"]), inline=True)
            
            if "categories" in backup:
                embed.add_field(name="📁 Categorias", value=len(backup["categories"]), inline=True)
            
            configs_count = len(backup.get("configs", {}))
            embed.add_field(name="⚙️ Configurações", value=configs_count, inline=True)
            
            # Status do MongoDB
            embed.add_field(name="💾 MongoDB", value="✅ Salvo", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="listarbackups", aliases=["listbkp"])
    @commands.has_permissions(administrator=True)
    async def listar_backups(self, ctx):
        """Lista todos os backups salvos no banco"""
        # Buscar em ambas as collections
        backups_main = await self.db.backups.find({}).to_list(None)
        backups_configs = await self.db.configs.find({}).to_list(None)
        
        # Combinar e remover duplicatas
        all_backups = {}
        for backup in backups_main + backups_configs:
            all_backups[backup["_id"]] = backup
        
        backups = list(all_backups.values())
        
        if not backups:
            embed = discord.Embed(title="❌ Nenhum backup encontrado", color=0xe74c3c)
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(title="📋 Lista de Backups", color=0x3498db)
        
        for backup in backups[:10]:  # Limitar a 10
            guild_name = backup.get("guild_name", "Servidor Desconhecido")
            backup_date = backup.get("backup_date", "Data não disponível")[:10]
            backup_type = backup.get("type", "completo")
            
            embed.add_field(
                name=f"🏰 {guild_name}",
                value=f"ID: `{backup['_id']}`\nData: {backup_date}\nTipo: {backup_type}",
                inline=True
            )
        
        if len(backups) > 10:
            embed.set_footer(text=f"Mostrando 10 de {len(backups)} backups")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="deletarbackup", aliases=["delbkp"])
    @commands.has_permissions(administrator=True)
    async def deletar_backup(self, ctx):
        """Deleta o backup do servidor atual"""
        result1 = await self.db.backups.delete_one({"_id": str(ctx.guild.id)})
        result2 = await self.db.configs.delete_one({"_id": str(ctx.guild.id)})
        
        total_deleted = result1.deleted_count + result2.deleted_count
        
        if total_deleted > 0:
            embed = discord.Embed(
                title="✅ Backup deletado com sucesso!", 
                description=f"{total_deleted} registro(s) removido(s)",
                color=0x2ecc71
            )
        else:
            embed = discord.Embed(title="❌ Nenhum backup encontrado para deletar", color=0xe74c3c)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="testardb", aliases=["testdb"])
    @commands.has_permissions(administrator=True)
    async def testar_db(self, ctx):
        """Testa a conexão com o MongoDB"""
        try:
            # Tentar inserir um documento de teste
            test_doc = {
                "_id": f"test_{ctx.guild.id}",
                "test": True,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.db.test.insert_one(test_doc)
            await self.db.test.delete_one({"_id": f"test_{ctx.guild.id}"})
            
            embed = discord.Embed(
                title="✅ Conexão MongoDB OK!",
                description="Banco de dados está funcionando corretamente.",
                color=0x2ecc71
            )
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro na conexão MongoDB",
                description=f"```{str(e)}```",
                color=0xe74c3c
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Backup(bot))