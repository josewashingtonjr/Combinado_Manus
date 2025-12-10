# Correções de Templates e Rotas

## Problema
Erro ao acessar páginas de convites e ordens:
```
BuildError: Could not build url for endpoint 'cliente.ver_ordem' with values ['order_id']
BuildError: Could not build url for endpoint 'prestador.ver_ordem' with values ['order_id']
```

## Causa
Os templates estavam usando rotas incorretas:
- `cliente.ver_ordem` (não existe)
- `prestador.ver_ordem` (não existe)

A rota correta é `order.ver_ordem` (definida em `routes/order_routes.py`)

## Correções Aplicadas

### 1. templates/cliente/convites.html
**Antes:**
```html
<a href="{{ url_for('cliente.ver_ordem', order_id=invite.order_id) }}" 
   class="btn btn-outline-primary btn-sm" title="Ver Ordem de Serviço">
    <i class="fas fa-eye me-1"></i>Ver Ordem
</a>
```

**Depois:**
```html
<a href="{{ url_for('cliente.ordens') }}" 
   class="btn btn-outline-primary btn-sm" title="Ver Ordens de Serviço">
    <i class="fas fa-eye me-1"></i>Ver Ordens
</a>
```

### 2. templates/prestador/dashboard.html (2 ocorrências)
**Antes:**
```html
<a href="{{ url_for('prestador.ver_ordem', order_id=ordem.id) }}" class="btn btn-sm btn-outline-primary">
    <i class="fas fa-eye me-1"></i>Ver Detalhes
</a>
```

**Depois:**
```html
<a href="{{ url_for('order.ver_ordem', order_id=ordem.id) }}" class="btn btn-sm btn-outline-primary">
    <i class="fas fa-eye me-1"></i>Ver Detalhes
</a>
```

**Antes:**
```html
<a href="{{ url_for('prestador.ver_ordem', order_id=bloqueio.order_id) }}" class="btn btn-sm btn-outline-primary">
    <i class="fas fa-eye me-1"></i>Ver Ordem
</a>
```

**Depois:**
```html
<a href="{{ url_for('order.ver_ordem', order_id=bloqueio.order_id) }}" class="btn btn-sm btn-outline-primary">
    <i class="fas fa-eye me-1"></i>Ver Ordem
</a>
```

### 3. templates/prestador/ordens.html
**Status:** Já estava correto usando `order.ver_ordem`

### 4. routes/cliente_routes.py - Rota de ordens
**Problema:** Template esperava variável `statistics` que não estava sendo passada

**Correção:**
```python
# Calcular estatísticas
from models import Order
all_orders = Order.query.filter_by(client_id=user.id).all()
statistics = {
    'total': len(all_orders),
    'aguardando': len([o for o in all_orders if o.status == 'aceita']),
    'para_confirmar': len([o for o in all_orders if o.status == 'concluida']),
    'concluidas': len([o for o in all_orders if o.status == 'confirmada']),
    'em_disputa': len([o for o in all_orders if o.status == 'em_disputa']),
    'canceladas': len([o for o in all_orders if o.status == 'cancelada'])
}

return render_template('cliente/ordens.html', 
                     user=user, 
                     orders=orders,
                     statistics=statistics)  # ✅ Adicionado
```

## Arquivos Modificados
- `templates/cliente/convites.html`
- `templates/prestador/dashboard.html`
- `routes/cliente_routes.py`

## Resultado
✅ Páginas de convites e ordens agora carregam sem erros
✅ Links para visualizar ordens funcionam corretamente
✅ Estatísticas de ordens exibidas corretamente
✅ Servidor reiniciado e funcionando em http://127.0.0.1:5001
