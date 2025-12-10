# Documento de Design - Correções Críticas do Sistema

## Visão Geral

Este documento detalha o design das correções críticas necessárias para resolver problemas de integridade financeira, segurança e qualidade no sistema combinado. As correções abordam desde a migração de tipos de dados monetários até a implementação de controles de segurança robustos.

## Arquitetura

### Arquitetura Atual Identificada

O sistema atual possui:
- **Modelos de Dados**: User, AdminUser, Wallet, Transaction, Order, TokenRequest
- **Serviços**: WalletService, ValidationService, AdminService, etc.
- **Banco de Dados**: SQLAlchemy com SQLite/PostgreSQL
- **Framework**: Flask com blueprints modulares
- **Autenticação**: Sessões Flask com diferentes tipos de usuário

### Problemas Críticos Identificados

1. **Tipos Float**: Modelos Wallet, Transaction, Order, TokenRequest usam Float
2. **Falta de Atomicidade**: Operações financeiras não são atômicas
3. **Race Conditions**: Validação de saldo separada do débito
4. **Ausência de Constraints**: Banco permite saldo negativo
5. **Segurança**: CSRF parcial, sessões sem timeout, etc.

## Componentes e Interfaces

### 1. Sistema de Migração de Dados

#### 1.1 Migração de Tipos Monetários

**Componente**: `MonetaryMigrationService`

```python
class MonetaryMigrationService:
    @staticmethod
    def migrate_float_to_numeric():
        """Migra todos os campos Float para Numeric(18,2)"""
        
    @staticmethod
    def validate_migration_integrity():
        """Valida integridade após migração"""
```

**Campos Afetados**:
- `Wallet.balance`: Float → Numeric(18,2)
- `Wallet.escrow_balance`: Float → Numeric(18,2)  
- `Transaction.amount`: Float → Numeric(18,2)
- `Order.value`: Float → Numeric(18,2)
- `TokenRequest.amount`: Float → Numeric(18,2)
- `Invite.original_value`: Já é Numeric(10,2) ✓
- `Invite.final_value`: Já é Numeric(10,2) ✓

#### 1.2 Script de Migração

```sql
-- Migração para PostgreSQL
ALTER TABLE wallets 
  ALTER COLUMN balance TYPE NUMERIC(18,2),
  ALTER COLUMN escrow_balance TYPE NUMERIC(18,2);

ALTER TABLE transactions 
  ALTER COLUMN amount TYPE NUMERIC(18,2);

ALTER TABLE orders 
  ALTER COLUMN value TYPE NUMERIC(18,2);

ALTER TABLE token_requests 
  ALTER COLUMN amount TYPE NUMERIC(18,2);
```

### 2. Sistema de Transações Atômicas

#### 2.1 Contexto de Transação

**Componente**: `AtomicTransactionManager`

```python
class AtomicTransactionManager:
    @contextmanager
    def atomic_financial_operation():
        """Context manager para operações financeiras atômicas"""
        
    @staticmethod
    def execute_with_retry(operation, max_retries=3):
        """Executa operação com retry em caso de deadlock"""
```

#### 2.2 Refatoração do WalletService

**Métodos Críticos a Refatorar**:
- `credit_wallet()`: Adicionar transação atômica
- `debit_wallet()`: Validar saldo dentro da transação
- `transfer_to_escrow()`: Operação atômica completa
- `release_from_escrow()`: Múltiplas operações em uma transação
- `transfer_tokens_between_users()`: Débito e crédito atômicos

### 3. Sistema de Constraints de Banco

#### 3.1 Constraints de Saldo

```sql
-- Constraint para prevenir saldo negativo
ALTER TABLE wallets 
  ADD CONSTRAINT check_balance_non_negative 
  CHECK (balance >= 0);

ALTER TABLE wallets 
  ADD CONSTRAINT check_escrow_balance_non_negative 
  CHECK (escrow_balance >= 0);

-- Constraint para valores de transação válidos
ALTER TABLE transactions 
  ADD CONSTRAINT check_transaction_amount_not_zero 
  CHECK (amount != 0);

-- Constraint para valores de ordem positivos
ALTER TABLE orders 
  ADD CONSTRAINT check_order_value_positive 
  CHECK (value > 0);
```

#### 3.2 Índices para Performance

```sql
-- Índices para operações financeiras frequentes
CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_transactions_user_id_created ON transactions(user_id, created_at DESC);
CREATE INDEX idx_transactions_order_id ON transactions(order_id);
CREATE INDEX idx_orders_status_created ON orders(status, created_at DESC);
```

### 4. Sistema de Identificação Única de Transações

#### 4.1 Gerador de Transaction ID

**Componente**: `TransactionIdGenerator`

```python
class TransactionIdGenerator:
    @staticmethod
    def generate_unique_id():
        """Gera ID único no formato TXN-YYYYMMDD-HHMMSS-UUID8"""
        
    @staticmethod
    def validate_uniqueness(transaction_id):
        """Valida se ID é único no sistema"""
```

#### 4.2 Modificação do Modelo Transaction

```python
class Transaction(db.Model):
    # Adicionar campo transaction_id único
    transaction_id = db.Column(db.String(50), unique=True, nullable=False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.transaction_id:
            self.transaction_id = TransactionIdGenerator.generate_unique_id()
```

### 5. Sistema de Segurança Aprimorado

#### 5.1 Proteção CSRF Completa

**Componente**: `CSRFProtectionManager`

```python
class CSRFProtectionManager:
    @staticmethod
    def enable_csrf_for_all_forms():
        """Habilita CSRF para todos os formulários"""
        
    @staticmethod
    def validate_csrf_token(token):
        """Valida token CSRF"""
```

**Templates a Proteger**:
- Todos os formulários em `/templates/admin/`
- Todos os formulários em `/templates/cliente/`
- Todos os formulários em `/templates/prestador/`
- Formulários de autenticação

#### 5.2 Sistema de Timeout de Sessão

**Componente**: `SessionTimeoutManager`

```python
class SessionTimeoutManager:
    TIMEOUT_MINUTES = 30
    WARNING_MINUTES = 5
    
    @staticmethod
    def check_session_timeout():
        """Verifica se sessão expirou"""
        
    @staticmethod
    def extend_session():
        """Estende sessão em atividade"""
        
    @staticmethod
    def cleanup_expired_sessions():
        """Remove sessões expiradas"""
```

#### 5.3 Validação de Transições de Status

**Componente**: `OrderStatusValidator`

```python
class OrderStatusValidator:
    VALID_TRANSITIONS = {
        'disponivel': ['aceita', 'cancelada'],
        'aceita': ['em_andamento', 'cancelada'],
        'em_andamento': ['concluida', 'disputada', 'cancelada'],
        'concluida': ['disputada'],
        'disputada': ['concluida', 'cancelada'],
        'cancelada': []  # Estado final
    }
    
    @staticmethod
    def validate_transition(current_status, new_status):
        """Valida se transição de status é permitida"""
```

### 6. Sistema de Soft Delete

#### 6.1 Modificação dos Modelos

```python
class User(db.Model):
    # Adicionar campos para soft delete
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None

class AdminUser(db.Model):
    # Adicionar campos para soft delete
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
```

#### 6.2 Serviço de Soft Delete

**Componente**: `SoftDeleteService`

```python
class SoftDeleteService:
    @staticmethod
    def soft_delete_user(user_id, deleted_by_admin_id, reason):
        """Marca usuário como deletado sem remover dados"""
        
    @staticmethod
    def restore_user(user_id, restored_by_admin_id):
        """Restaura usuário deletado"""
        
    @staticmethod
    def get_active_users():
        """Retorna apenas usuários não deletados"""
```

### 7. Sistema de Controle de Criação de Tokens

#### 7.1 Modelo de Limites

```python
class TokenCreationLimit(db.Model):
    __tablename__ = 'token_creation_limits'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)
    daily_limit = db.Column(db.Numeric(18,2), nullable=False, default=10000.00)
    monthly_limit = db.Column(db.Numeric(18,2), nullable=False, default=100000.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 7.2 Serviço de Controle

**Componente**: `TokenCreationControlService`

```python
class TokenCreationControlService:
    @staticmethod
    def check_daily_limit(admin_id, amount):
        """Verifica se criação está dentro do limite diário"""
        
    @staticmethod
    def check_monthly_limit(admin_id, amount):
        """Verifica se criação está dentro do limite mensal"""
        
    @staticmethod
    def log_token_creation(admin_id, amount, reason):
        """Registra criação de tokens para auditoria"""
```

## Modelos de Dados

### Modificações nos Modelos Existentes

#### Wallet
```python
class Wallet(db.Model):
    balance = db.Column(db.Numeric(18,2), nullable=False, default=0.00)
    escrow_balance = db.Column(db.Numeric(18,2), nullable=False, default=0.00)
    
    __table_args__ = (
        db.CheckConstraint('balance >= 0', name='check_balance_non_negative'),
        db.CheckConstraint('escrow_balance >= 0', name='check_escrow_balance_non_negative'),
    )
```

#### Transaction
```python
class Transaction(db.Model):
    transaction_id = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Numeric(18,2), nullable=False)
    
    __table_args__ = (
        db.CheckConstraint('amount != 0', name='check_amount_not_zero'),
    )
```

#### Order
```python
class Order(db.Model):
    value = db.Column(db.Numeric(18,2), nullable=False)
    
    __table_args__ = (
        db.CheckConstraint('value > 0', name='check_value_positive'),
    )
```

### Novos Modelos

#### SessionTimeout
```python
class SessionTimeout(db.Model):
    __tablename__ = 'session_timeouts'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=True)
    admin_id = db.Column(db.Integer, nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## Tratamento de Erros

### Hierarquia de Exceções

```python
class SystemCriticalError(Exception):
    """Erro crítico do sistema"""
    pass

class FinancialIntegrityError(SystemCriticalError):
    """Erro de integridade financeira"""
    pass

class InsufficientBalanceError(FinancialIntegrityError):
    """Saldo insuficiente"""
    pass

class NegativeBalanceError(FinancialIntegrityError):
    """Tentativa de saldo negativo"""
    pass

class TransactionIntegrityError(FinancialIntegrityError):
    """Erro de integridade de transação"""
    pass
```

### Tratamento de Race Conditions

```python
class RaceConditionHandler:
    @staticmethod
    def handle_concurrent_balance_update(operation, max_retries=3):
        """Trata condições de corrida em atualizações de saldo"""
        for attempt in range(max_retries):
            try:
                return operation()
            except IntegrityError as e:
                if attempt == max_retries - 1:
                    raise TransactionIntegrityError("Falha após múltiplas tentativas")
                time.sleep(0.1 * (2 ** attempt))  # Backoff exponencial
```

## Estratégia de Testes

### Testes de Integridade Financeira

1. **Teste de Migração de Dados**
   - Verificar preservação de valores durante migração Float→Numeric
   - Validar que nenhum dado é perdido
   - Confirmar precisão decimal

2. **Testes de Atomicidade**
   - Simular falhas durante operações financeiras
   - Verificar rollback completo em caso de erro
   - Testar operações concorrentes

3. **Testes de Constraints**
   - Tentar criar saldo negativo (deve falhar)
   - Verificar rejeição de valores inválidos
   - Testar limites de precisão decimal

4. **Testes de Race Condition**
   - Operações simultâneas na mesma carteira
   - Múltiplos débitos concorrentes
   - Validação de saldo sob carga

### Testes de Segurança

1. **Testes de CSRF**
   - Verificar proteção em todos os formulários
   - Testar ataques CSRF simulados
   - Validar tokens únicos por sessão

2. **Testes de Timeout**
   - Verificar expiração automática
   - Testar limpeza de sessões
   - Validar redirecionamento após timeout

3. **Testes de Validação de Status**
   - Tentar transições inválidas
   - Verificar logs de auditoria
   - Testar estados finais

### Testes de Performance

1. **Testes de Carga Financeira**
   - Múltiplas transações simultâneas
   - Operações de escrow em massa
   - Transferências entre usuários

2. **Testes de Índices**
   - Consultas de histórico de transações
   - Busca por transaction_id
   - Relatórios financeiros

## Plano de Implementação

### Fase 1: Emergencial (Crítico)
1. Migração Float → Numeric(18,2)
2. Implementação de constraints de saldo
3. Testes de integridade de dados

### Fase 2: Crítica (Alta Prioridade)
1. Transações atômicas no WalletService
2. Correção de race conditions
3. Proteção CSRF completa
4. Sistema de timeout de sessão

### Fase 3: Alta (Média Prioridade)
1. Transaction ID único
2. Validação de transições de status
3. Sistema de soft delete
4. Controle de criação de tokens

### Fase 4: Melhorias (Baixa Prioridade)
1. Otimizações de performance
2. Relatórios de auditoria aprimorados
3. Monitoramento proativo
4. Alertas automáticos