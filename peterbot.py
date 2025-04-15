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




TOKEN = "MTMzODUzOTQxMjY4MTY1ODM3OA.Gd5vJ4.RDHatE6BI5hsyjNPbxLLJGPBNG0jP7lMnsB2AY"
ID_CANAL_MONITORADO = 1321965052454109194
ID_CANAL_COMANDOS = 1322216912691662868
ARQUIVO_JSON = "contas_abertas.json"

# Mapeamento de usuários
MAPEAMENTO_USUARIOS = {
    "gabrielb.b4b": "Gabriel Baunilia Silva",
    "alyssafurtuoso.b4b": "Alyssa Santos Furtuoso",
    "abigailgenaro.b4b_51008": "Abigail Dias Xavier Genaro",
    "aghataalves.b4b": "Aghata Alves dos Santos",
    "annasilva.b4b_72247": "Anna Julya De Paula Dias Da Silva",
    "arianebortolazzob4b": "Ariane Cristina Almeida Bortolazzo",
    "eduardameira.b4b": "Eduarda Saraiva Meira",
    "giovanasilva.b4b": "Giovana Vitória da Silva",
    "giovanniangelo.b4b": "Giovanni Oliveira Angelo",
    "joaof.b4b_77771": "João Pedro Furtuoso",
    "miriamfranzoi.b4b": "Miriam Helena Franzoi",
    "pedrosilva.b4b_51785": "Pedro Elias Almeida Silva",
    "ritacarmo.b4b": "Rita de Cassia Bueno do Carmo",
    "saraescobar.b4b_62845": "Sara Gabriely Escobar",
    "thalessebastiaob4b": "Thales Njea Ferreira Sebastião",
    "viniciusilva.b4b": "Vinicius Araujo Silva",
    "yasminsantos.b4b_53785": "Yasmin Leticia da Silva Santos",
    "yurisales.b4b": "Yuri Costa Cataia de Sales",
    "beatrizduarte.b4b": "Beatriz Duarte Reis",
    "gabrielagigo.b4b_30518": "Gabriela Gigo de Paula",
    "maluribeiro.b4b": "Maria Luisa Ribeiro da Silva",
    "carolinamattoos.b4b_04846": "Carolina de Mattos",
    "giovanamartins.b4b": "Giovana Martins da Cruz Carvalho",
    "isaaccampos.b4b": "Isaac Miguel da Silva Campos",
    "sofiavieira.b4b_52711": "Sofia Helena Vieira Domingues",
    "beatrizoliveira.b4b_00144": "Beatriz Reis de Oliveira",
    "christyanalves.b4b_69243":"Christyan Picoloto Alves",
    "emillyforner.b4b": "Emilly Dos Santos Forner",
    "matheusaugusto.b4b_45858": "Matheus Augusto Magoga Cabete",
    "lucaspais.b4b" : "Lucas Henrique Vieira Pais",
    "thiagomelo.b4b" : "Thiago Dos Santos Melo",
    "aghataalves.b4b": "Aghata Alves dos Santos",
    "juliovilchez.b4b_37346": "Julio Gonçalves Zarate Vilchez",
    "augustobueno.b4b": "Augusto Bueno de Almeida",
    "guilermenazarine.b4b": "Guilherme Barboza Nazarine",
    "luizleite.b4b_57110": "Luiz Augusto Bucharelli da Graça Leite",
    "thiagobarbosa.b4b_38105": "Thiago da Silva Barbosa",
    "thiagovieira.b4b": "Thiago Gabriel Vieira",
    "murilomattos.b4b_83994": "Murilo Miguel de Mattos Ozorio",
    "andreybizao.b4b": "Andrey de Souza Batista Bizão",
    "murilopires_b4b": "Murilo Ramalho Pires",
    "marianabarboza.b4b": "Mariana Gabriela Ferreira Barboza",
    "hellenanuncicao.b4b": "Hellen Geovana Silva Anunciação",
    "tamirismarteline.b4b": "Tamiris Mariany Marteline",
    "biancasarto.b4b_49906": "Bianca Sarto dos Santos",
    "julianasilva.b4b": "Juliana Cristina da Silva Reis",
    "larissasilva_04782": "Larissa Vitória Silva Sanches",
    "beatrizsoares.b4b": "Beatriz Pádua Soares"
}

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
bot = commands.Bot(command_prefix="!", intents=intents)

def normalizar_status(status):
    return ''.join(c for c in unicodedata.normalize('NFKD', status) if not unicodedata.combining(c)).lower()

def validar_status(status):
    status_normalizado = normalizar_status(status)
    return status_normalizado in ["analise", "aprovada"]

def padronizar_status(status):
    status_normalizado = normalizar_status(status)
    if status_normalizado == "analise":
        return "ANÁLISE"
    elif status_normalizado == "aprovada":
        return "APROVADA"
    else:
        return status

def validar_cnpj(cnpj):
    regex = r"^\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}$"
    return re.match(regex, cnpj) is not None


def padrao_origem(origem):
    return ''.join(c for c in unicodedata.normalize('NFD', origem) if not unicodedata.combining(c)).lower()

def validar_origem(origem):
    origem_normalizado = padrao_origem(origem)
    return origem_normalizado in ["lead manual", "repescagem", "discador", "mensageria", "indicacao", "ura","backoffice"]

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
    resetar_contas.start()

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
                await message.reply("❌ Status inválido. Use apenas 'Análise' ou 'Aprovada'.")
                return
            conta['status'] = padronizar_status(conta['status'])

        if 'origem' in conta:
            origem_normalizado  = padrao_origem(conta['origem'])
            if not validar_origem(conta['origem']):
                await message.reply("❌ Origem inválida. Use apenas 'Lead Manual', 'Repescagem', 'Discador', 'Mensageria', 'Ura', 'BackOffice' ou 'Indicação'.")
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

@bot.command()
async def exportar(ctx):
    print(f'Comando "!exportar" recebido no canal {ctx.channel.name} (ID: {ctx.channel.id})')

    if contas_abertas:
        for conta in contas_abertas:
            if "data" not in conta:
                conta["data"] = datetime.now().strftime("%d/%m/%Y")

        colunas_desejadas = ["data", "cnpj", "empresa", "consultor", "origem", "status"]
        df = pd.DataFrame(contas_abertas)
        df = df[[col for col in colunas_desejadas if col in df.columns]].fillna("")
        arquivo_excel = f"contas_abertas.xlsx"
        df.to_excel(arquivo_excel, index=False)

        await ctx.send("Aqui está o arquivo de contas abertas:", file=discord.File(arquivo_excel))
    else:
        await ctx.send("Nenhuma conta aberta registrada até o momento.")

bot.run(TOKEN)