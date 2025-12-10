# Form Helpers - Guia Rápido

## 🚀 Início Rápido

### 1. Incluir o Script

Adicione ao seu template (antes do `</body>`):

```html
<script src="{{ url_for('static', filename='js/form-helpers.js') }}"></script>
```

### 2. Usar nos Campos

Adicione os atributos `data-validate` e `data-mask`:

```html
<!-- E-mail obrigatório -->
<input 
    type="email" 
    data-validate="required,email"
    placeholder="seu@email.com"
>

<!-- Telefone com máscara -->
<input 
    type="tel" 
    data-mask="telefone"
    data-validate="required,telefone"
    placeholder="(00) 00000-0000"
>

<!-- Valor monetário -->
<input 
    type="text" 
    data-mask="valor"
    data-validate="required,valor"
    placeholder="0,00"
>
```

### 3. Pronto!

O sistema valida automaticamente:
- ✅ Ao digitar (tempo real)
- ✅ Ao sair do campo (blur)
- ✅ Ao submeter o formulário

## 📋 Validadores Mais Usados

| Atributo | Descrição |
|----------|-----------|
| `data-validate="required"` | Campo obrigatório |
| `data-validate="email"` | E-mail válido |
| `data-validate="telefone"` | Telefone brasileiro |
| `data-validate="cpf"` | CPF válido |
| `data-validate="valor"` | Valor monetário |
| `data-validate="senha-forte"` | Senha segura |

## 🎭 Máscaras Mais Usadas

| Atributo | Formato |
|----------|---------|
| `data-mask="telefone"` | (XX) XXXXX-XXXX |
| `data-mask="cpf"` | XXX.XXX.XXX-XX |
| `data-mask="cnpj"` | XX.XXX.XXX/XXXX-XX |
| `data-mask="valor"` | 1.234,56 |
| `data-mask="cep"` | XXXXX-XXX |
| `data-mask="data"` | DD/MM/AAAA |

## 💡 Exemplos Práticos

### Formulário de Cadastro

```html
<form>
    <div class="form-group">
        <label>Nome <span class="required">*</span></label>
        <input 
            type="text" 
            name="nome"
            data-validate="required"
        >
    </div>

    <div class="form-group">
        <label>E-mail <span class="required">*</span></label>
        <input 
            type="email" 
            name="email"
            data-validate="required,email"
        >
    </div>

    <div class="form-group">
        <label>Telefone <span class="required">*</span></label>
        <input 
            type="tel" 
            name="telefone"
            data-mask="telefone"
            data-validate="required,telefone"
        >
    </div>

    <button type="submit">Cadastrar</button>
</form>
```

### Formulário de Serviço

```html
<form>
    <div class="form-group">
        <label>Descrição <span class="required">*</span></label>
        <textarea 
            name="descricao"
            data-validate="required,minlength"
            data-minlength="20"
        ></textarea>
    </div>

    <div class="form-group">
        <label>Valor <span class="required">*</span></label>
        <input 
            type="text" 
            name="valor"
            data-mask="valor"
            data-validate="required,valor"
        >
    </div>

    <button type="submit">Criar Serviço</button>
</form>
```

## 🔧 API JavaScript

```javascript
// Validar campo
const input = document.querySelector('#campo');
window.formHelpers.validateField(input);

// Validar formulário
const form = document.querySelector('#form');
window.formHelpers.validateForm(form);

// Obter valor sem máscara
const valorLimpo = window.formHelpers.getCleanValue(input);
```

## 🎨 Estilos Automáticos

O sistema adiciona classes automaticamente:

- `.is-valid` - Campo válido (borda verde)
- `.is-invalid` - Campo inválido (borda vermelha)
- `.error-message` - Mensagem de erro

## 📱 Mobile-Friendly

- ✅ Campos com 44px de altura mínima
- ✅ Fonte de 16px (previne zoom no iOS)
- ✅ Teclado apropriado para cada tipo
- ✅ Mensagens de erro grandes e legíveis

## 🧪 Testar

Abra no navegador:
```
static/js/form-helpers-examples.html
```

## 📚 Documentação Completa

Veja `IMPLEMENTACAO_FORM_HELPERS.md` para:
- Lista completa de validadores
- Lista completa de máscaras
- Exemplos avançados
- Validadores customizados
- Máscaras customizadas

## ✅ Checklist de Integração

- [ ] Incluir script no template base
- [ ] Adicionar `data-validate` nos campos obrigatórios
- [ ] Adicionar `data-mask` nos campos de telefone/CPF/valor
- [ ] Testar no navegador desktop
- [ ] Testar em dispositivo móvel
- [ ] Verificar mensagens de erro
- [ ] Validar com usuários

## 🎯 Dicas

1. **Combine validadores**: `data-validate="required,email,maxlength"`
2. **Use máscaras**: Melhoram a experiência do usuário
3. **Teste em mobile**: Verifique os teclados apropriados
4. **Mensagens claras**: Todas em português brasileiro
5. **Feedback visual**: Verde = válido, Vermelho = inválido

## 🆘 Problemas Comuns

**Validação não funciona?**
- Verifique se o script está carregado
- Abra o console e procure por erros
- Confirme que os atributos estão corretos

**Máscara não aplica?**
- Use `data-mask="nome-da-mascara"`
- Verifique a ortografia
- Veja a lista de máscaras disponíveis

**Toast não aparece?**
- Certifique-se que `toast-feedback.js` está carregado
- Verifique se o container de toast existe no HTML

## 📞 Suporte

Para mais informações, consulte:
- `IMPLEMENTACAO_FORM_HELPERS.md` - Documentação completa
- `static/js/form-helpers-examples.html` - Exemplos interativos
- `test_form_helpers.py` - Testes automatizados
