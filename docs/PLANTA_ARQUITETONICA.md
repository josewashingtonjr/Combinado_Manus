# Planta Arquitetônica Detalhada - Sistema Combinado v2.0

## 1. Visão Geral da Arquitetura

O sistema "Combinado" é uma aplicação web baseada em Flask, projetada para gerenciar transações de tokens próprios (1 token = 1 real) entre clientes e prestadores de serviços, com um administrador centralizado para controle de tokenomics e configurações. O sistema implementa um modelo conceitual de blockchain internamente, sem usar blockchain real, para garantir rastreabilidade, auditabilidade e segurança das transações, evitando taxas de transação externa.

- **Framework Principal:** Flask (Python)
- **Banco de Dados:** SQLAlchemy com SQLite para desenvolvimento e PostgreSQL para produção.
- **Modelo Blockchain Interno:** O sistema segue o modelo conceitual de blockchain (carteiras, escrow, rastreabilidade, auditabilidade) mas implementado internamente no banco de dados, sem usar blockchain real para evitar taxas de transação. Todas as transações são rastreáveis e auditáveis através de logs internos.
- **Tokenomics:** Tokens próprios (1:1 com BRL), gerenciamento de compra e venda pelo administrador, dedução automática de taxas.
- **Papéis de Usuário:** Administrador, Cliente, Prestador (um usuário pode ter múltiplos papéis).
- **Implantação:** Código versionado no GitHub, backend hospedado em serviço de deploy para aplicações Flask.
- **Prototipagem:** Inicialmente web-based, com transição futura para integração com a API oficial do WhatsApp Business.

## 2. Estrutura de Arquivos e Módulos

O projeto deve seguir uma estrutura modular e organizada para facilitar a manutenção e o entendimento:

- `app.py`: Ponto de entrada da aplicação Flask, inicialização, configuração de extensões (DB, Migrações, etc.).
- `config.py`: Armazena configurações da aplicação, como chaves secretas, URI do banco de dados, configurações de ambiente (desenvolvimento, teste, produção).
- `routes/`: Diretório para Blueprints que definem as rotas da aplicação.
  - `admin_routes.py`: Rotas da área administrativa.
  - `auth_routes.py`: Rotas de autenticação.
  - `cliente_routes.py`: Rotas da área do cliente.
  - `prestador_routes.py`: Rotas da área do prestador.
- `models/`: Diretório para os modelos de dados (SQLAlchemy).
  - `user.py`, `wallet.py`, `transaction.py`, etc.
- `forms/`: Diretório para os formulários (WTForms).
- `services/`: Módulo para encapsular a lógica de negócio e funções utilitárias.
- `templates/`: Diretório para arquivos HTML (Jinja2).
- `static/`: Diretório para arquivos estáticos (CSS, JavaScript, imagens, fontes).
- `tests/`: Diretório para testes automatizados.
- `docs/`: Diretório para documentação do projeto.

## 3. Lógica de Funcionamento e Relacionamentos

- **Autenticação e Autorização:**
  - Usuários se autenticam via `auth_routes.py` e `auth_service.py`.
  - Decoradores (`@login_required`, `@admin_required`) controlam o acesso às rotas.
  - Tokens CSRF são gerados e validados em todos os formulários.
- **Gestão de Usuários:**
  - O administrador gerencia usuários através da área administrativa.
- **Tokenomics e Fluxo de Transações:**
  - A lógica de compra, venda e transferência de tokens é encapsulada em `services/token_service.py`.
  - O sistema de carteiras e escrow interno é gerenciado através de `services/wallet_service.py`.
  - Todas as transações são registradas com IDs únicos e timestamps para auditabilidade completa.

## 4. Conexões e Segurança

- **Conexão com Banco de Dados:** Utilizar SQLAlchemy para prevenir SQL Injection.
- **Sistema de Carteiras Interno:** Implementação de carteiras virtuais no banco de dados com controles rigorosos de integridade e validação de saldos.
- **HTTPS:** Todas as comunicações devem ser criptografadas.
- **Validação de Entrada:** Validação robusta no backend e frontend.
- **Logs de Auditoria:** Todas as ações críticas devem ser logadas.



## 5. Modelo Blockchain Interno

O sistema implementa um modelo conceitual de blockchain sem usar tecnologia blockchain real, proporcionando os benefícios de segurança, rastreabilidade e auditabilidade sem as desvantagens de taxas de transação externa.

### 5.1. Características do Modelo Interno

- **Carteiras Virtuais:** Cada usuário possui carteiras virtuais armazenadas no banco de dados com saldos controlados rigorosamente.
- **Sistema de Escrow:** Carteiras especiais para garantias de transações, liberadas apenas após confirmação de conclusão de serviços.
- **Rastreabilidade Total:** Cada transação possui ID único, timestamp e histórico completo de origem e destino.
- **Auditabilidade:** Logs imutáveis de todas as operações para fins de auditoria e compliance.
- **Integridade de Dados:** Validações rigorosas para garantir que saldos nunca fiquem inconsistentes.
- **Atomicidade:** Transações são processadas de forma atômica, garantindo que não ocorram estados intermediários inválidos.

### 5.2. Benefícios do Modelo

- **Custo Zero de Transação:** Sem taxas de blockchain externa.
- **Performance Superior:** Transações instantâneas sem dependência de rede externa.
- **Controle Total:** Administração completa do sistema de tokens e carteiras.
- **Flexibilidade:** Possibilidade de implementar regras de negócio específicas.
- **Segurança:** Controle total sobre a segurança e validação das transações.

## 6. Terminologia e Interface do Usuário

### 6.1. Diferenciação de Terminologia por Papel

O sistema utiliza terminologias diferentes dependendo do tipo de usuário para melhor experiência e compreensão:

**Para Administradores:**
- Utilizam a terminologia técnica "tokens" para gerenciamento interno
- Têm acesso a informações sobre tokenomics e configurações do sistema
- Visualizam relatórios técnicos com métricas de tokens

**Para Usuários (Clientes e Prestadores):**
- Visualizam apenas "saldo" em reais brasileiros (R$)
- Não têm conhecimento da existência de tokens internos
- Todas as transações são apresentadas em valores monetários (R$)
- Interface simplificada focada na experiência do usuário

### 6.2. Apresentação de Valores

- **Administradores:** "1000 tokens" ou "1000 TKN"
- **Usuários:** "R$ 1.000,00" ou "Saldo: R$ 1.000,00"

### 6.3. Benefícios da Abordagem

Esta diferenciação permite que os usuários finais tenham uma experiência mais familiar e intuitiva, trabalhando diretamente com valores em reais, enquanto o sistema mantém internamente a lógica de tokens para controle técnico e auditabilidade.
