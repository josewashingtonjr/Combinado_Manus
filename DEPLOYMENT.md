# Guia de Deployment - Sistema de Gestão de Ordens

Este documento fornece instruções completas para fazer o deployment do sistema de gestão de ordens de serviço em ambiente de produção.

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Variáveis de Ambiente](#variáveis-de-ambiente)
3. [Processo de Migration](#processo-de-migration)
4. [Seed de Configurações Iniciais](#seed-de-configurações-iniciais)
5. [Configuração do Cron Job](#configuração-do-cron-job)
6. [Configuração de Upload de Arquivos](#configuração-de-upload-de-arquivos)
7. [Checklist de Deployment](#checklist-de-deployment)
8. [Monitoramento e Logs](#monitoramento-e-logs)
9. [Rollback](#rollback)
10. [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

Antes de iniciar o deployment, certifique-se de que o ambiente possui:

- **Python 3.11+** instalado
- **PostgreSQL 12+** ou **SQLite 3.35+** (para desenvolvimento)
- **pip** e **virtualenv** instalados
- **Acesso root ou sudo** para configurar cron jobs
- **Espaço em disco**: Mínimo 10GB para uploads e logs
- **Memória RAM**: Mínimo 2GB recomendado

---

## Variáveis de Ambiente

Configure as seguintes variáveis de ambiente no arquivo `.env` ou no sistema:

### Configurações Básicas

```bash
# Ambiente de execução
FLASK_ENV=production
FLASK_APP=app.py
SECRET_KEY=sua-chave-secreta-super-segura-aqui

# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/sistema_combinado
# OU para SQLite:
# DATABASE_URL=sqlite:///instance/sistema_combinado.db

# Debug (SEMPRE False em produção)
DEBUG=False
```

### Configurações de Upload

```bash
# Diretório para upload de arquivos de prova
UPLOAD_FOLDER=/var/www/sistema/uploads/disputes
MAX_UPLOAD_SIZE=10485760  # 10MB em bytes
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf,mp4

# Permissões de diretório
UPLOAD_DIR_PERMISSIONS=0755
```

### Configurações do Job de Confirmação Automática

```bash
# Habilitar/desabilitar job automático
AUTO_CONFIRM_JOB_ENABLED=true

# Caminho para logs do job
AUTO_CONFIRM_LOG_PATH=/var/log/sistema/auto_confirm_orders.log

# Intervalo de execução (em horas, usado apenas para referência)
AUTO_CONFIRM_INTERVAL_HOURS=1
```

### Configurações de Segurança

```bash
# CSRF Protection
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600

# Session
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=3600

# Rate Limiting
RATELIMIT_ENABLED=True
RATELIMIT_STORAGE_URL=redis://localhost:6379
```

### Configurações de Logs

```bash
# Diretório de logs
LOG_DIR=/var/log/sistema

# Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Rotação de logs
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=10
```

### Exemplo de arquivo .env completo

```bash
# .env
FLASK_ENV=production
FLASK_APP=app.py
SECRET_KEY=gere-uma-chave-aleatoria-segura-com-32-caracteres-ou-mais
DATABASE_URL=postgresql://sistema_user:senha_forte@localhost:5432/sistema_combinado
DEBUG=False

UPLOAD_FOLDER=/var/www/sistema/uploads/disputes
MAX_UPLOAD_SIZE=10485760
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf,mp4

AUTO_CONFIRM_JOB_ENABLED=true
AUTO_CONFIRM_LOG_PATH=/var/log/sistema/auto_confirm_orders.log

LOG_DIR=/var/log/sistema
LOG_LEVEL=INFO
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=10

WTF_CSRF_ENABLED=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

---

## Processo de Migration

### 1. Backup do Banco de Dados

**SEMPRE faça backup antes de executar migrations!**

```bash
# PostgreSQL
pg_dump -U usuario -d sistema_combinado > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite
cp instance/sistema_combinado.db instance/sistema_combinado.db.backup_$(date +%Y%m%d_%H%M%S)
```

### 2. Executar Migrations

O sistema possui várias migrations que devem ser executadas em ordem:

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# 1. Migration de tipos monetários (se ainda não executada)
python apply_monetary_migration.py

# 2. Migration de campos de gestão de ordens
python apply_order_management_migration.py

# 3. Migration de índices de performance
python apply_order_indexes_migration.py

# 4. Migration de auditoria de propostas (se aplicável)
python apply_proposal_audit_migration.py

# 5. Migration de soft delete (se aplicável)
python apply_soft_delete_migration.py
```

### 3. Verificar Migrations

Após executar as migrations, verifique se foram aplicadas corretamente:

```bash
# Verificar estrutura do banco
python -c "
from app import app, db
from models import Order, SystemConfig
with app.app_context():
    # Verificar campos da Order
    print('Campos da tabela Order:')
    for col in Order.__table__.columns:
        print(f'  - {col.name}: {col.type}')
    
    # Verificar índices
    print('\nÍndices da tabela Order:')
    for idx in Order.__table__.indexes:
        print(f'  - {idx.name}')
"
```

### 4. Validar Integridade

```bash
# Executar script de validação
python validate_financial_constraints.py

# Verificar logs de migration
tail -n 50 logs/sistema_combinado.log
```

---

## Seed de Configurações Iniciais

### 1. Criar Configurações Padrão do Sistema

Execute o script de seed para criar as configurações iniciais:

```bash
python -c "
from app import app, db
from models import SystemConfig
from decimal import Decimal

with app.app_context():
    # Verificar se já existem configurações
    existing = SystemConfig.query.filter_by(key='platform_fee_percentage').first()
    
    if not existing:
        print('Criando configurações iniciais...')
        
        configs = [
            SystemConfig(
                key='platform_fee_percentage',
                value='5.0',
                description='Percentual cobrado pela plataforma sobre o valor do serviço',
                category='taxas'
            ),
            SystemConfig(
                key='contestation_fee',
                value='10.00',
                description='Taxa fixa de contestação bloqueada como garantia',
                category='taxas'
            ),
            SystemConfig(
                key='cancellation_fee_percentage',
                value='10.0',
                description='Percentual de multa aplicado em cancelamentos',
                category='taxas'
            ),
            SystemConfig(
                key='confirmation_deadline_hours',
                value='36',
                description='Prazo em horas para confirmação automática',
                category='prazos'
            ),
        ]
        
        for config in configs:
            db.session.add(config)
        
        db.session.commit()
        print('✓ Configurações criadas com sucesso!')
        
        # Exibir configurações
        print('\nConfigurações ativas:')
        for config in SystemConfig.query.filter_by(category='taxas').all():
            print(f'  - {config.key}: {config.value}')
    else:
        print('Configurações já existem. Pulando seed.')
"
```

### 2. Criar Usuário Admin (se necessário)

```bash
python -c "
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(email='admin@sistema.com').first()
    
    if not admin:
        admin = User(
            nome='Administrador',
            email='admin@sistema.com',
            telefone='11999999999',
            senha=generate_password_hash('senha_admin_segura'),
            papel='admin',
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        print('✓ Usuário admin criado com sucesso!')
    else:
        print('Usuário admin já existe.')
"
```

### 3. Criar Carteiras Iniciais

```bash
python -c "
from app import app, db
from models import User, Wallet
from decimal import Decimal

with app.app_context():
    # Criar carteira para admin se não existir
    admin = User.query.filter_by(papel='admin').first()
    if admin and not admin.wallet:
        wallet = Wallet(
            user_id=admin.id,
            saldo_disponivel=Decimal('0.00'),
            saldo_bloqueado=Decimal('0.00')
        )
        db.session.add(wallet)
        db.session.commit()
        print('✓ Carteira admin criada!')
    
    # Criar carteiras para usuários sem carteira
    users_without_wallet = User.query.filter(~User.wallet.has()).all()
    for user in users_without_wallet:
        wallet = Wallet(
            user_id=user.id,
            saldo_disponivel=Decimal('0.00'),
            saldo_bloqueado=Decimal('0.00')
        )
        db.session.add(wallet)
    
    if users_without_wallet:
        db.session.commit()
        print(f'✓ {len(users_without_wallet)} carteiras criadas!')
"
```

---

## Configuração do Cron Job

O sistema utiliza um job automático para confirmar ordens após 36 horas sem resposta do cliente.

### 1. Tornar o Script Executável

```bash
chmod +x jobs/auto_confirm_orders.py
```

### 2. Verificar o Shebang

Certifique-se de que o arquivo `jobs/auto_confirm_orders.py` possui o shebang correto:

```python
#!/usr/bin/env python3.11
```

Se sua instalação do Python estiver em outro local, ajuste o shebang:

```bash
# Descobrir o caminho do Python
which python3.11

# Atualizar o shebang no arquivo
# Por exemplo: #!/usr/bin/python3.11
```

### 3. Testar o Job Manualmente

Antes de configurar o cron, teste o job manualmente:

```bash
# Navegar até o diretório do projeto
cd /caminho/para/o/projeto

# Ativar ambiente virtual
source .venv/bin/activate

# Executar o job
python jobs/auto_confirm_orders.py

# Verificar logs
tail -f logs/auto_confirm_orders.log
```

### 4. Configurar o Cron Job

Edite o crontab do usuário que executará o job:

```bash
crontab -e
```

Adicione a seguinte linha para executar o job **a cada hora**:

```bash
# Confirmação automática de ordens (executa a cada hora)
0 * * * * cd /caminho/completo/para/o/projeto && /caminho/completo/para/.venv/bin/python jobs/auto_confirm_orders.py >> logs/cron_auto_confirm.log 2>&1
```

**Exemplo com caminhos reais:**

```bash
0 * * * * cd /home/ubuntu/sistema-combinado && /home/ubuntu/sistema-combinado/.venv/bin/python jobs/auto_confirm_orders.py >> /home/ubuntu/sistema-combinado/logs/cron_auto_confirm.log 2>&1
```

### 5. Verificar Cron Job Configurado

```bash
# Listar cron jobs ativos
crontab -l

# Verificar logs do cron (sistema)
sudo tail -f /var/log/syslog | grep CRON
```

### 6. Monitorar Execução do Job

```bash
# Verificar logs do job
tail -f logs/auto_confirm_orders.log

# Verificar logs do cron
tail -f logs/cron_auto_confirm.log
```

### Alternativas de Agendamento

Se preferir executar em intervalos diferentes:

```bash
# A cada 30 minutos
*/30 * * * * cd /caminho/projeto && python jobs/auto_confirm_orders.py

# A cada 2 horas
0 */2 * * * cd /caminho/projeto && python jobs/auto_confirm_orders.py

# Apenas em horário comercial (9h às 18h)
0 9-18 * * * cd /caminho/projeto && python jobs/auto_confirm_orders.py
```

---

## Configuração de Upload de Arquivos

### 1. Criar Diretórios de Upload

```bash
# Criar diretório para provas de contestação
sudo mkdir -p /var/www/sistema/uploads/disputes

# Criar diretório para recibos (se aplicável)
sudo mkdir -p /var/www/sistema/uploads/receipts

# Definir permissões
sudo chown -R www-data:www-data /var/www/sistema/uploads
sudo chmod -R 755 /var/www/sistema/uploads
```

### 2. Configurar Limites de Upload no Nginx

Se estiver usando Nginx como proxy reverso:

```nginx
# /etc/nginx/sites-available/sistema

server {
    listen 80;
    server_name seu-dominio.com;

    # Limite de tamanho de upload
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Servir arquivos estáticos
    location /static {
        alias /caminho/para/projeto/static;
    }
}
```

### 3. Configurar Limites no Apache

Se estiver usando Apache:

```apache
# /etc/apache2/sites-available/sistema.conf

<VirtualHost *:80>
    ServerName seu-dominio.com
    
    # Limite de upload
    LimitRequestBody 10485760
    
    WSGIDaemonProcess sistema python-path=/caminho/projeto python-home=/caminho/projeto/.venv
    WSGIProcessGroup sistema
    WSGIScriptAlias / /caminho/projeto/app.py
    
    <Directory /caminho/projeto>
        Require all granted
    </Directory>
</VirtualHost>
```

---

## Checklist de Deployment

Use este checklist para garantir que todos os passos foram executados:

### Pré-Deployment

- [ ] Código revisado e testado em ambiente de staging
- [ ] Backup do banco de dados criado
- [ ] Variáveis de ambiente configuradas no arquivo `.env`
- [ ] Dependências atualizadas (`pip install -r requirements.txt`)
- [ ] Testes automatizados executados com sucesso
- [ ] Documentação atualizada

### Deployment

- [ ] Ambiente virtual criado e ativado
- [ ] Banco de dados criado (se novo deployment)
- [ ] Migrations executadas em ordem:
  - [ ] `apply_monetary_migration.py`
  - [ ] `apply_order_management_migration.py`
  - [ ] `apply_order_indexes_migration.py`
  - [ ] Outras migrations aplicáveis
- [ ] Seed de configurações iniciais executado
- [ ] Usuário admin criado
- [ ] Carteiras iniciais criadas
- [ ] Diretórios de upload criados com permissões corretas
- [ ] Logs de migration verificados sem erros

### Configuração de Serviços

- [ ] Cron job configurado e testado
- [ ] Job de confirmação automática executado manualmente com sucesso
- [ ] Logs do cron job verificados
- [ ] Servidor web (Nginx/Apache) configurado
- [ ] Limites de upload configurados
- [ ] SSL/TLS configurado (HTTPS)
- [ ] Firewall configurado

### Pós-Deployment

- [ ] Aplicação iniciada com sucesso
- [ ] Login de admin testado
- [ ] Criação de ordem testada
- [ ] Confirmação automática testada (criar ordem de teste com prazo expirado)
- [ ] Upload de arquivos testado
- [ ] Notificações funcionando
- [ ] Logs sendo gerados corretamente
- [ ] Monitoramento configurado
- [ ] Alertas configurados
- [ ] Documentação de rollback preparada

### Validação Final

- [ ] Todas as rotas principais acessíveis
- [ ] Dashboard de cliente funcional
- [ ] Dashboard de prestador funcional
- [ ] Dashboard de admin funcional
- [ ] Transações financeiras funcionando corretamente
- [ ] Sistema de contestação funcional
- [ ] Performance aceitável (tempo de resposta < 2s)
- [ ] Sem erros críticos nos logs

---

## Monitoramento e Logs

### Estrutura de Logs

O sistema gera os seguintes arquivos de log:

```
logs/
├── sistema_combinado.log          # Log principal da aplicação
├── auto_confirm_orders.log        # Log do job de confirmação automática
├── cron_auto_confirm.log          # Log de saída do cron
├── order_operations.log           # Log de operações de ordens
├── audit.log                      # Log de auditoria
└── erros_criticos.log            # Log de erros críticos
```

### Monitorar Logs em Tempo Real

```bash
# Log principal
tail -f logs/sistema_combinado.log

# Log do job automático
tail -f logs/auto_confirm_orders.log

# Todos os logs
tail -f logs/*.log

# Filtrar apenas erros
tail -f logs/sistema_combinado.log | grep ERROR

# Filtrar operações de ordem
tail -f logs/order_operations.log
```

### Rotação de Logs

Configure logrotate para gerenciar o tamanho dos logs:

```bash
# Criar arquivo de configuração
sudo nano /etc/logrotate.d/sistema-combinado
```

Conteúdo:

```
/caminho/para/projeto/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload sistema-combinado
    endscript
}
```

### Alertas Importantes

Configure alertas para os seguintes eventos:

1. **Job de confirmação automática falhou por 2 horas consecutivas**
2. **Erro em transação financeira**
3. **Saldo inconsistente detectado**
4. **Falha em upload de arquivo**
5. **Erro de banco de dados**
6. **Uso de disco acima de 80%**

### Métricas para Monitorar

- Taxa de confirmação automática (% de ordens confirmadas automaticamente)
- Tempo médio de resposta do cliente (antes de confirmar/contestar)
- Taxa de contestação (% de ordens contestadas)
- Taxa de cancelamento (% de ordens canceladas)
- Volume de transações financeiras
- Erros por hora
- Tempo de resposta das APIs

---

## Rollback

### Plano de Rollback

Se algo der errado durante o deployment, siga estes passos:

#### 1. Rollback do Banco de Dados

```bash
# PostgreSQL
psql -U usuario -d sistema_combinado < backup_YYYYMMDD_HHMMSS.sql

# SQLite
cp instance/sistema_combinado.db.backup_YYYYMMDD_HHMMSS instance/sistema_combinado.db
```

#### 2. Rollback do Código

```bash
# Se usando Git
git checkout <commit-anterior>

# Reinstalar dependências da versão anterior
pip install -r requirements.txt
```

#### 3. Desabilitar Cron Job

```bash
# Editar crontab
crontab -e

# Comentar a linha do job
# 0 * * * * cd /caminho/projeto && python jobs/auto_confirm_orders.py
```

#### 4. Reiniciar Serviços

```bash
# Reiniciar aplicação
sudo systemctl restart sistema-combinado

# Reiniciar servidor web
sudo systemctl restart nginx
# ou
sudo systemctl restart apache2
```

#### 5. Verificar Estado

```bash
# Verificar logs
tail -f logs/sistema_combinado.log

# Verificar se aplicação está respondendo
curl http://localhost:5000/

# Verificar banco de dados
python -c "from app import app, db; app.app_context().push(); print(db.engine.execute('SELECT COUNT(*) FROM orders').scalar())"
```

---

## Troubleshooting

### Problema: Job de confirmação automática não está executando

**Sintomas:**
- Ordens não são confirmadas automaticamente após 36 horas
- Logs do cron vazios

**Soluções:**

1. Verificar se o cron job está configurado:
```bash
crontab -l
```

2. Verificar permissões do script:
```bash
ls -la jobs/auto_confirm_orders.py
chmod +x jobs/auto_confirm_orders.py
```

3. Testar execução manual:
```bash
cd /caminho/projeto
source .venv/bin/activate
python jobs/auto_confirm_orders.py
```

4. Verificar logs do sistema:
```bash
sudo tail -f /var/log/syslog | grep CRON
```

5. Verificar se o Python está no PATH do cron:
```bash
# Adicionar PATH no crontab
PATH=/usr/local/bin:/usr/bin:/bin
0 * * * * cd /caminho/projeto && python jobs/auto_confirm_orders.py
```

### Problema: Erro ao fazer upload de arquivos

**Sintomas:**
- Erro 413 (Request Entity Too Large)
- Erro de permissão ao salvar arquivo

**Soluções:**

1. Verificar limite de upload no Nginx/Apache
2. Verificar permissões do diretório:
```bash
ls -la /var/www/sistema/uploads/disputes
sudo chown -R www-data:www-data /var/www/sistema/uploads
```

3. Verificar espaço em disco:
```bash
df -h
```

4. Verificar variável MAX_UPLOAD_SIZE no .env

### Problema: Migrations falhando

**Sintomas:**
- Erro ao executar migration
- Tabelas ou colunas não criadas

**Soluções:**

1. Verificar backup antes de tentar novamente
2. Verificar logs de migration
3. Executar migrations uma por vez
4. Verificar se há migrations pendentes:
```bash
python -c "from app import app, db; app.app_context().push(); print(db.engine.table_names())"
```

5. Se necessário, reverter migration e tentar novamente

### Problema: Saldos inconsistentes

**Sintomas:**
- Saldo disponível + bloqueado não bate com transações
- Erro de validação financeira

**Soluções:**

1. Executar script de validação:
```bash
python validate_financial_constraints.py
```

2. Verificar logs de transações:
```bash
grep "transaction" logs/order_operations.log
```

3. Executar auditoria de carteiras:
```bash
python -c "
from app import app, db
from models import Wallet, Transaction
from decimal import Decimal

with app.app_context():
    wallets = Wallet.query.all()
    for wallet in wallets:
        print(f'Wallet {wallet.id} - User {wallet.user_id}')
        print(f'  Disponível: {wallet.saldo_disponivel}')
        print(f'  Bloqueado: {wallet.saldo_bloqueado}')
        print(f'  Total: {wallet.saldo_disponivel + wallet.saldo_bloqueado}')
"
```

### Problema: Performance lenta

**Sintomas:**
- Dashboard demora para carregar
- Queries lentas

**Soluções:**

1. Verificar se índices foram criados:
```bash
python test_order_indexes.py
```

2. Analisar queries lentas no PostgreSQL:
```sql
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

3. Verificar uso de eager loading nas queries
4. Considerar adicionar cache (Redis)

---

## Suporte

Para problemas não cobertos neste guia:

1. Verificar logs detalhados em `logs/`
2. Consultar documentação técnica em `docs/`
3. Revisar requirements e design em `.kiro/specs/sistema-gestao-ordens-completo/`
4. Contatar equipe de desenvolvimento

---

## Histórico de Versões

| Versão | Data | Alterações |
|--------|------|------------|
| 1.0 | 2025-11-19 | Versão inicial do guia de deployment |

---

**Última atualização:** 19 de novembro de 2025
