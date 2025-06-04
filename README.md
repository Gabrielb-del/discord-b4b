# 🤖 Discord B4B - Sistema de Rankeamento

> Sistema automatizado para monitoramento de contas abertas e rankeamento de desempenho

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Discord.py](https://img.shields.io/badge/Discord.py-2.0+-blue?logo=discord)
![Status](https://img.shields.io/badge/Status-Produção-brightgreen)

## 🚀 Funcionalidades Principais
- **Ranking automático** (atualização a cada 30 minutos)
- **Controle de metas diárias**
- **Comandos administrativos** via Discord
- **Exportação para Excel** (!exportar)
- **Gestão de operadores** via comandos
- **Monitoramento de qualificação**
- **Sistema de campanhas**

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
   - Adicione os operadores no formato especificado

## 🤖 Bots Disponíveis

### PeterBot (`peterbot.py`)
Bot principal para gerenciamento de contas e operadores.

**Comandos:**
- `!adicionar_operador [usuario_discord] [primeiro_nome] [nome_completo]`
- `!remover_operador [usuario_discord]`
- `!listar_operadores`
- `!atualizar_operador [usuario_discord] [novo_nome_completo]`
- `!exportar`

### RKDisc (`rkdisc.py` e `rkdisc2.py`)
Bot para gerenciamento do ranking de contas abertas.

**Comandos:**
- `!ranking`
- `!negada`
- `!add [nome] [quantidade]`

### RKQuali (`rkquali.py`)
Bot para gerenciamento do ranking de qualificação.

### Campanha (`campanha.py`)
Bot para gerenciamento de campanhas e avisos.

## 🔒 Segurança

- Todos os tokens são armazenados em variáveis de ambiente
- Arquivos sensíveis são ignorados pelo git
- Backup automático dos dados em JSON

## 📁 Estrutura de Arquivos

```
discord-b4b/
├── peterbot.py
├── rkdisc.py
├── rkdisc2.py
├── rkquali.py
├── campanha.py
├── requirements.txt
├── .env.example
├── .gitignore
├── operadores.example.json
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

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie sua branch de feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request
