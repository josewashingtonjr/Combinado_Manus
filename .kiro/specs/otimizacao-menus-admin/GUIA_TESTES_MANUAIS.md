# 🧪 Guia de Testes Manuais - Menus do Painel Admin

## 📋 Checklist de Testes

### ✅ Teste 1: Estrutura Visual dos Menus

#### Objetivo
Verificar se todos os menus têm aparência consistente

#### Passos
1. Acesse o painel administrativo
2. Observe o menu lateral
3. Verifique se todos os menus têm:
   - ✓ Mesmo tamanho de fonte
   - ✓ Mesmo espaçamento (padding)
   - ✓ Mesmos ícones alinhados
   - ✓ Mesmo estilo de chevron (▼)

#### Resultado Esperado
- Todos os 8 menus devem ter aparência idêntica
- Ícones alinhados à esquerda
- Chevron alinhado à direita
- Espaçamento uniforme

---

### ✅ Teste 2: Expansão e Colapso de Menus

#### Objetivo
Verificar se menus expandem e colapsam corretamente

#### Passos
1. Clique no menu "Usuários"
   - ✓ Menu deve expandir suavemente
   - ✓ Chevron deve girar 180° para cima (▲)
   - ✓ Submenus devem aparecer
2. Clique novamente no menu "Usuários"
   - ✓ Menu deve colapsar suavemente
   - ✓ Chevron deve voltar para baixo (▼)
   - ✓ Submenus devem desaparecer
3. Repita para todos os 8 menus

#### Resultado Esperado
- Animação suave (0.3s)
- Chevron gira corretamente
- Sem travamentos ou bugs visuais

---

### ✅ Teste 3: Estados Hover

#### Objetivo
Verificar feedback visual ao passar o mouse

#### Passos
1. Passe o mouse sobre o cabeçalho "Tokens"
   - ✓ Fundo deve mudar para cinza claro (#f8f9fa)
   - ✓ Cursor deve mudar para pointer
2. Expanda o menu "Tokens"
3. Passe o mouse sobre "Gerenciar"
   - ✓ Fundo deve mudar para cinza (#f1f3f5)
   - ✓ Texto deve ficar azul (#0d6efd)
   - ✓ Item deve deslizar levemente para direita
   - ✓ Borda azul deve aparecer à esquerda
4. Repita para outros menus e itens

#### Resultado Esperado
- Feedback visual imediato
- Transições suaves (0.2s)
- Cores consistentes

---

### ✅ Teste 4: Item Ativo (Página Atual)

#### Objetivo
Verificar se item da página atual é destacado

#### Passos
1. Navegue para "Ordens" → "Aguardando"
   - ✓ Menu "Ordens" deve estar expandido
   - ✓ Item "Aguardando" deve ter:
     - Fundo azul claro (#e7f1ff)
     - Texto azul (#0d6efd)
     - Texto em negrito
     - Borda azul à esquerda
2. Navegue para "Convites" → "Pendentes"
   - ✓ Menu "Convites" deve estar expandido
   - ✓ Item "Pendentes" deve estar destacado
   - ✓ Item "Aguardando" de Ordens não deve mais estar destacado
3. Teste com outras páginas

#### Resultado Esperado
- Apenas o item da página atual está destacado
- Menu pai sempre expandido
- Destaque claro e visível

---

### ✅ Teste 5: Persistência de Estado

#### Objetivo
Verificar se menus mantêm estado entre navegações

#### Passos
1. Expanda os menus "Usuários" e "Tokens"
2. Navegue para "Dashboard"
3. Volte para a página anterior
   - ✓ Menus "Usuários" e "Tokens" devem continuar expandidos
4. Recarregue a página (F5)
   - ✓ Menus devem manter o estado expandido
5. Feche o navegador e abra novamente
   - ✓ Estado deve ser restaurado

#### Resultado Esperado
- Estado persiste entre navegações
- Estado persiste após reload
- Estado persiste após fechar navegador

---

### ✅ Teste 6: Navegação por Teclado

#### Objetivo
Verificar acessibilidade via teclado

#### Passos
1. Pressione Tab até focar no menu lateral
2. Use Arrow Down (↓)
   - ✓ Foco deve mover para próximo item
   - ✓ Indicador de foco deve ser visível (outline azul)
3. Use Arrow Up (↑)
   - ✓ Foco deve mover para item anterior
4. Pressione Enter em um menu colapsado
   - ✓ Menu deve expandir
5. Pressione Space em um item de submenu
   - ✓ Deve navegar para a página
6. Teste navegação completa apenas com teclado

#### Resultado Esperado
- Todos os itens acessíveis por teclado
- Indicador de foco sempre visível
- Enter/Space funcionam corretamente

---

### ✅ Teste 7: Badges de Notificação

#### Objetivo
Verificar exibição de badges

#### Passos
1. Verifique o menu "Tokens" na navbar
   - ✓ Badge amarelo deve aparecer se houver solicitações pendentes
   - ✓ Número deve ser correto
2. Verifique o menu "Tokens" no menu lateral
   - ✓ Badge deve aparecer no cabeçalho
   - ✓ Badge deve aparecer em "Solicitações"
3. Crie uma nova solicitação de tokens
   - ✓ Badges devem atualizar automaticamente

#### Resultado Esperado
- Badges visíveis e legíveis
- Contagem correta
- Atualização em tempo real

---

### ✅ Teste 8: Navbar Superior

#### Objetivo
Verificar consistência da navbar

#### Passos
1. Navegue por diferentes páginas do admin
   - ✓ Navbar deve ser idêntica em todas
2. Clique no dropdown "Tokens"
   - ✓ Menu deve abrir suavemente
   - ✓ Itens devem estar alinhados
3. Clique no dropdown do usuário
   - ✓ Opções "Alterar Senha" e "Sair" devem aparecer
4. Teste todos os links da navbar
   - ✓ Todos devem funcionar

#### Resultado Esperado
- Navbar consistente em todas as páginas
- Dropdowns funcionais
- Links funcionais

---

### ✅ Teste 9: Responsividade Desktop

#### Objetivo
Verificar em diferentes resoluções desktop

#### Passos
1. Teste em 1920x1080
   - ✓ Menu lateral visível
   - ✓ Conteúdo bem distribuído
2. Teste em 1366x768
   - ✓ Menu lateral visível
   - ✓ Sem scroll horizontal
3. Teste em 1024x768
   - ✓ Menu lateral visível
   - ✓ Layout responsivo

#### Resultado Esperado
- Menu sempre visível em desktop
- Layout adaptável
- Sem quebras visuais

---

### ✅ Teste 10: Responsividade Mobile

#### Objetivo
Verificar em dispositivos móveis

#### Passos
1. Abra DevTools (F12)
2. Ative modo responsivo
3. Teste em 768x1024 (Tablet)
   - ✓ Menu lateral deve estar oculto
   - ✓ Navbar deve ter botão hamburger
4. Teste em 375x667 (Mobile)
   - ✓ Menu lateral oculto
   - ✓ Navbar colapsável
   - ✓ Conteúdo ocupa 100% da largura
5. Clique no botão hamburger
   - ✓ Menu deve aparecer

#### Resultado Esperado
- Menu oculto em telas pequenas
- Navbar responsiva
- Botão hamburger funcional

---

### ✅ Teste 11: Múltiplos Navegadores

#### Objetivo
Verificar compatibilidade cross-browser

#### Passos
1. Teste no Google Chrome
   - ✓ Todas as funcionalidades funcionam
2. Teste no Firefox
   - ✓ Todas as funcionalidades funcionam
3. Teste no Safari (se disponível)
   - ✓ Todas as funcionalidades funcionam
4. Teste no Edge
   - ✓ Todas as funcionalidades funcionam

#### Resultado Esperado
- Comportamento idêntico em todos os navegadores
- Sem bugs específicos de navegador

---

### ✅ Teste 12: Performance

#### Objetivo
Verificar velocidade e fluidez

#### Passos
1. Abra DevTools → Performance
2. Grave interação com menus
3. Expanda/colapsa vários menus rapidamente
   - ✓ Sem lag ou travamentos
   - ✓ Animações suaves
4. Navegue entre páginas
   - ✓ Carregamento rápido
   - ✓ Sem delay perceptível

#### Resultado Esperado
- Tempo de carregamento < 50ms
- Animações a 60fps
- Sem travamentos

---

### ✅ Teste 13: Acessibilidade com Leitor de Tela

#### Objetivo
Verificar compatibilidade com leitores de tela

#### Passos (se leitor de tela disponível)
1. Ative leitor de tela (NVDA, JAWS, VoiceOver)
2. Navegue pelo menu lateral
   - ✓ Títulos dos menus devem ser lidos
   - ✓ Estado (expandido/colapsado) deve ser anunciado
   - ✓ Itens de submenu devem ser lidos
3. Navegue pela navbar
   - ✓ Links devem ser identificados
   - ✓ Dropdowns devem ser anunciados

#### Resultado Esperado
- Todos os elementos são anunciados
- Estados são comunicados
- Navegação compreensível

---

### ✅ Teste 14: Fallback sem JavaScript

#### Objetivo
Verificar funcionamento sem JavaScript

#### Passos
1. Desabilite JavaScript no navegador
2. Recarregue a página
3. Tente expandir menus
   - ⚠️ Menus podem não colapsar (esperado)
   - ✓ Conteúdo deve estar acessível
   - ✓ Links devem funcionar
4. Navegue entre páginas
   - ✓ Navegação deve funcionar

#### Resultado Esperado
- Funcionalidade básica mantida
- Conteúdo acessível
- Degradação graciosa

---

### ✅ Teste 15: Filtros de Status

#### Objetivo
Verificar filtros em Ordens, Convites e Contestações

#### Passos
1. Clique em "Ordens" → "Aguardando"
   - ✓ URL deve ter `?status=aguardando_execucao`
   - ✓ Apenas ordens aguardando devem aparecer
2. Clique em "Convites" → "Pendentes"
   - ✓ URL deve ter `?status=pendente`
   - ✓ Apenas convites pendentes devem aparecer
3. Clique em "Contestações" → "Em Análise"
   - ✓ URL deve ter `?status=em_analise`
   - ✓ Apenas contestações em análise devem aparecer
4. Teste todos os filtros

#### Resultado Esperado
- Filtros aplicam corretamente
- URL reflete o filtro
- Resultados corretos

---

### ✅ Teste 16: Relatórios com Abas

#### Objetivo
Verificar navegação por abas em Relatórios

#### Passos
1. Clique em "Relatórios" → "Financeiro"
   - ✓ URL deve ter `#financeiro`
   - ✓ Aba Financeiro deve estar ativa
2. Clique em "Relatórios" → "Usuários"
   - ✓ URL deve ter `#usuarios`
   - ✓ Aba Usuários deve estar ativa
3. Recarregue a página
   - ✓ Aba correta deve estar ativa
4. Teste todas as abas

#### Resultado Esperado
- Âncoras funcionam corretamente
- Abas ativam automaticamente
- Estado persiste após reload

---

## 📊 Planilha de Resultados

| Teste | Status | Observações |
|-------|--------|-------------|
| 1. Estrutura Visual | ⬜ | |
| 2. Expansão/Colapso | ⬜ | |
| 3. Estados Hover | ⬜ | |
| 4. Item Ativo | ⬜ | |
| 5. Persistência | ⬜ | |
| 6. Navegação Teclado | ⬜ | |
| 7. Badges | ⬜ | |
| 8. Navbar | ⬜ | |
| 9. Responsividade Desktop | ⬜ | |
| 10. Responsividade Mobile | ⬜ | |
| 11. Múltiplos Navegadores | ⬜ | |
| 12. Performance | ⬜ | |
| 13. Leitor de Tela | ⬜ | |
| 14. Fallback sem JS | ⬜ | |
| 15. Filtros de Status | ⬜ | |
| 16. Relatórios com Abas | ⬜ | |

**Legenda:**
- ⬜ Não testado
- ✅ Passou
- ⚠️ Passou com ressalvas
- ❌ Falhou

---

## 🐛 Relatório de Bugs

Se encontrar algum problema, documente aqui:

### Bug #1
- **Teste:** [Número do teste]
- **Descrição:** [O que aconteceu]
- **Esperado:** [O que deveria acontecer]
- **Navegador:** [Chrome/Firefox/Safari/Edge]
- **Resolução:** [Largura x Altura]
- **Passos para Reproduzir:**
  1. [Passo 1]
  2. [Passo 2]
  3. [Passo 3]

---

## ✅ Critérios de Aceitação

Para considerar os testes bem-sucedidos:

- [ ] Todos os 16 testes passaram
- [ ] Nenhum bug crítico encontrado
- [ ] Performance aceitável (< 50ms)
- [ ] Funciona em Chrome, Firefox e Edge
- [ ] Responsivo em desktop e mobile
- [ ] Acessível por teclado
- [ ] Badges funcionam corretamente
- [ ] Persistência funciona
- [ ] Filtros aplicam corretamente
- [ ] Abas de relatórios funcionam

---

## 📝 Notas Adicionais

### Dicas para Testes
1. Use DevTools para simular diferentes dispositivos
2. Teste com dados reais (ordens, convites, etc.)
3. Teste com e sem notificações pendentes
4. Limpe localStorage entre testes se necessário
5. Teste em janela anônima para ambiente limpo

### Comandos Úteis
```javascript
// Limpar estado dos menus no console
localStorage.removeItem('admin_menu_state');

// Ver estado atual
console.log(localStorage.getItem('admin_menu_state'));

// Forçar reload sem cache
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

---

## 🎯 Conclusão

Após completar todos os testes, você deve ter:
- ✅ Confiança na qualidade da implementação
- ✅ Lista de bugs (se houver) para correção
- ✅ Evidências de que tudo funciona conforme esperado
- ✅ Documentação de qualquer comportamento inesperado

**Testador:** _______________  
**Data:** _______________  
**Resultado Final:** ⬜ Aprovado | ⬜ Aprovado com Ressalvas | ⬜ Reprovado

---

**Versão do Guia:** 1.0  
**Última Atualização:** 20 de novembro de 2025  
**Criado por:** Kiro AI
