# Guia - Template Helpers para Assets

## 📋 Visão Geral

O sistema agora inclui um helper `asset_url()` que automaticamente usa arquivos minificados em produção e arquivos normais em desenvolvimento.

## 🎯 Benefícios

- ✅ Troca automática entre arquivos normais e minificados
- ✅ Configurável via variável de ambiente
- ✅ Fallback automático se arquivo minificado não existir
- ✅ Código mais limpo nos templates

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Produção (usar arquivos minificados)
export USE_MINIFIED_ASSETS=true

# Desenvolvimento (usar arquivos normais)
export USE_MINIFIED_ASSETS=false
```

### Config.py

```python
# Configuração padrão
USE_MINIFIED_ASSETS = os.environ.get("USE_MINIFIED_ASSETS", "true").lower() == "true"
```

## 💻 Como Usar nos Templates

### Antes (Sem Helper)

```html
<!-- Desenvolvimento -->
<link href="{{ url_for('static', filename='css/mobile-first.css') }}" rel="stylesheet">

<!-- Produção -->
<link href="{{ url_for('static', filename='css/mobile-first.min.css') }}" rel="stylesheet">
```

### Depois (Com Helper)

```html
<!-- Funciona em desenvolvimento E produção -->
<link href="{{ url_for('static', filename=asset_url('css/mobile-first.css')) }}" rel="stylesheet">
<script src="{{ url_for('static', filename=asset_url('js/toast-feedback.js')) }}"></script>
```

## 🎨 Exemplos

### CSS

```html
<!-- Helper escolhe automaticamente entre .css e .min.css -->
<link href="{{ url_for('static', filename=asset_url('css/mobile-first.css')) }}" rel="stylesheet">
<link href="{{ url_for('static', filename=asset_url('css/toast-feedback.css')) }}" rel="stylesheet">
<link href="{{ url_for('static', filename=asset_url('css/touch-targets.css')) }}" rel="stylesheet">
```

### JavaScript

```html
<!-- Helper escolhe automaticamente entre .js e .min.js -->
<script src="{{ url_for('static', filename=asset_url('js/toast-feedback.js')) }}"></script>
<script src="{{ url_for('static', filename=asset_url('js/loading-states.js')) }}"></script>
<script src="{{ url_for('static', filename=asset_url('js/lazy-loading.js')) }}"></script>
```

### Imagens (Não Afetadas)

```html
<!-- Imagens não são minificadas, então helper retorna o mesmo nome -->
<img src="{{ url_for('static', filename=asset_url('images/logo.png')) }}" alt="Logo">
```

## 🔍 Como Funciona

### Lógica do Helper

```python
def asset_url(filename):
    """
    1. Verifica se USE_MINIFIED_ASSETS está ativo
    2. Se não, retorna filename original
    3. Se sim, verifica se é CSS ou JS
    4. Cria nome do arquivo minificado (adiciona .min.)
    5. Verifica se arquivo minificado existe
    6. Se existe, retorna nome minificado
    7. Se não existe, retorna nome original (fallback)
    """
```

### Exemplos de Transformação

```python
# Em produção (USE_MINIFIED_ASSETS=true)
asset_url('css/mobile-first.css')     → 'css/mobile-first.min.css'
asset_url('js/toast-feedback.js')     → 'js/toast-feedback.min.js'
asset_url('css/style.min.css')        → 'css/style.min.css' (já minificado)
asset_url('images/logo.png')          → 'images/logo.png' (não é CSS/JS)

# Em desenvolvimento (USE_MINIFIED_ASSETS=false)
asset_url('css/mobile-first.css')     → 'css/mobile-first.css'
asset_url('js/toast-feedback.js')     → 'js/toast-feedback.js'
```

## 🚀 Migração de Templates Existentes

### Script de Busca

```bash
# Encontrar todos os arquivos CSS/JS nos templates
grep -r "url_for('static'" templates/ | grep -E "\.(css|js)"
```

### Padrão de Substituição

**Buscar**:
```html
{{ url_for('static', filename='css/ARQUIVO.css') }}
```

**Substituir por**:
```html
{{ url_for('static', filename=asset_url('css/ARQUIVO.css')) }}
```

### Exemplo Completo

**Antes**:
```html
<head>
    <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/mobile-first.css') }}" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/toast-feedback.css') }}" rel="stylesheet">
</head>
<body>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    <script src="{{ url_for('static', filename='js/toast-feedback.js') }}"></script>
</body>
```

**Depois**:
```html
<head>
    <link href="{{ url_for('static', filename=asset_url('css/style.css')) }}" rel="stylesheet">
    <link href="{{ url_for('static', filename=asset_url('css/mobile-first.css')) }}" rel="stylesheet">
    <link href="{{ url_for('static', filename=asset_url('css/toast-feedback.css')) }}" rel="stylesheet">
</head>
<body>
    <script src="{{ url_for('static', filename=asset_url('js/main.js')) }}"></script>
    <script src="{{ url_for('static', filename=asset_url('js/toast-feedback.js')) }}"></script>
</body>
```

## ✅ Validação

### Testar em Desenvolvimento

```bash
# Desabilitar minificação
export USE_MINIFIED_ASSETS=false

# Iniciar servidor
python app.py

# Verificar no navegador que arquivos .css e .js são carregados
```

### Testar em Produção

```bash
# Habilitar minificação
export USE_MINIFIED_ASSETS=true

# Minificar assets
python minify_assets.py

# Iniciar servidor
python app.py

# Verificar no navegador que arquivos .min.css e .min.js são carregados
```

### Verificar no Código

```python
from app import app
from template_helpers import asset_url

with app.app_context():
    # Testar com minificação ativa
    app.config['USE_MINIFIED_ASSETS'] = True
    print(asset_url('css/mobile-first.css'))  # Deve retornar: css/mobile-first.min.css
    
    # Testar com minificação desativada
    app.config['USE_MINIFIED_ASSETS'] = False
    print(asset_url('css/mobile-first.css'))  # Deve retornar: css/mobile-first.css
```

## 🐛 Troubleshooting

### Problema: Helper não encontrado no template

**Causa**: Template helpers não foram registrados

**Solução**:
```python
# Verificar em app.py
from template_helpers import register_template_helpers
register_template_helpers(app)
```

### Problema: Sempre usa arquivo normal, nunca minificado

**Causa**: USE_MINIFIED_ASSETS está false ou arquivo minificado não existe

**Solução**:
```bash
# 1. Verificar configuração
echo $USE_MINIFIED_ASSETS

# 2. Minificar assets
python minify_assets.py

# 3. Verificar se arquivo existe
ls static/css/*.min.css
```

### Problema: Erro 404 para arquivo minificado

**Causa**: Arquivo minificado não foi gerado

**Solução**:
```bash
# Gerar arquivos minificados
python minify_assets.py

# Verificar geração
cat static/minification_report.json
```

## 📚 Referências

- **Implementação**: `template_helpers.py`
- **Configuração**: `config.py`
- **Integração**: `app.py`
- **Documentação completa**: `OTIMIZACAO_PERFORMANCE.md`

## 🎯 Próximos Passos

1. Atualizar templates existentes para usar `asset_url()`
2. Testar em desenvolvimento e produção
3. Validar que arquivos corretos são carregados
4. Documentar uso para equipe

---

**Criado em**: 2025-12-02  
**Parte de**: Tarefa 16 - Otimizar Carregamento
