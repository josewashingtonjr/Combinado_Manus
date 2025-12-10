# Guia Rápido de Navegação - Painel Administrativo

## 📋 Índice Rápido

- [Estrutura do Menu](#estrutura-do-menu)
- [Como Usar os Filtros](#como-usar-os-filtros)
- [Atalhos e Dicas](#atalhos-e-dicas)
- [Perguntas Frequentes](#perguntas-frequentes)

---

## 🗂️ Estrutura do Menu

### Menu Lateral

O menu lateral está sempre visível em desktop e pode ser acessado via botão hamburger em mobile.

```
📊 Dashboard
   └─ Visão geral do sistema

⚙️ Configurações
   ├─ 💰 Taxas do Sistema
   ├─ 🛡️ Segurança
   └─ 🔑 Alterar Senha

📊 Relatórios
   ├─ 💵 Financeiro
   ├─ 👥 Usuários
   └─ 📄 Contratos

✉️ Convites
   ├─ 📋 Todos
   ├─ ⏰ Pendentes
   ├─ ✅ Aceitos
   └─ ❌ Recusados

📋 Ordens
   ├─ 📋 Todas
   ├─ ⏰ Aguardando
   ├─ ⏳ Executadas
   ├─ ✅ Concluídas
   └─ ⚠️ Contestadas

⚠️ Contestações
   ├─ 📋 Todas
   ├─ ⏰ Pendentes
   └─ 🔍 Em Análise

👥 Usuários
🪙 Tokens
💰 Financeiro
```

---

## 🔍 Como Usar os Filtros

### Convites

**Para filtrar convites por status:**

1. Clique em **"Convites"** no menu lateral
2. Escolha o filtro desejado:
   - **Todos:** Mostra todos os convites do sistema
   - **Pendentes:** Convites aguardando resposta do prestador
   - **Aceitos:** Convites aceitos e convertidos em ordens
   - **Recusados:** Convites recusados pelos prestadores

**Exemplo de URL:**
```
/admin/convites?status=pendente
```

---

### Ordens

**Para filtrar ordens por status:**

1. Clique em **"Ordens"** no menu lateral
2. Escolha o filtro desejado:
   - **Todas:** Mostra todas as ordens
   - **Aguardando:** Ordens aguardando execução pelo prestador
   - **Executadas:** Serviço executado, aguardando confirmação do cliente
   - **Concluídas:** Ordens finalizadas e pagas
   - **Contestadas:** Ordens em disputa

**Exemplo de URL:**
```
/admin/ordens?status=aguardando_execucao
```

**Status Disponíveis:**
- `aguardando_execucao`
- `servico_executado`
- `concluida`
- `cancelada`
- `contestada`

---

### Contestações

**Para filtrar contestações por status:**

1. Clique em **"Contestações"** no menu lateral
2. Escolha o filtro desejado:
   - **Todas:** Mostra todas as contestações
   - **Pendentes:** Contestações aguardando análise do admin
   - **Em Análise:** Contestações sendo analisadas

**Exemplo de URL:**
```
/admin/contestacoes?status=pendente
```

---

### Relatórios

**Para acessar diferentes tipos de relatórios:**

1. Clique em **"Relatórios"** no menu lateral
2. Escolha a aba desejada:
   - **Financeiro:** Transações, saldos, taxas
   - **Usuários:** Cadastros, atividades, estatísticas
   - **Contratos:** Ordens, convites, performance

**Navegação por Abas:**
- As abas são navegáveis via clique
- A URL é atualizada automaticamente (ex: `/admin/relatorios#financeiro`)
- Você pode compartilhar o link direto para uma aba específica

**Exemplo de URLs:**
```
/admin/relatorios#financeiro
/admin/relatorios#usuarios
/admin/relatorios#contratos
```

---

## ⚡ Atalhos e Dicas

### Navegação Rápida

**Teclado:**
- `Tab` - Navegar entre elementos
- `Enter` - Ativar link/botão
- `Esc` - Fechar modais

**Mouse:**
- Clique nos ícones para expandir/colapsar submenus
- Hover sobre links para ver tooltip (quando disponível)

### Filtros Rápidos

**Convites Pendentes:**
```
/admin/convites?status=pendente
```

**Ordens Aguardando:**
```
/admin/ordens?status=aguardando_execucao
```

**Contestações Pendentes:**
```
/admin/contestacoes?status=pendente
```

### Persistência de Estado

- Os menus colapsáveis mantêm seu estado (aberto/fechado)
- O estado é salvo no navegador
- Ao retornar à página, os menus estarão como você deixou

---

## ❓ Perguntas Frequentes

### 1. O menu lateral desapareceu. O que fazer?

**Resposta:** Isso não deve mais acontecer após a otimização. Se acontecer:
- Recarregue a página (F5)
- Limpe o cache do navegador
- Verifique se está em modo mobile (botão hamburger no canto superior esquerdo)

### 2. Como voltar para "Todos" depois de aplicar um filtro?

**Resposta:** Clique no submenu "Todos" ou remova o parâmetro `?status=` da URL.

### 3. Os filtros não estão funcionando. O que fazer?

**Resposta:** 
- Verifique se a URL contém o parâmetro correto (ex: `?status=pendente`)
- Recarregue a página
- Se o problema persistir, contate o suporte técnico

### 4. Como acessar uma aba específica de relatórios diretamente?

**Resposta:** Use a URL com âncora:
- Financeiro: `/admin/relatorios#financeiro`
- Usuários: `/admin/relatorios#usuarios`
- Contratos: `/admin/relatorios#contratos`

### 5. Posso compartilhar links com filtros aplicados?

**Resposta:** Sim! As URLs com filtros podem ser compartilhadas:
```
/admin/convites?status=pendente
/admin/ordens?status=contestada
/admin/relatorios#financeiro
```

### 6. Como saber qual filtro está ativo?

**Resposta:** 
- O submenu ativo fica destacado
- A URL mostra o filtro aplicado
- O título da página indica o filtro (quando aplicável)

### 7. Os menus funcionam em mobile?

**Resposta:** Sim! Em mobile:
- O menu lateral fica oculto por padrão
- Clique no botão hamburger (☰) no canto superior esquerdo
- O menu aparecerá em overlay
- Clique fora do menu para fechá-lo

### 8. Como alterar as configurações de taxas?

**Resposta:**
1. Clique em **"Configurações"** no menu lateral
2. Clique em **"Taxas do Sistema"**
3. Altere os valores desejados
4. Clique em **"Salvar Configurações"**

### 9. Como alterar as configurações de segurança?

**Resposta:**
1. Clique em **"Configurações"** no menu lateral
2. Clique em **"Segurança"**
3. Altere as configurações desejadas
4. Clique em **"Salvar Configurações"**

### 10. Posso ter múltiplos filtros ao mesmo tempo?

**Resposta:** Atualmente, apenas um filtro de status por vez é suportado. Para filtros mais complexos, use a página de relatórios.

---

## 📱 Responsividade

### Desktop (>768px)
- Menu lateral sempre visível
- Todos os submenus acessíveis
- Hover effects ativos

### Tablet (768px - 1024px)
- Menu lateral visível
- Layout adaptado
- Touch interactions

### Mobile (<768px)
- Menu lateral oculto por padrão
- Botão hamburger visível
- Menu em overlay ao abrir
- Touch-friendly

---

## 🎨 Legenda de Ícones

| Ícone | Significado |
|-------|-------------|
| 📊 | Dashboard / Relatórios |
| ⚙️ | Configurações |
| 💰 | Taxas / Financeiro |
| 🛡️ | Segurança |
| 🔑 | Senha / Autenticação |
| ✉️ | Convites |
| 📋 | Listagem / Todas |
| ⏰ | Pendente / Aguardando |
| ✅ | Aceito / Concluído |
| ❌ | Recusado / Cancelado |
| ⏳ | Em Execução |
| ⚠️ | Contestação / Alerta |
| 🔍 | Em Análise |
| 👥 | Usuários |
| 🪙 | Tokens |

---

## 📞 Suporte

**Problemas com navegação?**
- Verifique a documentação completa em: `.kiro/specs/otimizacao-menus-admin/DOCUMENTACAO_FINAL.md`
- Execute testes de validação: `python test_menu_navigation_integration.py`
- Verifique acessibilidade: `python test_accessibility_validation.py`

**Contato:**
- Documentação técnica: `.kiro/specs/otimizacao-menus-admin/`
- Relatórios de tarefas: `.kiro/specs/otimizacao-menus-admin/RELATORIO_*.md`

---

**Última atualização:** Novembro 2025  
**Versão:** 1.0
