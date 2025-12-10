# Jobs Agendados - Sistema de Pré-Ordens

Este diretório contém jobs agendados para manutenção automática do sistema.

## Job de Expiração de Pré-Ordens

O job `expire_pre_orders.py` é responsável por:

1. **Notificar pré-ordens próximas da expiração** (24h antes)
2. **Marcar pré-ordens expiradas automaticamente**
3. **Enviar notificações** para ambas as partes

### Configuração com Cron (Linux/Mac)

Para executar o job a cada hora, adicione ao crontab:

```bash
# Editar crontab
crontab -e

# Adicionar linha (executar a cada hora)
0 * * * * cd /caminho/para/projeto && /caminho/para/.venv/bin/python jobs/expire_pre_orders.py >> logs/expire_pre_orders.log 2>&1
```

### Configuração com APScheduler (Recomendado)

Para integrar com a aplicação Flask, adicione ao `app.py`:

```python
from apscheduler.schedulers.background import BackgroundScheduler
from jobs.expire_pre_orders import PreOrderExpirationJob

# Criar scheduler
scheduler = BackgroundScheduler()

# Adicionar job para executar a cada hora
scheduler.add_job(
    func=lambda: PreOrderExpirationJob.run(),
    trigger='interval',
    hours=1,
    id='expire_pre_orders',
    name='Expirar pré-ordens',
    replace_existing=True
)

# Iniciar scheduler
scheduler.start()

# Garantir que o scheduler seja desligado ao encerrar a aplicação
import atexit
atexit.register(lambda: scheduler.shutdown())
```

### Configuração com Celery (Para produção)

Para ambientes de produção com alta carga, use Celery:

```python
# celery_tasks.py
from celery import Celery
from jobs.expire_pre_orders import PreOrderExpirationJob

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def expire_pre_orders_task():
    with app.app_context():
        return PreOrderExpirationJob.run()

# Configurar beat schedule
celery.conf.beat_schedule = {
    'expire-pre-orders-every-hour': {
        'task': 'celery_tasks.expire_pre_orders_task',
        'schedule': 3600.0,  # A cada hora
    },
}
```

### Execução Manual

Para testar ou executar manualmente:

```bash
python jobs/expire_pre_orders.py
```

### Logs

Os logs são salvos em:
- `logs/expire_pre_orders.log` - Log do job
- Console (stdout/stderr)

### Monitoramento

O job retorna um dicionário com estatísticas:

```python
{
    'success': True,
    'duration_seconds': 1.23,
    'expiring_checked': 5,
    'expiring_notified': 3,
    'expired_checked': 10,
    'expired_count': 2,
    'timestamp': '2025-01-15T10:00:00'
}
```

### Configurações

As configurações estão em `config.py`:

- `PRE_ORDER_DEFAULT_NEGOTIATION_DAYS`: Prazo padrão de negociação (7 dias)
- `PRE_ORDER_EXPIRATION_WARNING_HOURS`: Horas antes da expiração para notificar (24h)

### Troubleshooting

**Problema**: Job não está executando
- Verifique se o cron está ativo: `sudo service cron status`
- Verifique os logs: `tail -f logs/expire_pre_orders.log`
- Teste manualmente: `python jobs/expire_pre_orders.py`

**Problema**: Notificações duplicadas
- O job verifica o histórico antes de enviar notificações
- Se ainda houver duplicatas, verifique se há múltiplas instâncias do job rodando

**Problema**: Pré-ordens não estão expirando
- Verifique se o campo `expires_at` está configurado corretamente
- Verifique se o status está em um estado válido para expiração
- Execute o job manualmente para debug
