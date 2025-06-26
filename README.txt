# 🤖 NatanBot - Bot Profissional para Discord

Este é um bot profissional multifuncional feito com `discord.py v2.5.2`, pronto para múltiplos servidores com sistemas completos de economia, XP, moderação, VIP, YouTube e muito mais.

---

## 📌 Requisitos

* Python 3.10 ou superior
* Uma conta no MongoDB Atlas (gratuito)
* Uma conta no Render (gratuito)
* Um token de bot do Discord

---

## 📁 Instalação Local

1. Clone o repositório:

```bash
git clone https://github.com/seuusuario/seubot.git
cd seubot
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Crie um arquivo `.env`:

```env
TOKEN=seu_token_do_discord
MONGO_URI=sua_url_do_mongo
```

4. Inicie o bot:

```bash
python main.py
```

---

## ☁️ Banco de Dados: Como hospedar no MongoDB Atlas

1. Acesse: [https://www.mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Crie um cluster gratuito (M0)
3. Crie um banco chamado `natanbot` com as collections padrão (ex: `usuarios`, `canais_youtube`, etc)
4. Crie um usuário e copie a **MongoDB URI**
5. Use essa URI no `.env`:

```env
MONGO_URL=mongodb+srv://<user>:<senha>@<cluster>.mongodb.net/natanbot?retryWrites=true&w=majority
```

---

## 🚀 Hospedagem: Como hospedar o bot na Render (gratuito)

1. Acesse: [https://render.com](https://render.com)

2. Crie um novo Web Service

3. Escolha seu repositório do GitHub

4. Configure:

   * Build Command: `pip install -r requirements.txt`
   * Start Command: `python main.py`
   * Runtime: Python 3.10

5. Em **Environment**, adicione as variáveis:

   * `TOKEN` = seu token do bot
   * `MONGO_URL` = sua URI do MongoDB
   * `AUTOPING` = sua URL do render

6. Clique em **Deploy**

---

## 💡 Dica: Se quiser usar JSON local em vez de MongoDB

Só voce alterar um pouco os códigos, caso n saiba pode pedir suporte de 3 revisões no bot, posso acrescentar
coisas caso voces queiram!

---

## 📚 Comandos

Use `!ajuda` no Discord para ver todos os comandos organizados por categoria.

---

## 📌 Autor

Desenvolvido por \[Natan]
