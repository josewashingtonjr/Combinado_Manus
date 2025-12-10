# Guia de Teste Manual - Checkpoint 16

## Como Testar a Interface Funcional

Este guia ajuda você a testar manualmente todas as funcionalidades implementadas no Checkpoint 16.

---

## Pré-requisitos

1. Servidor Flask rodando (`python app.py`)
2. Banco de dados configurado
3. Dois usuários criados (um cliente e um prestador)
4. Uma pré-ordem criada

---

## Teste 1: Navegação Completa do Fluxo

### Objetivo
Verificar que o fluxo completo de negociação funciona corretamente.

### Passos

1. **Login como Cliente**
   - Acesse `/login`
   - Entre com credenciais do cliente
   - Navegue até o dashboard

2. **Visualizar Pré-Ordem**
   - Clique em uma pré-ordem na lista
   - Verifique que todos os dados são exibidos:
     - Título e descrição
     - Valor atual e original
     - Prazo de entrega
     - Status
     - Indicadores de aceitação

3. **Login como Prestador (nova aba)**
   - Abra uma nova aba/janela
   - Faça login como prestador
   - Acesse a mesma pré-ordem

4. **Propor Alteração**
   - Como prestador, role até o formulário de proposta
   - Altere o valor (ex: de R$ 1000 para R$ 1200)
   - Escreva uma justificativa (mínimo 50 caracteres)
   - Clique em "Enviar Proposta"
   - Verifique a mensagem de sucesso

5. **Aceitar Proposta**
   - Volte para a aba do cliente
   - Atualize a página (ou aguarde atualização automática)
   - Verifique que a proposta aparece
   - Clique em "Aceitar Proposta"
   - Verifique que o valor foi atualizado

6. **Aceitar Termos**
   - Como cliente, clique em "Aceitar Termos"
   - Confirme no modal
   - Verifique que o indicador de aceitação mudou

7. **Aceitar Termos (Prestador)**
   - Volte para a aba do prestador
   - Atualize a página
   - Clique em "Aceitar Termos"
   - Confirme no modal

8. **Verificar Aceitação Mútua**
   - Verifique que ambos os indicadores mostram "Aceitou"
   - Verifique que o status mudou para "Pronto para Conversão"
   - Verifique a notificação de sucesso

### Resultado Esperado
✅ Fluxo completo funciona sem erros
✅ Todas as transições de estado ocorrem corretamente
✅ Notificações são exibidas em cada etapa

---

## Teste 2: Responsividade

### Objetivo
Verificar que a interface se adapta a diferentes tamanhos de tela.

### Passos

1. **Desktop (1920x1080)**
   - Abra a pré-ordem em tela cheia
   - Verifique que todos os elementos são visíveis
   - Verifique o layout em 3 colunas

2. **Tablet (768x1024)**
   - Redimensione o navegador para 768px de largura
   - Ou use DevTools (F12) > Toggle Device Toolbar
   - Verifique que o layout se adapta
   - Verifique que botões ficam empilhados

3. **Mobile (375x667)**
   - Redimensione para 375px de largura
   - Verifique que:
     - Cards ficam em coluna única
     - Botões ocupam largura total
     - Timeline é legível
     - Formulários são usáveis

4. **Rotação de Tela**
   - Em mobile, teste modo retrato e paisagem
   - Verifique que a interface se adapta

### Resultado Esperado
✅ Interface é usável em todos os tamanhos
✅ Nenhum elemento fica cortado ou sobreposto
✅ Botões e formulários são acessíveis

---

## Teste 3: Atualizações em Tempo Real

### Objetivo
Verificar que as atualizações acontecem automaticamente.

### Passos

1. **Preparação**
   - Abra a mesma pré-ordem em duas abas
   - Aba 1: Cliente
   - Aba 2: Prestador

2. **Teste de Proposta**
   - Na aba do prestador, crie uma proposta
   - Aguarde 5-30 segundos
   - Verifique que a aba do cliente atualiza automaticamente
   - Verifique a notificação toast

3. **Teste de Aceitação**
   - Na aba do cliente, aceite a proposta
   - Aguarde 5-30 segundos
   - Verifique que a aba do prestador atualiza
   - Verifique a notificação toast

4. **Teste de Presença**
   - Mantenha ambas as abas abertas
   - Verifique o indicador "Outra parte visualizando"
   - Feche uma aba
   - Aguarde 1-2 minutos
   - Verifique que o indicador desaparece

5. **Teste de Atualização Manual**
   - Clique no botão "Atualizar" (ícone de sincronização)
   - Verifique que os dados são atualizados imediatamente

### Resultado Esperado
✅ Atualizações acontecem automaticamente (5-30s)
✅ Notificações toast aparecem para eventos importantes
✅ Indicador de presença funciona
✅ Botão de atualização manual funciona

---

## Teste 4: Validações de Formulário

### Objetivo
Verificar que as validações impedem dados inválidos.

### Passos

1. **Justificativa Curta**
   - Tente criar uma proposta com justificativa de 10 caracteres
   - Verifique que aparece erro
   - Mensagem esperada: "mínimo 50 caracteres"

2. **Valor Negativo**
   - Tente propor um valor negativo (ex: -100)
   - Verifique que aparece erro
   - Mensagem esperada: "valor inválido"

3. **Valor Muito Alto**
   - Tente propor um valor muito alto (ex: 999999)
   - Verifique o aviso de proposta extrema

4. **Data Passada**
   - Tente propor uma data de entrega no passado
   - Verifique que aparece erro
   - Mensagem esperada: "data deve ser futura"

5. **Proposta Sem Alterações**
   - Tente enviar proposta sem alterar nenhum campo
   - Verifique que aparece erro
   - Mensagem esperada: "altere pelo menos um campo"

6. **Cancelamento Sem Motivo**
   - Tente cancelar sem informar motivo
   - Verifique que aparece erro
   - Mensagem esperada: "motivo é obrigatório"

7. **Proposta Válida**
   - Preencha todos os campos corretamente
   - Verifique que a proposta é aceita

### Resultado Esperado
✅ Todas as validações funcionam
✅ Mensagens de erro são claras
✅ Formulários válidos são aceitos

---

## Teste 5: Histórico e Auditoria

### Objetivo
Verificar que todas as ações são registradas.

### Passos

1. **Realizar Várias Ações**
   - Crie uma proposta
   - Aceite a proposta
   - Aceite os termos
   - (Opcional) Cancele a pré-ordem

2. **Visualizar Histórico**
   - Role até a seção "Histórico de Negociação"
   - Verifique que todos os eventos aparecem
   - Verifique a ordem cronológica (mais recente primeiro)

3. **Verificar Detalhes dos Eventos**
   - Para cada evento, verifique:
     - Tipo de evento (ícone e cor)
     - Nome do ator
     - Data e hora
     - Descrição
     - Dados adicionais (valores, justificativas)

4. **Consultar via API**
   - Abra DevTools > Console
   - Execute: `fetch('/pre-ordem/1/historico').then(r => r.json()).then(console.log)`
   - Verifique o JSON retornado

### Resultado Esperado
✅ Todos os eventos são registrados
✅ Timeline é clara e organizada
✅ Detalhes dos eventos são completos
✅ API de histórico funciona

---

## Teste 6: Indicadores Visuais

### Objetivo
Verificar que os indicadores visuais funcionam corretamente.

### Passos

1. **Badge de Status**
   - Verifique a cor do badge:
     - Azul: Em Negociação
     - Amarelo: Aguardando Resposta
     - Ciano: Pronto para Conversão
     - Verde: Convertida
     - Vermelho: Cancelada
     - Cinza: Expirada

2. **Indicadores de Aceitação**
   - Antes de aceitar: Badge amarelo "Pendente"
   - Depois de aceitar: Badge verde "Aceitou"
   - Verifique para cliente e prestador

3. **Indicador de Proposta Pendente**
   - Quando há proposta: Card amarelo pulsante
   - Quando não há: Card oculto

4. **Alertas de Expiração**
   - Pré-ordem expirando em <24h: Alerta vermelho
   - Pré-ordem expirando em 1-3 dias: Alerta amarelo
   - Pré-ordem com >3 dias: Sem alerta

5. **Diferença de Valores**
   - Ao alterar valor no formulário:
     - Aumento: Seta vermelha para cima
     - Redução: Seta verde para baixo
     - Percentual calculado automaticamente

### Resultado Esperado
✅ Todos os indicadores são visíveis
✅ Cores e ícones são apropriados
✅ Animações funcionam (pulsação, transições)

---

## Checklist Final

Antes de considerar o teste completo, verifique:

- [ ] Navegação completa funciona sem erros
- [ ] Interface é responsiva em 3 tamanhos de tela
- [ ] Atualizações em tempo real funcionam
- [ ] Todas as validações impedem dados inválidos
- [ ] Histórico registra todas as ações
- [ ] Indicadores visuais são claros e corretos
- [ ] Notificações aparecem nos momentos certos
- [ ] Botões e formulários são intuitivos
- [ ] Performance é aceitável (carregamento <2s)
- [ ] Não há erros no console do navegador

---

## Problemas Comuns

### Atualização em tempo real não funciona
- Verifique se o servidor está rodando
- Verifique se há erros no console
- Tente o botão de atualização manual
- Verifique se o polling está ativo (fallback)

### Validações não aparecem
- Verifique se o JavaScript está carregado
- Abra DevTools > Console para ver erros
- Verifique se o arquivo `pre-ordem-interactions.js` está acessível

### Interface não é responsiva
- Limpe o cache do navegador (Ctrl+Shift+R)
- Verifique se o CSS está carregado
- Verifique se há erros de CSS no console

### Histórico não aparece
- Verifique se há eventos registrados no banco
- Verifique a rota `/pre-ordem/<id>/historico`
- Verifique se há erros no servidor

---

## Relatando Problemas

Se encontrar algum problema, anote:

1. **O que você estava fazendo**
2. **O que esperava que acontecesse**
3. **O que realmente aconteceu**
4. **Mensagens de erro** (se houver)
5. **Navegador e versão**
6. **Tamanho da tela**
7. **Screenshots** (se possível)

---

**Boa sorte com os testes!** 🚀

Se todos os testes passarem, a interface está pronta para produção.
