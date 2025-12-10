# 🧪 Guia de Teste Manual - Componente Toast Feedback

## Objetivo
Validar o funcionamento do componente de toast feedback em diferentes cenários.

## Pré-requisitos
- Servidor Flask rodando
- Navegador moderno (Chrome, Firefox, Safari, Edge)
- Dispositivo mobile ou emulador (opcional)

## 📋 Testes a Realizar

### Teste 1: Página de Exemplos
**Objetivo**: Verificar todos os tipos de toast e funcionalidades

1. Abra no navegador: `http://localhost:5000/static/js/toast-examples.html`
2. Clique em cada botão de tipo de toast:
   - ✅ Sucesso (verde)
   - ✅ Erro (vermelho)
   - ✅ Aviso (amarelo)
   - ✅ Info (azul)
3. Verifique que cada toast:
   - Aparece no topo da tela
   - Tem a cor correta
   - Tem o ícone correto
   - Desaparece após 5 segundos
   - Pode ser fechado manualmente

**Resultado Esperado**: Todos os toasts aparecem corretamente com cores e ícones apropriados.

---

### Teste 2: Durações Personalizadas
**Objetivo**: Verificar diferentes durações de exibição

1. Na página de exemplos, clique nos botões de duração:
   - 2 segundos (desaparece rápido)
   - 5 segundos (padrão)
   - 10 segundos (demora mais)
   - Permanente (não desaparece)

2. Para o toast permanente, clique no X para fechar

**Resultado Esperado**: Cada toast respeita sua duração configurada.

---

### Teste 3: Múltiplos Toasts
**Objetivo**: Verificar empilhamento de toasts

1. Clique no botão "Mostrar 3 Toasts"
2. Observe que 3 toasts aparecem empilhados
3. Clique em "Limpar Todos"

**Resultado Esperado**: 
- Toasts aparecem empilhados verticalmente
- Todos desaparecem ao clicar em "Limpar Todos"

---

### Teste 4: Pausa no Hover
**Objetivo**: Verificar que o toast pausa ao passar o mouse

1. Mostre um toast qualquer
2. Passe o mouse sobre o toast
3. Mantenha o mouse sobre o toast por mais de 5 segundos
4. Retire o mouse

**Resultado Esperado**: 
- Toast não desaparece enquanto o mouse está sobre ele
- Toast desaparece 2 segundos após retirar o mouse

---

### Teste 5: Integração com Flask Flash
**Objetivo**: Verificar conversão automática de mensagens Flask

1. Faça login no sistema
2. Execute uma ação que gera mensagem flash (ex: salvar dados)
3. Observe se a mensagem aparece como toast

**Resultado Esperado**: Mensagens flash do Flask aparecem como toasts automaticamente.

---

### Teste 6: Responsividade Mobile
**Objetivo**: Verificar comportamento em telas pequenas

1. Abra a página de exemplos em um celular OU
2. Use DevTools (F12) e ative o modo mobile (Ctrl+Shift+M)
3. Teste todos os tipos de toast
4. Verifique:
   - Toast ocupa 95% da largura
   - Botões são fáceis de tocar (48px mínimo)
   - Texto é legível (16px)
   - Não há scroll horizontal

**Resultado Esperado**: Toast funciona perfeitamente em mobile.

---

### Teste 7: Acessibilidade - Teclado
**Objetivo**: Verificar navegação por teclado

1. Mostre um toast
2. Pressione Tab até focar no botão de fechar
3. Pressione Enter para fechar

**Resultado Esperado**: É possível fechar o toast usando apenas o teclado.

---

### Teste 8: Acessibilidade - Leitor de Tela
**Objetivo**: Verificar compatibilidade com leitores de tela

1. Ative um leitor de tela (NVDA, JAWS, VoiceOver)
2. Mostre um toast
3. Ouça o que o leitor de tela anuncia

**Resultado Esperado**: Leitor de tela anuncia a mensagem do toast.

---

### Teste 9: Modo Escuro
**Objetivo**: Verificar aparência em modo escuro

1. Ative o modo escuro do sistema operacional
2. Abra a página de exemplos
3. Mostre alguns toasts

**Resultado Esperado**: Toasts têm fundo escuro e texto claro.

---

### Teste 10: Movimento Reduzido
**Objetivo**: Verificar respeito a preferências de acessibilidade

1. Ative "Reduzir movimento" nas configurações do sistema
2. Mostre alguns toasts
3. Observe as animações

**Resultado Esperado**: Animações são reduzidas ou removidas.

---

### Teste 11: Mensagens Longas
**Objetivo**: Verificar comportamento com textos extensos

1. Clique no botão "Mensagem Longa"
2. Observe como o toast se ajusta

**Resultado Esperado**: 
- Toast expande verticalmente
- Texto quebra corretamente
- Não há overflow

---

### Teste 12: Uso em Formulários
**Objetivo**: Testar em cenário real de uso

1. Vá para uma página com formulário (ex: criar convite)
2. Preencha o formulário
3. Submeta
4. Observe o toast de sucesso/erro

**Resultado Esperado**: Toast aparece após submissão do formulário.

---

## 🎯 Checklist de Validação

Marque cada item após testar:

### Funcionalidade
- [ ] Toasts aparecem no topo da tela
- [ ] 4 tipos de toast funcionam (success, error, warning, info)
- [ ] Auto-dismiss após 5 segundos
- [ ] Botão de fechar manual funciona
- [ ] Múltiplos toasts empilham corretamente
- [ ] Pausa no hover funciona
- [ ] Barra de progresso é visível

### Visual
- [ ] Cores semânticas corretas
- [ ] Ícones apropriados para cada tipo
- [ ] Animações suaves de entrada/saída
- [ ] Layout não quebra em mobile
- [ ] Texto legível em todas as telas

### Acessibilidade
- [ ] Navegação por teclado funciona
- [ ] Leitor de tela anuncia mensagens
- [ ] Contraste de cores adequado
- [ ] Touch targets de 48px mínimo
- [ ] Modo escuro funciona
- [ ] Movimento reduzido respeitado

### Integração
- [ ] CSS carregado corretamente
- [ ] JavaScript carregado corretamente
- [ ] Mensagens Flask convertidas automaticamente
- [ ] API global `toast.*` disponível
- [ ] Sem erros no console

## 🐛 Problemas Encontrados

Se encontrar algum problema, documente aqui:

**Problema 1:**
- Descrição:
- Passos para reproduzir:
- Navegador/Dispositivo:
- Screenshot (se aplicável):

**Problema 2:**
- Descrição:
- Passos para reproduzir:
- Navegador/Dispositivo:
- Screenshot (se aplicável):

## ✅ Aprovação

Após completar todos os testes:

- [ ] Todos os testes passaram
- [ ] Nenhum problema crítico encontrado
- [ ] Componente pronto para uso em produção

**Testado por**: _______________
**Data**: _______________
**Assinatura**: _______________

---

## 📞 Suporte

Se precisar de ajuda ou encontrar problemas:
1. Verifique o console do navegador (F12)
2. Consulte `IMPLEMENTACAO_TOAST_FEEDBACK.md`
3. Veja exemplos em `static/js/toast-examples.html`
