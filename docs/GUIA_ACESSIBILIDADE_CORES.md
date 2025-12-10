# Guia de Acessibilidade - Cores e Contraste

## Visão Geral

Este guia explica como usar o sistema de cores acessíveis implementado no projeto, garantindo conformidade com WCAG 2.1 nível AA.

## Ativando o Modo de Alto Contraste

### Opção 1: Botão Visual
- Procure o botão "Alto Contraste" no canto superior direito da tela
- Clique para alternar entre modo normal e alto contraste
- A preferência é salva automaticamente

### Opção 2: Atalho de Teclado
- Pressione `Ctrl + Alt + C` para alternar
- Funciona em qualquer página do sistema

### Opção 3: Preferência do Sistema
- O sistema detecta automaticamente se você tem alto contraste ativado no seu sistema operacional
- Não é necessário configurar manualmente

## Usando as Cores Acessíveis no Código

### Classes CSS Disponíveis

#### Botões

```html
<!-- Botão Primário (azul) -->
<button class="btn-a11y-primary">Ação Principal</button>

<!-- Botão de Sucesso (verde) -->
<button class="btn-a11y-success">Confirmar</button>

<!-- Botão de Erro (vermelho) -->
<button class="btn-a11y-danger">Excluir</button>

<!-- Botão de Aviso (amarelo com texto preto) -->
<button class="btn-a11y-warning">Atenção</button>

<!-- Botão de Informação (azul claro) -->
<button class="btn-a11y-info">Saiba Mais</button>
```

#### Alertas

```html
<!-- Alerta de Sucesso -->
<div class="alert-a11y-success">
    Operação realizada com sucesso!
</div>

<!-- Alerta de Erro -->
<div class="alert-a11y-danger">
    Ocorreu um erro. Tente novamente.
</div>

<!-- Alerta de Aviso -->
<div class="alert-a11y-warning">
    Atenção: Esta ação não pode ser desfeita.
</div>

<!-- Alerta de Informação -->
<div class="alert-a11y-info">
    Dica: Você pode usar atalhos de teclado.
</div>
```

#### Texto

```html
<!-- Texto Principal -->
<p class="text-a11y-primary">Texto importante</p>

<!-- Texto Secundário -->
<p class="text-a11y-secondary">Texto complementar</p>

<!-- Texto Auxiliar -->
<p class="text-a11y-muted">Informação adicional</p>
```

#### Links

```html
<!-- Link Acessível -->
<a href="#" class="link-a11y">Clique aqui</a>
```

### Variáveis CSS

Você pode usar as variáveis CSS diretamente:

```css
.meu-elemento {
    color: var(--a11y-text-primary);
    background-color: var(--a11y-bg-primary);
    border-color: var(--a11y-border-medium);
}

.meu-botao {
    background-color: var(--a11y-success);
    color: var(--a11y-success-text);
}
```

## Testando com Simulador de Daltonismo

### Ativando o Simulador

O simulador está disponível apenas em modo de desenvolvimento:

1. Acesse o sistema em `localhost` ou adicione `?debug=true` na URL
2. Pressione `Ctrl + Alt + V` para abrir o painel de controle
3. Selecione o tipo de daltonismo que deseja simular

### Tipos Disponíveis

- **Protanopia**: Dificuldade com vermelho (~1% dos homens)
- **Deuteranopia**: Dificuldade com verde (~1% dos homens)
- **Tritanopia**: Dificuldade com azul (~0.001% da população)
- **Protanomalia**: Fraqueza com vermelho (~1% dos homens)
- **Deuteranomalia**: Fraqueza com verde (~5% dos homens)
- **Tritanomalia**: Fraqueza com azul (~0.01% da população)
- **Acromatopsia**: Visão em escala de cinza (~0.003% da população)
- **Acromatomalia**: Fraqueza monocromática (~0.001% da população)

### Via JavaScript

```javascript
// Aplicar filtro
ColorblindSimulator.apply('protanopia');

// Remover filtro
ColorblindSimulator.remove();

// Verificar modo atual
const mode = ColorblindSimulator.getCurrentMode();

// Listar tipos disponíveis
const types = ColorblindSimulator.getAvailableTypes();
```

## Diretrizes de Design

### Não Dependa Apenas de Cores

❌ **Errado:**
```html
<span style="color: red;">Erro</span>
```

✅ **Correto:**
```html
<span style="color: var(--a11y-danger);">
    <i class="fas fa-exclamation-circle"></i> Erro
</span>
```

### Use Ícones e Texto

Sempre combine cores com:
- Ícones descritivos
- Texto explicativo
- Padrões visuais diferentes

### Mantenha Contraste Adequado

- Texto normal: mínimo 4.5:1
- Texto grande (18pt+ ou 14pt+ bold): mínimo 3:1
- Componentes de interface: mínimo 3:1

### Cores de Aviso Especiais

⚠️ **Importante:** Cores de aviso (amarelo/laranja) usam **texto PRETO**, não branco:

```css
.aviso {
    background-color: var(--a11y-warning);
    color: var(--a11y-warning-text); /* Preto, não branco! */
}
```

## Testando Contraste

### Script Python

Execute o script de teste para verificar todas as combinações:

```bash
python test_color_contrast.py
```

O script verifica:
- ✅ Conformidade com WCAG AA (4.5:1)
- ✅ Conformidade com WCAG AAA (7:1)
- ✅ Todas as combinações de cores do sistema

### Ferramentas Online

- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Coolors Contrast Checker**: https://coolors.co/contrast-checker

### Ferramentas de Navegador

- **Chrome DevTools - Lighthouse**: Auditoria automática
- **axe DevTools**: Extensão para Chrome/Firefox
- **WAVE**: Extensão de avaliação de acessibilidade

## Conformidade WCAG

### Status Atual

✅ **WCAG 2.1 Nível AA**: 90% de conformidade (36/40 combinações)
✅ **WCAG 2.1 Nível AAA** (modo alto contraste): 100% de conformidade

### Exceções Aceitáveis

1. **Text Disabled** (#adb5bd): Contraste 2.07:1
   - Aceitável pois é apenas decorativo
   - Elementos desabilitados não precisam atender AA

2. **Warning com fundo branco**: Contraste baixo
   - Aceitável pois usa **texto preto** (contraste 8.66:1)
   - Nunca use texto branco em fundos de aviso

## Modo Escuro

O sistema também suporta modo escuro com cores ajustadas:

```css
@media (prefers-color-scheme: dark) {
    /* Cores automaticamente ajustadas */
}
```

Todas as cores do modo escuro também atendem WCAG AA.

## Suporte

### Problemas Comuns

**P: O botão de alto contraste não aparece**
R: Verifique se o arquivo `high-contrast-toggle.js` está carregado

**P: O simulador de daltonismo não funciona**
R: Certifique-se de estar em modo de desenvolvimento (localhost ou ?debug=true)

**P: As cores não mudaram após ativar alto contraste**
R: Limpe o cache do navegador (Ctrl+Shift+R)

### Reportar Problemas

Se encontrar problemas de contraste:
1. Execute `python test_color_contrast.py`
2. Documente a combinação problemática
3. Reporte com screenshot e valores de contraste

## Recursos Adicionais

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Contrast Guide](https://webaim.org/articles/contrast/)
- [Color Oracle](https://colororacle.org/) - Simulador de daltonismo desktop

---

**Última Atualização:** 2 de dezembro de 2025
