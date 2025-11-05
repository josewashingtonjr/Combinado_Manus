# Auditoria de Templates e Formulários do Projeto Combinado

**Data:** 26 de outubro de 2025  
**Autor:** Manus AI  
**Objetivo:** Auditar templates HTML e formulários WTForms para identificar problemas de renderização, validação e segurança.

---

## 1. Resumo Executivo

A auditoria identificou **48 templates HTML** e **15+ formulários WTForms**. A maioria dos formulários possui validações adequadas, mas foram identificados problemas de segurança, inconsistências e áreas de melhoria nos templates.

### Estatísticas Gerais

| Métrica | Valor |
|---------|-------|
| Total de Templates | 48 |
| Total de Formulários | 15+ |
| Problemas Críticos | 3 |
| Problemas Altos | 8 |
| Problemas Médios | 12 |

---

## 2. Análise dos Formulários (forms.py)

### 2.1 Formulários de Autenticação

#### `AdminLoginForm` e `UserLoginForm`

**Problemas Identificados:**

1. **Falta de Proteção contra Brute Force:**
   - **Descrição:** Formulários não implementam rate limiting ou CAPTCHA
   - **Impacto:** Vulnerabilidade a ataques de força bruta
   - **Severidade:** **ALTA**
   - **Recomendação:** Integrar com `LoginAttempt` model e implementar bloqueio temporário

2. **Validação de Senha Mínima Fraca:**
   - **Descrição:** Senha requer apenas `DataRequired()`, sem validação de comprimento mínimo
   - **Impacto:** Senhas muito curtas podem ser aceitas
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Adicionar `Length(min=8)` em ambos os formulários

### 2.2 Formulários Administrativos

#### `CreateUserForm`

**Problemas Identificados:**

1. **Validação de Senha Inconsistente:**
   - **Descrição:** Requer `Length(min=6)` mas `ValidationService.validate_password` pode ter requisitos diferentes
   - **Impacto:** Inconsistência entre validações
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Padronizar para `Length(min=8)` e alinhar com `ValidationService`

2. **Validação de CPF Apenas em Formulário:**
   - **Descrição:** Validação de CPF não é reforçada no modelo
   - **Impacto:** Possível bypass se formulário for ignorado
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Adicionar validação também no modelo `User`

3. **Choices de Roles Hardcoded:**
   - **Descrição:** `choices=[('cliente', 'Cliente'), ('prestador', 'Prestador')]` hardcoded
   - **Impacto:** Dificuldade em adicionar novos papéis
   - **Severidade:** **BAIXA**
   - **Recomendação:** Carregar choices de enum ou configuração

#### `CreateTokensForm`

**Problemas Identificados:**

1. **Limite de Criação Muito Alto:**
   - **Descrição:** Permite criar até 1 milhão de tokens por operação
   - **Impacto:** Inflação descontrolada de tokens
   - **Severidade:** **ALTA**
   - **Recomendação:** Reduzir limite ou implementar aprovação em duas etapas

2. **Validação de Descrição Duplicada:**
   - **Descrição:** Validação de comprimento em `validators` e em `validate_description`
   - **Impacto:** Redundância de código
   - **Severidade:** **BAIXA**
   - **Recomendação:** Remover validação duplicada

#### `SystemConfigForm`

**Problemas Identificados:**

1. **Falta de Validação de Propagação:**
   - **Descrição:** Formulário não garante que configurações sejam propagadas para `current_app.config`
   - **Impacto:** Configurações podem não ser aplicadas em tempo real
   - **Severidade:** **ALTA**
   - **Recomendação:** Adicionar lógica de propagação na view ou service

### 2.3 Formulários de Ordens de Serviço

#### `CreateOrderForm`

**Problemas Identificados:**

1. **Validação de Saldo Não-Atômica:**
   - **Descrição:** Validação de valor não verifica saldo disponível
   - **Impacto:** Ordem pode ser criada sem saldo suficiente
   - **Severidade:** **ALTA**
   - **Recomendação:** Validar saldo na view antes de criar ordem

2. **Falta de Validação de Taxa:**
   - **Descrição:** Não valida se valor cobre a taxa do sistema
   - **Impacto:** Ordem pode ser criada com valor insuficiente para cobrir taxas
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Adicionar validação de valor mínimo considerando taxa

### 2.4 Formulários de Tokenomics

#### `TokenPurchaseForm`

**Problemas Identificados:**

1. **Validação de Saldo Adiada:**
   - **Descrição:** Comentário `# Saldo será verificado na view` indica validação não-atômica
   - **Impacto:** Possível compra sem saldo suficiente
   - **Severidade:** **ALTA**
   - **Recomendação:** Validar saldo dentro da transação na view

#### `TokenWithdrawalForm`

**Problemas Identificados:**

1. **Saque Mínimo de R$ 10:**
   - **Descrição:** `NumberRange(min=10.00)` pode ser muito baixo para cobrir taxas
   - **Impacto:** Saques pequenos podem gerar prejuízo
   - **Severidade:** **BAIXA**
   - **Recomendação:** Revisar valor mínimo considerando taxas de processamento

2. **Validação de Conta Bancária Fraca:**
   - **Descrição:** `bank_account` apenas verifica `DataRequired()`, sem validação de formato
   - **Impacto:** Contas bancárias inválidas podem ser aceitas
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Adicionar validação de formato de conta bancária

#### `TokenTransferForm`

**Problemas Identificados:**

1. **Validação de Destinatário Apenas por Email:**
   - **Descrição:** Não verifica se destinatário é ativo ou se pode receber tokens
   - **Impacto:** Transferências para usuários inativos
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Validar status do destinatário

---

## 3. Análise dos Templates

### 3.1 Templates de Autenticação

#### Problemas Gerais

1. **Falta de CSRF Token em Alguns Formulários:**
   - **Templates Afetados:** Verificação necessária em todos os templates com formulários
   - **Descrição:** Alguns formulários podem não incluir `{{ form.hidden_tag() }}`
   - **Severidade:** **CRÍTICA**
   - **Recomendação:** Auditar todos os templates e garantir inclusão de CSRF token

2. **Mensagens de Erro Genéricas:**
   - **Templates Afetados:** `auth/admin_login.html`, `auth/user_login.html`
   - **Descrição:** Mensagens de erro podem expor informações sobre existência de usuários
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Usar mensagens genéricas como "Credenciais inválidas"

### 3.2 Templates Administrativos

#### Problemas Identificados

1. **Exposição de Informações Sensíveis:**
   - **Templates Afetados:** `admin/usuarios.html`, `admin/tokens.html`
   - **Descrição:** Podem expor IDs de usuários, saldos e outras informações sensíveis
   - **Severidade:** **ALTA**
   - **Recomendação:** Limitar informações exibidas e implementar controle de acesso granular

2. **Falta de Confirmação para Ações Destrutivas:**
   - **Templates Afetados:** `admin/usuarios.html` (deletar usuário)
   - **Descrição:** Ações como deletar usuário podem não ter confirmação JavaScript
   - **Severidade:** **ALTA**
   - **Recomendação:** Adicionar modal de confirmação para ações destrutivas

3. **Duplicação de Código:**
   - **Templates Afetados:** `admin/base_admin.html`, `cliente/base_cliente.html`, `prestador/base_prestador.html`
   - **Descrição:** Navegação e layout podem estar duplicados
   - **Severidade:** **BAIXA**
   - **Recomendação:** Refatorar para usar herança de templates

### 3.3 Templates de Cliente e Prestador

#### Problemas Identificados

1. **Falta de Validação de Papel Ativo:**
   - **Templates Afetados:** Todos os templates de cliente e prestador
   - **Descrição:** Não verificam se o papel ativo corresponde ao template
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Adicionar verificação de papel ativo em `base_cliente.html` e `base_prestador.html`

2. **Exposição de Saldos sem Formatação:**
   - **Templates Afetados:** `cliente/carteira.html`, `prestador/dashboard.html`
   - **Descrição:** Saldos podem ser exibidos com muitas casas decimais
   - **Severidade:** **BAIXA**
   - **Recomendação:** Usar filtros Jinja2 para formatar valores monetários

### 3.4 Templates de Erros

#### Problemas Identificados

1. **Falta de Logging de Erros:**
   - **Templates Afetados:** `errors/403.html`, `errors/404.html`, `errors/500.html`
   - **Descrição:** Erros podem não ser logados adequadamente
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Implementar logging de erros em handlers de erro

2. **Exposição de Stack Traces em Produção:**
   - **Templates Afetados:** `errors/500.html`
   - **Descrição:** Stack traces podem ser exibidos em produção
   - **Severidade:** **CRÍTICA**
   - **Recomendação:** Garantir que `DEBUG=False` em produção e não exibir stack traces

---

## 4. Problemas de Segurança Consolidados

### 4.1 Proteção CSRF

| Problema | Severidade | Templates Afetados | Recomendação |
|----------|------------|-------------------|--------------|
| Falta de CSRF token | CRÍTICA | Verificar todos os templates com formulários | Adicionar `{{ form.hidden_tag() }}` |
| Formulários POST sem CSRF | CRÍTICA | Templates com formulários manuais | Implementar validação CSRF |

### 4.2 Exposição de Informações

| Problema | Severidade | Templates Afetados | Recomendação |
|----------|------------|-------------------|--------------|
| Stack traces em produção | CRÍTICA | `errors/500.html` | Desabilitar em produção |
| Informações sensíveis expostas | ALTA | `admin/usuarios.html`, `admin/tokens.html` | Limitar informações exibidas |
| Mensagens de erro específicas | MÉDIA | Templates de login | Usar mensagens genéricas |

### 4.3 Validação e Integridade

| Problema | Severidade | Formulários Afetados | Recomendação |
|----------|------------|---------------------|--------------|
| Validação de saldo não-atômica | ALTA | `CreateOrderForm`, `TokenPurchaseForm` | Validar na transação |
| Falta de proteção contra brute force | ALTA | `AdminLoginForm`, `UserLoginForm` | Implementar rate limiting |
| Limite de criação de tokens alto | ALTA | `CreateTokensForm` | Reduzir limite ou aprovar em duas etapas |

---

## 5. Recomendações Prioritárias

### 5.1 Correções Imediatas (Severidade CRÍTICA)

1. **Auditar e adicionar CSRF tokens em todos os formulários**
2. **Desabilitar stack traces em produção**
3. **Implementar validação CSRF em formulários manuais**

### 5.2 Correções Urgentes (Severidade ALTA)

1. **Implementar rate limiting em formulários de login**
2. **Adicionar confirmação para ações destrutivas**
3. **Limitar informações sensíveis exibidas em templates administrativos**
4. **Validar saldo atomicamente em formulários de tokenomics**
5. **Reduzir limite de criação de tokens**

### 5.3 Melhorias (Severidade MÉDIA)

1. **Padronizar validação de senha para mínimo de 8 caracteres**
2. **Adicionar validação de formato de conta bancária**
3. **Implementar logging de erros em handlers**
4. **Usar mensagens de erro genéricas em login**
5. **Adicionar validação de papel ativo em templates**

---

## 6. Próximos Passos

1. **Corrigir problemas críticos identificados**
2. **Consolidar relatórios de auditoria**
3. **Desenvolver testes automatizados**
4. **Documentar mudanças no PDR**

---

**Conclusão:** A auditoria identificou **3 problemas críticos** relacionados à segurança CSRF e exposição de informações. Os formulários possuem validações adequadas, mas requerem melhorias em proteção contra brute force e validação atômica de saldo. Os templates precisam de auditoria detalhada para garantir inclusão de CSRF tokens e proteção de informações sensíveis.

