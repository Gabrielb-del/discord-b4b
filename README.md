# 🤖 Discord B4B - Sistema de Rankeamento

> Sistema automatizado para monitoramento de contas abertas e rankeamento de desempenho

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Discord.py](https://img.shields.io/badge/Discord.py-2.0+-blue?logo=discord)
![Status](https://img.shields.io/badge/Status-Produção-brightgreen)

## 🚀 Funcionalidades Principais
- **Ranking automático** (atualização a cada 30 minutos)
- **Controle de metas diárias** (70 contas/dia)
- **Comandos administrativos** via Discord
- **Exportação para Excel** (!exportar)
- **Sincronização em nuvem** (Google Cloud VM)

## ⚙️ Configuração

### Pré-requisitos
- Python 3.9+
- Conta no Discord Developer
- VM na Google Cloud (Recomendado: e2-small)

### Instalação
```bash
# Clone o repositório
git clone https://github.com/Gabrielb-del/discord-b4b.git

# Configure o ambiente
cd discord-b4b
python -m venv venv
source venv/bin/activate
pip install //instalar as dependências
