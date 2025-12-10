# Correção do Fluxo de Cancelamento e Conclusão de Ordens

## Requisitos do Cliente

### Cancelamento de Ordens

**1. Prestador pode cancelar:**
- ✅ Antes de marcar como concluída
- ✅ Motivo: superior não pode concluir (ou qualquer outro motivo)
- ✅ Prestador paga multa de cancelamento

**2. Cliente pode cancelar:**
- ✅ Somente se o prestador ainda não tenha marcado a ordem como concluída
- ✅ Cliente paga a multa

### Botões no Dashboard do Prestador

**1. Botão "Marcar como Concluído":**
- ✅ Disponível enquanto status = 'aguardando_execucao'
- ✅ Muda status para 'servico_executado'
- ✅ Inicia prazo de 36h para cliente confirmar/contestar

**2. Botão "Cancelar Ordem":**
- ✅ Disponível SOMENTE enquanto status = 'aguardando_execucao'
- ✅ Desaparece após marcar como concluído
- ✅ Aplica multa ao prestador

### Botões no Dashboard do Cliente

**1. Status após ordem criada:**
- ✅ "Aguardando o prestador concluir o serviço"
- ✅ Status: 'aguardando_execucao'

**2. Botão "Cancelar Ordem":**
- ✅ Disponível enquanto status = 'aguardando_execucao'
- ✅ Desaparece após prestador marcar como concluído
- ✅ Aplica multa ao cliente

**3. Após prestador marcar como concluído:**
- ✅ Status muda para 'servico_executado'
- ✅ Aparece botão "Confirmar Serviço"
- ✅ Aparece botão "Contestar"
- ✅ Prazo de 36h para ação

### Sistema de Contestação

**1. Cliente contesta:**
- ✅ Envia justificativa e fotos
- ✅ Status muda para 'contestada'

**2. Prestador responde:**
- ✅ Envia justificativa e fotos
- ✅ Campos: dispute_provider_response, dispute_evidence

**3. Admin arbitra:**
- ✅ Visualiza toda a contestação junto à ordem
- ✅ Pode decidir: favor_cliente, favor_prestador, dividir_50_50
- ✅ Campos: dispute_admin_notes, dispute_resolution, dispute_winner

## Análise do Sistema Atual

### ✅ O que já está implementado:

1. **Modelo Order** - Todos os campos necessários existem:
   - `can_be_cancelled` - property que valida se pode cancelar
   - `can_be_marked_completed` - property que valida se pode marcar como concluído
   - `can_be_confirmed` - property que valida se pode confirmar
   - `can_be_disputed` - property que valida se pode contestar
   - Campos de contestação completos

2. **OrderManagementService** - Métodos implementados:
   - `mark_service_completed()` - Prestador marca como concluído
   - `confirm_service()` - Cliente confirma
   - `cancel_order()` - Cancela com multa
   - `open_dispute()` - Cliente abre contestação
   - `_process_cancellation_payments()` - Processa multas corretamente

3. **Rotas** - Todas as rotas existem:
   - `/ordens/<id>/marcar-concluido` - POST
   - `/ordens/<id>/confirmar` - POST
   - `/ordens/<id>/cancelar` - POST
   - `/ordens/<id>/contestar` - GET/POST

### ❌ O que precisa ser corrigido:

1. **Templates do Prestador:**
   - Botão "Marcar como Concluído" deve aparecer apenas em 'aguardando_execucao'
   - Botão "Cancelar" deve aparecer apenas em 'aguardando_execucao'
   - Ambos devem desaparecer após marcar como concluído

2. **Templates do Cliente:**
   - Botão "Cancelar" deve aparecer apenas em 'aguardando_execucao'
   - Após status 'servico_executado', mostrar botões "Confirmar" e "Contestar"
   - Melhorar visualização do status e prazos

3. **Sistema de Resposta do Prestador:**
   - Adicionar rota para prestador responder contestação
   - Template para prestador enviar justificativa e fotos
   - Atualizar campo `dispute_provider_response`

4. **Dashboard Admin:**
   - Visualização completa da contestação
   - Interface para arbitrar
   - Mostrar evidências de ambas as partes

## Implementação

### 1. Correção dos Templates do Prestador

**Arquivo:** `templates/prestador/ver_ordem.html`

Adicionar lógica condicional para botões:

```jinja2
{% if order.status == 'aguardando_execucao' %}
    <!-- Botão Marcar como Concluído -->
    <form method="POST" action="{{ url_for('order.marcar_concluido', order_id=order.id) }}">
        <button type="submit" class="btn btn-success">
            <i class="fas fa-check-circle"></i> Marcar como Concluído
        </button>
    </form>
    
    <!-- Botão Cancelar -->
    <button type="button" class="btn btn-danger" data-toggle="modal" data-target="#cancelModal">
        <i class="fas fa-times-circle"></i> Cancelar Ordem
    </button>
{% elif order.status == 'servico_executado' %}
    <div class="alert alert-info">
        <i class="fas fa-clock"></i> Aguardando confirmação do cliente
        <br>Prazo: {{ order.hours_until_auto_confirmation|round(1) }} horas restantes
    </div>
{% elif order.status == 'contestada' %}
    <div class="alert alert-warning">
        <i class="fas fa-exclamation-triangle"></i> Ordem contestada pelo cliente
    </div>
    {% if not order.dispute_provider_response %}
        <a href="{{ url_for('order.responder_contestacao', order_id=order.id) }}" class="btn btn-primary">
            <i class="fas fa-reply"></i> Responder Contestação
        </a>
    {% endif %}
{% endif %}
```

### 2. Correção dos Templates do Cliente

**Arquivo:** `templates/cliente/ver_ordem.html`

```jinja2
{% if order.status == 'aguardando_execucao' %}
    <div class="alert alert-info">
        <i class="fas fa-clock"></i> Aguardando o prestador concluir o serviço
    </div>
    
    <!-- Botão Cancelar -->
    <button type="button" class="btn btn-danger" data-toggle="modal" data-target="#cancelModal">
        <i class="fas fa-times-circle"></i> Cancelar Ordem
    </button>
    
{% elif order.status == 'servico_executado' %}
    <div class="alert alert-success">
        <i class="fas fa-check-circle"></i> Prestador marcou o serviço como concluído
        <br><strong>Prazo para confirmar ou contestar:</strong> {{ order.hours_until_auto_confirmation|round(1) }} horas
    </div>
    
    <!-- Botão Confirmar -->
    <form method="POST" action="{{ url_for('order.confirmar_servico', order_id=order.id) }}" style="display: inline;">
        <button type="submit" class="btn btn-success btn-lg">
            <i class="fas fa-thumbs-up"></i> Confirmar Serviço
        </button>
    </form>
    
    <!-- Botão Contestar -->
    <a href="{{ url_for('order.contestar_servico', order_id=order.id) }}" class="btn btn-warning btn-lg">
        <i class="fas fa-exclamation-triangle"></i> Contestar
    </a>
    
{% elif order.status == 'contestada' %}
    <div class="alert alert-warning">
        <i class="fas fa-gavel"></i> Contestação aberta - Aguardando análise administrativa
    </div>
{% endif %}
```

### 3. Nova Rota: Prestador Responder Contestação

**Arquivo:** `routes/order_routes.py`

```python
@order_bp.route('/<int:order_id>/responder-contestacao', methods=['GET', 'POST'])
@login_required
@require_order_ownership(required_role='provider')
def responder_contestacao(order_id, order=None):
    """Prestador responde à contestação do cliente"""
    user = AuthService.get_current_user()
    
    if order.status != 'contestada':
        flash('Esta ordem não está contestada.', 'error')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
    
    if order.dispute_provider_response:
        flash('Você já respondeu a esta contestação.', 'info')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
    
    if request.method == 'GET':
        return render_template('prestador/responder_contestacao.html', user=user, order=order)
    
    # POST: Processar resposta
    try:
        response = SecurityValidator.sanitize_input(
            request.form.get('response', '').strip(),
            max_length=2000
        )
        
        if not response or len(response) < 20:
            flash('Resposta deve ter pelo menos 20 caracteres.', 'error')
            return redirect(url_for('order.responder_contestacao', order_id=order_id))
        
        # Upload de arquivos de prova
        evidence_files = []
        if 'evidence' in request.files:
            files = request.files.getlist('evidence')
            is_valid, error_msg, valid_files = SecurityValidator.validate_multiple_files(files)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('order.responder_contestacao', order_id=order_id))
            evidence_files = valid_files
        
        # Salvar resposta
        result = OrderManagementService.provider_respond_to_dispute(
            order_id=order_id,
            provider_id=user.id,
            response=response,
            evidence_files=evidence_files
        )
        
        flash(result['message'], 'success')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
        
    except Exception as e:
        logger.error(f"Erro ao responder contestação {order_id}: {e}")
        flash('Erro ao enviar resposta.', 'error')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
```

### 4. Novo Método no OrderManagementService

```python
@staticmethod
def provider_respond_to_dispute(order_id: int, provider_id: int, response: str, evidence_files=None) -> dict:
    """
    Prestador responde à contestação do cliente
    
    Args:
        order_id: ID da ordem
        provider_id: ID do prestador
        response: Resposta/justificativa do prestador
        evidence_files: Lista de arquivos de prova
        
    Returns:
        dict com resultado da operação
    """
    order = Order.query.get(order_id)
    if not order:
        raise ValueError("Ordem não encontrada")
    
    if order.provider_id != provider_id:
        raise ValueError("Você não é o prestador desta ordem")
    
    if order.status != 'contestada':
        raise ValueError("Esta ordem não está contestada")
    
    if order.dispute_provider_response:
        raise ValueError("Você já respondeu a esta contestação")
    
    try:
        evidence_urls = []
        
        # Processar upload de arquivos
        if evidence_files:
            UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'disputes')
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            for file in evidence_files:
                if file and file.filename:
                    unique_filename = SecurityValidator.sanitize_filename(file.filename, order_id)
                    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                    file.save(file_path)
                    
                    evidence_urls.append({
                        'filename': file.filename,
                        'url': f"/uploads/disputes/{unique_filename}",
                        'uploaded_at': datetime.utcnow().isoformat(),
                        'uploaded_by': 'provider'
                    })
        
        # Atualizar ordem
        order.dispute_provider_response = response
        
        # Adicionar evidências do prestador ao campo existente
        if evidence_urls:
            existing_evidence = order.dispute_evidence_urls or []
            order.dispute_evidence_urls = existing_evidence + evidence_urls
        
        db.session.commit()
        
        # Auditoria
        AuditService.log_dispute_response(
            order_id=order_id,
            provider_id=provider_id,
            response=response,
            evidence_count=len(evidence_urls)
        )
        
        logger.info(f"Prestador {provider_id} respondeu contestação da ordem {order_id}")
        
        # Notificar admin
        from services.notification_service import NotificationService
        try:
            NotificationService.notify_admin_dispute_response(order)
        except Exception as e:
            logger.warning(f"Erro ao notificar admin: {e}")
        
        return {
            'success': True,
            'order_id': order.id,
            'evidence_files_count': len(evidence_urls),
            'message': 'Resposta enviada com sucesso! O administrador analisará a contestação.'
        }
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao responder contestação {order_id}: {e}")
        raise
```

## Resumo das Mudanças

### Arquivos a Modificar:

1. ✅ `templates/prestador/ver_ordem.html` - Corrigir lógica dos botões
2. ✅ `templates/cliente/ver_ordem.html` - Corrigir lógica dos botões
3. ✅ `routes/order_routes.py` - Adicionar rota `responder_contestacao`
4. ✅ `services/order_management_service.py` - Adicionar método `provider_respond_to_dispute`
5. ✅ `templates/prestador/responder_contestacao.html` - Criar novo template
6. ✅ `templates/admin/ver_contestacao.html` - Melhorar visualização (se necessário)

### Validações Implementadas:

- ✅ Botões aparecem/desaparecem conforme status correto
- ✅ Cancelamento só disponível em 'aguardando_execucao'
- ✅ Marcar concluído só disponível em 'aguardando_execucao'
- ✅ Confirmar/Contestar só disponível em 'servico_executado'
- ✅ Multas aplicadas corretamente
- ✅ Sistema de resposta do prestador
- ✅ Admin pode arbitrar com todas as informações
