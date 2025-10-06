# Documento de Design

## Visão Geral

O design para completar o Sistema Combinado foca em uma abordagem incremental e sistemática, seguindo rigorosamente o PDR (Processo de Mudanças Rigoroso) estabelecido. O sistema já possui uma base sólida com autenticação funcionando, modelos de dados definidos, templates criados e serviços estruturados. O objetivo é completar, testar e corrigir todas as funcionalidades para que o sistema funcione de ponta a ponta.

## Arquitetura

### Arquitetura Atual (Base Existente)
- **Framework**: Flask com blueprints organizados (auth, admin, cliente, prestador, home, app)
- **Banco de Dados**: PostgreSQL com SQLAlchemy e migrações via Alembic
- **Autenticação**: Sistema de sessões com decoradores de autorização
- **Templates**: Jinja2 com herança e componentes organizados
- **Modelo de Dados**: User, AdminUser, Wallet, Transaction, Order definidos
- **Serviços**: Camada de lógica de negócio estruturada

### Arquitetura de Completude
O design seguirá uma abordagem de "completar e testar" onde cada componente será:
1. **Validado**: Verificar se está funcionando corretamente
2. **Completado**: Implementar funcionalidades faltantes
3. **Testado**: Criar testes para garantir funcionamento
4. **Integrado**: Conectar com outros componentes
5. **Documentado**: Atualizar documentação conforme PDR

## Componentes e Interfaces

### 1. Sistema de Autenticação e Autorização
**Status**: ✅ Funcional (corrigido em 05/10/2025)
**Componentes**:
- `AuthService`: Gerenciamento de sessões e verificações
- Decoradores: `@admin_required`, `@login_required`, `@cliente_required`, `@prestador_required`
- Templates de login: admin_login.html, user_login.html

**Melhorias Necessárias**:
- Validar redirecionamentos pós-login para usuários dual
- Implementar "lembrar-me" se necessário
- Adicionar logs de auditoria para logins

### 2. Sistema de Carteiras (Wallet)
**Status**: ⚠️ Modelo definido, lógica não implementada
**Componentes**:
- `Wallet` model: Saldos e escrow
- `WalletService`: Lógica de transações
- Templates de carteira para cliente e prestador

**Funcionalidades a Implementar**:
- Criação automática de carteira para novos usuários
- Operações de débito/crédito com validação de saldo
- Sistema de escrow para ordens em andamento
- Histórico de transações com rastreabilidade

### 3. Sistema de Ordens de Serviço
**Status**: ⚠️ Modelo definido, fluxo não implementado
**Componentes**:
- `Order` model: Estados e relacionamentos
- `OrderService`: Lógica de negócio
- Templates para criação, listagem e gerenciamento

**Fluxo de Estados**:
```
disponivel → aceita → em_andamento → concluida
     ↓         ↓           ↓           ↓
  cancelada  cancelada  disputada   disputada
```

### 4. Dashboard Administrativo
**Status**: ✅ Interface criada, dados mockados
**Componentes**:
- Menu lateral expansível com 8 categorias
- Cards coloridos com métricas em tempo real
- Sistema de contestações com análise
- Configurações de taxas e multas

**Dados Reais a Implementar**:
- Estatísticas reais do banco de dados
- Sistema de contestações funcional
- Persistência de configurações

### 5. Dashboards de Usuário
**Status**: ⚠️ Templates criados, dados mockados
**Componentes**:
- Dashboard do cliente: Saldo, ordens, histórico
- Dashboard do prestador: Ganhos, ordens disponíveis, estatísticas
- Alternância de papéis para usuários dual

### 6. Sistema de Convites
**Status**: 🆕 Novo componente a implementar
**Componentes**:
- `Invite` model: Convites com dados completos do serviço
- `InviteService`: Lógica completa de negócio para convites
- Templates para criação, visualização e gerenciamento
- Sistema de notificações automáticas

**Modelo de Dados Invite**:
```python
class Invite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invited_email = db.Column(db.String(120), nullable=False)
    service_title = db.Column(db.String(200), nullable=False)
    service_description = db.Column(db.Text, nullable=False)
    original_value = db.Column(db.Numeric(10, 2), nullable=False)
    final_value = db.Column(db.Numeric(10, 2), nullable=True)
    delivery_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pendente')  # pendente, aceito, recusado, expirado, convertido
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    responded_at = db.Column(db.DateTime, nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
```

**Funcionalidades Implementadas**:
- Criação de convites por clientes com validação de saldo (valor + taxa contestação)
- Notificação automática por email/sistema para prestadores
- Visualização de convites recebidos com detalhes completos
- Aceitação com possibilidade de alteração de valor e data de entrega
- Recusa com notificação automática ao cliente
- Conversão automática de convite aceito em ordem de serviço
- Cadastro de novos usuários através de token único do convite
- Sistema de expiração automática de convites não respondidos

**Fluxo de Estados do Convite**:
```
pendente → aceito → convertido (vira Order)
    ↓        ↓
recusado  expirado
```

**Validações de Saldo**:
- Cliente: deve ter saldo ≥ (valor_serviço + taxa_contestação)
- Prestador: deve ter saldo ≥ taxa_contestação (para aceitar)
- Sistema bloqueia criação/aceitação se saldo insuficiente

**InviteService Métodos**:
- `create_invite()`: Cria convite com validações
- `accept_invite()`: Aceita convite com validação de saldo
- `reject_invite()`: Recusa convite e notifica cliente
- `update_invite_terms()`: Permite alteração de valor/data
- `convert_invite_to_order()`: Converte em ordem ativa
- `expire_old_invites()`: Expira convites antigos automaticamente
- `send_invite_notification()`: Envia notificações automáticas

## Modelo de Dados

### Relacionamentos Principais
```
User (1) ←→ (1) Wallet
User (1) ←→ (N) Transaction
User (1) ←→ (N) Order (como cliente)
User (1) ←→ (N) Order (como prestador)
User (1) ←→ (N) Invite (como cliente - convites enviados)
User (1) ←→ (N) Invite (como prestador convidado - via email)
Order (1) ←→ (N) Transaction
Invite (1) ←→ (0..1) Order (quando aceito e convertido)
Wallet (1) ←→ (N) Transaction (origem e destino)
```

### Relacionamentos Específicos do Sistema de Convites
```
Cliente → cria → Invite (client_id)
Invite → convida → Prestador (invited_email)
Prestador → aceita/recusa → Invite (status)
Invite aceito → gera → Order (order_id)
Order → bloqueia → Wallet.escrow_balance
```

### Campos Críticos para Implementar
- `Wallet.balance`: Saldo disponível
- `Wallet.escrow_balance`: Saldo em garantia
- `Transaction.type`: Tipos de transação (deposito, saque, pagamento, recebimento, taxa)
- `Order.status`: Estados da ordem
- `Order.value`: Valor da ordem
- `Invite.status`: Estados do convite (pendente, aceito, recusado, expirado)
- `Invite.original_value`: Valor original proposto pelo cliente
- `Invite.final_value`: Valor final após alterações do prestador
- `Invite.invited_email`: Email do prestador convidado
- `Invite.token`: Token único para acesso ao convite

### Integridade de Dados
- Validações de saldo antes de transações
- Atomicidade em operações financeiras
- Logs imutáveis para auditoria
- IDs únicos para rastreabilidade

## Tratamento de Erros

### Estratégia de Tratamento
1. **Validação no Frontend**: JavaScript para feedback imediato
2. **Validação no Backend**: Python com mensagens claras
3. **Páginas de Erro**: 404.html e 500.html personalizadas
4. **Logs Estruturados**: Para debugging e auditoria

### Tipos de Erro
- **Validação**: Campos obrigatórios, formatos inválidos
- **Autorização**: Acesso negado, sessão expirada
- **Negócio**: Saldo insuficiente, ordem indisponível
- **Sistema**: Erro de banco, falha de conexão

### Terminologia por Usuário
- **Admin**: Mensagens técnicas com "tokens"
- **Usuários**: Mensagens amigáveis com "saldo em R$"
- **Logs**: Sempre técnicos para auditoria

## Estratégia de Testes

### Testes Unitários
- Modelos: Validações e relacionamentos
- Serviços: Lógica de negócio
- Utilitários: Formatação, validação

### Testes de Integração
- Fluxos completos: Login → Dashboard → Ação
- APIs: Requisições e respostas
- Banco de dados: Transações e rollbacks

### Testes de Interface
- Templates: Renderização correta
- JavaScript: Interatividade
- Responsividade: Diferentes dispositivos

### Testes de Segurança
- Autenticação: Tentativas de bypass
- Autorização: Acesso a recursos protegidos
- Validação: Injeção de dados maliciosos

### Testes Específicos do Sistema de Convites
- **Testes de Modelo**: Validação de campos obrigatórios, relacionamentos, constraints
- **Testes de Serviço**: Criação, aceitação, recusa, alteração de termos, conversão para ordem
- **Testes de Validação**: Saldo insuficiente, convites expirados, tokens inválidos
- **Testes de Fluxo**: Fluxo completo cliente→prestador→ordem, cadastro via convite
- **Testes de Notificação**: Envio automático de emails, notificações do sistema
- **Testes de Segurança**: Acesso via token, validação de permissões, proteção contra spam

## Fluxo de Implementação

### Fase 1: Validação da Base
1. Testar sistema de autenticação completo
2. Validar renderização de todos os templates
3. Verificar navegação entre páginas
4. Confirmar funcionamento do banco de dados

### Fase 2: Sistema de Carteiras
1. Implementar criação automática de carteiras
2. Desenvolver operações básicas (débito/crédito)
3. Criar sistema de escrow
4. Implementar histórico de transações

### Fase 3: Sistema de Ordens
1. Implementar criação de ordens
2. Desenvolver fluxo de aceitação
3. Criar sistema de conclusão
4. Implementar cancelamentos e disputas

### Fase 4: Sistema de Convites
1. Implementar modelo Invite e relacionamentos
2. Desenvolver InviteService com lógica de negócio
3. Criar templates para criação e gerenciamento de convites
4. Implementar validações de saldo para ambas as partes
5. Desenvolver fluxo de conversão convite→ordem

### Fase 5: Dashboards Funcionais
1. Conectar dashboards com dados reais
2. Implementar métricas em tempo real
3. Criar sistema de alertas
4. Desenvolver relatórios

### Fase 6: Testes e Refinamentos
1. Criar suite de testes completa
2. Testar fluxos de ponta a ponta
3. Corrigir bugs encontrados
4. Otimizar performance

## Considerações de Segurança

### Autenticação e Autorização
- Senhas hasheadas com scrypt
- Sessões seguras com tokens
- Decoradores de autorização em todas as rotas protegidas
- Timeout de sessão configurável

### Transações Financeiras
- Validação dupla de saldos
- Transações atômicas
- Logs imutáveis de auditoria
- Verificação de integridade

### Proteção de Dados
- Validação de entrada rigorosa
- Sanitização de dados
- Proteção contra CSRF
- Headers de segurança

## Terminologia e Interface

### Diferenciação por Papel
- **Administradores**: Veem "tokens", "tokenomics", métricas técnicas
- **Clientes/Prestadores**: Veem "saldo", "R$", interface simplificada
- **Sistema**: Mantém lógica interna com tokens (1 token = 1 real)

### Implementação da Terminologia
- Filtro Jinja2 `format_currency` para conversão automática
- Contexto de template diferenciado por papel
- Validação de não vazamento de terminologia técnica

## Métricas e Monitoramento

### Métricas de Negócio
- Total de usuários ativos
- Volume de transações
- Ordens criadas/concluídas
- Taxa de conclusão de ordens

### Métricas Técnicas
- Tempo de resposta das páginas
- Erros por endpoint
- Uso de recursos do servidor
- Integridade do banco de dados

### Alertas
- Saldo baixo para usuários
- Ordens disponíveis para prestadores
- Contestações pendentes para admin
- Erros críticos do sistema