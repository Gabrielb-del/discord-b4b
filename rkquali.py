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
DATA_FILE = "contatos.json"
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

# Carregar operadores de qualificação ao iniciar
MAPEAMENTO_USUARIOS_QUALI = carregar_operadores_quali()

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

        for qualificador in operadores:
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

@tasks.loop(seconds=10)  # Verifica a cada 10 segundos
async def monitorar_operadores():
    if arquivo_foi_modificado():
        global MAPEAMENTO_USUARIOS_QUALI
        MAPEAMENTO_USUARIOS_QUALI = carregar_operadores_quali()
        atualizar_lista_operadores()
        canal = bot.get_channel(CANAL_QUALIFICACAO_ID)
        if canal:
            await canal.send("📝 Lista de operadores atualizada automaticamente!")
            await contatos(bot.get_context(await canal.fetch_message(canal.last_message_id)))

@bot.event
async def on_ready():
    print(f" {bot.user.name} está online!")
    global ultima_modificacao
    ultima_modificacao = os.path.getmtime(ARQUIVO_OPERADORES_QUALI)
    atualizar_lista_operadores()  # Atualiza a lista de operadores ao iniciar
    monitorar_operadores.start()  # Inicia o monitoramento do arquivo
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
            if username in MAPEAMENTO_USUARIOS_QUALI:
                operador = obter_nome_ranking(MAPEAMENTO_USUARIOS_QUALI[username])
                contatos = carregar_contatos()
                contatos[operador] = contatos.get(operador, 0) + 1
                salvar_contatos(contatos)
                await message.add_reaction("✅")
            else:
                await message.channel.send(f"❌ Nome de usuário {username} não está mapeado no time de qualificação. Contate o administrador.")

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

    for qualificador in operadores:
        quantidade = contatos.get(qualificador, 0)
        mensagem += f"{qualificador} - {quantidade if quantidade > 0 else ''}\n"

    await ctx.send(mensagem)

bot.run(TOKEN)