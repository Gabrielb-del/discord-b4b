import discord
import json
import pandas as pd
import os
import re
import asyncio
import datetime
from discord.ext import commands, tasks
from datetime import datetime, time



TOKEN = "MTMzODUzOTQxMjY4MTY1ODM3OA.GQqBP3.gUB9Jt9iXW_3mA3YSBdaMAehHUXSrq8cwdGIzA"
ID_CANAL_MONITORADO = 1321965052454109194
ID_CANAL_COMANDOS = 1322216912691662868
ARQUIVO_JSON = "contas_abertas.json"

# Mapeamento de usuários
MAPEAMENTO_USUARIOS = {
    "gabrielb.b4b": "Gabriel Baunilia Silva",
    "alyssafurtuoso.b4b": "Alyssa Santos Furtuoso",
    "abigailgenaro.b4b": "Abigail Dias Xavier Genaro",
    "aghataalves.b4b": "Aghata Alves dos Santos",
    "annasilva.b4b": "Anna Julya De Paula Dias Da Silva",
    "arianebortolazzob4b": "Ariane Cristina Almeida Bortolazzo",
    "eduardameira.b4b": "Eduarda Saraiva Meira",
    "giovanasilva.b4b": "Giovana Vitória da Silva",
    "giovanniangelo.b4b": "Giovanni Oliveira Angelo",
    "joaof.b4b_77771": "João Pedro Furtuoso",
    "miriamfranzoi.b4b": "Miriam Helena Franzoi",
    "pedrosilva.b4b_51785": "Pedro Elias Almeida Silva",
    "ritacarmo.b4b": "Rita de Cassia Bueno do Carmo",
    "saraescobar.b4b": "Sara Gabriely Escobar",
    "thalessebastiaob4b": "Thales Njea Ferreira Sebastião",
    "viniciusilva.b4b": "Vinicius Araujo Silva",
    "yasminsantos.b4b": "Yasmin Leticia da Silva Santos",
    "yurisales.b4b": "Yuri Costa Cataia de Sales",
    "beatrizduarte.b4b": "Beatriz Duarte Reis",
    "gabrielgigo.b4b": "Gabriela Gigo de Paula",
    "maluribeiro.b4b": "Maria Luisa Ribeiro da Silva",
    "carolinamattos.b4b": "Carolina de Mattos",
    "giovanamartins.b4b": "Giovana Martins da Cruz Carvalho",
    "isaaccampos.b4b": "Isaac Miguel da Silva Campos",
    "liviagomes.b4b": "Livia Kai Lani Gomes de Oliveira",
    "sofiavieira.b4b": "Sofia Helena Vieira Domingues",
}

# Carregar dados existentes
def carregar_dados():
    if os.path.exists(ARQUIVO_JSON):
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            try:
                dados = json.load(f)
                if isinstance(dados, list):  # Verifica se é uma lista
                    return dados
                else:
                    print("Arquivo JSON não contém uma lista. Convertendo para lista.")
                    return []
            except json.JSONDecodeError:
                print("Erro ao decodificar o arquivo JSON. Retornando lista vazia.")
                return []
    return []

contas_abertas = carregar_dados()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Permite que o bot leia o conteúdo das mensagens
bot = commands.Bot(command_prefix="!", intents=intents)

# Função para validar CNPJ
def validar_cnpj(cnpj):
    regex = r"^\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}$"
    return re.match(regex, cnpj) is not None

# Função para validar Status
def validar_status(status):
    return status.lower() in ["análise", "aprovada"]

# Função para validar Origem
def validar_origem(origem):
    return origem in ["Lead Manual", "Repescagem", "Discador", "Mensageria", "Indicação"]

# Função para validar E-mail
def validar_email(email):
    return "@" in email

# Função para resetar o JSON de contas abertas
@tasks.loop(time=time(hour=0, minute=0))  # Reset à meia-noite
async def resetar_contas():
    global contas_abertas
    contas_abertas = []  # Reseta a lista de contas
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(contas_abertas, f, indent=4, ensure_ascii=False)
    print("🔄 Contas resetadas para o novo dia.")

@bot.event
async def on_ready():
    print(f'Logado como {bot.user}')
    resetar_contas.start()  # Inicia a tarefa de reset ao ligar o bot

@bot.event
async def on_message(message):
    if message.author.bot:  # Ignora mensagens enviadas por bots
        return

    await bot.process_commands(message)

    print(f'Mensagem recebida no canal {message.channel.name} (ID: {message.channel.id}): {message.content}')  # Depuração

    if message.author == bot.user:
        return

    # Verificar se a mensagem veio do canal de prospecção pela ID
    if message.channel.id == ID_CANAL_MONITORADO:
        # Verificar se a mensagem contém pelo menos alguns campos obrigatórios
        if not any(keyword in message.content for keyword in ["Empresa:", "CNPJ:", "Nome:", "Tel:", "E-mail:", "Origem:", "Consultor:", "Status:"]):
            return  # Ignora a mensagem se não for uma conta aberta

        # Limpar espaços extras e quebras de linha
        dados = message.content.strip().replace("\n", "").replace("\r", "")
        print(f'Dados antes de processar: "{dados}"')  # Depuração

        # Regex para capturar os dados
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
                print(f'Campo "{chave}" encontrado: {conta[chave]}')  # Depuração
            else:
                campos_faltantes.append(chave)
                print(f'Campo "{chave}" não encontrado na mensagem.')  # Depuração

        # Verificar se todos os campos obrigatórios estão presentes
        if len(campos_faltantes) > 0:
            await message.reply(f"❌ Faltam os seguintes campos: {', '.join(campos_faltantes)}. Por favor, envie novamente.")
            return

        # Validação do CNPJ
        if 'cnpj' in conta:
            if not validar_cnpj(conta['cnpj']):
                await message.reply("❌ CNPJ inválido. O CNPJ deve ter 14 dígitos.")
                return

        # Validação do Status
        if 'status' in conta:
            if not validar_status(conta['status']):
                await message.reply("❌ Status inválido. Use apenas 'Análise' ou 'Aprovada'.")
                return

        # Validação da Origem
        if 'origem' in conta:
            if not validar_origem(conta['origem']):
                await message.reply("❌ Origem inválida. Use apenas 'Lead Manual', 'Repescagem', 'Discador', 'Mensageria' ou 'Indicação'.")
                return

        # Validação do E-mail
        if 'email' in conta:
            if not validar_email(conta['email']):
                await message.reply("❌ E-mail inválido. O e-mail deve conter '@'.")
                return

        # Mapear o nome de usuário do Discord para o nome do consultor
        nome_usuario = message.author.name  # Nome de usuário do Discord
        if nome_usuario in MAPEAMENTO_USUARIOS:
            conta['consultor'] = MAPEAMENTO_USUARIOS[nome_usuario]
        else:
            await message.reply(f"❌ Nome de usuário '{nome_usuario}' não está mapeado. Contate o administrador.")
            return

        # Verificar se o CNPJ já foi registrado
        if 'cnpj' in conta:
            if not any('cnpj' in c and c['cnpj'] == conta['cnpj'] for c in contas_abertas):
                # Adicionar o ID da mensagem à conta
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
    # Verificar se a mensagem excluída está no canal de prospecção
    if message.channel.id == ID_CANAL_MONITORADO:
        print(f'Mensagem excluída detectada: ID {message.id}')  # Depuração
        for conta in contas_abertas:
            if 'mensagem_id' in conta and conta['mensagem_id'] == message.id:
                # Remover a conta
                contas_abertas.remove(conta)
                with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
                    json.dump(contas_abertas, f, indent=4, ensure_ascii=False)
                print(f'Conta removida: {conta}')
                break

@bot.command()
async def exportar(ctx):
    print(f'Comando "!exportar" recebido no canal {ctx.channel.name} (ID: {ctx.channel.id})')  # Depuração
    agora = datetime.datetime.now()

    if contas_abertas:
        for conta in contas_abertas:
            if "data" not in conta:
                conta["data"] = datetime.now().strftime("%d/%m/%Y")  # Formato: DD/MM/AAAA

        # Filtrando apenas os campos necessários
        colunas_desejadas = ["data", "cnpj", "empresa", "consultor", "origem", "status"]
        df = pd.DataFrame(contas_abertas)

        # Garantindo que apenas as colunas desejadas apareçam e lidando com valores ausentes
        df = df[[col for col in colunas_desejadas if col in df.columns]].fillna("")

        # Nome do arquivo
        arquivo_excel = f"contas_abertas{agora}.xlsx"
        df.to_excel(arquivo_excel, index=False)

        await ctx.send("Aqui está o arquivo de contas abertas:", file=discord.File(arquivo_excel))
    else:
        await ctx.send("Nenhuma conta aberta registrada até o momento.")

bot.run(TOKEN)