import discord
import json
import pandas as pd
import os
import re
import asyncio
import datetime
from discord.ext import commands, tasks
from datetime import datetime, time
import unicodedata
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém o token do arquivo .env
TOKEN = os.getenv('PETERBOT_TOKEN')
if not TOKEN:
    raise ValueError("Token não encontrado no arquivo .env. Por favor, configure a variável PETERBOT_TOKEN")

ID_CANAL_MONITORADO = 1321965052454109194
ID_CANAL_COMANDOS = 1322216912691662868
ARQUIVO_JSON = "contas_abertas.json"
ARQUIVO_OPERADORES = "operadores.json"

# Função para carregar operadores
def carregar_operadores():
    if os.path.exists(ARQUIVO_OPERADORES):
        with open(ARQUIVO_OPERADORES, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Função para salvar operadores
def salvar_operadores(operadores):
    with open(ARQUIVO_OPERADORES, "w", encoding="utf-8") as f:
        json.dump(operadores, f, indent=4, ensure_ascii=False)

# Carregar operadores ao iniciar
MAPEAMENTO_USUARIOS = carregar_operadores()

def carregar_dados():
    if os.path.exists(ARQUIVO_JSON):
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            try:
                dados = json.load(f)
                if isinstance(dados, list):
                    return dados
                else:
                    return []
            except json.JSONDecodeError:
                return []
    return []

contas_abertas = carregar_dados()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

def normalizar_status(status):
    return ''.join(c for c in unicodedata.normalize('NFKD', status) if not unicodedata.combining(c)).lower()

def validar_status(status):
    status_normalizado = normalizar_status(status)
    return status_normalizado in ["analise", "aprovada", "carimbada", "reprovada"]

def padronizar_status(status):
    status_normalizado = normalizar_status(status)
    if status_normalizado == "analise":
        return "ANÁLISE"
    elif status_normalizado == "aprovada":
        return "APROVADA"
    elif status_normalizado == "carimbada":
        return "CARIMBADA"
    
    elif status_normalizado == "reprovada":
        return "REPROVADA"

    else:
        return status

def validar_cnpj(cnpj):
    regex = r"^\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}$"
    return re.match(regex, cnpj) is not None


def padrao_origem(origem):
    return ''.join(c for c in unicodedata.normalize('NFD', origem) if not unicodedata.combining(c)).lower()

def validar_origem(origem):
    origem_normalizado = padrao_origem(origem)
    return origem_normalizado in ["lead manual", "repescagem", "discador", "mensageria", "indicacao", "ura","backoffice", "repescagem ura", "sms"]

def padronizar_origem(origem):
    origem_normalizado = padrao_origem(origem)
    if origem_normalizado == "lead manual":
        return "LEAD MANUAL"
    elif origem_normalizado == "repescagem":
        return "REPESCAGEM"
    
    elif origem_normalizado == "discador":
        return "DISCADOR"
    
    elif origem_normalizado == "mensageria":
        return "MENSAGERIA"
    elif origem_normalizado == "indicacao":
        return "INDICAÇÃO"
    
    elif origem_normalizado == "ura":
        return "URA"
    
    elif origem_normalizado == "backoffice":
        return "BACKOFFICE"
    
    elif origem_normalizado == "repescagem ura":
        return "REPESCAGEM URA"
    
    elif origem_normalizado == "sms":
        return "sms"
    
    else:

        return origem


def validar_email(email):
    return "@" in email

@tasks.loop(time=time(hour=0, minute=0))
async def resetar_contas():
    global contas_abertas
    contas_abertas = []
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(contas_abertas, f, indent=4, ensure_ascii=False)
    print("🔄 Contas resetadas para o novo dia.")

@bot.event
async def on_ready():
    print(f'Logado como {bot.user}')
    print(f'Comandos registrados: {[cmd.name for cmd in bot.commands]}')
    resetar_contas.start()


#Evento para verificar a mensagem a adicionar a conta indicada no 'contas_abertas.json'
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.author == bot.user:
        return

    if message.channel.id == ID_CANAL_MONITORADO:
        if not any(keyword in message.content for keyword in ["Empresa:", "CNPJ:", "Nome:", "Tel:", "E-mail:", "Origem:", "Consultor:", "Status:"]):
            return

        dados = message.content.strip().replace("\n", "").replace("\r", "")
        print(f'Dados antes de processar: "{dados}"')

        padrao = {
            "empresa": r"Empresa:\s*(.*?)(?=\s*CNPJ:|$)",
            "cnpj": r"CNPJ:\s*(\d+)(?=\s*Nome:|$)",
            "nome": r"Nome:\s*(.*?)(?=\s*Tel:|$)",
            "telefone": r"Tel:\s*(\d+)(?=\s*E-mail:|$)",
            "email": r"E-mail:\s*(.*?)(?=\s*Origem:|$)",
            "origem": r"Origem:\s*(.*?)(?=\s*Consultor:|$)",
            "consultor": r"Consultor:\s*(.*?)(?=\s*Status:|$)",
            "status": r"Status:\s*(.*)"
        }

        conta = {}
        campos_faltantes = []
        for chave, regex in padrao.items():
            resultado = re.search(regex, dados)
            if resultado:
                conta[chave] = resultado.group(1).strip()
                print(f'Campo "{chave}" encontrado: {conta[chave]}')
            else:
                campos_faltantes.append(chave)
                print(f'Campo "{chave}" não encontrado na mensagem.')
        conta["hora_envio"] = datetime.now().strftime("%H:00")


        if len(campos_faltantes) > 0:
            await message.reply(f"❌ Faltam os seguintes campos: {', '.join(campos_faltantes)}. Por favor, envie novamente.")
            return

        if 'cnpj' in conta:
            if not validar_cnpj(conta['cnpj']):
                await message.reply("❌ CNPJ inválido. O CNPJ deve ter 14 dígitos.")
                return

        if 'status' in conta:
            status_normalizado = normalizar_status(conta['status'])
            if not validar_status(conta['status']):
                await message.reply("❌ Status inválido. Use apenas 'Análise', 'Aprovada', 'Carimbada' ou 'Reprovada'.")
                return
            conta['status'] = padronizar_status(conta['status'])

        if 'origem' in conta:
            origem_normalizado  = padrao_origem(conta['origem'])
            if not validar_origem(conta['origem']):
                await message.reply("❌ Origem inválida. Use apenas 'Lead Manual', 'Repescagem', 'Discador', 'Mensageria', 'Ura', 'Repescagem Ura', 'SMS', 'BackOffice' ou 'Indicação'.")
                return
            conta['origem'] = padronizar_origem(conta['origem'])

        if 'email' in conta:
            if not validar_email(conta['email']):
                await message.reply("❌ E-mail inválido. O e-mail deve conter '@'.")
                return

        nome_usuario = message.author.name
        if nome_usuario in MAPEAMENTO_USUARIOS:
            conta['consultor'] = MAPEAMENTO_USUARIOS[nome_usuario]
        else:
            await message.reply(f"❌ Nome de usuário '{nome_usuario}' não está mapeado. Contate o administrador.")
            return

        if 'cnpj' in conta:
            if not any('cnpj' in c and c['cnpj'] == conta['cnpj'] for c in contas_abertas):
                conta['mensagem_id'] = message.id
                contas_abertas.append(conta)
                with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
                    json.dump(contas_abertas, f, indent=4, ensure_ascii=False)
                print(f'Conta registrada: {conta}')
            else:
                print(f'CNPJ {conta["cnpj"]} já registrado.')
                await message.reply(f"⚠️ CNPJ {conta['cnpj']} já foi registrado anteriormente.")
        else:
            print(f'Chave "cnpj" não encontrada na conta: {conta}')
            await message.reply("❌ A mensagem não contém um CNPJ válido.")

#Se a mensagem da conta indicada for apagada no chat, essa conta será removida do json
@bot.event
async def on_message_delete(message):
    if message.channel.id == ID_CANAL_MONITORADO:
        print(f'Mensagem excluída detectada: ID {message.id}')
        for conta in contas_abertas:
            if 'mensagem_id' in conta and conta['mensagem_id'] == message.id:
                contas_abertas.remove(conta)
                with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
                    json.dump(contas_abertas, f, indent=4, ensure_ascii=False)
                print(f'Conta removida: {conta}')
                break

@bot.command(name="exportar")
async def exportar(ctx):
    print(f'Comando "!exportar" recebido no canal {ctx.channel.name} (ID: {ctx.channel.id})')
    if ctx.channel.id == ID_CANAL_MONITORADO:
        return

    if contas_abertas:
        for conta in contas_abertas:
            if "data" not in conta:
                conta["data"] = datetime.now().strftime("%d/%m/%Y")

        colunas_desejadas = ["data", "hora_envio", "cnpj", "empresa", "consultor", "origem", "status"]
        df = pd.DataFrame(contas_abertas)
        df = df[[col for col in colunas_desejadas if col in df.columns]].fillna("")
        arquivo_excel = f"CONTAS_ABERTAS_{datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx"
        df.to_excel(arquivo_excel, index=False)

        await ctx.send("Aqui está o arquivo de contas abertas:", file=discord.File(arquivo_excel))
    else:
        await ctx.send("Nenhuma conta aberta registrada até o momento.")

# Comandos para gerenciar operadores
@bot.command(name="adicionar_operador")
async def adicionar_operador(ctx, usuario_discord: str, primeiro_nome: str, *, nome_completo: str):
    """Adiciona um novo operador
    Exemplo: !adicionar_operador joao.b4b João 'João Silva Santos'"""
    if ctx.channel.id != ID_CANAL_COMANDOS:
        return
        
    global MAPEAMENTO_USUARIOS
    MAPEAMENTO_USUARIOS[usuario_discord] = nome_completo
    salvar_operadores(MAPEAMENTO_USUARIOS)
    await ctx.send(f"✅ Operador adicionado com sucesso!\nUsuário Discord: {usuario_discord}\nNome Completo: {nome_completo}")

@bot.command(name="remover_operador")
async def remover_operador(ctx, usuario_discord: str):
    """Remove um operador
    Exemplo: !remover_operador joao.b4b"""
    if ctx.channel.id != ID_CANAL_COMANDOS:
        return
        
    global MAPEAMENTO_USUARIOS
    if usuario_discord in MAPEAMENTO_USUARIOS:
        del MAPEAMENTO_USUARIOS[usuario_discord]
        salvar_operadores(MAPEAMENTO_USUARIOS)
        await ctx.send(f"✅ Operador {usuario_discord} removido com sucesso!")
    else:
        await ctx.send(f"❌ Operador {usuario_discord} não encontrado!")

@bot.command(name="listar_operadores")
async def listar_operadores(ctx):
    """Lista todos os operadores cadastrados"""
    if ctx.channel.id != ID_CANAL_COMANDOS:
        return
        
    if not MAPEAMENTO_USUARIOS:
        await ctx.send("Nenhum operador cadastrado!")
        return
        
    mensagem = "📋 **Lista de Operadores:**\n\n"
    for usuario, nome in MAPEAMENTO_USUARIOS.items():
        mensagem += f"👤 **{usuario}** - {nome}\n"
    
    await ctx.send(mensagem)

@bot.command(name="atualizar_operador")
async def atualizar_operador(ctx, usuario_discord: str, *, novo_nome_completo: str):
    """Atualiza o nome completo de um operador
    Exemplo: !atualizar_operador joao.b4b 'João Silva Santos Junior'"""
    if ctx.channel.id != ID_CANAL_COMANDOS:
        return
        
    global MAPEAMENTO_USUARIOS
    if usuario_discord in MAPEAMENTO_USUARIOS:
        MAPEAMENTO_USUARIOS[usuario_discord] = novo_nome_completo
        salvar_operadores(MAPEAMENTO_USUARIOS)
        await ctx.send(f"✅ Nome do operador {usuario_discord} atualizado para: {novo_nome_completo}")
    else:
        await ctx.send(f"❌ Operador {usuario_discord} não encontrado!")

bot.run(TOKEN)