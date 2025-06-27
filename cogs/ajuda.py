import discord
from discord.ext import commands

class Ajuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Dicionário com todas as categorias e seus comandos
        self.categorias = {
            "aniversario": {
                "emoji": "🎉",
                "nome": "Aniversário",
                "comandos": {
                    "🛠️ **Configuração:**": [
                        "`!configurarcanal`, `!setbdchannel` - Define canal de aniversários",
                        "`!testeaniversario`, `!testbd` - Testa mensagem de aniversário",
                        "`!statuscanal`, `!bdchannelinfo` - Mostra status do canal"
                    ],
                    "🗂️ **Gerenciamento:**": [
                        "`!adicionardata <DD/MM>`, `!addbd <DD/MM>` - Adiciona seu aniversário",
                        "`!removeraniversario`, `!rmbd` - Remove seu aniversário"
                    ],
                    "🔍 **Consulta:**": [
                        "`!aniversariantes`, `!bds` - Lista todos os aniversários",
                        "`!meuaniversario`, `!mybd` - Mostra seu aniversário",
                        "`!proximosaniversarios`, `!nextbds` - Próximos aniversários",
                        "`!aniversariohoje`, `!bdtoday` - Aniversários de hoje"
                    ]
                }
            },
            "antipalavrao": {
                "emoji": "🛡️",
                "nome": "Anti-palavrão",
                "comandos": {
                    "🚫 **Filtro de Palavrões:**": [
                        "`!adicionarpalavrao <palavra>` - Adiciona palavra à lista",
                        "`!removerpalavrao <palavra>` - Remove palavra da lista",
                        "`!palavroes` - Mostra lista de palavrões",
                        "`!togglefiltro` - Liga/desliga o filtro"
                    ]
                }
            },
            "sorteios": {
                "emoji": "🎁",
                "nome": "Sorteios",
                "comandos": {
                    "🎲 **Gerenciar Sorteios:**": [
                        "`!comecarsorteio <premio>` - Inicia um sorteio",
                        "`!vencedor` - Sorteia um vencedor",
                        "`!encerrarsorteio` - Encerra o sorteio atual",
                        "`!canaldecomando #canal` - Define canal de comandos",
                        "`!canaldosorteio #canal` - Define canal do sorteio"
                    ]
                }
            },
            "xp": {
                "emoji": "📈",
                "nome": "Sistema XP",
                "comandos": {
                    "⚙️ **Configuração XP:**": [
                        "`!mensagemporxp <min> <max>` - XP por mensagem",
                        "`!basexp <valor>` - XP base para subir de nível",
                        "`!adicionarxppornivel <valor>` - XP adicional por nível",
                        "`!tempodexp <normal> [vip]` - Tempo entre ganhos de XP",
                        "`!configxp` - Mostra configurações atuais"
                    ]
                }
            },
            "vip": {
                "emoji": "💎",
                "nome": "Sistema VIP",
                "comandos": {
                    "👑 **Gerenciar VIP:**": [
                        "`!vip @user dias` - Adiciona VIP a usuário",
                        "`!removervip @user` - Remove VIP de usuário",
                        "`!configvip` - Configurações VIP",
                        "`!cargovip <ID>` - Define cargo VIP",
                        "`!listvip` - Lista usuários VIP",
                        "`!checkvip [@user]` - Verifica status VIP"
                    ]
                }
            },
            "moderacao": {
                "emoji": "🔨",
                "nome": "Moderação",
                "comandos": {
                    "⚖️ **Punições:**": [
                        "`!aviso @user [motivo]` - Aplica aviso",
                        "`!removeraviso @user [número]` - Remove aviso",
                        "`!avisos [@user]` - Lista avisos",
                        "`!mutar @user tempo [motivo]` - Muta usuário",
                        "`!desmutar @user` - Desmuta usuário"
                    ],
                    "🚫 **Ações Severas:**": [
                        "`!banir @user` - Bane usuário",
                        "`!expulsar @user` - Expulsa usuário",
                        "`!limparmensagem [quantidade]` - Limpa mensagens",
                        "`!configmod` - Configurações de moderação"
                    ]
                }
            },
            "boasvindas": {
                "emoji": "👋",
                "nome": "Boas-vindas",
                "comandos": {
                    "🚪 **Configurar Mensagens:**": [
                        "`!canalconfig #canal` - Canal de configuração",
                        "`!canalentrada #canal` - Canal de entrada",
                        "`!canalsaida #canal` - Canal de saída",
                        "`!msgentrada <mensagem>` - Mensagem de entrada",
                        "`!msgsaida <mensagem>` - Mensagem de saída"
                    ],
                    "🧪 **Testes:**": [
                        "`!configmsg` - Ver configurações",
                        "`!testentrada` - Testar entrada",
                        "`!testsaida` - Testar saída"
                    ]
                }
            },
            "economia": {
                "emoji": "💰",
                "nome": "Economia",
                "comandos": {
                    "💵 **Básico:**": [
                        "`!saldo`, `!bal` - Ver saldo",
                        "`!diario`, `!daily` - Bônus diário",
                        "`!inventario`, `!inv` - Ver inventário",
                        "`!depositar <valor>`, `!dep <valor>` - Depositar no banco",
                        "`!sacar <valor>`, `!withdraw <valor>` - Sacar do banco"
                    ],
                    "💼 **Trabalho:**": [
                        "`!trabalhar`, `!work` - Trabalhar",
                        "`!empregos`, `!jobs` - Ver empregos",
                        "`!contratar @user`, `!hire @user` - Contratar funcionário",
                        "`!demitir @user`, `!fire @user` - Demitir funcionário"
                    ],
                    "🛒 **Loja:**": [
                        "`!loja`, `!shop` - Ver loja",
                        "`!comprar <item>`, `!buy <item>` - Comprar item",
                        "`!vender <item>`, `!sell <item>` - Vender item"
                    ],
                    "🎰 **Riscos:**": [
                        "`!crime` - Cometer crime",
                        "`!roubar @user`, `!rob @user` - Roubar usuário",
                        "`!apostar <valor>`, `!bet <valor>` - Apostar dinheiro"
                    ]
                }
            },
            "diversao": {
                "emoji": "🎮",
                "nome": "Diversão",
                "comandos": {
                    "⚙️ **Configuração:**": [
                        "`!setlang en/pt` - Define idioma | Set language"
                    ],
                    "🎲 **Jogos | Games:**": [
                        "`!dado [lados]`, `!dice [sides]` - Rolar dado | Roll dice",
                        "`!moeda`, `!coin` - Cara ou coroa | Flip coin",
                        "`!rps <opção>`, `!rps <option>` - Pedra, papel, tesoura | Rock, paper, scissors",
                        "`!8ball <pergunta>`, `!8ball <question>` - Bola 8 mágica | Magic 8-ball",
                        "`!aleatorio [min] [max]`, `!random [min] [max]` - Número aleatório | Random number"
                    ],
                    "😄 **Entretenimento | Entertainment:**": [
                        "`!piada`, `!joke` - Piada aleatória | Tell a joke",
                        "`!curiosidade`, `!fact` - Curiosidade | Interesting fact",
                        "`!pergunta`, `!question` - Pergunta aleatória | Random question",
                        "`!escolher <opções>`, `!choose <options>` - Escolher opção | Choose option",
                        "`!love @user1 @user2` - Calculadora do amor | Love calculator",
                        "`!motivar [@usuário]`, `!motivate [@user]` - Frase motivacional | Motivational phrase",
                        "`!clima`, `!mood` - Clima do servidor | Server mood",
                        "`!estatisticas`, `!stats` - Estatísticas do sistema | System statistics"
                    ]
                }
            },
            "utilidades": {
                "emoji": "🔧",
                "nome": "Utilidades",
                "comandos": {
                    "ℹ️ **Informações:**": [
                        "`!botinfo` - Info do bot",
                        "`!userinfo [@user]` - Info do usuário",
                        "`!serverinfo` - Info do servidor",
                        "`!ping` - Latência do bot",
                        "`!uptime` - Tempo online"
                    ],
                    "🖼️ **Perfil:**": [
                        "`!avatar [@user]` - Avatar do usuário",
                        "`!banner [@user]` - Banner do usuário",
                        "`!membercount` - Contador de membros"
                    ]
                }
            },
            "lembretes": {
                "emoji": "⏰",
                "nome": "Lembretes",
                "comandos": {
                    "📝 **Gerenciar Lembretes:**": [
                        "`!lembrete <minutos> <mensagem>` - Define lembrete pessoal",
                        "`!meuslembretes` - Mostra info sobre lembretes"
                    ]
                }
            },
            "eventos": {
                "emoji": "📅",
                "nome": "Eventos",
                "comandos": {
                    "⚙️ **Configuração:**": [
                        "`!configcanal #eventos` - Define canal de eventos",
                        "`!configaviso #avisos` - Define canal de avisos"
                    ],
                    "📋 **Gerenciamento:**": [
                        "`!criarevento <DD/MM/AAAA> <HH:MM> <nome>` - Cria evento",
                        "`!eventos` - Lista todos os eventos",
                        "`!detalhesevento <ID>` - Mostra detalhes do evento",
                        "`!removerevento <ID>` - Remove evento"
                    ]
                }
            },
            "sugestoes": {
                "emoji": "💡",
                "nome": "Sugestões",
                "comandos": {
                    "🔧 **Configuração (Admin):**": [
                        "`!config_sugestoes [#canal]` - Define canal de sugestões"
                    ],
                    "📝 **Para Usuários:**": [
                        "`!sugerir <texto>` - Envia nova sugestão (máx. 1000 chars)",
                        "`!ver_sugestoes [@usuário]` - Ver últimas 10 sugestões"
                    ],
                    "👨‍💼 **Moderação:**": [
                        "`!aprovar <id_mensagem>` - Aprova sugestão",
                        "`!rejeitar <id_mensagem> [motivo]` - Rejeita sugestão",
                        "`!stats_sugestoes` - Estatísticas do servidor",
                        "`!limpar_sugestoes` - Remove TODAS as sugestões"
                    ]
                }
            },
            "backup": {
                "emoji": "💾",
                "nome": "Backup",
                "comandos": {
                    "📋 **Gerenciar Backup:**": [
                        "`!backup [tipo]`, `!bkp [tipo]` - Cria backup",
                        "`!restaurar [modo]`, `!restore [modo]` - Restaura backup",
                        "`!verbackup [modo]`, `!vbkp [modo]` - Mostra backup salvo"
                    ],
                    "🗂️ **Administração:**": [
                        "`!listarbackups`, `!listbkp` - Lista todos os backups",
                        "`!deletarbackup`, `!delbkp` - Deleta backup do servidor"
                    ]
                }
            },
            "cargoreacao": {
                "emoji": "🎯",
                "nome": "Cargo por Reação",
                "comandos": {
                    "⚙️ **Configuração:**": [
                        "`!roles` - Ver comandos disponíveis",
                        "`!roles setup #canal` - Configurar sistema"
                    ],
                    "🎭 **Painel Interativo:**": [
                        "`!roles panel` - Criar painel",
                        "**Clicar no botão** no painel para adicionar cargos"
                    ],
                    "🔧 **Gerenciamento:**": [
                        "`!roles remove` - Apenas se precisar remover algo"
                    ]
                }
            },
            "embeds": {
                "emoji": "📝",
                "nome": "Embeds Personalizadas",
                "comandos": {
                    "✨ **Criar Embeds:**": [
                        "`!embed <mensagem>` - Cria embed personalizada"
                    ]
                }
            },
            "mensagensautomaticas": {
                "emoji": "🔄",
                "nome": "Mensagens Automáticas",
                "comandos": {
                    "⚙️ **Configuração:**": [
                        "`!adicionarmensagem <horas> <mensagem>`, `!addmsg <horas> <mensagem>` - Adiciona mensagem automática",
                        "`!removermensagem <parte da mensagem>`, `!rmmsg <parte da mensagem>` - Remove mensagem automática",
                        "`!testmensagem <parte da mensagem>`, `!testmsg <parte da mensagem>` - Testa mensagem automática"
                    ],
                    "📋 **Gerenciamento:**": [
                        "`!mensagens`, `!listmsg` - Lista todas as mensagens automáticas",
                        "`!statusmsg` - Verifica status da conexão com banco de dados"
                    ]
                }
            }
        }
        
        # Categorias especiais (não incluídas no dicionário principal)
        self.categorias_especiais = {
            "roleplay": {
                "emoji": "🎭", 
                "nome": "Roleplay",
                "aliases": ["rp"]
            },
            "logs": {
                "emoji": "📜", 
                "nome": "Sistema de Logs",
                "aliases": ["log"]
            },
            "tickets": {
                "emoji": "🎫", 
                "nome": "Sistema de Tickets",
                "aliases": ["ticket"]
            },
            "status": {
                "emoji": "📡", 
                "nome": "Status do Bot",
                "aliases": []
            }
        }

    @commands.command(name="cmds", aliases=["comandos", "categorias"])
    async def listar_categorias(self, ctx):
        """Lista todas as categorias disponíveis"""
        embed = discord.Embed(
            title="📚 Categorias de Comandos",
            description="Use `!ajuda <categoria>` para ver os comandos específicos\n"
                       "Exemplo: `!ajuda economia`",
            color=discord.Color.gold()
        )
        
        # Categorias principais - Página 1
        categorias_p1 = ""
        count = 0
        for key, categoria in list(self.categorias.items())[:8]:
            categorias_p1 += f"{categoria['emoji']} **{categoria['nome']}** - `{key}`\n"
            count += 1
        
        embed.add_field(
            name="📋 Categorias Principais (1/2):",
            value=categorias_p1,
            inline=False
        )
        
        # Categorias principais - Página 2
        categorias_p2 = ""
        for key, categoria in list(self.categorias.items())[8:]:
            categorias_p2 += f"{categoria['emoji']} **{categoria['nome']}** - `{key}`\n"
        
        if categorias_p2:
            embed.add_field(
                name="📋 Categorias Principais (2/2):",
                value=categorias_p2,
                inline=False
            )
        
        # Categorias especiais
        especiais_texto = ""
        for key, categoria in self.categorias_especiais.items():
            especiais_texto += f"{categoria['emoji']} **{categoria['nome']}** - `{key}`\n"
        
        embed.add_field(
            name="💫 Categorias Especiais:",
            value=especiais_texto,
            inline=False
        )
        
        embed.set_footer(text="💡 Use !ajuda <categoria> para ver comandos específicos")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await ctx.send(embed=embed)

    @commands.command(name="ajuda", aliases=["h"])
    async def ajuda_categoria(self, ctx, categoria: str = None):
        """Mostra comandos de uma categoria específica ou menu principal"""
        
        if not categoria:
            await self.listar_categorias(ctx)
            return
        
        categoria = categoria.lower()
        
        # Verifica aliases para categorias especiais
        categoria_especial = None
        for key, info in self.categorias_especiais.items():
            if categoria == key or categoria in info.get("aliases", []):
                categoria_especial = key
                break
        
        # Categorias especiais
        if categoria_especial:
            if categoria_especial == "roleplay":
                await self.ajuda_roleplay(ctx)
            elif categoria_especial == "logs":
                await self.ajuda_logs(ctx)
            elif categoria_especial == "tickets":
                await self.ajuda_tickets(ctx)
            elif categoria_especial == "status":
                await self.ajuda_status(ctx)
            return
        
        # Verifica se a categoria existe nas principais
        if categoria not in self.categorias:
            # Tenta encontrar uma categoria similar
            sugestoes = []
            for key in self.categorias.keys():
                if categoria in key or key.startswith(categoria):
                    sugestoes.append(key)
            
            embed = discord.Embed(
                title="❌ Categoria não encontrada",
                description=f"A categoria `{categoria}` não existe.",
                color=discord.Color.red()
            )
            
            if sugestoes:
                embed.add_field(
                    name="💡 Você quis dizer:",
                    value="\n".join([f"`{s}`" for s in sugestoes[:3]]),
                    inline=False
                )
            
            embed.add_field(
                name="📝 Ajuda:",
                value="Use `!cmds` para ver todas as categorias disponíveis.",
                inline=False
            )
            
            await ctx.send(embed=embed)
            return
        
        # Mostra comandos da categoria
        await self.mostrar_categoria(ctx, categoria)

    async def mostrar_categoria(self, ctx, categoria):
        """Mostra os comandos de uma categoria específica"""
        cat_info = self.categorias[categoria]
        
        embed = discord.Embed(
            title=f"{cat_info['emoji']} {cat_info['nome']}",
            description=f"Comandos da categoria **{cat_info['nome']}**",
            color=discord.Color.blue()
        )
        
        for secao, comandos in cat_info['comandos'].items():
            comandos_texto = "\n".join(comandos)
            embed.add_field(
                name=secao,
                value=comandos_texto,
                inline=False
            )
        
        embed.set_footer(text=f"Use !cmds para ver todas as categorias | Página: {categoria}")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await ctx.send(embed=embed)

    async def ajuda_roleplay(self, ctx):
        """Comandos de roleplay"""
        embed = discord.Embed(
            title="🎭 Roleplay",
            description="Comandos de interação entre usuários",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="💕 **Carinhosos:**",
            value="`!abracar @usuário` - Abraçar alguém\n"
                  "`!beijar @usuário` - Beijar alguém\n"
                  "`!cafune @usuário` - Fazer cafuné\n"
                  "`!tocaaqui @usuário` - Toca aqui",
            inline=False
        )
        
        embed.add_field(
            name="😤 **Agressivos:**",
            value="`!bofetada @usuário` - Dar bofetada\n"
                  "`!atacar @usuário` - Atacar alguém",
            inline=False
        )
        
        embed.add_field(
            name="🕺 **Outros:**",
            value="`!dancar @usuário` - Dançar com alguém\n"
                  "`!roleplay` - Ver todos comandos RP",
            inline=False
        )
        
        embed.set_footer(text="Use !cmds para ver todas as categorias")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await ctx.send(embed=embed)

    async def ajuda_logs(self, ctx):
        """Sistema de logs"""
        embed = discord.Embed(
            title="📜 Sistema de Logs",
            description="Configure logs para monitorar atividades do servidor",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="📝 **Configuração:**",
            value="`!canaldelogs #canal` - Define canal de logs\n"
                  "`!configlogs` - Ver configurações de logs\n"
                  "`!togglelogs` - Liga/desliga sistema de logs",
            inline=False
        )
        
        embed.add_field(
            name="📊 **Tipos de Logs:**",
            value="• Mensagens editadas/deletadas\n"
                  "• Membros entrando/saindo\n"
                  "• Mudanças de cargo\n"
                  "• Ações de moderação",
            inline=False
        )
        
        embed.set_footer(text="Use !cmds para ver todas as categorias")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await ctx.send(embed=embed)

    async def ajuda_tickets(self, ctx):
        """Sistema de tickets"""
        embed = discord.Embed(
            title="🎫 Sistema de Tickets",
            description="Sistema de suporte com tickets privados",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🎫 **Gerenciar Tickets:**",
            value="`!ticket` - Criar novo ticket\n"
                  "`!fecharticket` - Fechar ticket atual\n"
                  "`!configticket` - Ver configurações\n"
                  "`!canaldecomandoticket #canal` - Canal de comandos",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ **Configuração:**",
            value="`!adicionarcategoriaticket <ID>` - Adicionar categoria\n"
                  "`!removercategoriaticket <ID>` - Remover categoria\n"
                  "`!listatickets` - Listar tickets ativos",
            inline=False
        )
        
        embed.set_footer(text="Use !cmds para ver todas as categorias")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await ctx.send(embed=embed)

    async def ajuda_status(self, ctx):
        """Sistema de status do bot"""
        embed = discord.Embed(
            title="📡 Status do Bot",
            description="Configure o status e atividade do bot",
            color=discord.Color.blurple()
        )
        
        embed.add_field(
            name="🤖 **Configurar Status:**",
            value="`!statusmodo <online/idle/dnd/invisible>` - Alterar status\n"
                  "`!listarstatus` - Listar status disponíveis\n"
                  "`!statusintervalo <minutos>` - Intervalo de mudança\n"
                  "`!statusmanual <texto>` - Definir status manual",
            inline=False
        )
        
        embed.add_field(
            name="🎮 **Atividades:**",
            value="`!atividade <tipo> <texto>` - Definir atividade\n"
                  "**Tipos:** `playing`, `watching`, `listening`, `streaming`\n"
                  "`!limparatividade` - Remover atividade atual",
            inline=False
        )
        
        embed.set_footer(text="Use !cmds para ver todas as categorias")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await ctx.send(embed=embed)

    @commands.command(name="buscarcomando", aliases=["search", "procurar"])
    async def buscar_comando(self, ctx, *, termo: str):
        """Busca por comandos que contenham o termo especificado"""
        termo = termo.lower()
        resultados = []
        
        # Busca nas categorias principais
        for categoria_key, categoria in self.categorias.items():
            for secao, comandos in categoria['comandos'].items():
                for comando in comandos:
                    if termo in comando.lower():
                        resultados.append({
                            'categoria': categoria['nome'],
                            'comando': comando,
                            'emoji': categoria['emoji']
                        })
        
        if not resultados:
            embed = discord.Embed(
                title="🔍 Busca sem Resultados",
                description=f"Nenhum comando encontrado para: `{termo}`",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 Dica:",
                value="Tente usar termos mais específicos ou use `!cmds` para ver todas as categorias.",
                inline=False
            )
        else:
            embed = discord.Embed(
                title=f"🔍 Resultados para: `{termo}`",
                description=f"Encontrados {len(resultados)} comando(s)",
                color=discord.Color.green()
            )
            
            # Limita a 10 resultados para não sobrecarregar
            for resultado in resultados[:10]:
                embed.add_field(
                    name=f"{resultado['emoji']} {resultado['categoria']}",
                    value=resultado['comando'],
                    inline=False
                )
            
            if len(resultados) > 10:
                embed.set_footer(text=f"Mostrando 10 de {len(resultados)} resultados")
        
        await ctx.send(embed=embed)

    @ajuda_categoria.error
    async def ajuda_error(self, ctx, error):
        """Tratamento de erros para o comando ajuda"""
        if isinstance(error, commands.MissingRequiredArgument):
            await self.listar_categorias(ctx)
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Ocorreu um erro ao processar o comando de ajuda.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ajuda(bot))