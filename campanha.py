import discord
from discord.ext import commands, tasks
import json
import asyncio
import datetime
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Obtém o token do arquivo .env
TOKEN = os.getenv('CAMPANHA_TOKEN')
if not TOKEN:
    raise ValueError("Token não encontrado no arquivo .env. Por favor, configure a variável CAMPANHA_TOKEN")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Carrega IDs dos canais do arquivo .env
CANAL_PROSPEC = int(os.getenv('CANAL_PROSPECAO', '0'))
CANAL_QUALI = int(os.getenv('CANAL_QUALIFICACAO', '0'))
CANAL_CASH = int(os.getenv('CANAL_CASH', '0'))

def esta_no_horario():
    agora = datetime.datetime.now()
    return agora.weekday() < 5 and 9 <= agora.hora < 18  # Segunda a sexta, entre 9h e 18h

@tasks.loop(minutes=60)
async def enviar_campanha_periodico():
    

    agora = datetime.datetime.now()

    # Verifica se é um dia útil (segunda a sexta) e se está dentro do horário de funcionamento
    if agora.weekday() < 5 and 8 <= agora.hour < 18:
        
        data_atual = agora.strftime("%d/%m")


        mensagem = f"\n**📢 Campanhas do Dia!**\n\n"
        mensagem += "**☕ Café da Tarde com a Liderança:**\n"
        mensagem += "Premiação para quem atingir o maior **ICM** no período! 🏆\n\n"

        canal_prospec = bot.get_channel(CANAL_PROSPEC)
        canal_quali = bot.get_channel(CANAL_QUALI)
        canal_cash = bot.get_channel(CANAL_CASH)
        if canal_prospec and canal_quali and canal_cash:
            await canal_cash.send(mensagem)
            await canal_quali.send(mensagem)
            await canal_prospec.send(mensagem)


    else:
        print("⏳ Fora do horário comercial. O ranking não será enviado agora.")


@bot.event
async def on_ready():
    print(f" {bot.user.name} está online!")
    enviar_campanha_periodico.start()


bot.run(TOKEN)