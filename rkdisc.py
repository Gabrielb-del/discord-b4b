import discord
from discord.ext import commands, tasks
import json
import asyncio
import datetime
import os
from collections import defaultdict
from dotenv import load_dotenv
import time

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém o token do arquivo .env
TOKEN = os.getenv('RKDISC_TOKEN')
if not TOKEN:
    raise ValueError("Token não encontrado no arquivo .env. Por favor, configure a variável RKDISC_TOKEN")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
DATA_FILE = "ranking.json"
META_DIARIA = 60 
CANAL_ID = 1321965052454109194
CONTAS_ABERTAS_FILE = "contas_abertas.json"
ARQUIVO_OPERADORES = "operadores.json"  # Arquivo compartilhado com o peterbot.py

# Variável para armazenar a última modificação do arquivo
ultima_modificacao = 0

# Função para carregar operadores do arquivo JSON
def carregar_operadores():
    if os.path.exists(ARQUIVO_OPERADORES):
        with open(ARQUIVO_OPERADORES, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Função para verificar se o arquivo foi modificado
def arquivo_foi_modificado():
    global ultima_modificacao
    try:
        modificacao_atual = os.path.getmtime(ARQUIVO_OPERADORES)
        if modificacao_atual != ultima_modificacao:
            ultima_modificacao = modificacao_atual
            return True
    except OSError:
        pass
    return False

# Função para salvar operadores no arquivo JSON
def salvar_operadores(operadores):
    with open(ARQUIVO_OPERADORES, "w", encoding="utf-8") as f:
        json.dump(operadores, f, indent=4, ensure_ascii=False)

# Carregar operadores ao iniciar
MAPEAMENTO_USUARIOS = carregar_operadores()

# Lista de operadores ativos (será atualizada dinamicamente)
operadores = []

def atualizar_lista_operadores():
    global operadores, MAPEAMENTO_USUARIOS
    # Obtém todos os nomes completos dos operadores
    nomes_completos = list(MAPEAMENTO_USUARIOS.values())
    
    # Cria um dicionário para agrupar operadores com mesmo primeiro nome
    nomes_agrupados = defaultdict(list)
    for nome in nomes_completos:
        partes = nome.split()
        primeiro_nome = partes[0]
        nomes_agrupados[primeiro_nome].append(nome)
    
    # Lista final de nomes para o ranking
    nomes_ranking = []
    for primeiro_nome, lista_nomes in nomes_agrupados.items():
        if len(lista_nomes) == 1:
            # Se só tem um operador com esse primeiro nome, usa só o primeiro nome
            nomes_ranking.append(primeiro_nome)
        else:
            # Se tem mais de um, usa primeiro nome + primeiro sobrenome para cada um
            for nome_completo in lista_nomes:
                partes = nome_completo.split()
                if len(partes) > 1:
                    nomes_ranking.append(f"{partes[0]} {partes[1]}")
                else:
                    nomes_ranking.append(partes[0])
    
    operadores = sorted(nomes_ranking)

def obter_nome_ranking(nome_completo):
    """Retorna o nome que deve aparecer no ranking para um determinado operador"""
    if not nome_completo:
        return nome_completo
        
    partes = nome_completo.split()
    primeiro_nome = partes[0]
    
    # Conta quantos operadores têm o mesmo primeiro nome
    mesmo_primeiro_nome = sum(1 for nome in MAPEAMENTO_USUARIOS.values() 
                            if nome.split()[0] == primeiro_nome)
    
    if mesmo_primeiro_nome > 1:
        # Se tem mais de um operador com o mesmo primeiro nome, usa nome + sobrenome
        return f"{partes[0]} {partes[1]}" if len(partes) > 1 else partes[0]
    else:
        # Se é único, usa só o primeiro nome
        return primeiro_nome

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
        status = conta.get("status", "").upper()
        if status in ["CARIMBADA", "REPROVADA"]:
            continue

        consultor_completo = conta.get("consultor")
        if consultor_completo:
            # Usa a função de obter nome para o ranking
            nome_ranking = obter_nome_ranking(consultor_completo)
            ranking[nome_ranking] = ranking.get(nome_ranking, 0) + 1

    return ranking

meta_batida = False

@tasks.loop(minutes=30)
async def enviar_ranking_periodico():
    global meta_batida
    global operadores  # Usamos a variável global para controlar o estado

    agora = datetime.datetime.now()

    # Verifica se é um dia útil (segunda a sexta) e se está dentro do horário de funcionamento
    if agora.weekday() < 5 and 9 <= agora.hour < 18:
        ranking = contar_contas_por_consultor()
        data_atual = agora.strftime("%d/%m")

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

@tasks.loop(seconds=10)  # Verifica a cada 10 segundos
async def monitorar_operadores():
    if arquivo_foi_modificado():
        global MAPEAMENTO_USUARIOS
        MAPEAMENTO_USUARIOS = carregar_operadores()
        atualizar_lista_operadores()
        canal = bot.get_channel(CANAL_ID)
        if canal:
            await canal.send("📝 Lista de operadores atualizada automaticamente!")
            await ranking(bot.get_context(await canal.fetch_message(canal.last_message_id)))

@bot.event
async def on_ready():
    print(f'Bot está online como {bot.user.name}')
    global ultima_modificacao
    ultima_modificacao = os.path.getmtime(ARQUIVO_OPERADORES)
    atualizar_lista_operadores()  # Atualiza a lista de operadores ao iniciar
    monitorar_operadores.start()  # Inicia o monitoramento do arquivo
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
    for operador in operadores:
            contas = ranking.get(operador, 0)
            contas_str = str(contas) if contas > 0 else ""
            mensagem += f"{operador} - {contas_str}\n"

    top3 = [op for op, c in ranking_ordenado[:3]]
    if len(top3) >= 1: mensagem += f"\n 1º {top3[0]}\n"
    if len(top3) >= 2: mensagem += f"2º {top3[1]}\n"
    if len(top3) >= 3: mensagem += f"3º {top3[2]}\n"

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

@bot.command(name="atualizar_operadores")
async def atualizar_operadores_cmd(ctx):
    """Atualiza a lista de operadores do ranking em tempo real"""
    if ctx.channel.id != CANAL_ID:
        await ctx.send("❌ Este comando só pode ser usado no canal de prospecção.")
        return

    global MAPEAMENTO_USUARIOS
    # Recarrega os operadores do arquivo
    MAPEAMENTO_USUARIOS = carregar_operadores()
    # Atualiza a lista de nomes para o ranking
    atualizar_lista_operadores()
    
    await ctx.send("✅ Lista de operadores atualizada com sucesso!")
    # Mostra o ranking atualizado
    await ranking(ctx)

bot.run(TOKEN)




