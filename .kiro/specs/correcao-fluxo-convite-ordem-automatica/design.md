# Design Document

## Overview

Este documento detalha o design da solução para corrigir o fluxo de aceitação de convites e criação automática de ordens de serviço. O problema atual é que quando ambas as partes (cliente e prestador) aceitam um convite, o sistema não está criando automaticamente a ordem de serviço nem bloqueando os valores necessários em escrow.

### Problema Atual

1. **Fluxo Quebrado**: Convites aceitos por ambas as partes não geram ordens automaticamente
2. **Bloqueio Manual**: Valores não são bloqueados em escrow automaticamente
3. **Dashboards Incompletas**: Ordens em aberto e fundos bloqueados não aparecem nas dashboards
4. **Falta de Notificações**: Usuários não são notificados quando ordens são criadas

### Solução Proposta

Implementar um sistema de aceitação mútua que:
- Detecta quando ambas as partes aceitaram o convite
- Cria automaticamente a ordem de serviço
- Bloqueia valores em escrow de forma atômica
- Atualiza dashboards em tempo real
- Envia notificações apropriadas

## Architecture

### Componentes Principais

1. **InviteAcceptanceCoordinator** (Novo)
   - Coordena o processo de aceitação mútua
   - Detecta quando ambas as partes aceitaram
   - Orquestra a criação da ordem e bloqueio de valores

2. **OrderCreationService** (Atualização)
   - Método específico para criação a partir de convite aceito
   - Validação de saldos antes da criação
   - Bloqueio atômico de valores

3. **DashboardDataService** (Novo)
   - Agrega dados de ordens em aberto
   - Calcula fundos bloqueados por usuário
   - Fornece dados para visualização em tempo real

4. **NotificationService** (Atualização)
   - Notificações de criação de ordem
   - Alertas de saldo insuficiente
   - Atualizações de status

### Fluxo de Dados

```
Convite Criado → Prestador Aceita → Cliente Aceita → 
InviteAcceptanceCoordinator detecta aceitação mútua →
Valida saldos → Cria Ordem → Bloqueia Valores →
Atualiza Convite → Notifica Partes → Atualiza Dashboards
```

## Components and Interfaces

### 1. InviteAcceptanceCoordinator

Novo serviço responsável por coordenar a aceitação mútua de convites.


**Métodos:**

```python
class InviteAcceptanceCoordinator:
    @staticmethod
    def process_acceptance(invite_id, accepting_user_id, acceptance_type):
        """
        Processa aceitação de convite e verifica se ambas as partes aceitaram
        
        Args:
            invite_id: ID do convite
            accepting_user_id: ID do usuário aceitando
            acceptance_type: 'client' ou 'provider'
            
        Returns:
            dict com status e detalhes da operação
        """
        
    @staticmethod
    def check_mutual_acceptance(invite):
        """
        Verifica se ambas as partes aceitaram o convite
        
        Returns:
            (bool, str): (aceito_mutuamente, mensagem)
        """
        
    @staticmethod
    def create_order_from_mutual_acceptance(invite):
        """
        Cria ordem quando há aceitação mútua
        
        Fluxo:
        1. Valida saldos de ambas as partes
        2. Cria ordem de serviço
        3. Bloqueia valores em escrow atomicamente
        4. Atualiza status do convite
        5. Envia notificações
        """
```

### 2. Modelo Invite - Novos Campos

Adicionar campos para rastrear aceitação de ambas as partes:

```python
class Invite(db.Model):
    # Campos existentes...
    
    # Novos campos para aceitação mútua
    client_accepted = db.Column(db.Boolean, default=False)
    client_accepted_at = db.Column(db.DateTime, nullable=True)
    provider_accepted = db.Column(db.Boolean, default=False)
    provider_accepted_at = db.Column(db.DateTime, nullable=True)
    
    @property
    def is_mutually_accepted(self):
        """Verifica se ambas as partes aceitaram"""
        return self.client_accepted and self.provider_accepted
    
    @property
    def pending_acceptance_from(self):
        """Retorna quem ainda precisa aceitar"""
        if not self.client_accepted:
            return 'client'
        if not self.provider_accepted:
            return 'provider'
        return None
```

### 3. DashboardDataService

Novo serviço para agregar dados das dashboards:

```python
class DashboardDataService:
    @staticmethod
    def get_open_orders(user_id, role):
        """
        Retorna ordens em aberto para o usuário
        
        Args:
            user_id: ID do usuário
            role: 'cliente' ou 'prestador'
            
        Returns:
            list: Ordens com status aceita, em_andamento ou aguardando_confirmacao
        """
        
    @staticmethod
    def get_blocked_funds_summary(user_id):
        """
        Retorna resumo de fundos bloqueados
        
        Returns:
            dict: {
                'total_blocked': Decimal,
                'by_order': [{'order_id', 'amount', 'title'}]
            }
        """
        
    @staticmethod
    def get_dashboard_metrics(user_id, role):
        """
        Retorna todas as métricas para a dashboard
        
        Inclui:
        - Saldo disponível e bloqueado
        - Ordens em aberto
        - Estatísticas do mês
        - Alertas e notificações
        """
```

### 4. Atualização do InviteService

Modificar métodos de aceitação para usar o coordenador:

```python
class InviteService:
    @staticmethod
    def accept_invite_as_client(invite_id, client_id):
        """Cliente aceita o convite"""
        invite = Invite.query.get(invite_id)
        
        # Validar que é o cliente correto
        if invite.client_id != client_id:
            raise ValueError("Usuário não autorizado")
        
        # Validar saldo suficiente
        required_amount = invite.current_value + CONTESTATION_FEE
        if not WalletService.has_sufficient_balance(client_id, required_amount):
            raise ValueError("Saldo insuficiente")
        
        # Marcar aceitação do cliente
        invite.client_accepted = True
        invite.client_accepted_at = datetime.utcnow()
        db.session.commit()
        
        # Processar através do coordenador
        return InviteAcceptanceCoordinator.process_acceptance(
            invite_id, client_id, 'client'
        )
    
    @staticmethod
    def accept_invite_as_provider(invite_id, provider_id):
        """Prestador aceita o convite"""
        invite = Invite.query.get(invite_id)
        
        # Validar que é o prestador correto
        provider = User.query.get(provider_id)
        if provider.phone != invite.invited_phone:
            raise ValueError("Usuário não autorizado")
        
        # Validar saldo suficiente para taxa
        if not WalletService.has_sufficient_balance(provider_id, CONTESTATION_FEE):
            raise ValueError("Saldo insuficiente para taxa de contestação")
        
        # Marcar aceitação do prestador
        invite.provider_accepted = True
        invite.provider_accepted_at = datetime.utcnow()
        db.session.commit()
        
        # Processar através do coordenador
        return InviteAcceptanceCoordinator.process_acceptance(
            invite_id, provider_id, 'provider'
        )
```

### 5. Atualização das Rotas

Modificar rotas de aceitação para usar novos métodos:

```python
# routes/cliente_routes.py
@cliente_bp.route('/convites/<int:invite_id>/aceitar', methods=['POST'])
@login_required
def aceitar_convite(invite_id):
    user = AuthService.get_current_user()
    
    try:
        result = InviteService.accept_invite_as_client(invite_id, user.id)
        
        if result['order_created']:
            flash(f'Convite aceito! Ordem #{result["order_id"]} criada automaticamente.', 'success')
        else:
            flash(f'Convite aceito! Aguardando aceitação do prestador.', 'info')
            
        return redirect(url_for('cliente.convites'))
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('cliente.ver_convite', invite_id=invite_id))

# routes/prestador_routes.py
@prestador_bp.route('/convites/<token>/aceitar', methods=['POST'])
@login_required
def aceitar_convite(token):
    user = AuthService.get_current_user()
    
    try:
        invite = InviteService.get_invite_by_token(token)
        result = InviteService.accept_invite_as_provider(invite.id, user.id)
        
        if result['order_created']:
            flash(f'Convite aceito! Ordem #{result["order_id"]} criada automaticamente.', 'success')
        else:
            flash(f'Convite aceito! Aguardando aceitação do cliente.', 'info')
            
        return redirect(url_for('prestador.convites'))
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('prestador.ver_convite', token=token))
```

## Data Models

### Alterações no Modelo Invite

```python
# Adicionar campos de aceitação mútua
client_accepted = db.Column(db.Boolean, default=False, nullable=False)
client_accepted_at = db.Column(db.DateTime, nullable=True)
provider_accepted = db.Column(db.Boolean, default=False, nullable=False)
provider_accepted_at = db.Column(db.DateTime, nullable=True)

# Índices para performance
__table_args__ = (
    db.Index('idx_invite_mutual_acceptance', 'client_accepted', 'provider_accepted', 'status'),
    # ... outros índices existentes
)
```

### Sem Alterações no Modelo Order

O modelo Order já possui todos os campos necessários. Apenas garantir que:
- `invite_id` está sendo preenchido corretamente
- `provider_id` é definido na criação
- `status` inicial é 'aceita' (não 'disponivel')

## Error Handling

### Cenários de Erro e Tratamento

1. **Saldo Insuficiente do Cliente**
   - Detectar antes da aceitação
   - Mensagem clara: "Saldo insuficiente. Necessário: R$ X.XX (serviço + taxa). Atual: R$ Y.YY"
   - Sugerir adicionar saldo

2. **Saldo Insuficiente do Prestador**
   - Detectar antes da aceitação
   - Mensagem clara: "Saldo insuficiente para taxa de contestação. Necessário: R$ X.XX. Atual: R$ Y.YY"
   - Sugerir adicionar saldo

3. **Falha na Criação da Ordem**
   - Rollback completo da transação
   - Manter convite como aceito por ambas as partes
   - Registrar erro em log
   - Notificar administrador

4. **Falha no Bloqueio de Valores**
   - Rollback da criação da ordem
   - Reverter status do convite
   - Mensagem de erro técnico
   - Permitir retry

5. **Convite Expirado**
   - Impedir aceitação
   - Mensagem: "Este convite expirou"
   - Sugerir criar novo convite

### Estratégia de Rollback

```python
def create_order_from_mutual_acceptance(invite):
    try:
        # Iniciar transação
        db.session.begin_nested()
        
        # 1. Criar ordem
        order = Order(...)
        db.session.add(order)
        db.session.flush()
        
        # 2. Bloquear valores
        WalletService.transfer_to_escrow(client_id, value, order.id)
        WalletService.transfer_to_escrow(provider_id, fee, order.id)
        
        # 3. Atualizar convite
        invite.status = 'convertido'
        invite.order_id = order.id
        
        # Commit da transação
        db.session.commit()
        
        # 4. Enviar notificações (fora da transação)
        NotificationService.notify_order_created(order.id)
        
        return {'success': True, 'order_id': order.id}
        
    except InsufficientBalanceError as e:
        db.session.rollback()
        raise ValueError(f"Saldo insuficiente: {str(e)}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar ordem: {str(e)}")
        raise
```

## Testing Strategy

### Testes Unitários

1. **InviteAcceptanceCoordinator**
   - `test_detect_mutual_acceptance`
   - `test_create_order_on_mutual_acceptance`
   - `test_insufficient_balance_client`
   - `test_insufficient_balance_provider`
   - `test_rollback_on_error`

2. **DashboardDataService**
   - `test_get_open_orders_cliente`
   - `test_get_open_orders_prestador`
   - `test_get_blocked_funds_summary`
   - `test_dashboard_metrics_calculation`

3. **InviteService Updates**
   - `test_accept_as_client`
   - `test_accept_as_provider`
   - `test_mutual_acceptance_triggers_order`
   - `test_validation_before_acceptance`

### Testes de Integração

1. **Fluxo Completo de Aceitação**
   ```python
   def test_complete_acceptance_flow():
       # 1. Cliente cria convite
       # 2. Prestador aceita
       # 3. Cliente aceita
       # 4. Verificar ordem criada
       # 5. Verificar valores bloqueados
       # 6. Verificar dashboards atualizadas
   ```

2. **Fluxo com Saldo Insuficiente**
   ```python
   def test_insufficient_balance_flow():
       # 1. Cliente com saldo baixo
       # 2. Tentar aceitar convite
       # 3. Verificar erro apropriado
       # 4. Adicionar saldo
       # 5. Aceitar com sucesso
   ```

3. **Fluxo de Rollback**
   ```python
   def test_rollback_on_escrow_failure():
       # 1. Simular falha no bloqueio de escrow
       # 2. Verificar rollback da ordem
       # 3. Verificar convite ainda aceito
       # 4. Verificar possibilidade de retry
   ```

### Testes de UI

1. **Dashboard do Cliente**
   - Verificar exibição de ordens em aberto
   - Verificar exibição de fundos bloqueados
   - Verificar atualização em tempo real

2. **Dashboard do Prestador**
   - Verificar exibição de ordens em aberto
   - Verificar exibição de fundos bloqueados
   - Verificar ações disponíveis

3. **Fluxo de Aceitação**
   - Verificar mensagens de feedback
   - Verificar redirecionamentos
   - Verificar notificações

## Implementation Notes

### Ordem de Implementação

1. **Fase 1: Modelo e Migração**
   - Adicionar campos ao modelo Invite
   - Criar migração de banco de dados
   - Testar migração

2. **Fase 2: Serviços Core**
   - Implementar InviteAcceptanceCoordinator
   - Atualizar InviteService
   - Implementar DashboardDataService

3. **Fase 3: Rotas e Controllers**
   - Atualizar rotas de aceitação
   - Adicionar validações
   - Implementar tratamento de erros

4. **Fase 4: Templates e UI**
   - Atualizar dashboards
   - Adicionar visualização de fundos bloqueados
   - Implementar atualizações em tempo real

5. **Fase 5: Notificações**
   - Implementar notificações de criação de ordem
   - Adicionar alertas de saldo insuficiente
   - Configurar notificações em tempo real

6. **Fase 6: Testes**
   - Testes unitários
   - Testes de integração
   - Testes de UI

### Considerações de Performance

1. **Índices de Banco de Dados**
   - Índice composto em (client_accepted, provider_accepted, status)
   - Índice em order_id para joins rápidos

2. **Caching**
   - Cache de dados de dashboard (30 segundos)
   - Cache de fundos bloqueados por usuário

3. **Queries Otimizadas**
   - Usar joins em vez de queries separadas
   - Limitar resultados com paginação
   - Usar select_related para relacionamentos

### Segurança

1. **Validação de Autorização**
   - Verificar que usuário é o cliente correto
   - Verificar que usuário é o prestador correto
   - Impedir aceitação duplicada

2. **Validação de Saldo**
   - Sempre validar antes de aceitar
   - Usar transações atômicas
   - Prevenir race conditions

3. **Auditoria**
   - Registrar todas as aceitações
   - Registrar criação de ordens
   - Registrar bloqueios de valores

## Diagrams

### Diagrama de Sequência - Aceitação Mútua

```
Cliente                 Sistema                 Prestador
  |                       |                        |
  |-- Aceita Convite ---->|                        |
  |                       |-- Valida Saldo ------->|
  |                       |-- Marca Aceitação ---->|
  |                       |-- Verifica Mútua ----->|
  |<-- Aguardando --------|                        |
  |                       |                        |
  |                       |<-- Aceita Convite -----|
  |                       |-- Valida Saldo ------->|
  |                       |-- Marca Aceitação ---->|
  |                       |-- Verifica Mútua ----->|
  |                       |-- AMBOS ACEITARAM ---->|
  |                       |                        |
  |                       |-- Cria Ordem --------->|
  |                       |-- Bloqueia Valores --->|
  |                       |-- Atualiza Convite --->|
  |                       |                        |
  |<-- Ordem Criada ------|-- Ordem Criada ------->|
  |<-- Notificação -------|-- Notificação -------->|
```

### Diagrama de Estados do Convite

```
[Pendente] 
    |
    |--> Cliente Aceita --> [Cliente Aceitou]
    |                            |
    |--> Prestador Aceita --> [Prestador Aceitou]
                                 |
                                 v
                    [Ambos Aceitaram] --> Cria Ordem
                                 |
                                 v
                           [Convertido]
```

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────┐
│              Camada de Apresentação              │
│  ┌──────────────┐         ┌──────────────┐     │
│  │  Dashboard   │         │  Dashboard   │     │
│  │   Cliente    │         │  Prestador   │     │
│  └──────────────┘         └──────────────┘     │
└─────────────────────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────┐
│              Camada de Rotas                     │
│  ┌──────────────┐         ┌──────────────┐     │
│  │ cliente_bp   │         │prestador_bp  │     │
│  └──────────────┘         └──────────────┘     │
└─────────────────────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────┐
│           Camada de Serviços                     │
│  ┌──────────────────────────────────────┐       │
│  │  InviteAcceptanceCoordinator         │       │
│  └──────────────────────────────────────┘       │
│  ┌──────────────┐  ┌─────────────────┐         │
│  │InviteService │  │DashboardDataSvc │         │
│  └──────────────┘  └─────────────────┘         │
│  ┌──────────────┐  ┌─────────────────┐         │
│  │ OrderService │  │  WalletService  │         │
│  └──────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────┐
│              Camada de Dados                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │
│  │ Invite │ │ Order  │ │ Wallet │ │Transaction│ │
│  └────────┘ └────────┘ └────────┘ └────────┘  │
└─────────────────────────────────────────────────┘
```
