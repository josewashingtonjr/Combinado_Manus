# Sistema Combinado

Plataforma segura para conectar clientes e prestadores de serviços com sistema de pagamentos protegidos por escrow.

## 📋 Descrição

O Sistema Combinado é uma aplicação web desenvolvida em Flask que permite a conexão entre clientes e prestadores de serviços, com um sistema interno de tokens (1 token = R$ 1,00) para gerenciamento de transações de forma segura e auditável.

### Características Principais

- **Sistema de Escrow**: Pagamentos seguros com liberação apenas após conclusão do serviço
- **Modelo Blockchain Interno**: Rastreabilidade e auditabilidade completa sem taxas de blockchain externa
- **Múltiplos Papéis**: Usuários podem ser clientes, prestadores ou ambos simultaneamente
- **Painel Administrativo**: Gestão completa de usuários, tokens e configurações
- **Segurança**: Autenticação robusta, hash de senhas, CSRF protection

## 🚀 Tecnologias

- **Backend**: Flask (Python 3.11)
- **Banco de Dados**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Autenticação**: Session-based com tokens
- **Segurança**: Werkzeug, Flask-CORS

## 📁 Estrutura do Projeto

```
projeto/
├── app.py                  # Aplicação principal
├── config.py              # Configurações
├── models.py              # Modelos de dados
├── forms.py               # Formulários
├── routes/                # Rotas da aplicação
│   ├── auth_routes.py     # Autenticação
│   ├── admin_routes.py    # Administração
│   ├── cliente_routes.py  # Área do cliente
│   ├── prestador_routes.py # Área do prestador
│   └── home_routes.py     # Página inicial
├── services/              # Lógica de negócio
│   ├── auth_service.py
│   ├── admin_service.py
│   ├── cliente_service.py
│   ├── prestador_service.py
│   └── wallet_service.py
├── templates/             # Templates HTML
│   ├── auth/
│   ├── admin/
│   ├── cliente/
│   ├── prestador/
│   ├── home/
│   └── errors/
├── static/                # Arquivos estáticos
│   ├── css/
│   └── js/
└── docs/                  # Documentação
    ├── PLANTA_ARQUITETONICA.md
    ├── PDR_mudancas.md
    └── ...
```

## 🔧 Instalação

### Pré-requisitos

- Python 3.11+
- PostgreSQL 12+
- pip

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/SEU_USUARIO/combinado.git
cd combinado
```

2. Crie um ambiente virtual:
```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o banco de dados:
```bash
# Crie um banco PostgreSQL
createdb combinado

# Configure a variável de ambiente
export DATABASE_URL="postgresql://usuario:senha@localhost/combinado"
```

5. Configure as variáveis de ambiente:
```bash
export SECRET_KEY="sua-chave-secreta-aqui"
export FLASK_ENV="development"
```

6. Execute as migrações:
```bash
python migrate.py
```

7. Inicie o servidor:
```bash
python app.py
```

O sistema estará disponível em `http://localhost:5001`

## 👥 Credenciais de Teste

### Administrador
- **E-mail**: admin@combinado.com
- **Senha**: admin12345

### Cliente
- **E-mail**: cliente@teste.com
- **Senha**: cliente123

### Prestador
- **E-mail**: prestador@teste.com
- **Senha**: prestador123

## 📖 Documentação

A documentação completa está disponível na pasta `/docs`:

- **PLANTA_ARQUITETONICA.md**: Arquitetura detalhada do sistema
- **PDR_mudancas.md**: Processo de mudanças rigoroso
- **CORRECOES_TRATAMENTO_ERRO.md**: Tratamento de erros implementado
- **GUIA_CONSULTA_RAPIDA.md**: Guia rápido de consulta

## 🔐 Segurança

- Senhas hasheadas com Werkzeug (scrypt)
- Proteção CSRF em todos os formulários
- Validação de entrada no backend e frontend
- Sessões seguras com tokens
- CORS configurado adequadamente
- Logs de auditoria para ações críticas

## 🎯 Funcionalidades

### Para Clientes
- Buscar prestadores de serviços
- Criar ordens de serviço
- Gerenciar carteira (saldo em R$)
- Avaliar prestadores
- Histórico de transações

### Para Prestadores
- Publicar serviços oferecidos
- Receber e gerenciar ordens
- Receber pagamentos instantâneos
- Gerenciar carteira
- Histórico de trabalhos

### Para Administradores
- Gestão completa de usuários
- Controle de tokens do sistema
- Configuração de taxas
- Relatórios e estatísticas
- Logs de auditoria
- Resolução de disputas

## 📊 Status do Projeto

✅ Sistema de autenticação funcionando  
✅ Painéis admin, cliente e prestador criados  
✅ Tratamento de erros implementado  
✅ Templates responsivos  
⏳ Sistema de carteiras (em desenvolvimento)  
⏳ Sistema de ordens (em desenvolvimento)  
⏳ Sistema de avaliações (planejado)  

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

**Importante**: Siga o PDR (Processo de Mudanças Rigoroso) documentado em `/docs/PDR_mudancas.md`

## 📝 Licença

Este projeto é proprietário. Todos os direitos reservados.

## 📞 Contato

**Desenvolvedor**: W-Jr  
**Telefone**: (89) 98137-5841

---

**Versão**: 1.0.0  
**Última atualização**: 05 de Outubro de 2025
