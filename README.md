# Sistema Combinado v1.0.0

Sistema de gestão de tokens e serviços entre clientes e prestadores, com administração centralizada.

## 🚀 Características Principais

- **Sistema de Tokens Próprios**: 1 token = 1 real brasileiro
- **Papéis Duais**: Usuários podem ser clientes e prestadores simultaneamente
- **Sistema de Convites**: Clientes podem convidar prestadores específicos
- **Gestão de Ordens**: Criação, aceitação e conclusão de serviços
- **Carteiras Digitais**: Saldos, escrow e transações auditáveis
- **Dashboard Administrativo**: Controle completo do sistema
- **Interface Responsiva**: Funciona em desktop, tablet e mobile

## 🛠️ Tecnologias

- **Backend**: Python 3.11 + Flask
- **Banco de Dados**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Frontend**: Bootstrap 5 + JavaScript
- **Autenticação**: Flask-Login com sessões seguras
- **Formulários**: Flask-WTF com validação CSRF

## 📦 Instalação

### Pré-requisitos
- Python 3.11+
- pip (gerenciador de pacotes Python)

### Configuração

1. **Clone o repositório**
```bash
git clone <url-do-repositorio>
cd Combinado_Manus
```

2. **Crie um ambiente virtual**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

3. **Instale as dependências**
```bash
pip install flask flask-sqlalchemy flask-migrate flask-wtf flask-cors
pip install requests  # Para testes
```

4. **Execute o sistema**
```bash
python app.py
```

5. **Acesse o sistema**
- URL: http://127.0.0.1:5001
- Admin: http://127.0.0.1:5001/auth/admin-login

## 🔐 Credenciais Padrão

- **Email**: admin@combinado.com
- **Senha**: admin123
- **Saldo inicial**: 100.000 tokens

## 📋 Funcionalidades

### Para Administradores
- ✅ Dashboard com métricas do sistema
- ✅ Gestão de usuários (criar, editar, desativar)
- ✅ Controle de tokens (criar, distribuir)
- ✅ Monitoramento de transações
- ✅ Relatórios financeiros
- ✅ Configurações do sistema
- ✅ Logs e auditoria

### Para Clientes
- ✅ Dashboard personalizado
- ✅ Carteira digital com saldo
- ✅ Criação de ordens de serviço
- ✅ Sistema de convites para prestadores
- ✅ Histórico de transações
- ✅ Alternância para papel de prestador

### Para Prestadores
- ✅ Dashboard de oportunidades
- ✅ Visualização de ordens disponíveis
- ✅ Recebimento e resposta a convites
- ✅ Gestão de serviços aceitos
- ✅ Controle de ganhos
- ✅ Alternância para papel de cliente

## 🏗️ Arquitetura

```
Sistema Combinado/
├── app.py                 # Aplicação principal
├── config.py              # Configurações
├── models.py              # Modelos do banco de dados
├── forms.py               # Formulários WTF
├── version.py             # Informações de versão
├── routes/                # Rotas organizadas por módulo
│   ├── admin_routes.py    # Rotas administrativas
│   ├── auth_routes.py     # Autenticação
│   ├── cliente_routes.py  # Área do cliente
│   ├── prestador_routes.py # Área do prestador
│   └── ...
├── services/              # Lógica de negócio
│   ├── admin_service.py   # Serviços administrativos
│   ├── wallet_service.py  # Gestão de carteiras
│   ├── order_service.py   # Gestão de ordens
│   └── ...
├── templates/             # Templates HTML
│   ├── admin/             # Templates administrativos
│   ├── cliente/           # Templates do cliente
│   ├── prestador/         # Templates do prestador
│   └── ...
└── static/                # Arquivos estáticos (CSS, JS)
```

## 🔄 Fluxo de Uso

1. **Admin** cria usuários e distribui tokens iniciais
2. **Clientes** criam ordens ou enviam convites para prestadores
3. **Prestadores** aceitam ordens/convites e executam serviços
4. **Sistema** gerencia escrow e libera pagamentos automaticamente
5. **Todos** podem alternar entre papéis conforme necessário

## 🛡️ Segurança

- Autenticação baseada em sessões Flask
- Validação CSRF em todos os formulários
- Sanitização de dados de entrada
- Logs de auditoria para todas as operações
- Controle de acesso baseado em papéis
- Transações atômicas no banco de dados

## 📊 Monitoramento

- Dashboard administrativo com métricas em tempo real
- Logs estruturados em arquivos separados
- Alertas para atividades suspeitas
- Relatórios financeiros detalhados
- Validação de integridade do sistema

## 🤝 Contribuição

Este é um sistema proprietário desenvolvido por W-jr.

## 📞 Contato

- **Desenvolvedor**: W-jr
- **Telefone**: (89) 98137-5841
- **Versão**: 1.0.0
- **Data**: 05/11/2025

## 📄 Licença

© 2025 W-jr (89) 98137-5841. Todos os direitos reservados.

---

**Sistema Combinado v1.0.0** - A primeira versão estável e funcional do sistema de gestão de tokens e serviços.