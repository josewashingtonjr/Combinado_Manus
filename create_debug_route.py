#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Adicionar rota de debug para convites
"""

def add_debug_route():
    """Adiciona rota de debug ao arquivo auth_routes.py"""
    
    debug_route = '''

@auth_bp.route('/convite/<token>/debug')
def debug_convite(token):
    """Página de debug para convites"""
    try:
        from services.invite_service import InviteService
        
        # Verificar se o convite existe e é válido
        invite = InviteService.get_invite_by_token(token)
        
        return render_template('debug_invite.html', 
                             invite=invite, 
                             token=token)
        
    except ValueError as e:
        flash('Convite não encontrado ou inválido.', 'error')
        return redirect(url_for('auth.user_login'))
    except Exception as e:
        flash('Erro ao processar convite. Tente novamente.', 'error')
        return redirect(url_for('auth.user_login'))
'''
    
    # Ler o arquivo atual
    with open('routes/auth_routes.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adicionar a rota no final do arquivo, antes da última linha
    lines = content.split('\n')
    
    # Encontrar onde inserir (antes do final)
    insert_index = len(lines) - 1
    
    # Inserir a nova rota
    lines.insert(insert_index, debug_route)
    
    # Escrever de volta
    with open('routes/auth_routes.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ Rota de debug adicionada com sucesso!")
    print("🔗 Acesse: http://127.0.0.1:5001/auth/convite/HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa/debug")

if __name__ == "__main__":
    add_debug_route()