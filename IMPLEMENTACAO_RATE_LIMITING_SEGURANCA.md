# Implementação de Rate Limiting e Segurança - Tarefa 23

## Resumo da Implementação

Este documento descreve a implementação completa de rate limiting e medidas de segurança para o sistema de pré-ordens, conforme especificado na tarefa 23.

## 📦 Dependências Instaladas

- **Flask-Limiter 4.0.0**: Framework de rate limiting para Flask
- **bleach 6.3.0**: Biblioteca para sanitização de HTML e prevenção de XSS

## 🛡️ Funcionalidades Implementadas

### 1. Rate Limiting

#### Configurações Implementadas

**Arquivo**: `services/rate_limiter_service.py`

- **Propostas de Pré-Ordem**: Máximo 10 propostas por hora
- **Cancelamentos**: Máximo 5 cancelamentos por dia
- **Requisições Gerais**: Máximo 20 requisições por minuto
- **Visualizações**: Máximo 60 visualizações por minuto
- **Aceitação de Termos**: Máximo 20 aceitações por hora
- **Aceitação/Rejeição de Propostas**: Máximo 30 por hora

#### Rotas Protegidas

Todas as rotas de pré-ordem em `routes/pre_ordem_routes.py` foram protegidas:

1. `GET /pre-ordem/<id>` - Visualização (60/min)
2. `POST /pre-ordem/<id>/propor-alteracao` - Propostas (10/hora)
3. `POST /pre-ordem/<id>/aceitar-proposta/<pid>` - Aceitação (30/hora)
4. `POST /pre-ordem/<id>/rejeitar-proposta/<pid>` - Rejeição (30/hora)
5. `POST /pre-ordem/<id>/aceitar-termos` - Aceitar termos (20/hora)
6. `POST /pre-ordem/<id>/cancelar` - Cancelamento (5/dia)
7. `GET /pre-ordem/<id>/historico` - Histórico (30/min)
8. `GET /pre-ordem/<id>/verificar-saldo` - Verificação de saldo (30/min)
9. `GET /pre-ordem/<id>/status` - Status (60/min)
10. `POST /pre-ordem/<id>/adicionar-saldo-e-aceitar` - Adicionar saldo (10/hora)

### 2. Sanitização de Inputs

#### Proteção contra XSS

**Arquivo**: `services/security_validator.py`

Implementado método `sanitize_input()` usando bleach:
- Remove todas as tags HTML por padrão
- Remove caracteres de controle perigosos
- Limita comprimento de texto
- Preserva texto válido

#### Validação de Valores Monetários

Método `validate_monetary_value()`:
- Valida valores positivos
- Limites configuráveis (padrão: R$ 0,01 a R$ 1.000.000,00)
- Máximo 2 casas decimais
- Suporta formato brasileiro (vírgula como separador decimal)

#### Validação de Datas

Método `validate_date_future()`:
- Valida que datas são futuras
- Limites configuráveis (padrão: 1 a 365 dias no futuro)
- Suporta string ou datetime
- Mensagens de erro claras em português

### 3. Validação de Autorização

#### Decorador de Permissão

**Arquivo**: `routes/pre_ordem_routes.py`

Decorador `@require_pre_order_participant()`:
- Valida que usuário é cliente ou prestador da pré-ordem
- Bloqueia acesso não autorizado
- Registra tentativas de acesso não autorizado com detalhes:
  - ID do usuário
  - Nome do usuário
  - IP address
  - User-Agent
  - Rota acessada

### 4. Logging de Segurança

#### Eventos Registrados

1. **Tentativas de Acesso Não Autorizado**:
   ```
   ACESSO NÃO AUTORIZADO - Usuário X (Nome) tentou acessar pré-ordem Y sem permissão.
   IP: xxx.xxx.xxx.xxx, User-Agent: ..., Rota: ...
   ```

2. **Rate Limit Excedido**:
   ```
   Rate limit excedido - User X - Ação: propor_alteracao
   ```

3. **Validações Falhadas**:
   ```
   Valor monetário inválido: -10.00 - valor deve ser maior que zero
   Data inválida: 2023-01-01 - data deve ser pelo menos 1 dia(s) no futuro
   ```

### 5. Tratamento de Erros

#### Página de Erro 429

**Arquivo**: `templates/errors/429.html`

Página amigável exibida quando rate limit é atingido:
- Mensagem clara em português
- Explicação do motivo
- Botões para voltar ou ir para página inicial
- Design responsivo e acessível

#### Handler de Erro

**Arquivo**: `app.py`

Registrado handler customizado para erro 429:
- Retorna JSON para requisições AJAX
- Retorna HTML para requisições normais
- Mensagens em português

## 🔒 Proteções Implementadas

### Contra XSS (Cross-Site Scripting)

✅ Sanitização de todos os inputs de texto usando bleach
✅ Remoção de tags HTML maliciosas
✅ Escape de caracteres especiais

### Contra Injection

✅ Validação rigorosa de valores numéricos
✅ Validação de datas com limites
✅ Sanitização de strings
✅ Uso de ORM (SQLAlchemy) que previne SQL injection

### Contra Abuso

✅ Rate limiting em todas as rotas críticas
✅ Limites diferenciados por tipo de ação
✅ Identificação por usuário autenticado ou IP
✅ Mensagens claras quando limites são atingidos

### Contra Acesso Não Autorizado

✅ Validação de permissão em todas as rotas
✅ Logging detalhado de tentativas não autorizadas
✅ Mensagens de erro que não revelam informações sensíveis

## 📊 Testes Implementados

**Arquivo**: `test_rate_limiting_security.py`

### Cobertura de Testes

- ✅ 25 testes implementados
- ✅ 100% de sucesso
- ✅ Cobertura de todos os métodos de validação
- ✅ Testes de casos extremos
- ✅ Testes de proteção contra ataques

### Categorias de Testes

1. **Sanitização de Inputs** (9 testes)
   - Remoção de HTML
   - Limitação de comprimento
   - Remoção de caracteres de controle
   - Proteção contra XSS
   - Proteção contra SQL injection

2. **Validação de Valores Monetários** (5 testes)
   - Valores válidos
   - Valores negativos
   - Valor zero
   - Valores muito grandes
   - Precisão decimal

3. **Validação de Datas** (4 testes)
   - Datas futuras válidas
   - Datas no passado
   - Datas muito distantes
   - Formato string

4. **Configuração de Rate Limiting** (4 testes)
   - Existência de configurações
   - Limites de propostas
   - Limites de cancelamentos
   - Limites gerais

5. **Casos Extremos** (3 testes)
   - Strings vazias
   - Apenas espaços
   - Valores nos limites

## 🚀 Como Usar

### Aplicar Rate Limiting em Nova Rota

```python
from services.rate_limiter_service import limiter

@app.route('/minha-rota')
@limiter.limit("10 per hour")
def minha_rota():
    # Sua lógica aqui
    pass
```

### Sanitizar Input do Usuário

```python
from services.security_validator import SecurityValidator

# Sanitizar texto
texto_limpo = SecurityValidator.sanitize_input(
    texto_usuario,
    max_length=1000
)

# Validar valor monetário
valor = SecurityValidator.validate_monetary_value(
    valor_str,
    field_name="Valor da proposta"
)

# Validar data futura
data = SecurityValidator.validate_date_future(
    data_str,
    field_name="Data de entrega"
)
```

### Validar Permissão

```python
from routes.pre_ordem_routes import require_pre_order_participant

@app.route('/pre-ordem/<int:pre_order_id>/acao')
@login_required
@require_pre_order_participant()
def minha_acao(pre_order_id, pre_order=None):
    # pre_order já está validado e disponível
    pass
```

## 📝 Configurações de Produção

### Recomendações

1. **Redis para Rate Limiting**:
   ```python
   # Em services/rate_limiter_service.py
   storage_uri="redis://localhost:6379"
   ```

2. **Ajustar Limites**:
   - Monitorar uso real
   - Ajustar limites conforme necessário
   - Considerar diferentes limites para usuários premium

3. **Logging**:
   - Configurar rotação de logs
   - Monitorar tentativas de acesso não autorizado
   - Alertar sobre padrões suspeitos

4. **HTTPS**:
   - Sempre usar HTTPS em produção
   - Configurar HSTS
   - Usar certificados válidos

## ✅ Checklist de Implementação

- [x] Instalar Flask-Limiter
- [x] Instalar bleach
- [x] Adicionar rate limiting: máximo 10 propostas por pré-ordem por hora
- [x] Adicionar rate limiting: máximo 5 cancelamentos por usuário por dia
- [x] Adicionar rate limiting: máximo 20 requisições por minuto por usuário
- [x] Implementar validação de autorização em todas as rotas
- [x] Adicionar sanitização de campos de texto usando bleach
- [x] Adicionar validação rigorosa de valores numéricos
- [x] Adicionar validação de datas (futuras, dentro de limites)
- [x] Implementar proteção CSRF (já existente via Flask-WTF)
- [x] Adicionar logging de tentativas de acesso não autorizado
- [x] Criar testes para validar implementação
- [x] Criar página de erro 429
- [x] Documentar implementação

## 🎯 Requisitos Atendidos

Todos os requisitos da tarefa 23 foram implementados com sucesso:

1. ✅ Rate limiting configurado e funcionando
2. ✅ Validações de segurança implementadas
3. ✅ Sanitização de inputs com bleach
4. ✅ Logging de segurança ativo
5. ✅ Proteção CSRF mantida
6. ✅ Testes passando (25/25)
7. ✅ Documentação completa

## 📈 Próximos Passos

1. Monitorar logs de segurança em produção
2. Ajustar limites de rate limiting baseado em uso real
3. Considerar implementar Redis para rate limiting distribuído
4. Adicionar alertas automáticos para padrões suspeitos
5. Revisar e atualizar limites periodicamente
