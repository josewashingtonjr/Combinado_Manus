# Especificação: Sistema de Gestão de Ordens de Serviço

## Visão Geral
Sistema completo de gerenciamento de ordens com 3 fluxos principais: execução normal, cancelamento e contestação.

## Estados da Ordem

### 1. Estados Principais
- `aguardando_execucao` - Ordem criada, aguardando prestador executar
- `servico_executado` - Prestador marcou como concluído, aguardando confirmação do cliente
- `concluida` - Cliente confirmou, pagamento liberado
- `cancelada` - Ordem cancelada por uma das partes
- `contestada` - Cliente contestou o serviço, aguardando arbitragem do admin
- `resolvida` - Contestação resolvida pelo admin

## Fluxo 1: Execução Normal

### Passo 1: Ordem Criada (aguardando_execucao)
- Status inicial após conversão do convite
- Valores bloqueados em escrow:
  - Cliente: valor do serviço + taxa de contestação
  - Prestador: taxa de contestação (garantia)
- Prestador deve executar o serviço até a data combinada

### Passo 2: Serviço Executado (servico_executado)
- Prestador clica em "Marcar como Concluído"
- Status muda para `servico_executado`
- **Cliente tem 36 horas para confirmar ou contestar**
- **IMPORTANTE**: Após 36h sem resposta, a ordem é automaticamente confirmada
- Botões disponíveis para cliente:
  - ✅ Confirmar Serviço
  - ⚠️ Contestar Serviço
- Cliente deve ser notificado sobre o prazo de 36h

### Passo 3: Serviço Confirmado (concluida)
- Cliente confirma que o serviço foi bem executado
- Pagamentos liberados:
  - Prestador recebe: valor do serviço - taxa da plataforma
  - Prestador recebe de volta: taxa de contestação (garantia)
  - Cliente recebe de volta: taxa de contestação
- Status final: `concluida`

## Fluxo 2: Cancelamento

### Cancelamento pelo Prestador (antes de marcar como concluído)
- Prestador pode cancelar se houver imprevisto
- Multa aplicada: % definida pelo admin (ex: 10% do valor do serviço)
- Distribuição da multa:
  - 50% para a plataforma
  - 50% para o cliente (parte prejudicada)
- Valores devolvidos:
  - Cliente recebe: valor do serviço + taxa de contestação + 50% da multa
  - Prestador perde: taxa de contestação + multa

### Cancelamento pelo Cliente (antes do prestador marcar como concluído)
- Cliente pode cancelar antes da execução
- Multa aplicada: % definida pelo admin (ex: 10% do valor do serviço)
- Distribuição da multa:
  - 50% para a plataforma
  - 50% para o prestador (parte prejudicada)
- Valores devolvidos:
  - Prestador recebe: taxa de contestação + 50% da multa
  - Cliente perde: multa (deduzida do valor bloqueado)

### Regras de Cancelamento
- Apenas possível antes do prestador marcar como concluído
- Após marcar como concluído, só é possível contestar
- Multa é calculada sobre o valor do serviço
- Multa mínima e máxima definidas pelo admin

## Fluxo 3: Contestação

### Abertura de Contestação
- Cliente pode contestar após prestador marcar como concluído
- **Prazo para contestar: 36 horas após conclusão**
- **Após 36h, ordem é automaticamente confirmada**
- Cliente deve:
  - Descrever o motivo da contestação
  - Anexar provas (imagens, textos, áudios)
  - Pagar taxa de contestação (já bloqueada)
- Status muda para: `contestada`

### Arbitragem pelo Admin
- Admin analisa as provas de ambas as partes
- Admin pode solicitar informações adicionais
- Admin toma decisão final

### Decisão a Favor do Cliente
- Cliente ganha a contestação
- Pagamentos:
  - Cliente recebe de volta: valor do serviço
  - Cliente perde: taxa de contestação (vai para plataforma)
  - Prestador não recebe: valor do serviço
  - Prestador perde: taxa de contestação (garantia)
- Status final: `resolvida`

### Decisão a Favor do Prestador
- Prestador ganha a contestação
- Pagamentos:
  - Prestador recebe: valor do serviço - taxa da plataforma
  - Prestador recebe de volta: taxa de contestação (garantia)
  - Cliente perde: valor do serviço + taxa de contestação
- Status final: `resolvida`

## Taxas e Valores Bloqueados

### No Momento da Criação da Ordem
```
Cliente bloqueia:
- Valor do serviço
- Taxa de contestação (R$ 10,00)
- Taxa de cancelamento (% do valor, ex: 10%)

Prestador bloqueia:
- Taxa de contestação (R$ 10,00) - garantia
- Taxa de cancelamento (% do valor, ex: 10%)
```

### Configurações do Admin
- Taxa da plataforma: % sobre o valor do serviço (ex: 5%)
- Taxa de contestação: valor fixo (ex: R$ 10,00)
- Taxa de cancelamento: % sobre o valor do serviço (ex: 10%)
- **Prazo para confirmação/contestação: 36 horas (fixo)**
- Após 36h sem resposta: confirmação automática

## Dashboard de Ordens

### Visão do Cliente
- Minhas Ordens
- Filtros: Todas, Aguardando, Em Execução, Concluídas, Canceladas, Contestadas
- Ações disponíveis por status:
  - `aguardando_execucao`: Cancelar (com multa)
  - `servico_executado`: Confirmar ou Contestar
  - `contestada`: Ver detalhes da contestação

### Visão do Prestador
- Minhas Ordens
- Filtros: Todas, Aguardando, Em Execução, Concluídas, Canceladas, Contestadas
- Ações disponíveis por status:
  - `aguardando_execucao`: Marcar como Concluído ou Cancelar (com multa)
  - `servico_executado`: Aguardar confirmação do cliente
  - `contestada`: Adicionar provas/resposta

### Visão do Admin
- Todas as Ordens
- Filtros especiais: Contestações Pendentes, Cancelamentos
- Ações:
  - Arbitrar contestações
  - Ver histórico completo
  - Ajustar configurações de taxas

## Notificações

### Eventos que Geram Notificações
1. Ordem criada → Notificar ambas as partes
2. **Serviço marcado como concluído → Notificar cliente (URGENTE: 36h para responder)**
3. **Lembrete após 24h → Notificar cliente (faltam 12h para confirmação automática)**
4. **Confirmação automática → Notificar ambas as partes**
5. Serviço confirmado manualmente → Notificar prestador
6. Ordem cancelada → Notificar parte prejudicada
7. Contestação aberta → Notificar admin e prestador
8. Contestação resolvida → Notificar ambas as partes

## Campos Adicionais no Modelo Order

```python
# Campos de cancelamento
cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
cancelled_at = db.Column(db.DateTime, nullable=True)
cancellation_reason = db.Column(db.Text, nullable=True)
cancellation_fee = db.Column(db.Numeric(10, 2), nullable=True)

# Campos de contestação
dispute_evidence = db.Column(db.JSON, nullable=True)  # Array de URLs de provas
dispute_client_statement = db.Column(db.Text, nullable=True)
dispute_provider_response = db.Column(db.Text, nullable=True)
dispute_admin_notes = db.Column(db.Text, nullable=True)
dispute_winner = db.Column(db.String(20), nullable=True)  # 'client' ou 'provider'

# Campos de prazos
service_deadline = db.Column(db.DateTime, nullable=False)  # Data de entrega
confirmation_deadline = db.Column(db.DateTime, nullable=True)  # Prazo para confirmar
dispute_deadline = db.Column(db.DateTime, nullable=True)  # Prazo para contestar

# Campos de valores
platform_fee = db.Column(db.Numeric(10, 2), nullable=True)
contestation_fee = db.Column(db.Numeric(10, 2), nullable=True)
cancellation_fee_percentage = db.Column(db.Numeric(5, 2), nullable=True)
```

## Sistema de Confirmação Automática

### Job Automático (Cron)
- Executar a cada hora
- Buscar ordens com status `servico_executado`
- Verificar se `confirmation_deadline` foi ultrapassado (36h)
- Se sim:
  - Mudar status para `concluida`
  - Processar pagamentos automaticamente
  - Enviar notificações para ambas as partes
  - Registrar no histórico: "Confirmação automática após 36h"

### Cálculo do Prazo
```python
# Quando prestador marca como concluído
completed_at = datetime.utcnow()
confirmation_deadline = completed_at + timedelta(hours=36)
dispute_deadline = confirmation_deadline  # Mesmo prazo
```

### Avisos ao Cliente
1. **Imediatamente após conclusão**: "Você tem 36 horas para confirmar ou contestar"
2. **Após 24 horas**: "Faltam 12 horas para confirmação automática"
3. **Após 36 horas**: "Ordem confirmada automaticamente"

## Próximos Passos de Implementação

1. ✅ Atualizar modelo Order com novos campos
2. ✅ Criar migrations
3. ✅ Implementar serviço de gestão de ordens (OrderManagementService)
4. ✅ Implementar job de confirmação automática
5. ✅ Criar rotas para ações de ordem
6. ✅ Criar templates de dashboard de ordens
7. ✅ Implementar sistema de upload de provas
8. ✅ Criar painel de arbitragem para admin
9. ✅ Implementar sistema de notificações
10. ✅ Testes de integração
