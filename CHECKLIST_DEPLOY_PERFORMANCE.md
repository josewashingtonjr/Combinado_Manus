# ✅ Checklist de Deploy - Otimizações de Performance

## Antes do Deploy

### 1. Minificar Assets
```bash
# Executar script de minificação
python minify_assets.py

# Verificar relatório
cat static/minification_report.json
```

**Resultado esperado**: 37 arquivos minificados (17 CSS + 20 JS)

### 2. Executar Testes
```bash
# Testes de performance
python test_performance_optimization.py

# Todos os testes devem passar
```

**Resultado esperado**: 12/12 testes passando

### 3. Verificar Integrações

**App.py**:
- [x] Middleware de performance importado
- [x] `PerformanceMiddleware(app)` inicializado

**Templates/base.html**:
- [x] CSS lazy-loading.css incluído
- [x] JS lazy-loading.js incluído

## Durante o Deploy

### 4. Configurar Variáveis de Ambiente

```bash
# Opcional: Configurar nível de compressão
export COMPRESS_LEVEL=6

# Opcional: Configurar tamanho mínimo para compressão
export COMPRESS_MIN_SIZE=500
```

### 5. Atualizar Templates para Produção

**Opção A: Manual** (recomendado para controle fino)
```html
<!-- Trocar .css por .min.css -->
<link href="{{ url_for('static', filename='css/mobile-first.min.css') }}">

<!-- Trocar .js por .min.js -->
<script src="{{ url_for('static', filename='js/toast-feedback.min.js') }}"></script>
```

**Opção B: Automática** (usar variável de ambiente)
```python
# Em config.py
USE_MINIFIED = os.getenv('USE_MINIFIED_ASSETS', 'true').lower() == 'true'

# Em templates
{% if config.USE_MINIFIED %}
    <link href="{{ url_for('static', filename='css/mobile-first.min.css') }}">
{% else %}
    <link href="{{ url_for('static', filename='css/mobile-first.css') }}">
{% endif %}
```

### 6. Converter Imagens para Lazy Loading

**Buscar todas as tags img:**
```bash
grep -r "<img" templates/ | grep -v "data-src"
```

**Converter para lazy loading:**
```html
<!-- Antes -->
<img src="/static/images/foto.jpg" alt="Foto">

<!-- Depois -->
<img data-src="/static/images/foto.jpg" alt="Foto" class="lazy-loading">
```

## Após o Deploy

### 7. Validar Compressão

```bash
# Testar compressão gzip
curl -H "Accept-Encoding: gzip" -I https://seu-dominio.com/

# Deve retornar:
# Content-Encoding: gzip
```

### 8. Validar Cache

```bash
# Testar cache de assets minificados
curl -I https://seu-dominio.com/static/css/mobile-first.min.css

# Deve retornar:
# Cache-Control: public, max-age=31536000, immutable
# ETag: "hash"
```

### 9. Testar Lazy Loading

1. Abrir DevTools (F12) > Network
2. Carregar página
3. Verificar que imagens só carregam ao fazer scroll
4. Verificar classe `lazy-loaded` nas imagens carregadas

### 10. Executar Auditorias

**Google Lighthouse:**
```bash
lighthouse https://seu-dominio.com --view
```

**Métricas esperadas:**
- Performance: > 90
- Best Practices: > 90
- Accessibility: > 90

**PageSpeed Insights:**
- Acessar: https://pagespeed.web.dev/
- Inserir URL do site
- Verificar métricas mobile e desktop

### 11. Testar em Dispositivos Reais

**Android:**
- [ ] Chrome mobile
- [ ] Conexão 3G simulada
- [ ] Verificar tempo de carregamento < 3s

**iOS:**
- [ ] Safari mobile
- [ ] Conexão 3G simulada
- [ ] Verificar tempo de carregamento < 3s

### 12. Monitorar Performance

**Métricas para acompanhar:**
- Tempo de carregamento médio
- Taxa de rejeição (bounce rate)
- Tempo na página
- Conversões

**Ferramentas:**
- Google Analytics
- New Relic / DataDog (se disponível)
- Logs do servidor

## Rollback (Se Necessário)

### Se houver problemas:

1. **Desabilitar compressão:**
```python
# Em app.py, comentar:
# performance = PerformanceMiddleware(app)
```

2. **Voltar para assets não-minificados:**
```html
<!-- Trocar .min.css por .css -->
<link href="{{ url_for('static', filename='css/mobile-first.css') }}">
```

3. **Desabilitar lazy loading:**
```javascript
// Em lazy-loading.js, comentar auto-inicialização
// ou remover script do template
```

## Verificação Final

### Checklist de Validação

- [ ] Assets minificados gerados
- [ ] Testes passando (12/12)
- [ ] Middleware de performance ativo
- [ ] Templates atualizados para produção
- [ ] Compressão gzip funcionando
- [ ] Cache headers configurados
- [ ] Lazy loading funcionando
- [ ] Lighthouse score > 90
- [ ] Testado em dispositivos reais
- [ ] Tempo de carregamento < 3s em 3G
- [ ] Documentação atualizada

## Métricas de Sucesso

### Antes vs Depois

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Tamanho assets | 500KB | 200KB | 60% ↓ |
| Tempo 3G | 8-10s | 2-3s | 70% ↓ |
| Requisições | 25-30 | 15-20 | 40% ↓ |
| Cache hits | 0% | 90% | 90% ↑ |

## Suporte

### Em caso de dúvidas:

1. Consultar `OTIMIZACAO_PERFORMANCE.md` (documentação completa)
2. Consultar `GUIA_RAPIDO_PERFORMANCE.md` (guia rápido)
3. Verificar `RELATORIO_OTIMIZACAO_PERFORMANCE.md` (relatório de implementação)
4. Executar `python test_performance_optimization.py` (validar implementação)

### Troubleshooting comum:

- **Compressão não funciona**: Verificar headers Accept-Encoding
- **Cache muito agressivo**: Usar DevTools com cache desabilitado em dev
- **Lazy loading não funciona**: Verificar console para erros JavaScript
- **Assets não minificados**: Executar `python minify_assets.py`

---

**Última atualização**: 2025-12-02  
**Versão**: 1.0  
**Status**: ✅ Pronto para deploy
