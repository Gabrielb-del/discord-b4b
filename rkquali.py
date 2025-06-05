import discord
from discord.ext import commands, tasks
import json
import datetime
import os
from collections import defaultdict
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Obtém o token do arquivo .env
TOKEN = os.getenv('RKQUALI_TOKEN')
if not TOKEN:
    raise ValueError("Token não encontrado no arquivo .env. Por favor, configure a variável RKQUALI_TOKEN")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

RESET_HORARIO = datetime.time(hour=0, minute=0)  # Reset à meia-noite
CONTATOS_FILE = "contatos_qualificados.json"
CANAL_QUALIFICACAO_ID = 1321967249111781398
ARQUIVO_OPERADORES_QUALI = "operadores_quali.json"

# Variável para armazenar a última modificação do arquivo
ultima_modificacao = 0

# Função para carregar operadores de qualificação
def carregar_operadores_quali():
    if os.path.exists(ARQUIVO_OPERADORES_QUALI):
        with open(ARQUIVO_OPERADORES_QUALI, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Função para verificar se o arquivo foi modificado
def arquivo_foi_modificado():
    global ultima_modificacao
    try:
        modificacao_atual = os.path.getmtime(ARQUIVO_OPERADORES_QUALI)
        if modificacao_atual != ultima_modificacao:
            ultima_modificacao = modificacao_atual
            return True
    except OSError:
        pass
    return False

# Lista de operadores ativos (será atualizada dinamicamente)
operadores = []

def atualizar_lista_operadores():
    global operadores, MAPEAMENTO_USUARIOS_QUALI
    # Obtém todos os nomes completos dos operadores
    nomes_completos = list(MAPEAMENTO_USUARIOS_QUALI.values())
    
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
    mesmo_primeiro_nome = sum(1 for nome in MAPEAMENTO_USUARIOS_QUALI.values() 
                            if nome.split()[0] == primeiro_nome)
    
    if mesmo_primeiro_nome > 1:
        # Se tem mais de um operador com o mesmo primeiro nome, usa nome + sobrenome
        return f"{partes[0]} {partes[1]}" if len(partes) > 1 else partes[0]
    else:
        # Se é único, usa só o primeiro nome
        return primeiro_nome

def carregar_contatos_qualificados():
    try:
        with open(CONTATOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def contar_contatos_por_operador():
    contatos = carregar_contatos_qualificados()
    contagem = defaultdict(int)
    data_atual = datetime.datetime.now().strftime("%d/%m/%Y")
    
    for contato in contatos:
        if contato.get("data_registro") == data_atual:
            nome_completo = contato.get("consultor", "")
            if nome_completo:
                nome_ranking = obter_nome_ranking(nome_completo)
                contagem[nome_ranking] += 1
    
    return contagem

# Carregar operadores de qualificação ao iniciar
MAPEAMENTO_USUARIOS_QUALI = carregar_operadores_quali()

@tasks.loop(minutes=30)
async def enviar_contatos_periodicos():
    agora = datetime.datetime.now()
    
    if agora.weekday() < 5 and 9 <= agora.hour < 18:  
        contagem = contar_contatos_por_operador()
        data_atual = agora.strftime("%d/%m")
        
        total_contatos = sum(contagem.values())
        mensagem = f"**CONTATOS {data_atual} ✨📞**\n\n"

        for qualificador in operadores:
            quantidade = contagem.get(qualificador, 0)
            mensagem += f"{qualificador} - {quantidade if quantidade > 0 else ''}\n"

        mensagem += f"\n🚀 **TOTAL CONTATOS:** 💛 {total_contatos} 🖤"

        canal = bot.get_channel(CANAL_QUALIFICACAO_ID)
        if canal:
            await canal.send(mensagem)

@bot.command(name="contatos")
async def contatos(ctx):
    if ctx.channel.id != CANAL_QUALIFICACAO_ID:
        return

    contagem = contar_contatos_por_operador()
    data_atual = datetime.datetime.now().strftime("%d/%m")
    
    total_contatos = sum(contagem.values())
    mensagem = f"**CONTATOS {data_atual} ✨📞**\n\n"

    for qualificador in operadores:
        quantidade = contagem.get(qualificador, 0)
        mensagem += f"{qualificador} - {quantidade if quantidade > 0 else ''}\n"

    mensagem += f"\n🚀 **TOTAL CONTATOS:** 💛 {total_contatos} 🖤"
    
    await ctx.send(mensagem)

@tasks.loop(seconds=10)  # Verifica a cada 10 segundos
async def monitorar_operadores():
    global MAPEAMENTO_USUARIOS_QUALI, ultima_modificacao
    try:
        if os.path.exists(ARQUIVO_OPERADORES_QUALI):
            modificacao_atual = os.path.getmtime(ARQUIVO_OPERADORES_QUALI)
            if modificacao_atual != ultima_modificacao:
                print(f"Detectada modificação no arquivo de operadores de qualificação")
                MAPEAMENTO_USUARIOS_QUALI = carregar_operadores_quali()
                atualizar_lista_operadores()
                ultima_modificacao = modificacao_atual
                
                canal = bot.get_channel(CANAL_QUALIFICACAO_ID)
                if canal:
                    await canal.send("📝 Lista de operadores atualizada automaticamente!")
                    ctx = await bot.get_context(await canal.fetch_message(canal.last_message_id))
                    await contatos(ctx)
    except Exception as e:
        print(f"Erro ao monitorar operadores: {e}")

@bot.event
async def on_ready():
    print(f" {bot.user.name} está online!")
    global ultima_modificacao
    try:
        ultima_modificacao = os.path.getmtime(ARQUIVO_OPERADORES_QUALI) if os.path.exists(ARQUIVO_OPERADORES_QUALI) else 0
    except Exception as e:
        print(f"Erro ao obter última modificação do arquivo: {e}")
        ultima_modificacao = 0
    
    atualizar_lista_operadores()  # Atualiza a lista de operadores ao iniciar
    monitorar_operadores.start()  # Inicia o monitoramento do arquivo
    enviar_contatos_periodicos.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return  

    await bot.process_commands(message)

bot.run(TOKEN)