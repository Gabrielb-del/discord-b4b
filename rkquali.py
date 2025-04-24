import discord
from discord.ext import commands, tasks
import json
import datetime

TOKEN = "MTMzODUzOTQxMjY4MTY1ODM3OA.Gd5vJ4.RDHatE6BI5hsyjNPbxLLJGPBNG0jP7lMnsB2AY"
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

RESET_HORARIO = datetime.time(hour=0, minute=0)  # Reset à meia-noite
DATA_FILE = "contatos.json"
CANAL_QUALIFICACAO_ID = 1321967249111781398 

QUALIFICADORES = [
    "Nazarine", "Luiz", "Augusto", "Thiago Barbosa", "Ariane", "Alexandre"
]


MAPEAMENTO_USUARIOS = {
    "gabrielb.b4b": "Baunilia",
    "luizleite.b4b_57110": "Luiz",
    "augustobueno.b4b": "Augusto",
    "guilermenazarine.b4b": "Nazarine",
    "thiagobarbosa.b4b_38105": "Thiago Barbosa",
    "arianebortolazzob4b": "Ariane",
    "alexandrescarabelo.b4b": "Alexandre"


}
def carregar_contatos():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def salvar_contatos(dados):
    with open(DATA_FILE, "w") as f:
        json.dump(dados, f, indent=4)

@tasks.loop(minutes=30)
async def enviar_contatos_periodicos():
    agora = datetime.datetime.now()
    
    if agora.weekday() < 5 and 9 <= agora.hour < 18:  
        contatos = carregar_contatos()
        data_atual = agora.strftime("%d/%m")
        
        total_contatos = sum(contatos.values())  
        mensagem = f"**CONTATOS {data_atual} ✨📞**\n\n"

        for qualificador in QUALIFICADORES:
            quantidade = contatos.get(qualificador, 0)
            mensagem += f"{qualificador} - {quantidade if quantidade > 0 else ''}\n"

        mensagem += f"\n🚀 **TOTAL CONTATOS:** 💛 {total_contatos} 🖤"

        canal = bot.get_channel(CANAL_QUALIFICACAO_ID)
        if canal:
            await canal.send(mensagem)
    else:
        print("⏳ Fora do horário comercial. Os contatos não serão enviados agora.")

@tasks.loop(time=datetime.time(hour=0, minute=0))
async def resetar_contatos():
    agora = datetime.datetime.now()
    print("🔄 Resetando os contatos...")
    salvar_contatos({})  
    canal = bot.get_channel(CANAL_QUALIFICACAO_ID)
    
    if agora.weekday() < 5:
        if canal:
            await canal.send("🌙 **Os contatos foram resetados!** Um novo dia começa. 🚀")

@bot.event
async def on_ready():
    print(f" {bot.user.name} está online!")
    enviar_contatos_periodicos.start()
    resetar_contatos.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return  

    if message.channel.id == CANAL_QUALIFICACAO_ID:
        # Verifica se a mensagem está no formato esperado
        if all(keyword in message.content for keyword in ["Empresa:", "CNPJ:", "Nome:", "Tel:", "E-mail:"]):
            # Obtém o nome de usuário do autor da mensagem
            username = message.author.name
            if username in MAPEAMENTO_USUARIOS:
                operador = MAPEAMENTO_USUARIOS[username]
                contatos = carregar_contatos()
                contatos[operador] = contatos.get(operador, 0) + 1
                salvar_contatos(contatos)
                await message.channel.send(f"✅ Contato adicionado para {operador}.")
            else:
                await message.channel.send(f"❌ Nome de usuário {username} não mapeado.")

    await bot.process_commands(message)

@bot.command()
async def contatos(ctx):
    if ctx.channel.id != CANAL_QUALIFICACAO_ID:
        await ctx.send("❌ Este comando só pode ser usado no canal de qualificação.")
        return

    contatos = carregar_contatos()
    if not contatos:
        await ctx.send("📊 Nenhum contato registrado ainda!")
        return

    total_contatos = sum(contatos.values())
    data_atual = datetime.datetime.now().strftime("%d/%m")
    mensagem = f"**🏆 CONTATOS {data_atual}**\n🚀 **TOTAL CONTATOS:** 💛 {total_contatos} 🖤\n\n"

    for qualificador in QUALIFICADORES:
        quantidade = contatos.get(qualificador, 0)
        mensagem += f"{qualificador}: {quantidade}\n"

    await ctx.send(mensagem)

bot.run(TOKEN)