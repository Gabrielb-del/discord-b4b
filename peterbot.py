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
ID_CANAL_QUALIFICACAO = 1321967249111781398  # Substitua pelo ID correto do canal de qualificação
ARQUIVO_JSON = "contas_abertas.json"
ARQUIVO_OPERADORES = "operadores.json"
ARQUIVO_QUALIFICADOS = "contatos_qualificados.json"
ARQUIVO_OPERADORES_QUALI = "operadores_quali.json"  # Novo arquivo para operadores de qualificação

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

# Função para carregar contatos qualificados
def carregar_qualificados():
    if os.path.exists(ARQUIVO_QUALIFICADOS):
        with open(ARQUIVO_QUALIFICADOS, "r", encoding="utf-8") as f:
            try:
                dados = json.load(f)
                if isinstance(dados, list):
                    return dados
                else:
                    return []
            except json.JSONDecodeError:
                return []
    return []

# Lista para armazenar os contatos qualificados
contatos_qualificados = carregar_qualificados()

# Função para carregar operadores de qualificação
def carregar_operadores_quali():
    if os.path.exists(ARQUIVO_OPERADORES_QUALI):
        with open(ARQUIVO_OPERADORES_QUALI, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Função para salvar operadores de qualificação
def salvar_operadores_quali(operadores):
    with open(ARQUIVO_OPERADORES_QUALI, "w", encoding="utf-8") as f:
        json.dump(operadores, f, indent=4, ensure_ascii=False)

# Carregar operadores de qualificação ao iniciar
MAPEAMENTO_USUARIOS_QUALI = carregar_operadores_quali()

# Variável para armazenar a última modificação dos arquivos
ultima_modificacao_operadores = 0
ultima_modificacao_operadores_quali = 0

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

def salvar_contas_abertas():
    try:
        with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(contas_abertas, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        print(f"✅ Arquivo de contas abertas salvo com sucesso. Total de contas: {len(contas_abertas)}")
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo de contas abertas: {e}")

def salvar_contatos_qualificados():
    try:
        with open(ARQUIVO_QUALIFICADOS, "w", encoding="utf-8") as f:
            json.dump(contatos_qualificados, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        print(f"✅ Arquivo de contatos qualificados salvo com sucesso. Total de contatos: {len(contatos_qualificados)}")
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo de contatos qualificados: {e}")

@tasks.loop(time=time(hour=0, minute=0))
async def resetar_contas():
    global contas_abertas
    contas_abertas = []
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(contas_abertas, f, indent=4, ensure_ascii=False)
    print("🔄 Contas resetadas para o novo dia.")

@tasks.loop(time=time(hour=0, minute=0))
async def resetar_quali():
    try:
        global contatos_qualificados
        print("🔄 Iniciando reset dos contatos qualificados...")
        
        # Faz backup dos dados antigos antes de resetar
        if contatos_qualificados:
            data_anterior = (datetime.now() - datetime.timedelta(days=1)).strftime("%d%m%Y")
            arquivo_backup = f"backup_contatos_qualificados_{data_anterior}.json"
            try:
                with open(arquivo_backup, "w", encoding="utf-8") as f:
                    json.dump(contatos_qualificados, f, indent=4, ensure_ascii=False)
                print(f"✅ Backup dos contatos salvos em: {arquivo_backup}")
            except Exception as e:
                print(f"❌ Erro ao criar backup dos contatos: {e}")
        
        # Reseta a lista de contatos
        contatos_qualificados = []
        salvar_contatos_qualificados()
        print("✅ Contatos qualificados resetados para o novo dia.")
    except Exception as e:
        print(f"❌ Erro ao resetar contatos qualificados: {e}")

@tasks.loop(seconds=10)
async def monitorar_arquivos_operadores():
    global MAPEAMENTO_USUARIOS, MAPEAMENTO_USUARIOS_QUALI, ultima_modificacao_operadores, ultima_modificacao_operadores_quali
    
    try:
        # Verifica alterações no arquivo de operadores
        if os.path.exists(ARQUIVO_OPERADORES):
            mod_operadores = os.path.getmtime(ARQUIVO_OPERADORES)
            if mod_operadores != ultima_modificacao_operadores:
                print("📝 Detectada modificação no arquivo de operadores")
                MAPEAMENTO_USUARIOS = carregar_operadores()
                ultima_modificacao_operadores = mod_operadores
                
                # Notifica no canal de comandos
                canal = bot.get_channel(ID_CANAL_COMANDOS)
                if canal:
                    await canal.send("📝 Lista de operadores atualizada!")
        
        # Verifica alterações no arquivo de operadores de qualificação
        if os.path.exists(ARQUIVO_OPERADORES_QUALI):
            mod_quali = os.path.getmtime(ARQUIVO_OPERADORES_QUALI)
            if mod_quali != ultima_modificacao_operadores_quali:
                print("📝 Detectada modificação no arquivo de operadores de qualificação")
                MAPEAMENTO_USUARIOS_QUALI = carregar_operadores_quali()
                ultima_modificacao_operadores_quali = mod_quali
                
                # Notifica no canal de comandos
                canal = bot.get_channel(ID_CANAL_COMANDOS)
                if canal:
                    await canal.send("📝 Lista de operadores de qualificação atualizada!")
    
    except Exception as e:
        print(f"❌ Erro ao monitorar arquivos de operadores: {e}")

@bot.event
async def on_ready():
    print(f'Logado como {bot.user}')
    print(f'Comandos registrados: {[cmd.name for cmd in bot.commands]}')
    
    # Inicializa as variáveis de última modificação
    global ultima_modificacao_operadores, ultima_modificacao_operadores_quali
    try:
        ultima_modificacao_operadores = os.path.getmtime(ARQUIVO_OPERADORES) if os.path.exists(ARQUIVO_OPERADORES) else 0
        ultima_modificacao_operadores_quali = os.path.getmtime(ARQUIVO_OPERADORES_QUALI) if os.path.exists(ARQUIVO_OPERADORES_QUALI) else 0
    except Exception as e:
        print(f"❌ Erro ao obter última modificação dos arquivos: {e}")
        ultima_modificacao_operadores = 0
        ultima_modificacao_operadores_quali = 0
    
    # Inicia os loops de tarefas
    resetar_contas.start()
    resetar_quali.start()
    monitorar_arquivos_operadores.start()

# Função para validar e limpar os dados do contato
def processar_dados_contato(dados):
    try:
        # Padrões para extrair informações do contato qualificado
        padrao_quali = {
            "empresa": r"(?:Empresa|Razão Social):\s*(.*?)(?=\s*CNPJ:|$)",
            "cnpj": r"CNPJ:\s*(\d+)(?=\s*Nome:|$)",
            "nome": r"Nome:\s*(.*?)(?=\s*Tel:|$)",
            "telefone": r"Tel:\s*(\d+)(?=\s*E-mail:|$)",
            "email": r"E-mail:\s*(.*?)(?=\s*Faturamento da Empresa:|$)",
            "faturamento": r"Faturamento da Empresa:\s*(.*?)(?=\s*Data conta aberta:|$)",
            "data_conta": r"Data conta aberta:\s*(.*?)(?=\s*Nome do Consultor:|$)",
            "consultor": r"Nome do Consultor:\s*(.*?)(?=\s*Qualificada ou Contato:|$)",
            "tipo_qualificacao": r"Qualificada ou Contato:\s*(.*?)(?=\s*Observações sobre o contato:|$)",
            "observacoes": r"Observações sobre o contato:\s*(.*?)$"
        }

        contato = {}
        campos_faltantes = []
        
        # Processa cada campo com validação extra
        for chave, regex in padrao_quali.items():
            resultado = re.search(regex, dados, re.DOTALL | re.IGNORECASE)
            if resultado:
                valor = resultado.group(1).strip()
                # Remove quebras de linha e espaços extras
                valor = ' '.join(valor.splitlines()).strip()
                
                # Validações específicas por campo
                if chave == "cnpj" and valor:
                    # Remove caracteres não numéricos do CNPJ
                    valor = re.sub(r'\D', '', valor)
                elif chave == "telefone" and valor:
                    # Remove caracteres não numéricos do telefone
                    valor = re.sub(r'\D', '', valor)
                elif chave == "tipo_qualificacao" and valor:
                    # Padroniza o tipo de qualificação
                    valor = valor.upper().strip()
                    if valor not in ['QUALIFICADA', 'CONTATO']:
                        raise ValueError(f"Tipo de qualificação inválido: {valor}")
                
                contato[chave] = valor
            else:
                campos_faltantes.append(chave)
        
        return contato, campos_faltantes
    except Exception as e:
        print(f"❌ Erro ao processar dados do contato: {e}")
        return None, ["erro_processamento"]

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.author == bot.user:
        return

    # Processamento de contas abertas
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

    # Processamento de contatos qualificados
    elif message.channel.id == ID_CANAL_QUALIFICACAO:
        dados = message.content.strip()
        
        # Processa os dados do contato
        contato, campos_faltantes = processar_dados_contato(dados)
        
        if not contato:
            return
            
        if campos_faltantes:
            await message.reply(f"❌ Faltam os seguintes campos: {', '.join(campos_faltantes)}. Por favor, envie novamente.")
            return

        # Adiciona campos de controle
        contato["hora_envio"] = datetime.now().strftime("%H:%M")
        contato["data_registro"] = datetime.now().strftime("%d/%m/%Y")
        contato["mensagem_id"] = message.id

        # Verifica o operador
        nome_usuario = message.author.name
        if nome_usuario in MAPEAMENTO_USUARIOS_QUALI:
            contato['operador_quali'] = MAPEAMENTO_USUARIOS_QUALI[nome_usuario]
            contato['consultor'] = contato['operador_quali']
        else:
            await message.reply(f"❌ Nome de usuário '{nome_usuario}' não está mapeado no time de qualificação. Contate o administrador.")
            return

        # Verifica duplicidade de CNPJ
        if 'cnpj' in contato:
            for contato_existente in contatos_qualificados:
                if contato_existente['cnpj'] == contato['cnpj']:
                    if contato_existente.get('operador_quali') == MAPEAMENTO_USUARIOS_QUALI[message.author.name]:
                        await message.add_reaction("✅")
                        return
                    else:
                        await message.reply(f"⚠️ Este CNPJ já foi registrado pelo operador: {contato_existente.get('operador_quali')}")
                        return

        # Salva o contato
        contatos_qualificados.append(contato)
        try:
            salvar_contatos_qualificados()
            await message.add_reaction("✅")
        except Exception as e:
            print(f"❌ Erro ao salvar contato: {e}")
            await message.reply("❌ Erro ao salvar o contato. Por favor, tente novamente.")
            contatos_qualificados.remove(contato)

@bot.event
async def on_message_delete(message):
    try:
        # Processamento de exclusão de contas abertas
        if message.channel.id == ID_CANAL_MONITORADO:
            print(f'🗑️ Mensagem excluída detectada no canal monitorado: ID {message.id}')
            print(f'Total de contas antes da remoção: {len(contas_abertas)}')
            
            conta_removida = None
            indice_remocao = None
            
            # Procura a conta a ser removida
            for i, conta in enumerate(contas_abertas):
                if conta.get('mensagem_id') == message.id:
                    conta_removida = conta
                    indice_remocao = i
                    break
            
            # Remove a conta se encontrada
            if conta_removida and indice_remocao is not None:
                del contas_abertas[indice_remocao]
                print(f'✅ Conta encontrada e removida: {conta_removida}')
                print(f'Total de contas após remoção: {len(contas_abertas)}')
                
                # Força a atualização do arquivo
                try:
                    salvar_contas_abertas()
                    print(f'Conta removida com sucesso - CNPJ: {conta_removida.get("cnpj", "N/A")}, Consultor: {conta_removida.get("consultor", "N/A")}')
                except Exception as e:
                    print(f"❌ Erro ao salvar arquivo após remoção: {e}")
            else:
                print(f'❌ Nenhuma conta encontrada para a mensagem ID {message.id}')
                print(f'IDs das mensagens nas contas: {[c.get("mensagem_id") for c in contas_abertas]}')
        
        # Processamento de exclusão de contatos qualificados
        elif message.channel.id == ID_CANAL_QUALIFICACAO:
            print(f'🗑️ Mensagem de qualificação excluída detectada: ID {message.id}')
            print(f'Total de contatos antes da remoção: {len(contatos_qualificados)}')
            
            contato_removido = None
            indice_remocao = None
            
            # Procura o contato a ser removido
            for i, contato in enumerate(contatos_qualificados):
                if contato.get('mensagem_id') == message.id:
                    contato_removido = contato
                    indice_remocao = i
                    break
            
            # Remove o contato se encontrado
            if contato_removido and indice_remocao is not None:
                del contatos_qualificados[indice_remocao]
                print(f'✅ Contato qualificado encontrado e removido: {contato_removido}')
                print(f'Total de contatos após remoção: {len(contatos_qualificados)}')
                
                # Força a atualização do arquivo
                try:
                    salvar_contatos_qualificados()
                    print(f'Contato removido com sucesso - CNPJ: {contato_removido.get("cnpj", "N/A")}, Operador: {contato_removido.get("operador_quali", "N/A")}')
                except Exception as e:
                    print(f"❌ Erro ao salvar arquivo após remoção: {e}")
            else:
                print(f'❌ Nenhum contato qualificado encontrado para a mensagem ID {message.id}')
                print(f'IDs das mensagens nos contatos: {[c.get("mensagem_id") for c in contatos_qualificados]}')
    
    except Exception as e:
        print(f"❌ Erro ao processar exclusão de mensagem: {e}")

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

@bot.command(name="expquali")
async def expquali(ctx):
    print(f'Comando "!expquali" recebido no canal {ctx.channel.name} (ID: {ctx.channel.id})')
    if ctx.channel.id == ID_CANAL_MONITORADO:
        return

    if contatos_qualificados:
        # Criar uma cópia dos contatos para não modificar os originais
        contatos_para_excel = []
        for contato in contatos_qualificados:
            contato_modificado = contato.copy()
            # Procurar o nome completo do operador
            nome_usuario = next((usuario for usuario, nome in MAPEAMENTO_USUARIOS_QUALI.items() 
                              if nome == contato['consultor']), None)
            if nome_usuario:
                contato_modificado['consultor'] = MAPEAMENTO_USUARIOS_QUALI[nome_usuario]
            contatos_para_excel.append(contato_modificado)

        colunas_desejadas = ["data_registro", "hora_envio", "cnpj", "empresa", "nome", "telefone", "email", 
                            "faturamento", "data_conta", "consultor", "tipo_qualificacao", "observacoes"]
        df = pd.DataFrame(contatos_para_excel)
        df = df[[col for col in colunas_desejadas if col in df.columns]].fillna("")
        arquivo_excel = f"CONTATOS_QUALIFICADOS_{datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx"
        df.to_excel(arquivo_excel, index=False)

        await ctx.send("📊 Aqui está o arquivo de contatos qualificados:", file=discord.File(arquivo_excel))
        
        # Remover o arquivo após enviar
        os.remove(arquivo_excel)
    else:
        await ctx.send("❌ Nenhum contato qualificado registrado até o momento.")

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

# Comandos para gerenciar operadores de qualificação
@bot.command(name="adicionar_quali")
async def adicionar_operador_quali(ctx, usuario_discord: str, primeiro_nome: str, *, nome_completo: str):
    """Adiciona um novo operador ao time de qualificação
    Exemplo: !adicionar_quali joao.b4b João 'João Silva Santos'"""
    if ctx.channel.id != ID_CANAL_COMANDOS:
        return
        
    global MAPEAMENTO_USUARIOS_QUALI
    MAPEAMENTO_USUARIOS_QUALI[usuario_discord] = nome_completo
    salvar_operadores_quali(MAPEAMENTO_USUARIOS_QUALI)
    await ctx.send(f"✅ Operador de qualificação adicionado com sucesso!\nUsuário Discord: {usuario_discord}\nNome Completo: {nome_completo}")

@bot.command(name="remover_quali")
async def remover_operador_quali(ctx, usuario_discord: str):
    """Remove um operador do time de qualificação
    Exemplo: !remover_quali joao.b4b"""
    if ctx.channel.id != ID_CANAL_COMANDOS:
        return
        
    global MAPEAMENTO_USUARIOS_QUALI
    if usuario_discord in MAPEAMENTO_USUARIOS_QUALI:
        del MAPEAMENTO_USUARIOS_QUALI[usuario_discord]
        salvar_operadores_quali(MAPEAMENTO_USUARIOS_QUALI)
        await ctx.send(f"✅ Operador de qualificação {usuario_discord} removido com sucesso!")
    else:
        await ctx.send(f"❌ Operador de qualificação {usuario_discord} não encontrado!")

@bot.command(name="listar_quali")
async def listar_operadores_quali(ctx):
    """Lista todos os operadores do time de qualificação"""
    if ctx.channel.id != ID_CANAL_COMANDOS:
        return
        
    if not MAPEAMENTO_USUARIOS_QUALI:
        await ctx.send("Nenhum operador de qualificação cadastrado!")
        return
        
    mensagem = "📋 **Lista de Operadores de Qualificação:**\n\n"
    for usuario, nome in MAPEAMENTO_USUARIOS_QUALI.items():
        mensagem += f"👤 **{usuario}** - {nome}\n"
    
    await ctx.send(mensagem)

@bot.command(name="atualizar_quali")
async def atualizar_operador_quali(ctx, usuario_discord: str, *, novo_nome_completo: str):
    """Atualiza o nome completo de um operador de qualificação
    Exemplo: !atualizar_quali joao.b4b 'João Silva Santos Junior'"""
    if ctx.channel.id != ID_CANAL_COMANDOS:
        return
        
    global MAPEAMENTO_USUARIOS_QUALI
    if usuario_discord in MAPEAMENTO_USUARIOS_QUALI:
        MAPEAMENTO_USUARIOS_QUALI[usuario_discord] = novo_nome_completo
        salvar_operadores_quali(MAPEAMENTO_USUARIOS_QUALI)
        await ctx.send(f"✅ Nome do operador de qualificação {usuario_discord} atualizado para: {novo_nome_completo}")
    else:
        await ctx.send(f"❌ Operador de qualificação {usuario_discord} não encontrado!")

bot.run(TOKEN)