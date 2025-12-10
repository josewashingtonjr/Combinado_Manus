# Sistema de Confirmação Automática de Ordens

## Visão Geral

Após o prestador marcar o serviço como concluído, o cliente tem **36 horas** para:
- ✅ Confirmar que o serviço foi bem executado
- ⚠️ Contestar o serviço (se houver problemas)

**Se o cliente não responder em 36 horas, a ordem é automaticamente confirmada e os pagamentos são processados.**

## Fluxo Detalhado

### 1. Prestador Marca como Concluído
```
Prestador clica em "Marcar como Concluído"
↓
Status: aguardando_execucao → servico_executado
↓
completed_at = agora
confirmation_deadline = agora + 36 horas
↓
Cliente é notificado: "Você tem 36h para confirmar ou contestar"
```

### 2. Cliente Tem 3 Opções

#### Opção A: Confirmar Manualmente (Antes de 36h)
```
Cliente clica em "Confirmar Serviço"
↓
Status: servico_executado → concluida
↓
Pagamentos processados:
- Prestador recebe: valor - taxa plataforma
- Prestador recebe de volta: garantia (R$ 10)
- Cliente recebe de volta: garantia (R$ 10)
- Plataforma recebe: taxa (5% do valor)
```

#### Opção B: Contestar (Antes de 36h)
```
Cliente clica em "Contestar Serviço"
↓
Cliente adiciona provas e motivo
↓
Status: servico_executado → contestada
↓
Admin arbitra o caso
```

#### Opção C: Não Responder (Após 36h)
```
36 horas se passam sem resposta
↓
Job automático detecta ordem expirada
↓
Status: servico_executado → concluida (automático)
↓
Pagamentos processados automaticamente
↓
Ambas as partes são notificadas
```

## Avisos ao Cliente

### Imediatamente Após Conclusão
```
⏰ ATENÇÃO: Serviço Concluído!

O prestador marcou o serviço como concluído.

Você tem 36 HORAS para:
✅ Confirmar o serviço (se está tudo OK)
⚠️ Contestar o serviço (se houver problemas)

⚠️ IMPORTANTE: Se você não responder em 36 horas, 
o serviço será automaticamente confirmado e o 
pagamento será liberado para o prestador.

Prazo: [Data e Hora]
```

### Após 24 Horas (Lembrete)
```
⏰ LEMBRETE: Faltam 12 Horas!

Você ainda não confirmou o serviço:
"[Título do Serviço]"

Faltam apenas 12 HORAS para confirmação automática.

Por favor, confirme ou conteste o serviço antes de:
[Data e Hora]

[Botão: Confirmar Agora]
[Botão: Contestar]
```

### Após 36 Horas (Confirmação Automática)
```
✅ Serviço Confirmado Automaticamente

O serviço "[Título]" foi automaticamente confirmado 
pois o prazo de 36 horas expirou.

Pagamentos processados:
- Prestador recebeu: R$ [valor]
- Sua garantia foi devolvida: R$ 10,00

Obrigado por usar o Sistema Combinado!
```

## Job Automático

### Configuração
- **Frequência**: A cada hora
- **Script**: `jobs/auto_confirm_orders.py`
- **Log**: `logs/auto_confirm_orders.log`

### O Que o Job Faz
1. Busca ordens com status `servico_executado`
2. Verifica se `confirmation_deadline` foi ultrapassado
3. Para cada ordem expirada:
   - Muda status para `concluida`
   - Processa pagamentos automaticamente
   - Registra no histórico
   - Envia notificações

### Instalação do Cron Job
```bash
# Editar crontab
crontab -e

# Adicionar linha (executar a cada hora)
0 * * * * cd /home/ubuntu/projeto && /usr/bin/python3.11 jobs/auto_confirm_orders.py >> logs/cron_auto_confirm.log 2>&1

# Verificar instalação
crontab -l

# Ver logs
tail -f logs/cron_auto_confirm.log
```

### Execução Manual (Para Testes)
```bash
cd /home/ubuntu/projeto
python3.11 jobs/auto_confirm_orders.py
```

## Cálculo de Prazos

### Exemplo Prático
```
Prestador marca como concluído: 14/11/2025 10:00
↓
Prazo de confirmação: 16/11/2025 22:00 (36h depois)
↓
Lembrete enviado: 15/11/2025 10:00 (24h depois)
↓
Se cliente não responder até 16/11/2025 22:00:
→ Confirmação automática
```

### Fuso Horário
- Todos os cálculos usam UTC
- Conversão para horário local é feita na interface

## Segurança e Garantias

### Proteções Implementadas
1. ✅ Apenas o cliente pode confirmar ou contestar
2. ✅ Apenas o prestador pode marcar como concluído
3. ✅ Prazo de 36h é fixo e não pode ser alterado
4. ✅ Confirmação automática é irreversível
5. ✅ Todos os eventos são registrados em log
6. ✅ Transações são atômicas (tudo ou nada)

### Auditoria
- Todas as confirmações automáticas são registradas
- Logs incluem: ordem_id, cliente_id, prestador_id, timestamp
- Histórico de status é mantido

## Benefícios

### Para o Prestador
- ✅ Garantia de pagamento após 36h
- ✅ Não fica refém de cliente que não responde
- ✅ Processo transparente e automático

### Para o Cliente
- ✅ 36 horas para avaliar o serviço
- ✅ Lembretes para não esquecer
- ✅ Pode contestar se houver problemas

### Para a Plataforma
- ✅ Reduz disputas por falta de resposta
- ✅ Acelera o fluxo de pagamentos
- ✅ Melhora a experiência do usuário

## Monitoramento

### Métricas Importantes
- Número de confirmações automáticas por dia
- Tempo médio de resposta do cliente
- Taxa de contestações vs confirmações
- Ordens que chegam perto do prazo

### Alertas
- Se job falhar por 2 horas consecutivas
- Se taxa de confirmação automática > 50%
- Se houver erros no processamento de pagamentos

## FAQ

**P: O que acontece se o sistema estiver fora do ar quando o prazo expirar?**
R: O job roda a cada hora. Quando o sistema voltar, o job processará todas as ordens expiradas.

**P: O cliente pode contestar após a confirmação automática?**
R: Não. Após 36h, a ordem é finalizada e não pode mais ser contestada.

**P: O prestador pode cancelar após marcar como concluído?**
R: Não. Após marcar como concluído, apenas o cliente pode confirmar ou contestar.

**P: E se o cliente contestar no último minuto?**
R: A contestação interrompe o prazo e a ordem não será confirmada automaticamente.

**P: Como o cliente sabe que tem 36h?**
R: Recebe notificação imediata + lembrete após 24h + contador na interface.
