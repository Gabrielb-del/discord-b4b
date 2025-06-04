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
TOKEN = os.getenv('RKDISC2_TOKEN')
if not TOKEN:
    raise ValueError("Token não encontrado no arquivo .env. Por favor, configure a variável RKDISC2_TOKEN")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
DATA_FILE = "ranking.json"
META_DIARIA = int(os.getenv('META_DIARIA', '30'))
CANAL_ID = int(os.getenv('CANAL_PROSPECAO', '0'))
CONTAS_ABERTAS_FILE = "contas_abertas.json"  # Arquivo JSON das contas abertas

MAPEAMENTO_USUARIOS = {
    "gabrielb.b4b": "Baunilia",
    "alyssafurtuoso.b4b": "Alyssa",
    "abigailgenaro.b4b_51008": "Abigail",
    "aghataalves.b4b": "Ághata",
    "annasilva.b4b_72247": "Anna Julya",
    "arianebortolazzob4b": "Ariane",
    "eduardameira.b4b": "Eduarda",
    "giovanasilva.b4b": "Giovana Vitória",
    "giovanniangelo.b4b": "Giovanni",
    "joaof.b4b_77771": "João",
    "miriamfranzoi.b4b": "Mia",
    "ritacarmo.b4b": "Rita",
    "saraescobar.b4b_62845": "Sara",
    "thalessebastiaob4b": "Thaleco",
    "viniciusilva.b4b": "Vinícius",
    "yasminsantos.b4b_53785": "Yasmin",
    "yurisales.b4b": "Yuri",
    "beatrizduarte.b4b": "Beatriz Duarte",
    "gabrielagigo.b4b_30518": "Gabriela",
    "maluribeiro.b4b": "Maria Luisa",
    "carolinamattos.b4b": "Carolina",
    "giovanamartins.b4b": "Giovana Martins",
    "isaaccampos.b4b": "Isaac",
    "liviagomes.b4b": "Livia",
    "sofiavieira.b4b_52711": "Sofia",
    "beatrizoliveira.b4b_00144" : "Beatriz Oliveira",
    "christyanalves.b4b_69243":"Christyan",
    "emillyforner.b4b": "Emilly",
    "matheusaugusto.b4b_45858": "Matheus",
    "lucaspais.b4b": "Lucas",
    "thiagomelo.b4b": "Thiago",
    "juliovilchez.b4b_37346": "Julio",
    "aghataalves.b4b": "Aghata",
    "murilopires_b4b": "Murilo Pires",
    "marianabarboza.b4b": "Mariana",
    "murilomattos.b4b_83994": "Murilo Mattos",
    "luizleite.b4b_57110": "Luiz Augusto",
    "thiagobarbosa.b4b_38105": "Thiago Barbosa",
    "andreybizao.b4b": "Andrey",
    "hellenanuncicao.b4b": "Hellen"


}

# Mapeamento reverso (nome completo -> nome no ranking)
MAPEAMENTO_REVERSO = {
    "Gabriel Baunilia Silva": "Baunilia",
    "Alyssa Santos Furtuoso": "Alyssa",
    "Abigail Dias Xavier Genaro": "Abigail",
    "Aghata Alves dos Santos": "Ághata",
    "Anna Julya De Paula Dias Da Silva": "Anna Julya",
    "Ariane Cristina Almeida Bortolazzo": "Ariane",
    "Eduarda Saraiva Meira": "Eduarda",
    "Giovana Vitória da Silva": "Giovana Vitória",
    "Giovanni Oliveira Angelo": "Giovanni",
    "João Pedro Furtuoso": "João",
    "Miriam Helena Franzoi": "Mia",
    "Rita de Cassia Bueno do Carmo": "Rita",
    "Sara Gabriely Escobar": "Sara",
    "Thales Njea Ferreira Sebastião": "Thaleco",
    "Vinicius Araujo Silva": "Vinícius",
    "Yasmin Leticia da Silva Santos": "Yasmin",
    "Yuri Costa Cataia de Sales": "Yuri",
    "Beatriz Duarte Reis": "Beatriz Duarte",
    "Gabriela Gigo de Paula": "Gabriela",
    "Maria Luisa Ribeiro da Silva": "Maria Luisa",
    "Carolina de Mattos": "Carolina",
    "Giovana Martins da Cruz Carvalho": "Giovana Martins",
    "Isaac Miguel da Silva Campos": "Isaac",
    "Livia Kai Lani Gomes de Oliveira": "Livia",
    "Sofia Helena Vieira Domingues": "Sofia",
    "Beatriz Reis de Oliveira": "Beatriz Oliveira",
    "Christyan Picoloto Alves": "Christyan",
    "Matheus Augusto Magoga Cabete": "Matheus",
    "Emilly Dos Santos Forner": "Emilly",
    "Lucas Henrique Vieira Pais": "Lucas",
    "Thiago Dos Santos Melo": "Thiago",
    "Julio Gonçalves Zarate Vilchez": "Julio",
    "Aghata Alves dos Santos": "Aghata",
    "Mariana Gabriela Ferreira Barboza": "Mariana",
    "Murilo Ramalho Pires": "Murilo Pires",
    "Murilo Miguel de Mattos Ozorio": "Murilo Mattos",
    "Thiago da Silva Barbosa": "Thiago Barbosa",
    "Luiz Augusto Bucharelli da Graça Leite": "Luiz Augusto",
    "Andrey de Souza Batista Bizão": "Andrey",
    "Hellen Geovana Silva Anunciação": "Hellen"


}
def esta_no_horario():
    agora = datetime.datetime.now()
    return agora.weekday() < 5 and 9 <= agora.hora < 18  # Segunda a sexta, entre 9h e 18h

def carregar_ranking():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def salvar_ranking(dados):
    with open(DATA_FILE, "w") as f:
        json.dump(dados, f, indent=4)



def carregar_contas_abertas():
    try:
        with open(CONTAS_ABERTAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def contar_contas_por_consultor():
    contas_abertas = carregar_contas_abertas()
    ranking = {}

    for conta in contas_abertas:
        consultor_completo = conta.get("consultor")
        if consultor_completo:
            # Converte o nome completo para o nome do ranking usando o mapeamento reverso
            consultor = MAPEAMENTO_REVERSO.get(consultor_completo, consultor_completo)
            ranking[consultor] = ranking.get(consultor, 0) + 1

    return ranking

meta_batida = False

@tasks.loop(minutes=30)
async def enviar_ranking_periodico():
    global meta_batida  # Usamos a variável global para controlar o estado

    agora = datetime.datetime.now()

    # Verifica se é um dia útil (segunda a sexta) e se está dentro do horário de funcionamento
    if agora.weekday() == 5 and 8 <= agora.hour < 13:
        ranking = contar_contas_por_consultor()
        data_atual = agora.strftime("%d/%m")

        operadores = [
            "Emilly", 
            "Mariana",
            "Giovana Martins",            
            "Giovanni",
            "Miriam",
            "Luiz Augusto",
            "Julio", 
            "Ariane",
            "Maria Luisa",
            "Thiago Barbosa",
            "Andrey",
            "Hellen"
            
        ]

        total_contas = sum(ranking.values())
        gap = max(META_DIARIA - total_contas, 0)

        horas_passadas = (agora - agora.replace(hour=8, minute=0, microsecond=0)).seconds / 3600
        contas_abertas_agora = total_contas
        if horas_passadas > 0:
            media_por_hora = contas_abertas_agora / horas_passadas
        else:
            media_por_hora = 0

        horas_restantes = 17 - agora.hour - (agora.minute / 60)
        projecao = int(media_por_hora * horas_restantes)
        total_projecao = contas_abertas_agora + projecao

        ranking_ordenado = sorted(ranking.items(), key=lambda x: x[1], reverse=True)

        mensagem = f"**CONTAS ABERTAS {data_atual} ✨🐺**\n\n"
        for operador in operadores:
            contas = ranking.get(operador, 0)
            contas_str = str(contas) if contas > 0 else ""
            mensagem += f"{operador} - {contas_str}\n"

        mensagem += f"\n🎯 **META DO DIA:** {META_DIARIA}\n"
        mensagem += "🎯 **META INDIVIDUAL:** 3\n"
        mensagem += f"🚀 **TOTAL CONTAS:** 💛 {total_contas} 🖤\n"
        mensagem += f"👎 **GAP:** {gap}\n"
        mensagem += f"📈 **PROJEÇÃO ATÉ O FIM DO EXPEDIENTE:** {total_projecao}\n\n"

        top3 = [op for op, c in ranking_ordenado[:3]]
        if len(top3) >= 1: mensagem += f"1º {top3[0]}\n"
        if len(top3) >= 2: mensagem += f"2º {top3[1]}\n"
        if len(top3) >= 3: mensagem += f"3º {top3[2]}\n"

        canal = bot.get_channel(CANAL_ID)
        if canal:
            # Verifica se a meta diária foi atingida
            if total_contas >= META_DIARIA and not meta_batida:
                # Envia mensagem de comemoração SE a meta for batida e ainda não foi comemorada
                mensagem_comemoracao = "**🎉 PARABÉNS! META DO DIA ATINGIDA! 🎉**\n"
                mensagem_comemoracao += "A meta diária foi batida! Vamos celebrar o esforço de todos!\n"
                mensagem_comemoracao += "Aqui está o ranking atualizado com os melhores de hoje! 🏆\n\n"
                await canal.send(mensagem_comemoracao)
                meta_batida = True  # Marca que a meta foi comemorada no dia

            # Sempre envia o ranking
            await canal.send(mensagem)

    else:
        print("⏳ Fora do horário comercial. O ranking não será enviado agora.")




@tasks.loop(time=datetime.time(hour=0, minute=0))
async def resetar_ranking():
    print("🔄 Resetando o ranking...")
    salvar_ranking({})
    canal = bot.get_channel(CANAL_ID)
    agora = datetime.datetime.now()

    # Verifica se é um dia útil (segunda a sexta) e se está dentro do horário de funcionamento
    if agora.weekday() < 5:
        if canal:
            await canal.send("🌙 **Ranking resetado!** Um novo dia começa. Vamos com tudo! 🚀")

@bot.event
async def on_ready():
    print(f" {bot.user.name} está online!")
    enviar_ranking_periodico.start()
    resetar_ranking.start()

@bot.command() 
async def ranking(ctx):
    if ctx.channel.id != CANAL_ID:
        await ctx.send("❌ Este comando só pode ser usado no canal de prospecção.")
        return

    ranking = contar_contas_por_consultor()
    if not ranking:
        await ctx.send("📊 O ranking ainda está vazio!")
        return

    ranking_ordenado = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
    data_atual = datetime.datetime.now().strftime("%d/%m")
    total_contas = sum(ranking.values())

    mensagem = f"**🏆 RANKING {data_atual}**\n"
    mensagem += f"🚀 **TOTAL CONTAS:** 💛 {total_contas} 🖤\n\n"
    for i, (usuario, contas) in enumerate(ranking_ordenado, start=1):
        mensagem += f"{i}º {usuario}: {contas}\n"

    await ctx.send(mensagem)

@bot.command()
async def negada(ctx):
    if ctx.channel.id != CANAL_ID:
        await ctx.send("❌ Este comando só pode ser usado no canal de prospecção.")
        return

    ranking = contar_contas_por_consultor()
    autor_discord = ctx.author.name.lower()  # Pegando o nome de usuário no formato minúsculo
    operador_nome = MAPEAMENTO_USUARIOS.get(autor_discord, autor_discord)

    if operador_nome in ranking and ranking[operador_nome] > 0:
        ranking[operador_nome] -= 1
        salvar_ranking(ranking)
        await ctx.send(f"🔻 {operador_nome}, uma conta foi removida. Agora você tem {ranking[operador_nome]} contas.")
    else:
        await ctx.send(f"⚠️ {operador_nome}, você ainda não tem contas registradas hoje ou já está em 0.")

@bot.command()
async def add(ctx, nome: str, quantidade: int):
    ranking = carregar_ranking()

    if nome in ranking:
        ranking[nome] += quantidade
    else:
        ranking[nome] = quantidade

    salvar_ranking(ranking)
    await ctx.send(f"✅ {quantidade} conta(s) adicionada(s) para {nome}. Agora ele(a) tem {ranking[nome]} conta(s).")

bot.run(TOKEN)