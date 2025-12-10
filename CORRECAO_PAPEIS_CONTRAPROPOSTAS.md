# Correção de Papéis em Contrapropostas

## Problema Identificado

Quando um usuário fazia uma contraproposta em um convite, ao reabrir o convite de contraproposta, o sistema estava exibindo a view incorreta:

- **Cliente** ao reabrir contraproposta → estava sendo direcionado para view do **prestador**
- **Prestador** ao reabrir contraproposta → estava sendo direcionado para view do **cliente**

## Causa Raiz

A lógica de criação de contrapropostas estava **correta** - sempre mantinha:
- `client_id` = quem vai pagar (sempre o cliente original)
- `invited_phone` = quem vai executar (sempre o prestador original)

O problema estava nas **rotas de visualização** (`ver_convite`), que não verificavam corretamente se o usuário logado era o cliente ou o prestador do convite antes de exibir a view apropriada.

## Solução Implementada

### 1. Rota do Cliente (`routes/cliente_routes.py`)

```python
@cliente_bp.route('/convites/<int:invite_id>')
@login_required
def ver_convite(invite_id):
    """Ver detalhes de um convite específico"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        from models import Invite, Proposal
        invite = Invite.query.get_or_404(invite_id)
        
        # Verificar se o convite pertence ao cliente
        # O cliente é sempre o client_id, independente de ser contraproposta ou não
        if invite.client_id != user.id:
            # Se o usuário não é o cliente, verificar se ele é o prestador
            # Nesse caso, redirecionar para a view do prestador
            if 'prestador' in user.roles and invite.invited_phone == user.phone:
                flash('Este convite deve ser visualizado na área do prestador.', 'info')
                return redirect(url_for('prestador.ver_convite', token=invite.token))
            
            flash('Convite não encontrado.', 'error')
            return redirect(url_for('cliente.convites'))
        
        # ... resto do código
```

### 2. Rota do Prestador (`routes/prestador_routes.py`)

```python
@prestador_bp.route('/convites/<token>')
@user_loader_required
def ver_convite(user, token):
    """Ver detalhes de um convite específico"""
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        invite = InviteService.get_invite_by_token(token)
        
        # Verificar se o convite é para este prestador OU se ele tem o token na sessão
        has_session_token = session.get('invite_token') == token
        is_invited_phone = invite.invited_phone == user.phone
        
        # Verificar se o usuário é o cliente do convite
        # Se for, redirecionar para a view do cliente
        if 'cliente' in user.roles and invite.client_id == user.id:
            flash('Este convite deve ser visualizado na área do cliente.', 'info')
            return redirect(url_for('cliente.ver_convite', invite_id=invite.id))
        
        # ... resto do código
```

## Fluxo Correto de Contrapropostas

### Cenário 1: Cliente cria convite → Prestador faz contraproposta

1. **Cliente cria convite original**
   - `client_id` = Cliente
   - `invited_phone` = Prestador
   - Cliente vê na lista de "enviados"
   - Prestador vê na lista de "recebidos"

2. **Prestador faz contraproposta**
   - Convite original é recusado
   - Novo convite é criado:
     - `client_id` = Cliente (mantém)
     - `invited_phone` = Prestador (mantém)
     - Marcado como contraproposta (🔄 no título)
   - Cliente vê na lista de "enviados"
   - Prestador vê na lista de "recebidos"

3. **Cliente reabre contraproposta**
   - Sistema verifica: `invite.client_id == user.id` ✅
   - Exibe view do **cliente** ✅

### Cenário 2: Prestador faz contraproposta → Cliente faz nova contraproposta

1. **Cliente faz nova contraproposta**
   - Convite anterior é recusado
   - Novo convite é criado:
     - `client_id` = Cliente (mantém)
     - `invited_phone` = Prestador (mantém)
     - Marcado como contraproposta
   - Cliente vê na lista de "enviados"
   - Prestador vê na lista de "recebidos"

2. **Prestador reabre contraproposta**
   - Sistema verifica: `invite.invited_phone == user.phone` ✅
   - Exibe view do **prestador** ✅

## Regras de Negócio Mantidas

1. **Cliente** sempre é o `client_id` (quem vai pagar)
2. **Prestador** sempre é o `invited_phone` (quem vai executar)
3. **Contrapropostas** mantêm os papéis originais
4. **Cliente** vê todos os convites na lista de "enviados"
5. **Prestador** vê todos os convites na lista de "recebidos"
6. **Redirecionamento automático** para a view correta baseado no papel do usuário

## Teste de Validação

Foi criado o teste `test_counter_proposal_role_fix.py` que valida:

✅ Cliente cria convite original
✅ Prestador faz contraproposta
✅ Cliente faz nova contraproposta
✅ Papéis são mantidos corretamente em todas as etapas
✅ Listagem de convites funciona corretamente para ambos os papéis
✅ Redirecionamento para view correta baseado no papel

## Resultado

Agora, independente de quantas contrapropostas sejam feitas:

- **Cliente** sempre vê a view do cliente ao abrir qualquer convite onde ele é o `client_id`
- **Prestador** sempre vê a view do prestador ao abrir qualquer convite onde ele é o `invited_phone`
- Sistema redireciona automaticamente se o usuário tentar acessar pela rota errada
- Usuários com papéis duplos (cliente + prestador) são redirecionados para a view apropriada

## Correções Adicionais

### Problema 2: Cliente criando contraproposta era redirecionado para área do prestador

**Causa:** A rota `propor_alteracao` em `routes/proposal_routes.py` verificava apenas se o usuário era prestador, impedindo que clientes criassem contrapropostas ou redirecionando incorretamente.

**Solução:** 
- Permitir que tanto cliente quanto prestador criem contrapropostas
- Redirecionar para a área correta baseado no papel do usuário:
  - Se cliente cria contraproposta → redireciona para `cliente.convites`
  - Se prestador cria contraproposta → redireciona para `prestador.convites`

```python
# Determinar papel do usuário para redirecionamento
from models import Invite
original_invite = Invite.query.get(invite_id)
is_client = original_invite and original_invite.client_id == user.id

# Redirecionar para a área correta
if is_client:
    return redirect(url_for('cliente.convites'))
else:
    return redirect(url_for('prestador.convites'))
```

### Problema 3: Botão de copiar link em contrapropostas

**Solução:** Os templates já estavam corretos:
- `templates/cliente/ver_convite.html` - Botão de link só aparece para convites originais (`{% if not invite.is_counter_proposal %}`)
- `templates/cliente/convites.html` - Botão de copiar link só aparece para convites originais na listagem
- Contrapropostas não precisam de link pois vão automaticamente para quem enviou

## Arquivos Modificados

1. `routes/cliente_routes.py` - Adicionada verificação de papel e redirecionamento
2. `routes/prestador_routes.py` - Adicionada verificação de papel e redirecionamento
3. `routes/proposal_routes.py` - Permitir cliente criar contrapropostas e redirecionar corretamente
4. `test_counter_proposal_role_fix.py` - Teste de validação criado

### Problema 4: Criador de contraproposta podia aceitar/recusar/cancelar a própria contraproposta

**Causa:** Não havia verificação para impedir que quem criou a contraproposta pudesse aceitar, recusar ou cancelar a própria proposta.

**Solução:** 
- Adicionado método `was_counter_proposal_created_by_client()` no modelo `Invite` para identificar quem criou a contraproposta
- Adicionado método `can_user_accept_counter_proposal(user_id)` para verificar se o usuário pode aceitar/recusar/cancelar
- Atualizado templates para desabilitar botões de aceitar/recusar/cancelar quando o usuário é o criador da contraproposta
- Exibir mensagem "Aguardando Resposta" quando o usuário criou a contraproposta

**Regra:** Quem cria a contraproposta **NÃO pode** aceitar, recusar ou cancelar - deve aguardar a outra parte responder.

**Botões desabilitados para o criador:**
- ❌ Aceitar Convite/Contraproposta
- ❌ Recusar Convite/Contraproposta  
- ❌ Cancelar Proposta
- ✅ Fazer Nova Contraproposta (permitido)

```python
def can_user_accept_counter_proposal(self, user_id):
    """
    Verifica se o usuário pode aceitar esta contraproposta
    Usuário NÃO pode aceitar se ele mesmo criou a contraproposta
    """
    if not self.is_counter_proposal:
        return True  # Não é contraproposta, pode aceitar normalmente
    
    # Verificar quem criou a contraproposta
    created_by_client = self.was_counter_proposal_created_by_client()
    
    # Se cliente criou, cliente NÃO pode aceitar
    if created_by_client and self.client_id == user_id:
        return False
    
    # Se prestador criou, prestador NÃO pode aceitar
    if not created_by_client and user.phone == self.invited_phone:
        return False
    
    return True
```

### Problema 5: Botões duplicados na listagem de convites do prestador

**Causa:** Havia dois botões ("Ver Detalhes" e "Responder") que faziam exatamente a mesma coisa.

**Solução:** 
- Removido botão duplicado "Responder"
- Mantido apenas "Ver Detalhes e Responder" (verde quando pendente, cinza quando finalizado)
- Interface mais limpa e intuitiva

## Arquivos Modificados

1. `routes/cliente_routes.py` - Adicionada verificação de papel e redirecionamento
2. `routes/prestador_routes.py` - Adicionada verificação de papel e redirecionamento
3. `routes/proposal_routes.py` - Permitir cliente criar contrapropostas e redirecionar corretamente
4. `models.py` - Adicionados métodos para identificar criador e verificar permissão de aceite/cancelamento
5. `templates/cliente/ver_convite.html` - Desabilitar botões quando cliente criou a contraproposta
6. `templates/prestador/ver_convite.html` - Desabilitar botões (aceitar/recusar/cancelar) quando prestador criou a contraproposta
7. `templates/prestador/convites.html` - Removido botão duplicado "Responder"
8. `test_counter_proposal_role_fix.py` - Teste de validação de papéis
9. `test_counter_proposal_accept_block.py` - Teste de validação de bloqueio de aceite
10. `test_counter_proposal_cancel_block.py` - Teste de validação de bloqueio de cancelamento

## Data da Correção

14 de novembro de 2025
