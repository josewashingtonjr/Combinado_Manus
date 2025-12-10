# 🚀 Toast Feedback - Guia Rápido

## Uso Básico

### JavaScript
```javascript
// Sucesso
toast.success('Operação concluída!');

// Erro
toast.error('Algo deu errado');

// Aviso
toast.warning('Atenção!');

// Informação
toast.info('Processando...');
```

### Python (Flask)
```python
from flask import flash

flash('Usuário criado!', 'success')
flash('Erro ao salvar', 'error')
flash('Verifique os dados', 'warning')
flash('Processando...', 'info')
```

## Opções Avançadas

### Duração Personalizada
```javascript
toast.success('Mensagem rápida', 2000);  // 2 segundos
toast.info('Mensagem longa', 10000);     // 10 segundos
toast.warning('Permanente', 0);          // Não desaparece
```

### Controle Manual
```javascript
// Salvar ID do toast
const id = toast.info('Processando...');

// Fechar depois
toast.hide(id);

// Fechar todos
toast.hideAll();
```

## Exemplos Práticos

### Formulário AJAX
```javascript
fetch('/api/save', {
    method: 'POST',
    body: formData
})
.then(response => {
    if (response.ok) {
        toast.success('Salvo!');
    } else {
        toast.error('Erro ao salvar');
    }
});
```

### Confirmação de Ação
```javascript
function deleteItem(id) {
    if (confirm('Tem certeza?')) {
        toast.info('Excluindo...');
        // ... código de exclusão
    }
}
```

### Copiar para Clipboard
```javascript
navigator.clipboard.writeText(text)
    .then(() => toast.success('Copiado!'))
    .catch(() => toast.error('Erro ao copiar'));
```

## Cores e Ícones

| Tipo | Cor | Ícone | Uso |
|------|-----|-------|-----|
| success | Verde | ✓ | Operação bem-sucedida |
| error | Vermelho | ✗ | Erro ou falha |
| warning | Amarelo | ⚠ | Atenção ou cuidado |
| info | Azul | ℹ | Informação geral |

## Dicas

✅ **Use para**:
- Confirmações de ações
- Erros de validação
- Status de operações
- Notificações rápidas

❌ **Não use para**:
- Informações críticas que precisam de ação
- Conteúdo extenso
- Formulários ou inputs
- Navegação principal

## Acessibilidade

- ✅ Leitores de tela anunciam automaticamente
- ✅ Pode ser fechado com teclado (Tab + Enter)
- ✅ Contraste adequado para baixa visão
- ✅ Respeita preferências de movimento

## Troubleshooting

**Toast não aparece?**
- Verifique se o JavaScript está carregado
- Abra o console (F12) e procure erros
- Confirme que `toast` está definido: `console.log(toast)`

**Toast aparece mas não desaparece?**
- Verifique se passou duração 0 (permanente)
- Feche manualmente: `toast.hideAll()`

**Mensagens Flask não aparecem?**
- Confirme que o template base está sendo usado
- Verifique se há erros no console

## Mais Informações

- 📖 Documentação completa: `IMPLEMENTACAO_TOAST_FEEDBACK.md`
- 🎨 Exemplos interativos: `static/js/toast-examples.html`
- 🧪 Testes: `python test_toast_feedback.py`
- 📋 Guia de testes: `TESTE_MANUAL_TOAST.md`
