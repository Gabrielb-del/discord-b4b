# 🤖 Discord B4B - Sistema de Rankeamento

> Sistema automatizado para monitoramento de contas abertas, qualificação e rankeamento de desempenho

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Discord.py](https://img.shields.io/badge/Discord.py-2.0+-blue?logo=discord)
![Status](https://img.shields.io/badge/Status-Produção-brightgreen)

## 🚀 Funcionalidades Principais
- **Ranking automático** (atualização a cada 30 minutos)
- **Controle de metas diárias**
- **Comandos administrativos** via Discord
- **Exportação para Excel**
- **Gestão de operadores** via comandos
- **Monitoramento de qualificação**
- **Sistema de campanhas**
- **Atualização automática de operadores**

## ⚙️ Configuração

### Pré-requisitos
- Python 3.9+
- Conta no Discord Developer
- VM na Google Cloud (Recomendado: e2-small)

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/discord-b4b.git
cd discord-b4b
```

2. Configure o ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
   - Copie o arquivo `.env.example` para `.env`
   - Preencha todas as variáveis no arquivo `.env`

5. Configure os operadores:
   - Copie o arquivo `operadores.example.json` para `operadores.json`
   - Copie o arquivo `operadores_quali.example.json` para `operadores_quali.json`
   - Adicione os operadores usando os comandos apropriados

## 🤖 Bots e Comandos

### PeterBot (`peterbot.py`)
Bot principal para gerenciamento de contas, operadores e qualificação.

**Comandos de Operadores de Prospecção:**
- `!adicionar_operador [usuario_discord] [primeiro_nome] [nome_completo]` - Adiciona um novo operador de prospecção
- `!remover_operador [usuario_discord]` - Remove um operador de prospecção
- `!listar_operadores` - Lista todos os operadores de prospecção
- `!atualizar_operador [usuario_discord] [novo_nome_completo]` - Atualiza o nome de um operador de prospecção
- `!exportar` - Exporta as contas abertas para Excel

**Comandos de Operadores de Qualificação:**
- `!adicionar_quali [usuario_discord] [primeiro_nome] [nome_completo]` - Adiciona um novo operador de qualificação
- `!remover_quali [usuario_discord]` - Remove um operador de qualificação
- `!listar_quali` - Lista todos os operadores de qualificação
- `!atualizar_quali [usuario_discord] [novo_nome_completo]` - Atualiza o nome de um operador de qualificação
- `!exportar_qualificados` - Exporta os contatos qualificados para Excel

### RKDisc (`rkdisc.py`)
Bot para gerenciamento do ranking de contas abertas.

**Comandos:**
- `!ranking` - Mostra o ranking atual de contas abertas
- `!negada` - Remove uma conta do ranking do operador
- `!add [nome] [quantidade]` - Adiciona contas manualmente para um operador
- `!atualizar_operadores` - Atualiza manualmente a lista de operadores (opcional, também atualiza automaticamente)

### RKQuali (`rkquali.py`)
Bot para gerenciamento do ranking de qualificação.

**Comandos:**
- `!contatos` - Mostra o ranking atual de contatos qualificados

### Campanha (`campanha.py`)
Bot para gerenciamento de campanhas e avisos.

## 📝 Formatos de Mensagem

### Contas Abertas
```
Empresa: [Nome da Empresa]
CNPJ: [CNPJ]
Nome: [Nome do Contato]
Tel: [Telefone]
E-mail: [Email]
Origem: [Lead Manual/Repescagem/Discador/Mensageria/URA/BackOffice/Indicação]
Consultor: [Nome do Consultor]
Status: [Análise/Aprovada/Carimbada/Reprovada]
```

### Contatos Qualificados
```
Empresa: [Nome da Empresa]
CNPJ: [CNPJ]
Nome: [Nome do Contato]
Tel: [Telefone]
E-mail: [Email]
Faturamento da Empresa: [Valor]
Data conta aberta: [Data]
Nome do Consultor: [Nome]
Qualificada ou Contato: [QUALIFICADA/CONTATO]
Observações sobre o contato: [Observações]
```

## 🔄 Atualizações Automáticas

- Os rankings são atualizados a cada 30 minutos
- A lista de operadores é atualizada automaticamente (a cada 10 segundos)
- Os rankings são resetados à meia-noite
- Backups automáticos dos dados em JSON

## 🔒 Segurança

- Todos os tokens são armazenados em variáveis de ambiente
- Arquivos sensíveis são ignorados pelo git
- Backup automático dos dados em JSON
- Validações de formato e duplicidade

## 📁 Estrutura de Arquivos

```
discord-b4b/
├── peterbot.py
├── rkdisc.py
├── rkquali.py
├── campanha.py
├── requirements.txt
├── .env.example
├── .gitignore
├── operadores.example.json
├── operadores_quali.example.json
└── README.md
```

## 🚀 Como Executar

1. Ative o ambiente virtual:
```bash
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows
```

2. Execute os bots necessários:
```bash
python peterbot.py
python rkdisc.py
python rkquali.py
python campanha.py
```

## 📝 Observações

- Os tokens dos bots devem ser mantidos em segredo
- O arquivo `.env` não deve ser commitado no git
- Faça backup regular dos arquivos JSON
- Mantenha os operadores atualizados via comandos do Discord
- Use os comandos no canal apropriado para cada função

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie sua branch de feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request
