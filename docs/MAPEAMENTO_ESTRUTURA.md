# Mapeamento da Estrutura do Projeto Combinado

**Data:** 26 de outubro de 2025  
**Autor:** Manus AI  
**Objetivo:** Mapear a estrutura do projeto para identificar os principais módulos e funcionalidades, servindo como base para a auditoria completa do sistema.

---

## 1. Visão Geral da Arquitetura

O projeto **Combinado** é uma aplicação web desenvolvida em **Flask** (Python) para gerenciar transações de tokens próprios entre clientes e prestadores de serviços. O sistema possui um administrador centralizado responsável pelo controle de tokenomics e configurações. A arquitetura é modular, com separação clara entre rotas, serviços, modelos e templates.

### Tecnologias Principais

- **Framework:** Flask (Python 3.11)
- **Banco de Dados:** PostgreSQL
- **ORM:** SQLAlchemy
- **Formulários:** WTForms
- **Templates:** Jinja2
- **Autenticação:** Sessões Flask com decoradores personalizados
- **Versionamento:** Git + GitHub

---

## 2. Estrutura de Diretórios e Arquivos

### 2.1 Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `app.py` | Ponto de entrada da aplicação Flask, inicialização e configuração de extensões |
| `models.py` | Definições dos modelos de dados (User, AdminUser, Order, Transaction, Wallet, etc.) |
| `forms.py` | Formulários de validação de entrada de dados usando WTForms |
| `config.py` | Configurações da aplicação (chaves secretas, URI do banco de dados, etc.) |

### 2.2 Módulo de Rotas (`routes/`)

O módulo de rotas contém os blueprints que definem os endpoints da aplicação:

| Arquivo | Blueprint | Prefixo | Descrição |
|---------|-----------|---------|-----------|
| `admin_routes.py` | `admin_bp` | `/admin` | Rotas administrativas (dashboard, gestão de usuários, configurações) |
| `app_routes.py` | `app_bp` | `/app` | Rotas da área do cliente (dashboard, perfil, ordens) |
| `auth_routes.py` | `auth_bp` | `/auth` | Rotas de autenticação (login, logout, registro, convites) |
| `cliente_routes.py` | `cliente_bp` | `/cliente` | Rotas específicas do cliente (histórico, transações) |
| `home_routes.py` | `home_bp` | `/` | Rotas públicas (página inicial, sobre, contato) |
| `prestador_routes.py` | `prestador_bp` | `/prestador` | Rotas do prestador (dashboard, ordens, carteira) |
| `role_routes.py` | `role_bp` | `/role` | Rotas de gerenciamento de papéis |

### 2.3 Módulo de Serviços (`services/`)

O módulo de serviços encapsula a lógica de negócio da aplicação:

| Arquivo | Descrição |
|---------|-----------|
| `admin_service.py` | Lógica de gerenciamento administrativo (estatísticas, usuários) |
| `auth_service.py` | Lógica de autenticação e autorização (decoradores, sessão) |
| `cliente_service.py` | Lógica específica do cliente |
| `config_service.py` | Gerenciamento de configurações do sistema |
| `invite_service.py` | Lógica de convites e onboarding |
| `order_service.py` | Lógica de gerenciamento de ordens/contratos |
| `prestador_service.py` | Lógica específica do prestador |
| `report_service.py` | Geração de relatórios e exportação de dados |
| `role_service.py` | Gerenciamento de papéis e permissões |
| `validation_service.py` | Validações complexas de dados |
| `wallet_service.py` | Lógica de carteiras e transações de tokens |

### 2.4 Modelos de Dados (`models.py`)

Os principais modelos de dados identificados são:

- **User:** Usuários do sistema (clientes e prestadores)
- **AdminUser:** Usuários administrativos
- **Order:** Ordens/contratos de serviço
- **Transaction:** Transações de tokens
- **Wallet:** Carteiras de usuários
- **SystemConfig:** Configurações dinâmicas do sistema
- **Invite:** Convites para novos usuários

### 2.5 Formulários (`forms.py`)

Os formulários de validação incluem:

- **CreateUserForm:** Criação de usuários
- **EditUserForm:** Edição de usuários
- **SystemConfigForm:** Configurações do sistema
- **AddTokensForm:** Adição de tokens
- Outros formulários de login, registro, ordens, etc.

### 2.6 Templates (`templates/`)

A estrutura de templates segue a organização por papel de usuário:

- `base.html`: Layout base da aplicação
- `auth/`: Templates de autenticação
- `admin/`: Templates administrativos
- `client/` ou `app/`: Templates do cliente
- `provider/` ou `prestador/`: Templates do prestador
- `home/`: Templates públicos

### 2.7 Arquivos Estáticos (`static/`)

Contém CSS, JavaScript, imagens e outros recursos estáticos.

---

## 3. Fluxo de Funcionalidades Principais

### 3.1 Autenticação e Autorização

1. **Login:** Usuários acessam `/auth/login` (cliente/prestador) ou `/auth/admin-login` (admin)
2. **Validação:** `auth_service.py` valida credenciais e cria sessão
3. **Controle de Acesso:** Decoradores (`@login_required`, `@admin_required`) protegem rotas
4. **Logout:** Limpa a sessão e redireciona para a página inicial

### 3.2 Gestão de Usuários (Admin)

1. **Listagem:** `/admin/usuarios` exibe todos os usuários
2. **Criação:** `/admin/usuarios/criar` permite criar novos usuários
3. **Edição:** `/admin/usuarios/<id>/editar` permite editar usuários existentes
4. **Remoção:** `/admin/usuarios/<id>/remover` remove usuários

### 3.3 Fluxo de Ordens

1. **Cliente cria ordem:** Através do dashboard do cliente
2. **Prestador visualiza ordens disponíveis:** No dashboard do prestador
3. **Prestador aceita ordem:** Ordem muda de status para "aceita"
4. **Conclusão:** Cliente ou prestador marca como concluída
5. **Transação:** Tokens são transferidos do cliente para o prestador, com dedução de taxa para o admin

### 3.4 Tokenomics

1. **Compra de Tokens:** Administrador disponibiliza tokens para clientes
2. **Transferência:** Tokens são transferidos entre carteiras durante transações
3. **Taxas:** Sistema deduz taxa automática e transfere para carteira do admin
4. **Saldo:** Carteiras são atualizadas em tempo real

---

## 4. Pontos de Atenção Identificados

### 4.1 Potenciais Inconsistências

- **Duplicação de rotas:** Verificar se `cliente_routes.py` e `app_routes.py` não possuem sobreposição
- **Decoradores de autenticação:** Garantir que todas as rotas protegidas possuem os decoradores adequados
- **Validação de formulários:** Verificar se todos os formulários estão sendo validados corretamente
- **Tratamento de erros:** Identificar rotas sem tratamento adequado de exceções

### 4.2 Áreas Críticas para Auditoria

1. **Segurança:**
   - Validação de entrada em todos os formulários
   - Proteção contra CSRF
   - Criptografia de senhas
   - Controle de acesso baseado em papéis

2. **Lógica de Negócio:**
   - Cálculo de taxas
   - Transferência de tokens
   - Atualização de saldos
   - Mudança de status de ordens

3. **Integridade de Dados:**
   - Transações atômicas
   - Validação de saldos antes de transferências
   - Logs de auditoria

4. **Performance:**
   - Queries N+1
   - Índices de banco de dados
   - Caching de configurações

---

## 5. Próximos Passos da Auditoria

1. **Fase 2:** Auditar arquivos de rotas para identificar inconsistências
2. **Fase 3:** Auditar serviços e modelos para verificar lógica de negócio
3. **Fase 4:** Auditar templates e formulários para problemas de renderização
4. **Fase 5:** Documentar problemas encontrados em relatório de auditoria
5. **Fases 6-8:** Desenvolver testes automatizados
6. **Fase 9:** Executar testes e corrigir falhas
7. **Fase 10:** Versionar código com testes
8. **Fase 11:** Entregar relatório final

---

**Conclusão:** O projeto possui uma estrutura modular bem definida, com separação clara de responsabilidades entre rotas, serviços e modelos. A auditoria completa permitirá identificar e corrigir proativamente possíveis falhas e inconsistências, garantindo a robustez e a qualidade do sistema.

