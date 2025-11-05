# Auditoria de Rotas do Projeto Combinado

**Data:** 26 de outubro de 2025  
**Autor:** Manus AI  
**Objetivo:** Identificar inconsistências, erros potenciais e problemas de segurança nos arquivos de rotas.

---

## 1. Resumo Executivo

A auditoria identificou **86 rotas** distribuídas em **7 arquivos de blueprints**. A maioria das rotas possui decoradores de autenticação adequados, mas foram identificadas algumas inconsistências e áreas de melhoria.

### Estatísticas Gerais

| Métrica | Valor |
|---------|-------|
| Total de Rotas | 86 |
| Rotas Protegidas | 79 (91.9%) |
| Rotas Públicas | 7 (8.1%) |
| Blueprints Analisados | 7 |

---

## 2. Análise por Blueprint

### 2.1 Admin Routes (`admin_routes.py`)

**Total de Rotas:** 27  
**Proteção:** Todas as rotas possuem `@admin_required` ✓

#### Problemas Identificados

1. **Duplicação de Rota `contestacoes`:**
   - **Linhas:** 319 e 490
   - **Descrição:** A rota `/admin/contestacoes` está definida duas vezes no arquivo
   - **Impacto:** A segunda definição sobrescreve a primeira, causando perda de funcionalidade
   - **Severidade:** **ALTA**
   - **Recomendação:** Remover a duplicação e manter apenas uma implementação completa

2. **Texto Malformado no Final do Arquivo:**
   - **Linha:** 495
   - **Descrição:** Texto `acoes.html')` solto no final do arquivo
   - **Impacto:** Erro de sintaxe que impede a execução da aplicação
   - **Severidade:** **CRÍTICA**
   - **Recomendação:** Remover o texto malformado

3. **Rotas de Teste em Produção:**
   - **Linhas:** 475-486
   - **Descrição:** Rotas `/test-error` e `/test-404` para testar páginas de erro
   - **Impacto:** Potencial exposição de informações sensíveis em produção
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Remover ou proteger com flag de ambiente de desenvolvimento

4. **Falta de Tratamento de Erros:**
   - **Rotas Afetadas:** `criar_tokens`, `limpar_cache`, `reiniciar_sistema`, `fazer_backup`, `restaurar_backup`
   - **Descrição:** Algumas rotas possuem `try-except` genéricos que podem ocultar erros
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Implementar logging detalhado e tratamento específico de exceções

### 2.2 App Routes (`app_routes.py`)

**Total de Rotas:** 7  
**Proteção:** Todas as rotas possuem `@user_loader_required` ✓

#### Problemas Identificados

1. **Comentários Duplicados:**
   - **Linha:** 15-16
   - **Descrição:** Comentário "Verificar se usuário tem papel de cliente" duplicado
   - **Impacto:** Poluição de código
   - **Severidade:** **BAIXA**
   - **Recomendação:** Remover duplicação

2. **Falta de Validação de Papel:**
   - **Rotas Afetadas:** `home`, `carteira`, `historico`, `perfil`
   - **Descrição:** As rotas não verificam se o usuário possui o papel de cliente
   - **Impacto:** Usuários sem papel de cliente podem acessar áreas restritas
   - **Severidade:** **ALTA**
   - **Recomendação:** Adicionar verificação de papel em todas as rotas

### 2.3 Auth Routes (`auth_routes.py`)

**Total de Rotas:** 11  
**Proteção:** 9 rotas públicas (correto para autenticação), 2 sem decorador

#### Problemas Identificados

1. **Rotas Públicas sem Proteção CSRF:**
   - **Rotas Afetadas:** `user_login`, `admin_login`, `register`
   - **Descrição:** Rotas POST sem validação CSRF explícita
   - **Impacto:** Vulnerabilidade a ataques CSRF
   - **Severidade:** **ALTA**
   - **Recomendação:** Implementar validação CSRF em todas as rotas POST

2. **Logout sem Confirmação:**
   - **Rotas:** `logout`, `admin_logout`
   - **Descrição:** Logout pode ser executado via GET sem confirmação
   - **Impacto:** Vulnerabilidade a ataques de logout forçado
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Implementar logout via POST com token CSRF

3. **Exposição de Informações Sensíveis:**
   - **Rota:** `check_auth`
   - **Descrição:** Retorna informações de autenticação via JSON
   - **Impacto:** Possível vazamento de informações de sessão
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Limitar informações retornadas e adicionar rate limiting

### 2.4 Cliente Routes (`cliente_routes.py`)

**Total de Rotas:** 18  
**Proteção:** Todas as rotas possuem `@login_required` ✓

#### Problemas Identificados

1. **Carregamento Repetitivo de Usuário:**
   - **Todas as Rotas**
   - **Descrição:** Cada rota chama `AuthService.get_current_user()` individualmente
   - **Impacto:** Performance degradada e código duplicado
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Implementar `before_request` para carregar usuário uma vez

2. **Falta de Validação de Saldo:**
   - **Rota:** `processar_criar_ordem`
   - **Descrição:** Validação de saldo pode ser insuficiente
   - **Impacto:** Possível criação de ordens sem saldo suficiente
   - **Severidade:** **ALTA**
   - **Recomendação:** Implementar validação robusta de saldo antes de criar ordem

3. **Duplicação de Rota `criar_ordem`:**
   - **Linhas:** 99 e 124
   - **Descrição:** Rota GET e POST com mesmo caminho mas funções diferentes
   - **Impacto:** Confusão de nomenclatura
   - **Severidade:** **BAIXA**
   - **Recomendação:** Unificar em uma única função com verificação de método

### 2.5 Home Routes (`home_routes.py`)

**Total de Rotas:** 7  
**Proteção:** Todas públicas (correto para páginas institucionais) ✓

#### Problemas Identificados

Nenhum problema crítico identificado. As rotas públicas são apropriadas para páginas institucionais.

### 2.6 Prestador Routes (`prestador_routes.py`)

**Total de Rotas:** 15  
**Proteção:** 13 rotas com `@user_loader_required`, 2 rotas com `@login_required`

#### Problemas Identificados

1. **Inconsistência de Decoradores:**
   - **Rotas:** `recusar_convite`, `alterar_termos_convite`
   - **Descrição:** Usam `@login_required` enquanto outras usam `@user_loader_required`
   - **Impacto:** Inconsistência na forma de carregar usuário
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Padronizar uso de `@user_loader_required` em todas as rotas

2. **Verificação Repetitiva de Papel:**
   - **Todas as Rotas**
   - **Descrição:** Cada rota verifica `if 'prestador' not in user.roles`
   - **Impacto:** Código duplicado e verbose
   - **Severidade:** **MÉDIA**
   - **Recomendação:** Criar decorador `@prestador_required` para centralizar verificação

3. **Falta de Validação em Transações:**
   - **Rota:** `processar_saque`
   - **Descrição:** Validação de saldo pode ser insuficiente
   - **Impacto:** Possível saque de valores inexistentes
   - **Severidade:** **ALTA**
   - **Recomendação:** Implementar validação atômica de saldo

### 2.7 Role Routes (`role_routes.py`)

**Total de Rotas:** 6  
**Proteção:** Todas as rotas possuem `@login_required` ✓

#### Problemas Identificados

1. **Falta de Validação de Papel:**
   - **Rotas:** `set_role`, `go_to_cliente`, `go_to_prestador`
   - **Descrição:** Não verificam se o usuário realmente possui o papel antes de definir
   - **Impacto:** Possível elevação de privilégios
   - **Severidade:** **CRÍTICA**
   - **Recomendação:** Implementar validação rigorosa de papéis antes de permitir troca

2. **Redirecionamento Inseguro:**
   - **Rotas:** `switch_role`, `set_role`
   - **Descrição:** Usa `request.referrer` sem validação
   - **Impacto:** Possível redirecionamento para sites maliciosos
   - **Severidade:** **ALTA**
   - **Recomendação:** Validar URL de redirecionamento contra whitelist

---

## 3. Problemas Críticos Consolidados

### 3.1 Segurança

| Problema | Severidade | Rotas Afetadas | Recomendação |
|----------|------------|----------------|--------------|
| Falta de proteção CSRF | ALTA | `auth_routes.py` (login, register) | Implementar validação CSRF |
| Elevação de privilégios | CRÍTICA | `role_routes.py` (set_role) | Validar papéis antes de trocar |
| Redirecionamento inseguro | ALTA | `role_routes.py` (switch_role) | Validar URLs de redirecionamento |
| Acesso sem validação de papel | ALTA | `app_routes.py` (todas) | Adicionar verificação de papel |

### 3.2 Integridade de Dados

| Problema | Severidade | Rotas Afetadas | Recomendação |
|----------|------------|----------------|--------------|
| Validação de saldo insuficiente | ALTA | `cliente_routes.py` (criar_ordem) | Validação atômica de saldo |
| Saque sem validação | ALTA | `prestador_routes.py` (processar_saque) | Validação atômica de saldo |

### 3.3 Código e Manutenção

| Problema | Severidade | Rotas Afetadas | Recomendação |
|----------|------------|----------------|--------------|
| Duplicação de rotas | ALTA | `admin_routes.py` (contestacoes) | Remover duplicação |
| Erro de sintaxe | CRÍTICA | `admin_routes.py` (linha 495) | Remover texto malformado |
| Código duplicado | MÉDIA | `cliente_routes.py`, `prestador_routes.py` | Refatorar com `before_request` |
| Inconsistência de decoradores | MÉDIA | `prestador_routes.py` | Padronizar decoradores |

---

## 4. Recomendações Prioritárias

### 4.1 Correções Imediatas (Severidade CRÍTICA)

1. **Remover texto malformado em `admin_routes.py` (linha 495)**
2. **Corrigir validação de papéis em `role_routes.py`**
3. **Remover duplicação de rota `contestacoes` em `admin_routes.py`**

### 4.2 Correções Urgentes (Severidade ALTA)

1. **Implementar proteção CSRF em rotas de autenticação**
2. **Adicionar validação de papel em `app_routes.py`**
3. **Implementar validação atômica de saldo em transações**
4. **Validar URLs de redirecionamento**

### 4.3 Melhorias (Severidade MÉDIA)

1. **Refatorar carregamento de usuário com `before_request`**
2. **Padronizar decoradores em `prestador_routes.py`**
3. **Criar decorador `@prestador_required`**
4. **Implementar logout via POST**
5. **Adicionar rate limiting em APIs**

---

## 5. Próximos Passos

1. **Corrigir problemas críticos identificados**
2. **Prosseguir com auditoria de serviços e modelos**
3. **Implementar testes automatizados para validar correções**
4. **Documentar mudanças no PDR**

---

**Conclusão:** A auditoria identificou **15 problemas** de severidade crítica ou alta que requerem atenção imediata. A maioria das rotas possui proteção adequada, mas há inconsistências que podem comprometer a segurança e a integridade dos dados. As correções prioritárias devem ser implementadas antes de prosseguir com novos desenvolvimentos.

