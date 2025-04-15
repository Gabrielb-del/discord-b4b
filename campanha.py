import discord
from discord.ext import commands, tasks
import json
import asyncio
import datetime

TOKEN = "MTMzNzE2NzA3ODA4MzI2ODY0OA.GRpZfN.UEmNy1fWnH1X5GwJXW7Oiy1yyeVFUMrjBWRqes"
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
CANAL_PROSPEC = 1321965052454109194
CANAL_QUALI = 1321967249111781398
CANAL_CASH = 1321971534348423303

def esta_no_horario():
    agora = datetime.datetime.now()
    return agora.weekday() < 5 and 9 <= agora.hora < 18  # Segunda a sexta, entre 9h e 18h

@tasks.loop(minutes=60)
async def enviar_campanha_periodico():
    

    agora = datetime.datetime.now()

    # Verifica se é um dia útil (segunda a sexta) e se está dentro do horário de funcionamento
    if agora.weekday() < 5 and 8 <= agora.hour < 18:
        
        data_atual = agora.strftime("%d/%m")


        mensagem = f"\n**🎈✨ Campanha Estoura Balão – Valendo Prêmios!** ✨🎈\n\n"
        mensagem += "Conquiste sua chance de estourar um balão e ganhar prêmios incríveis!\n"
        mensagem += f"🚀 **Você garante 1 balão ao atingir:**\n"
        mensagem += f"\n`✅ 2 contas aprovadas`\n"
        mensagem += f"`✅ 1 qualificação com evidência`\n"
        mensagem += f"`✅ 1 maquininha vendida (Apenas para o time de Cash)`\n\n"
        mensagem += f" Acumule conquistas, estoure mais balões e aumente suas chances de ganhar **1 Combo Lanche no Companheiro's Burguer**, **Voucher R$100**, **Voucher R$50**, **Saldo livre de R$10 até R$100 no Ifood e muito mais!!👀** \n\n"

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