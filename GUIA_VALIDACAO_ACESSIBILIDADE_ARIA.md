# Guia de Validação - Acessibilidade ARIA e Labels

## Visão Geral

Este documento descreve as melhorias de acessibilidade implementadas e como validá-las manualmente.

**Tarefa:** 14. Adicionar Labels e ARIA  
**Requirements:** 7.3, 7.4, 7.5

## Melhorias Implementadas

### 1. Labels em Campos de Formulário ✅

**O que foi feito:**
- Script JavaScript (`accessibility-aria.js`) adiciona automaticamente `aria-label` a campos sem label
- Campos obrigatórios recebem `aria-required="true"`
- Campos com erro recebem `aria-invalid="true"` e `aria-describedby`

**Como validar:**
1. Abra qualquer formulário (ex: criar convite, solicitar tokens)
2. Abra o DevTools (F12) e inspecione um campo de input
3. Verifique que o campo tem:
   - Um `<label for="campo_id">` associado, OU
   - Um atributo `aria-label="Descrição"`
4. Para campos obrigatórios, verifique `aria-required="true"`

**Exemplo esperado:**
```html
<input type="text" id="service_title" name="service_title" 
       aria-label="Título do Serviço" 
       aria-required="true" 
       required>
```

### 2. Ícones com ARIA ✅

**O que foi feito:**
- Ícones decorativos (com texto ao lado) recebem `aria-hidden="true"`
- Ícones funcionais (sem texto) recebem `aria-label` descritivo
- Mapeamento de 100+ ícones comuns do Font Awesome

**Como validar:**
1. Abra qualquer página do sistema
2. Inspecione ícones (elementos `<i class="fa-...">`)
3. Verifique que cada ícone tem:
   - `aria-hidden="true"` se está dentro de botão/link com texto, OU
   - `aria-label="Descrição"` e `role="img"` se está sozinho

**Exemplo esperado:**
```html
<!-- Ícone decorativo -->
<button>
    <i class="fas fa-home" aria-hidden="true"></i>
    Início
</button>

<!-- Ícone funcional -->
<i class="fas fa-search" aria-label="Buscar" role="img"></i>
```

### 3. Mensagens Dinâmicas com aria-live ✅

**O que foi feito:**
- Alertas recebem `aria-live="polite"` ou `"assertive"` (para erros)
- Badges e contadores recebem `aria-live="polite"`
- Toasts têm `role="alert"` e `aria-live`

**Como validar:**
1. Execute uma ação que gera mensagem (ex: criar convite)
2. Inspecione o alerta/toast que aparece
3. Verifique que tem:
   - `aria-live="polite"` ou `"assertive"`
   - `aria-atomic="true"`
   - `role="alert"` para mensagens importantes

**Exemplo esperado:**
```html
<div class="alert alert-success" 
     role="alert" 
     aria-live="polite" 
     aria-atomic="true">
    Convite criado com sucesso!
</div>
```

### 4. Navegação por Teclado ✅

**O que foi feito:**
- CSS com indicadores de foco visíveis e claros
- Skip links para pular para conteúdo principal
- Elementos interativos customizados são focáveis (tabindex="0")
- Suporte para Enter e Space em elementos com role="button"

**Como validar:**
1. Abra qualquer página
2. Pressione Tab repetidamente
3. Verifique que:
   - Todos os elementos interativos são focáveis
   - O foco é claramente visível (outline amarelo/azul)
   - A ordem de foco faz sentido
4. Pressione Shift+Tab para navegar para trás
5. No primeiro Tab, deve aparecer um "Skip Link" no topo

**Exemplo esperado:**
- Outline de 3px amarelo ao focar com teclado
- Box-shadow adicional para maior visibilidade
- Skip link visível ao focar

### 5. Suporte a Leitores de Tela ✅

**O que foi feito:**
- Landmarks semânticos (`<main>`, `<nav>`, `<footer>`)
- Navegação mobile com `role="navigation"` e `aria-label`
- Links ativos com `aria-current="page"`
- Imagens com texto alternativo

**Como validar:**
1. Use um leitor de tela (NVDA no Windows, VoiceOver no Mac)
2. Navegue pela página usando comandos do leitor
3. Verifique que:
   - Landmarks são anunciados corretamente
   - Links e botões têm descrições claras
   - Página atual é identificada na navegação
   - Imagens têm descrição alternativa

## Arquivos Criados/Modificados

### Novos Arquivos:
1. **`static/js/accessibility-aria.js`** - Script principal de melhorias ARIA
2. **`static/css/accessibility-keyboard.css`** - Estilos para navegação por teclado
3. **`test_accessibility_aria_labels.py`** - Testes automatizados

### Arquivos Modificados:
1. **`templates/base.html`** - Inclusão dos novos arquivos CSS e JS

## Checklist de Validação Manual

### Formulários
- [ ] Todos os campos têm label ou aria-label
- [ ] Campos obrigatórios têm aria-required
- [ ] Campos com erro têm aria-invalid
- [ ] Mensagens de erro são associadas aos campos

### Ícones
- [ ] Ícones decorativos têm aria-hidden
- [ ] Ícones funcionais têm aria-label
- [ ] Ícones em botões não interferem na leitura

### Mensagens
- [ ] Alertas têm aria-live
- [ ] Toasts aparecem e são anunciados
- [ ] Badges de notificação são acessíveis

### Navegação por Teclado
- [ ] Tab navega por todos os elementos interativos
- [ ] Foco é claramente visível
- [ ] Skip link funciona (primeiro Tab)
- [ ] Enter/Space ativam elementos customizados

### Leitores de Tela
- [ ] Landmarks são anunciados
- [ ] Navegação mobile é acessível
- [ ] Página atual é identificada
- [ ] Conteúdo dinâmico é anunciado

## Testes com Ferramentas

### 1. Lighthouse (Chrome DevTools)
```bash
1. Abra Chrome DevTools (F12)
2. Vá para aba "Lighthouse"
3. Selecione "Accessibility"
4. Clique em "Generate report"
5. Objetivo: Score > 90
```

### 2. axe DevTools (Extensão)
```bash
1. Instale extensão "axe DevTools" no Chrome
2. Abra qualquer página do sistema
3. Clique no ícone da extensão
4. Clique em "Scan ALL of my page"
5. Revise e corrija problemas encontrados
```

### 3. WAVE (Extensão)
```bash
1. Instale extensão "WAVE" no Chrome
2. Abra qualquer página do sistema
3. Clique no ícone da extensão
4. Revise alertas e erros
```

### 4. Leitor de Tela

**Windows (NVDA):**
```bash
1. Baixe NVDA: https://www.nvaccess.org/download/
2. Instale e inicie
3. Navegue pelo sistema usando:
   - Tab: Próximo elemento
   - Shift+Tab: Elemento anterior
   - H: Próximo heading
   - L: Próximo link
   - B: Próximo botão
   - F: Próximo campo de formulário
```

**Mac (VoiceOver):**
```bash
1. Pressione Cmd+F5 para ativar VoiceOver
2. Navegue usando:
   - VO+Right Arrow: Próximo item
   - VO+Left Arrow: Item anterior
   - VO+Space: Ativar item
   - VO = Control+Option
```

## Conformidade WCAG 2.1

As melhorias implementadas atendem aos seguintes critérios:

### Nível A:
- ✅ 1.1.1 - Conteúdo Não Textual (alt text em imagens)
- ✅ 1.3.1 - Informação e Relações (labels em formulários)
- ✅ 2.1.1 - Teclado (navegação completa por teclado)
- ✅ 2.4.1 - Ignorar Blocos (skip links)
- ✅ 3.3.2 - Labels ou Instruções (todos os campos têm labels)
- ✅ 4.1.2 - Nome, Função, Valor (ARIA em elementos customizados)

### Nível AA:
- ✅ 2.4.7 - Foco Visível (indicadores claros de foco)
- ✅ 3.3.3 - Sugestão de Erro (mensagens de erro claras)

## Problemas Conhecidos e Limitações

1. **Conteúdo Dinâmico:** 
   - O script usa MutationObserver para detectar mudanças
   - Pode haver atraso mínimo na aplicação de ARIA

2. **Compatibilidade:**
   - Testado em Chrome, Firefox, Safari
   - Leitores de tela: NVDA, VoiceOver
   - Pode haver diferenças em navegadores antigos

3. **Manutenção:**
   - Novos ícones precisam ser adicionados ao mapeamento
   - Novos componentes devem seguir padrões estabelecidos

## Próximos Passos

1. **Testes com Usuários Reais:**
   - Recrutar usuários com deficiência visual
   - Observar uso com leitores de tela
   - Coletar feedback e iterar

2. **Documentação:**
   - Criar guia de desenvolvimento acessível
   - Documentar padrões para novos componentes
   - Treinar equipe em acessibilidade

3. **Monitoramento:**
   - Configurar testes automatizados de acessibilidade
   - Incluir verificações no CI/CD
   - Auditorias periódicas

## Recursos Adicionais

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM](https://webaim.org/)
- [A11y Project](https://www.a11yproject.com/)

## Suporte

Para dúvidas ou problemas relacionados à acessibilidade:
1. Consulte este documento
2. Revise o código em `static/js/accessibility-aria.js`
3. Execute os testes em `test_accessibility_aria_labels.py`
4. Use ferramentas de auditoria (Lighthouse, axe, WAVE)
