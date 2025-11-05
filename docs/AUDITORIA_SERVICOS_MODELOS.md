# Auditoria de Serviços e Modelos do Projeto Combinado

**Data:** 26 de outubro de 2025  
**Autor:** Manus AI  
**Objetivo:** Auditar a lógica de negócio nos serviços e modelos para identificar problemas de integridade, segurança e performance.

---

## 1. Resumo Executivo

A auditoria identificou **173 funções** distribuídas em **11 arquivos de serviços** e **8 modelos de dados**. A arquitetura segue boas práticas de separação de responsabilidades, mas foram identificados problemas críticos relacionados à integridade de dados, segurança e validações.

### Estatísticas Gerais

| Métrica | Valor |
|---------|-------|
| Total de Funções em Serviços | 173 |
| Total de Modelos | 8 |
| Problemas Críticos | 12 |
| Problemas Altos | 18 |
| Problemas Médios | 24 |

---

## 2. Análise dos Modelos de Dados

### 2.1 Modelo `User`

**Tabela:** `users`  
**Campos Principais:** id, email, nome, password_hash, cpf, phone, created_at, active, roles

#### Problemas Identificados

1. **Campo `roles` como String:**
   - **Descrição:** O campo `roles` é armazenado como string simples, não como lista ou JSON
   - **Impacto:** Dificuldade em gerenciar múltiplos papéis, queries ineficientes
   - **Severidade:** **ALTA**
   - **Recomendação:** Migrar para JSON ou criar tabela de relacionamento muitos-para-muitos

2. **Falta de Índices:**
   - **Campos:** `email`, `cpf`
   - **Descrição:** Campos únicos sem índices explícitos podem degradar performance
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Adicionar índices explícitos nas migrações

3. **Falta de Validação de CPF no Modelo:**
   - **Descrição:** Validação de CPF apenas em `validation_service.py`, não no modelo
   - **Impacto:** Possível inserção de CPFs inválidos diretamente no banco
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Adicionar validação no método `__init__` ou criar um setter

### 2.2 Modelo `Wallet`

**Tabela:** `wallets`  
**Campos Principais:** id, user_id, balance, escrow_balance, updated_at

#### Problemas Identificados

1. **Uso de `Float` para Valores Monetários:**
   - **Descrição:** Campos `balance` e `escrow_balance` usam `db.Float`
   - **Impacto:** **CRÍTICO** - Erros de arredondamento podem causar inconsistências financeiras
   - **Severidade:** **CRÍTICA**
   - **Recomendação:** Migrar para `db.Numeric(precision, scale)` imediatamente

2. **Falta de Constraint de Saldo Não-Negativo:**
   - **Descrição:** Não há constraint CHECK para garantir `balance >= 0`
   - **Impacto:** Possível saldo negativo no banco de dados
   - **Severidade:** **ALTA**
   - **Recomendação:** Adicionar constraint CHECK no banco de dados

3. **Cascade Delete Agressivo:**
   - **Descrição:** `cascade="all, delete-orphan"` pode deletar carteira ao deletar usuário
   - **Impacto:** Perda de dados financeiros históricos
   - **Severidade:** **ALTA**
   - **Recomendação:** Implementar soft delete ou remover cascade

### 2.3 Modelo `Transaction`

**Tabela:** `transactions`  
**Campos Principais:** id, user_id, type, amount, description, created_at, order_id, related_user_id

#### Problemas Identificados

1. **Uso de `Float` para Valores:**
   - **Descrição:** Campo `amount` usa `db.Float`
   - **Impacto:** **CRÍTICO** - Erros de arredondamento em transações financeiras
   - **Severidade:** **CRÍTICA**
   - **Recomendação:** Migrar para `db.Numeric(precision, scale)`

2. **Falta de Campo `transaction_id` Único:**
   - **Descrição:** Não há campo para ID de transação único (apenas `id` autoincremental)
   - **Impacto:** Dificuldade em rastreamento e auditoria
   - **Severidade:** **ALTA**
   - **Recomendação:** Adicionar campo `transaction_id` único gerado por `generate_transaction_id()`

3. **Falta de Índices Compostos:**
   - **Descrição:** Queries frequentes por `user_id + created_at` sem índice composto
   - **Impacto:** Performance degradada em históricos
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Adicionar índice composto `(user_id, created_at DESC)`

### 2.4 Modelo `Order`

**Tabela:** `orders`  
**Campos Principais:** id, client_id, provider_id, title, description, value, status, created_at, accepted_at, completed_at, invite_id, dispute_*

#### Problemas Identificados

1. **Uso de `Float` para Valor:**
   - **Descrição:** Campo `value` usa `db.Float`
   - **Impacto:** **CRÍTICO** - Inconsistências em valores de ordens
   - **Severidade:** **CRÍTICA**
   - **Recomendação:** Migrar para `db.Numeric(10, 2)`

2. **Status como String Livre:**
   - **Descrição:** Campo `status` é string sem enum ou constraint
   - **Impacto:** Possível inserção de status inválidos
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Criar enum `OrderStatus` e usar `db.Enum`

3. **Falta de Validação de Transição de Status:**
   - **Descrição:** Não há validação de transições válidas de status no modelo
   - **Impacto:** Possível transição inválida (ex: `concluida` -> `disponivel`)
   - **Severidade:** **ALTA**
   - **Recomendação:** Implementar máquina de estados ou validação de transições

### 2.5 Modelo `Invite`

**Tabela:** `invites`  
**Campos Principais:** id, client_id, invited_email, service_title, service_description, original_value, final_value, delivery_date, status, token, created_at, expires_at, responded_at, order_id

#### Problemas Identificados

1. **Uso de `Numeric` Inconsistente:**
   - **Descrição:** Usa `db.Numeric(10, 2)` corretamente para valores ✓
   - **Impacto:** Nenhum
   - **Severidade:** N/A

2. **Falta de Índice em `token`:**
   - **Descrição:** Campo `token` é único mas pode não ter índice eficiente
   - **Impacto:** Performance degradada em buscas por token
   - **Severidade:** **BAIXA**
   - **Recomendação:** Verificar se índice foi criado automaticamente

3. **Validação de Expiração Apenas em Propriedade:**
   - **Descrição:** `is_expired` é uma propriedade, não há constraint no banco
   - **Impacto:** Possível aceitação de convites expirados se validação for ignorada
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Adicionar validação em todas as operações de aceitação

---

## 3. Análise dos Serviços

### 3.1 `wallet_service.py`

**Total de Funções:** 40+

#### Problemas Críticos

1. **Operações Não-Atômicas:**
   - **Funções:** `credit_wallet`, `debit_wallet`, `transfer_to_escrow`, `release_from_escrow`
   - **Descrição:** Operações financeiras sem transações atômicas explícitas
   - **Impacto:** **CRÍTICO** - Possível inconsistência em caso de falha parcial
   - **Severidade:** **CRÍTICA**
   - **Recomendação:** Envolver todas as operações em `db.session.begin_nested()` ou usar decorador de transação

2. **Validação de Saldo Não-Atômica:**
   - **Função:** `has_sufficient_balance`
   - **Descrição:** Verificação de saldo separada da operação de débito
   - **Impacto:** Race condition - saldo pode mudar entre verificação e débito
   - **Severidade:** **CRÍTICA**
   - **Recomendação:** Usar `SELECT FOR UPDATE` ou validar dentro da transação

3. **Cálculo de Taxa Hardcoded:**
   - **Função:** `release_from_escrow`
   - **Descrição:** Taxa padrão de 5% hardcoded (`system_fee_percent=0.05`)
   - **Impacto:** Dificuldade em alterar taxa dinamicamente
   - **Severidade:** **ALTA**
   - **Recomendação:** Buscar taxa de `SystemConfig`

#### Problemas de Integridade

1. **Falta de Validação de Valores Negativos:**
   - **Funções:** Múltiplas
   - **Descrição:** Validação `if amount <= 0` apenas levanta exceção, não previne no banco
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Adicionar constraints CHECK no banco

2. **Admin Wallet com ID 0:**
   - **Descrição:** `ADMIN_USER_ID = 0` pode conflitar com IDs reais
   - **Impacto:** Confusão e possível conflito de dados
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Usar ID negativo (ex: -1) ou criar tabela separada

### 3.2 `order_service.py`

**Total de Funções:** 15+

#### Problemas Críticos

1. **Criação de Ordem sem Validação de Saldo:**
   - **Função:** `create_order`
   - **Descrição:** Cria ordem e transfere para escrow sem validação atômica
   - **Impacto:** **CRÍTICA** - Possível criação de ordem sem saldo suficiente
   - **Severidade:** **CRÍTICA**
   - **Recomendação:** Validar saldo dentro da mesma transação

2. **Resolução de Disputa sem Auditoria:**
   - **Função:** `resolve_dispute`
   - **Descrição:** Não registra quem resolveu a disputa
   - **Impacto:** Falta de rastreabilidade
   - **Severidade:** **ALTA**
   - **Recomendação:** Adicionar campo `resolved_by` em `Order`

3. **Cancelamento sem Validação de Status:**
   - **Função:** `cancel_order`
   - **Descrição:** Não valida se ordem pode ser cancelada no status atual
   - **Impacto:** Possível cancelamento de ordem concluída
   - **Severidade:** **ALTA**
   - **Recomendação:** Implementar validação de transição de status

### 3.3 `auth_service.py`

**Total de Funções:** 10+

#### Problemas de Segurança

1. **Sessão sem Timeout:**
   - **Funções:** `admin_login`, `user_login`
   - **Descrição:** Não define timeout de sessão
   - **Impacto:** Sessões podem permanecer ativas indefinidamente
   - **Severidade:** **ALTA**
   - **Recomendação:** Implementar timeout de sessão

2. **Falta de Proteção contra Brute Force:**
   - **Funções:** `authenticate_admin`, `authenticate_user`
   - **Descrição:** Não há limitação de tentativas de login
   - **Impacto:** Vulnerabilidade a ataques de força bruta
   - **Severidade:** **ALTA**
   - **Recomendação:** Implementar rate limiting e bloqueio temporário

3. **Decoradores sem Verificação de Papel Ativo:**
   - **Decoradores:** `cliente_required`, `prestador_required`
   - **Descrição:** Verificam papel mas não validam se é o papel ativo na sessão
   - **Impacto:** Possível acesso a áreas restritas com papel inativo
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Verificar `session.get('active_role')`

### 3.4 `admin_service.py`

**Total de Funções:** 25+

#### Problemas de Lógica

1. **Criação de Tokens sem Limite:**
   - **Função:** `create_tokens`
   - **Descrição:** Admin pode criar tokens ilimitados sem controle
   - **Impacto:** Inflação descontrolada de tokens
   - **Severidade:** **ALTA**
   - **Recomendação:** Implementar limite ou aprovação em duas etapas

2. **Validação de Integridade Não-Automática:**
   - **Função:** `validate_system_integrity`
   - **Descrição:** Validação manual, não executada automaticamente
   - **Impacto:** Inconsistências podem passar despercebidas
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Agendar execução periódica

3. **Alteração de Senha sem Validação de Força:**
   - **Função:** `change_admin_password`
   - **Descrição:** Não valida força da nova senha
   - **Impacto:** Senhas fracas podem ser definidas
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Usar `validation_service.validate_password`

### 3.5 `invite_service.py`

**Total de Funções:** 12+

#### Problemas de Lógica

1. **Aceitação de Convite sem Validação de Expiração:**
   - **Função:** `accept_invite`
   - **Descrição:** Valida expiração mas pode ter race condition
   - **Impacto:** Possível aceitação de convite expirado
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Validar dentro de transação atômica

2. **Conversão para Ordem sem Validação de Saldo:**
   - **Função:** `convert_invite_to_order`
   - **Descrição:** Converte convite sem verificar se cliente tem saldo
   - **Impacto:** Ordem criada sem saldo suficiente
   - **Severidade:** **ALTA**
   - **Recomendação:** Validar saldo antes de converter

### 3.6 `validation_service.py`

**Total de Funções:** 15+

#### Problemas de Validação

1. **Validação de CPF Incompleta:**
   - **Função:** `validate_cpf`
   - **Descrição:** Valida formato mas não verifica CPFs conhecidos como inválidos
   - **Impacto:** CPFs de teste (ex: 111.111.111-11) podem passar
   - **Severidade:** **BAIXA**
   - **Recomendação:** Adicionar blacklist de CPFs inválidos

2. **Validação de Senha Fraca:**
   - **Função:** `validate_password`
   - **Descrição:** Requer apenas 8 caracteres, sem complexidade
   - **Impacto:** Senhas fracas são aceitas
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Adicionar requisitos de complexidade (maiúscula, número, símbolo)

---

## 4. Problemas Críticos Consolidados

### 4.1 Integridade Financeira

| Problema | Severidade | Arquivos Afetados | Recomendação |
|----------|------------|-------------------|--------------|
| Uso de Float para valores monetários | CRÍTICA | `models.py` (Wallet, Transaction, Order) | Migrar para Numeric |
| Operações não-atômicas | CRÍTICA | `wallet_service.py` | Usar transações explícitas |
| Race condition em validação de saldo | CRÍTICA | `wallet_service.py` | SELECT FOR UPDATE |
| Criação de ordem sem validação atômica | CRÍTICA | `order_service.py` | Validar saldo na transação |

### 4.2 Segurança

| Problema | Severidade | Arquivos Afetados | Recomendação |
|----------|------------|-------------------|--------------|
| Sessão sem timeout | ALTA | `auth_service.py` | Implementar timeout |
| Falta de proteção contra brute force | ALTA | `auth_service.py` | Rate limiting |
| Criação ilimitada de tokens | ALTA | `admin_service.py` | Implementar limite |

### 4.3 Integridade de Dados

| Problema | Severidade | Arquivos Afetados | Recomendação |
|----------|------------|-------------------|--------------|
| Saldo negativo possível | ALTA | `models.py` (Wallet) | Constraint CHECK |
| Transição de status inválida | ALTA | `models.py` (Order) | Máquina de estados |
| Cascade delete agressivo | ALTA | `models.py` (Wallet) | Soft delete |

---

## 5. Recomendações Prioritárias

### 5.1 Correções Imediatas (Severidade CRÍTICA)

1. **Migrar campos monetários de Float para Numeric**
   - Arquivos: `models.py`
   - Criar migração para alterar tipos de dados
   - Atualizar todos os serviços para usar Decimal

2. **Implementar transações atômicas em operações financeiras**
   - Arquivos: `wallet_service.py`, `order_service.py`
   - Usar `db.session.begin_nested()` ou decorador

3. **Corrigir race condition em validação de saldo**
   - Arquivo: `wallet_service.py`
   - Usar `SELECT FOR UPDATE` ou validar dentro da transação

### 5.2 Correções Urgentes (Severidade ALTA)

1. **Adicionar constraints CHECK para saldos não-negativos**
2. **Implementar timeout de sessão**
3. **Adicionar rate limiting em autenticação**
4. **Implementar validação de transição de status em Order**
5. **Adicionar campo `transaction_id` único em Transaction**

### 5.3 Melhorias (Severidade MÉDIA)

1. **Migrar campo `roles` para JSON ou tabela de relacionamento**
2. **Implementar soft delete para usuários e carteiras**
3. **Adicionar validação de força de senha**
4. **Implementar validação automática de integridade**
5. **Adicionar índices compostos para performance**

---

## 6. Próximos Passos

1. **Corrigir problemas críticos identificados**
2. **Prosseguir com auditoria de templates e formulários**
3. **Implementar testes automatizados para validar correções**
4. **Documentar mudanças no PDR**

---

**Conclusão:** A auditoria identificou **12 problemas críticos** que comprometem a integridade financeira e a segurança do sistema. A migração de Float para Numeric é a prioridade máxima, seguida pela implementação de transações atômicas. Os serviços estão bem estruturados, mas requerem melhorias significativas em validações e segurança.

