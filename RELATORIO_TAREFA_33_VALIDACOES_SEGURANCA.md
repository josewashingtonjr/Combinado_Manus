# Relatório de Implementação - Tarefa 33: Validações de Segurança

## Data
19 de novembro de 2025

## Objetivo
Implementar validações de segurança abrangentes em todas as rotas de ordens, incluindo validação de propriedade, validação de arquivos, sanitização de entrada e rate limiting.

## Implementações Realizadas

### 1. Serviço de Validação de Segurança (services/security_validator.py)

Criado serviço centralizado `SecurityValidator` com as seguintes funcionalidades:

#### 1.1 Validação de Propriedade de Ordem
```python
validate_order_ownership(order, user_id, required_role)
```
- Valida se o usuário tem permissão para acessar/modificar a ordem
- Suporta validação de papel específico (client/provider)
- Registra tentativas de acesso não autorizado em logs

#### 1.2 Validação de Upload de Arquivos
```python
validate_file_upload(file)
validate_multiple_files(files)
```
- **Tipos permitidos**: jpg, jpeg, png, pdf, mp4
- **Tamanho máximo**: 10MB por arquivo
- **Máximo de arquivos**: 5 por upload
- Validação de arquivo vazio
- Mensagens de erro detalhadas

#### 1.3 Sanitização de Nomes de Arquivo
```python
sanitize_filename(filename, order_id)
```
- Usa `secure_filename` do Werkzeug
- Remove caracteres especiais perigosos
- Adiciona timestamp para unicidade
- Limita tamanho do nome (255 caracteres)
- Previne path traversal attacks

#### 1.4 Rate Limiting
```python
check_rate_limit(user_id, action, max_attempts, window_seconds)
```
- Implementação em memória (para produção recomenda-se Redis)
- Configurável por ação
- Janela de tempo deslizante
- Logs de tentativas excedidas

#### 1.5 Sanitização de Entrada
```python
sanitize_input(text, max_length)
```
- Remove caracteres de controle
- Limita comprimento
- Previne XSS e injection attacks

#### 1.6 Validação de Permissões por Ação
```python
validate_order_action_permission(order, user_id, action)
```
- Valida permissões específicas por ação:
  - `mark_completed`: apenas prestador
  - `confirm`: apenas cliente
  - `dispute`: apenas cliente
  - `cancel`: cliente ou prestador
- Verifica status da ordem

### 2. Decorators de Segurança

#### 2.1 @require_order_ownership
```python
@require_order_ownership(required_role='client')
def my_route(order_id, order=None):
    ...
```
- Valida propriedade da ordem automaticamente
- Injeta objeto `order` nos kwargs
- Redireciona com mensagem de erro se inválido
- Suporta papel específico opcional

#### 2.2 @rate_limit
```python
@rate_limit('cancel_order', max_attempts=3, window_seconds=300)
def cancel_order_route():
    ...
```
- Aplica rate limiting automaticamente
- Suporta requisições AJAX (retorna JSON 429)
- Configurável por rota

### 3. Atualização das Rotas de Ordens (routes/order_routes.py)

#### 3.1 Rota: Ver Ordem
```python
@require_order_ownership()
def ver_ordem(order_id, order=None):
```
- ✅ Validação de propriedade via decorator
- ✅ Eager loading de relacionamentos

#### 3.2 Rota: Marcar Concluído
```python
@require_order_ownership(required_role='provider')
@rate_limit('mark_completed', max_attempts=10, window_seconds=60)
def marcar_concluido(order_id, order=None):
```
- ✅ Validação de propriedade (apenas prestador)
- ✅ Rate limiting (10 tentativas/minuto)
- ✅ Validação de permissão para ação

#### 3.3 Rota: Confirmar Serviço
```python
@require_order_ownership(required_role='client')
@rate_limit('confirm_service', max_attempts=10, window_seconds=60)
def confirmar_servico(order_id, order=None):
```
- ✅ Validação de propriedade (apenas cliente)
- ✅ Rate limiting (10 tentativas/minuto)
- ✅ Validação de permissão para ação

#### 3.4 Rota: Contestar Serviço
```python
@require_order_ownership(required_role='client')
def contestar_servico(order_id, order=None):
```
- ✅ Validação de propriedade (apenas cliente)
- ✅ Rate limiting manual (3 tentativas/5 minutos)
- ✅ Sanitização do motivo (max 2000 caracteres)
- ✅ Validação múltipla de arquivos
- ✅ Validação de tipo e tamanho de arquivo
- ✅ Sanitização de nomes de arquivo

#### 3.5 Rota: Cancelar Ordem
```python
@require_order_ownership()
@rate_limit('cancel_order', max_attempts=3, window_seconds=300)
def cancelar_ordem(order_id, order=None):
```
- ✅ Validação de propriedade (cliente ou prestador)
- ✅ Rate limiting (3 tentativas/5 minutos)
- ✅ Sanitização do motivo (max 500 caracteres)
- ✅ Validação de permissão para ação

#### 3.6 Rota: Status da Ordem (API)
```python
@require_order_ownership()
def get_order_status(order_id, order=None):
```
- ✅ Validação de propriedade via decorator
- ✅ Retorna JSON com status

### 4. Atualização do OrderManagementService

#### 4.1 Método: open_dispute
```python
def open_dispute(order_id, client_id, reason, evidence_files):
```
- ✅ Usa `SecurityValidator.validate_file_upload()` para cada arquivo
- ✅ Usa `SecurityValidator.sanitize_filename()` para nomes
- ✅ Validação integrada de tipo e tamanho
- ✅ Logs detalhados de uploads

### 5. Atualização das Rotas de Admin (routes/admin_routes.py)

#### 5.1 Rota: Resolver Contestação
```python
def resolver_contestacao(order_id):
```
- ✅ Rate limiting (10 tentativas/minuto)
- ✅ Sanitização das notas do admin (max 2000 caracteres)
- ✅ Validação mínima de 10 caracteres para notas
- ✅ Validação de winner ('client' ou 'provider')

### 6. Proteção CSRF

#### 6.1 Flask-WTF CSRF Protection
- ✅ Já configurado em `app.py` via `CSRFProtect(app)`
- ✅ Tokens CSRF injetados em todos os templates
- ✅ Validação automática em todas as requisições POST/PUT/DELETE
- ✅ Handler de erro 400 para erros CSRF

## Validações de Segurança Implementadas

### ✅ Validação de Propriedade da Ordem
- Implementada em todas as rotas de ordens
- Decorator `@require_order_ownership` para automação
- Logs de tentativas de acesso não autorizado

### ✅ Validação de Tipos de Arquivo
- Tipos permitidos: jpg, jpeg, png, pdf, mp4
- Validação case-insensitive
- Mensagens de erro claras

### ✅ Validação de Tamanho de Arquivo
- Máximo 10MB por arquivo
- Validação de arquivo vazio
- Mensagens com tamanho atual e máximo

### ✅ Sanitização de Nomes de Arquivo
- Usa `secure_filename` do Werkzeug
- Remove caracteres especiais
- Adiciona timestamp e order_id
- Previne path traversal

### ✅ Proteção CSRF
- Flask-WTF configurado
- Tokens em todos os formulários
- Handler de erro customizado

### ✅ Rate Limiting
- Implementado para ações críticas:
  - Marcar concluído: 10/minuto
  - Confirmar serviço: 10/minuto
  - Contestar: 3/5 minutos
  - Cancelar: 3/5 minutos
  - Resolver contestação (admin): 10/minuto

## Configurações de Segurança

### Limites de Upload
```python
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf', 'mp4'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILES_PER_UPLOAD = 5
```

### Rate Limiting (Padrões)
```python
# Ações normais
max_attempts=10, window_seconds=60  # 10 por minuto

# Ações críticas
max_attempts=3, window_seconds=300  # 3 por 5 minutos
```

### Sanitização de Texto
```python
# Motivo de contestação
max_length=2000

# Motivo de cancelamento
max_length=500

# Notas do admin
max_length=2000, min_length=10
```

## Logs de Segurança

Todos os eventos de segurança são registrados:

1. **Tentativas de acesso não autorizado**
   ```
   Tentativa de acesso não autorizado à ordem {order_id} pelo usuário {user_id}
   ```

2. **Rate limit excedido**
   ```
   Rate limit excedido para usuário {user_id} na ação '{action}'
   ```

3. **Uploads de arquivo**
   ```
   Arquivo de prova salvo: {filename} ({size}KB) para ordem {order_id}
   ```

4. **Validações de arquivo falhadas**
   ```
   Erro de validação ao contestar ordem {order_id}: {error}
   ```

## Melhorias de Segurança Implementadas

### 1. Defesa em Profundidade
- Múltiplas camadas de validação
- Decorators + validações manuais
- Validações no serviço e nas rotas

### 2. Princípio do Menor Privilégio
- Validação de papel específico por ação
- Cliente só pode confirmar/contestar
- Prestador só pode marcar concluído

### 3. Validação de Entrada
- Sanitização de todos os inputs de texto
- Validação de tipos e tamanhos de arquivo
- Remoção de caracteres de controle

### 4. Prevenção de Ataques
- **Path Traversal**: Sanitização de nomes de arquivo
- **XSS**: Sanitização de entrada de texto
- **CSRF**: Tokens em todos os formulários
- **DoS**: Rate limiting em ações críticas
- **File Upload Attacks**: Validação de tipo e tamanho

## Recomendações para Produção

### 1. Rate Limiting com Redis
```python
# Substituir implementação em memória por Redis
from redis import Redis
redis_client = Redis(host='localhost', port=6379, db=0)
```

### 2. Armazenamento de Arquivos
```python
# Usar S3 ou similar para arquivos
# Implementar URLs assinadas para acesso
```

### 3. Monitoramento
```python
# Implementar alertas para:
# - Múltiplas tentativas de acesso não autorizado
# - Rate limit excedido frequentemente
# - Uploads suspeitos
```

### 4. Auditoria
```python
# Registrar todas as ações de segurança em tabela de auditoria
# Incluir: user_id, action, timestamp, ip, user_agent
```

## Testes Recomendados

### 1. Testes de Validação de Propriedade
- Tentar acessar ordem de outro usuário
- Tentar executar ação sem permissão
- Verificar logs de tentativas não autorizadas

### 2. Testes de Upload de Arquivo
- Upload de arquivo com tipo não permitido
- Upload de arquivo maior que 10MB
- Upload de mais de 5 arquivos
- Upload de arquivo com nome malicioso

### 3. Testes de Rate Limiting
- Executar ação múltiplas vezes rapidamente
- Verificar bloqueio após limite
- Verificar reset após janela de tempo

### 4. Testes de Sanitização
- Input com caracteres especiais
- Input com scripts XSS
- Input com path traversal
- Input muito longo

## Conclusão

A tarefa 33 foi implementada com sucesso, adicionando múltiplas camadas de validação de segurança:

✅ **Validação de propriedade da ordem** em todas as rotas
✅ **Validação de tipos de arquivo** (jpg, jpeg, png, pdf, mp4)
✅ **Validação de tamanho de arquivo** (10MB max)
✅ **Sanitização de nomes de arquivo** (secure_filename + timestamp)
✅ **Proteção CSRF** em todos os formulários (Flask-WTF)
✅ **Rate limiting** para ações críticas

O sistema agora possui validações robustas que protegem contra:
- Acesso não autorizado
- Upload de arquivos maliciosos
- Ataques de path traversal
- XSS e injection attacks
- Ataques de força bruta (via rate limiting)
- CSRF attacks

Todas as validações são centralizadas no `SecurityValidator`, facilitando manutenção e testes.
