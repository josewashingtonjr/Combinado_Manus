# Guia Rápido - Otimização de Performance

## 🚀 Início Rápido

### 1. Minificar Assets (Antes de Deploy)

```bash
# Minificar todos os CSS e JS
python minify_assets.py

# Ver relatório
cat static/minification_report.json
```

### 2. Usar Arquivos Minificados em Produção

**Em desenvolvimento** (arquivos normais):
```html
<link href="{{ url_for('static', filename='css/mobile-first.css') }}" rel="stylesheet">
<script src="{{ url_for('static', filename='js/toast-feedback.js') }}"></script>
```

**Em produção** (arquivos minificados):
```html
<link href="{{ url_for('static', filename='css/mobile-first.min.css') }}" rel="stylesheet">
<script src="{{ url_for('static', filename='js/toast-feedback.min.js') }}"></script>
```

### 3. Adicionar Lazy Loading em Imagens

**Antes**:
```html
<img src="/static/images/foto.jpg" alt="Foto">
```

**Depois**:
```html
<img data-src="/static/images/foto.jpg" 
     alt="Foto"
     class="lazy-loading">
```

**Para backgrounds**:
```html
<div data-bg="/static/images/background.jpg" 
     class="hero-section lazy-loading">
</div>
```

### 4. Configurar Cache em Rotas

**Cache de 5 minutos**:
```python
from services.performance_middleware import cache_control

@app.route('/api/data')
@cache_control(max_age=300)
def get_data():
    return jsonify(data)
```

**Sem cache (tempo real)**:
```python
from services.performance_middleware import no_cache

@app.route('/api/realtime')
@no_cache
def get_realtime():
    return jsonify(realtime_data)
```

## 📊 Verificar Melhorias

### Testar Compressão
```bash
curl -H "Accept-Encoding: gzip" -I http://localhost:5000/
# Deve retornar: Content-Encoding: gzip
```

### Testar Cache
```bash
curl -I http://localhost:5000/static/css/mobile-first.min.css
# Deve retornar: Cache-Control: public, max-age=31536000
```

### Executar Testes
```bash
python test_performance_optimization.py
```

## ✅ Checklist de Deploy

- [ ] Executar `python minify_assets.py`
- [ ] Atualizar templates para usar `.min.css` e `.min.js`
- [ ] Converter imagens para lazy loading
- [ ] Verificar que middleware está ativo
- [ ] Testar em conexão 3G
- [ ] Executar Lighthouse audit

## 🎯 Resultados Esperados

- **42% redução** no tamanho dos assets
- **60-80% redução** com compressão gzip
- **2-3 segundos** de carregamento em 3G
- **90% economia** em visitas repetidas (cache)

## 📚 Documentação Completa

Ver `OTIMIZACAO_PERFORMANCE.md` para detalhes completos.
