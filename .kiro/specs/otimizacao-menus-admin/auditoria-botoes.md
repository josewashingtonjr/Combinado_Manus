# Auditoria de Botões - Painel Administrativo

## Data da Auditoria
20 de novembro de 2025

## Objetivo
Identificar e documentar todos os botões nos templates do painel administrativo, verificar sua funcionalidade e remover aqueles sem função ou duplicados.

## Metodologia
1. Análise de todos os templates em `templates/admin/`
2. Verificação de rotas correspondentes em `routes/admin_routes.py`
3. Identificação de botões sem rota ou ação JavaScript
4. Documentação de botões duplicados

## Rotas Existentes no Sistema

### Rotas Principais
- `/admin/dashboard` - Dashboard administrativo
- `/admin/alterar-senha` - Alteração de senha
- `/admin/usuarios` - Listagem de usuários
- `/admin/usuarios/criar` - Criar novo usuário
- `/admin/usuarios/<id>/editar` - Editar usuário
- `/admin/usuarios/<id>/deletar` - Deletar usuário (soft delete)
- `/admin/usuarios/<id>/restaurar` - Restaurar usuário deletado
- `/admin/usuarios/deletados` - Listar usuários deletados

### Rotas de Convites
- `/admin/convites` - Listagem de convites (com filtro por status)
- `/admin/convites/<id>` - Ver detalhes do convite

### Rotas de Ordens
- `/admin/ordens` - Listagem de ordens (com filtros)
- `/admin/ordens/<id>` - Ver detalhes da ordem

### Rotas de Contratos
- `/admin/contratos` - Listagem de contratos
- `/admin/contratos/ativos` - Contratos ativos
- `/admin/contratos/finalizados` - Contratos finalizados

### Rotas de Tokens
- `/admin/tokens` - Gestão de tokens
- `/admin/tokens/adicionar` - Adicionar tokens para usuário
- `/admin/tokens/criar` - Criar novos tokens
- `/admin/tokens/solicitacoes` - Solicitações de tokens
- `/admin/tokens/solicitacoes/<id>/processar` - Processar solicitação
- `/admin/tokens/solicitacoes/<id>/comprovante` - Ver comprovante

### Rotas de Configurações
- `/admin/configuracoes` - Página principal de configurações
- `/admin/configuracoes/taxas` - Configurações de taxas (GET e POST)
- `/admin/configuracoes/seguranca` - Configurações de segurança (GET e POST)

### Rotas de Contestações
- `/admin/contestacoes` - Listagem de contestações (com filtro por status)
- `/admin/contestacoes/<id>` - Ver detalhes da contestação
- `/admin/contestacoes/<id>/resolver` - Resolver contestação

### Rotas de Relatórios
- `/admin/relatorios` - Página de relatórios
- `/admin/relatorios/gerar-pdf/<tipo>` - Gerar PDF de relatório

### Rotas de Sistema
- `/admin/logs` - Visualizar logs
- `/admin/sistema/limpar-cache` - Limpar cache
- `/admin/sistema/reiniciar` - Reiniciar sistema
- `/admin/sistema/backup` - Fazer backup
- `/admin/sistema/restaurar` - Restaurar backup
- `/admin/sistema/auditoria` - Auditoria do sistema

## Análise por Template

### 1. dashboard.html
**Botões Encontrados:**
- ✅ "Criar Usuário" → `url_for('admin.criar_usuario')` - FUNCIONAL
- ✅ "Adicionar Tokens" → `url_for('admin.adicionar_tokens')` - FUNCIONAL
- ✅ "Configurações" → `url_for('admin.configuracoes')` - FUNCIONAL
- ✅ "Relatórios" → `url_for('admin.relatorios')` - FUNCIONAL
- ✅ "Solicitações de Tokens" → `url_for('admin.solicitacoes_tokens')` - FUNCIONAL
- ✅ Link "Ver Todas" (contestações) → `url_for('admin.contestacoes')` - FUNCIONAL
- ✅ Link "PROCESSAR AGORA" (solicitações) → `url_for('admin.solicitacoes_tokens')` - FUNCIONAL

**Status:** Todos os botões são funcionais

### 2. usuarios.html
**Botões Encontrados:**
- ✅ "Usuários Deletados" → `url_for('admin.usuarios_deletados')` - FUNCIONAL
- ✅ "Novo Usuário" → `url_for('admin.criar_usuario')` - FUNCIONAL
- ✅ Botão "Editar" → `url_for('admin.editar_usuario')` - FUNCIONAL
- ✅ Botão "Deletar" → Modal + POST para `url_for('admin.deletar_usuario')` - FUNCIONAL
- ✅ Botão fechar alerta → `data-bs-dismiss="alert"` - FUNCIONAL (Bootstrap)

**Observações:**
- Modal de exclusão usa `data-toggle="modal"` (Bootstrap 4) mas deveria usar `data-bs-toggle="modal"` (Bootstrap 5)
- Checkbox de confirmação é obrigatório antes de deletar

**Status:** Todos os botões são funcionais, mas há inconsistência na versão do Bootstrap

### 3. ordens.html
**Botões Encontrados:**
- ✅ "Relatórios" → `url_for('admin.relatorios')` - FUNCIONAL
- ✅ Botão "Filtrar" → Submit do formulário GET - FUNCIONAL
- ✅ "Limpar Filtros" → `url_for('admin.ordens')` - FUNCIONAL
- ✅ Botão "Ver Detalhes" → `url_for('admin.ver_ordem')` - FUNCIONAL
- ✅ Botão "Analisar Contestação" → `url_for('admin.analisar_contestacao')` - FUNCIONAL
- ✅ Botão fechar alerta → `data-bs-dismiss="alert"` - FUNCIONAL

**Observações:**
- Rota `admin.analisar_contestacao` não existe, deveria ser `admin.ver_contestacao`

**Status:** Botão "Analisar Contestação" aponta para rota inexistente

### 4. contestacoes.html
**Botões Encontrados:**
- ✅ Botão "Analisar" → `url_for('admin.ver_contestacao')` - FUNCIONAL
- ✅ Botão fechar alerta → `data-bs-dismiss="alert"` - FUNCIONAL

**Status:** Todos os botões são funcionais

### 5. convites.html
**Botões Encontrados:**
- ✅ Select de filtro → Submit automático via `onchange="this.form.submit()"` - FUNCIONAL
- ✅ "Limpar Filtro" → `url_for('admin.convites')` - FUNCIONAL
- ✅ Botão "Ver Detalhes" → `url_for('admin.ver_convite')` - FUNCIONAL

**Status:** Todos os botões são funcionais

### 6. contratos.html
**Botões Encontrados:**
- ✅ Botão "Filtrar" → Submit do formulário - FUNCIONAL
- ✅ "Limpar" → `url_for('admin.contratos')` - FUNCIONAL
- ✅ Botão "Ver detalhes" → `url_for('admin.ver_contrato')` - FUNCIONAL
- ✅ Botão "Analisar disputa" → `url_for('admin.analisar_contestacao')` - ROTA INEXISTENTE
- ✅ "Ver Todos os Contratos" → `url_for('admin.contratos')` - FUNCIONAL

**Observações:**
- Rota `admin.analisar_contestacao` não existe, deveria ser `admin.ver_contestacao`

**Status:** Botão "Analisar disputa" aponta para rota inexistente

### 7. ver_contrato.html
**Botões Encontrados:**
- ✅ "Analisar Disputa" → `url_for('admin.analisar_contestacao')` - ROTA INEXISTENTE
- ✅ "Voltar à Lista" → `url_for('admin.contratos')` - FUNCIONAL

**Status:** Botão "Analisar Disputa" aponta para rota inexistente

### 8. tokens.html
**Botões Encontrados:**
- ✅ "Criar Tokens" → `url_for('admin.criar_tokens')` - FUNCIONAL
- ✅ "Adicionar para Usuário" → `url_for('admin.adicionar_tokens')` - FUNCIONAL
- ✅ "Solicitações" → `url_for('admin.solicitacoes_tokens')` - FUNCIONAL
- ✅ "Configurações" → `url_for('admin.configuracoes')` - FUNCIONAL
- ✅ "Ver Logs" → `url_for('admin.logs')` - FUNCIONAL
- ✅ "Ver Todos os Alertas" → `url_for('admin.alertas_tokens')` - ROTA INEXISTENTE
- ✅ Botão fechar alerta → `data-bs-dismiss="alert"` - FUNCIONAL

**Observações:**
- Rota `admin.alertas_tokens` não existe no sistema

**Status:** Botão "Ver Todos os Alertas" aponta para rota inexistente

### 9. alertas_sistema.html
**Botões Encontrados:**
- ✅ Botão "Ver detalhes" → `onclick="verDetalhesAlerta()"` + modal - FUNCIONAL (JavaScript)
- ✅ Botão "Resolver" → Submit do formulário POST - FUNCIONAL
- ✅ Botão fechar alerta → `data-bs-dismiss="alert"` - FUNCIONAL

**Status:** Todos os botões são funcionais

## Resumo de Problemas Encontrados

### Rotas Inexistentes Referenciadas
1. **`admin.analisar_contestacao`** - Referenciada em:
   - `templates/admin/ordens.html` (linha 238)
   - `templates/admin/contratos.html` (linha 238)
   - `templates/admin/ver_contrato.html` (linha 100)
   - **Solução:** Substituir por `admin.ver_contestacao`

2. **`admin.alertas_tokens`** - Referenciada em:
   - `templates/admin/tokens.html` (linha 50)
   - **Solução:** Remover botão ou criar rota

### Inconsistências de Bootstrap
- `templates/admin/usuarios.html` usa `data-toggle` (Bootstrap 4) em vez de `data-bs-toggle` (Bootstrap 5)

### Botões Duplicados ou Redundantes
Nenhum botão verdadeiramente duplicado foi encontrado. Todos os botões têm propósitos distintos.

## Ações Recomendadas

### Prioridade Alta
1. ✅ Corrigir referências a `admin.analisar_contestacao` → `admin.ver_contestacao`
2. ✅ Remover ou corrigir botão "Ver Todos os Alertas" em tokens.html

### Prioridade Média
3. ✅ Atualizar `data-toggle` para `data-bs-toggle` em usuarios.html

### Prioridade Baixa
4. Considerar criar rota `admin.alertas_tokens` se funcionalidade for necessária

## Conclusão

A auditoria revelou que a maioria dos botões no painel administrativo são funcionais. Os principais problemas são:
- 3 referências a rota inexistente `admin.analisar_contestacao`
- 1 referência a rota inexistente `admin.alertas_tokens`
- Inconsistência na versão do Bootstrap em um template

Não foram encontrados botões verdadeiramente sem função, apenas referências a rotas que não existem ou foram renomeadas.
