# PDR - Correção de Erros de Templates e Rotas

**Data:** 21 de Outubro de 2025

---

## 1. Problemas Identificados

### 1.1. Erro `jinja2.exceptions.UndefinedError: 'user' is undefined`

**Localização:** Rotas de cliente, como `/app/home` (dashboard do cliente).

**Descrição:** O template `cliente/dashboard.html` e outros templates de cliente esperam receber um objeto `user` para exibir informações como `{{ user.nome }}`, mas esse objeto não está sendo passado para o `render_template` na função da rota. Isso causa um erro 500 no servidor e impede a exibição correta das páginas do cliente logado.

**Causa Provável:** As correções anteriores que passavam o objeto `user` para as rotas do cliente foram sobrescritas ou perdidas durante a clonagem do repositório, ou a lógica não foi aplicada consistentemente.

### 1.2. Erro 500 em `/admin/usuarios/criar`

**Localização:** Rota `/admin/usuarios/criar` (criação de usuário no painel administrativo).

**Descrição:** A página de criação de usuário admin está gerando um erro 500. Isso indica que o template `admin/criar_usuario.html` não está sendo renderizado corretamente ou que a lógica de processamento do formulário na rota está falhando. As correções anteriores para esta rota (que adaptavam o formulário para não usar WTForms) podem ter sido perdidas.

**Causa Provável:** Similar ao problema anterior, as alterações feitas no `admin_routes.py` e no template `admin/criar_usuario.html` foram revertidas ou não estão presentes na versão atual do projeto.

---

## 2. Soluções Propostas

### 2.1. Correção para `UndefinedError: 'user' nas rotas de cliente`

**Ação:** Revisar e corrigir as funções das rotas em `/home/ubuntu/projeto/routes/app_routes.py` (e outras rotas de cliente, se aplicável) para:
1. Importar o modelo `User`.
2. Recuperar o `user_id` da sessão.
3. Buscar o objeto `User` correspondente no banco de dados.
4. Passar o objeto `user` para a função `render_template`.

**Exemplo:**
```python
# Antes (problema)
# return render_template('cliente/dashboard.html')

# Depois (solução)
from models import User
user_id = session.get('user_id')
user = User.query.get(user_id) if user_id else None
if not user: # Redirecionar se o usuário não for encontrado
    return redirect(url_for('auth.login'))
return render_template('cliente/dashboard.html', user=user)
```

### 2.2. Correção para Erro 500 em `/admin/usuarios/criar`

**Ação:**
1. **Verificar Template:** Assegurar que o template `/home/ubuntu/projeto/templates/admin/criar_usuario.html` existe e está configurado para receber dados via `request.form` (sem WTForms).
2. **Reaplicar Lógica da Rota:** Reimplementar a lógica da rota `criar_usuario` em `/home/ubuntu/projeto/routes/admin_routes.py` para processar os dados do formulário diretamente via `request.form`, incluindo validações de campos (nome, email, senha, etc.) e tratamento de erros com `flash` messages.

**Exemplo (Lógica da Rota):**
```python
# Antes (problema)
# form = CreateUserForm()
# if form.validate_on_submit():
#    ...

# Depois (solução)
if request.method == 'POST':
    # Coletar dados de request.form
    # Validar dados (senhas coincidem, min length, etc.)
    # Chamar AdminService.create_user
    # flash messages para sucesso/erro
return render_template('admin/criar_usuario.html')
```

---

## 3. Critérios de Aceitação

- [ ] **Login de Cliente:** Após login como cliente, o dashboard (`/app/home`) e outras páginas de cliente devem carregar sem erros 500 e exibir corretamente o nome do usuário.
- [ ] **Criação de Usuário Admin:** A página `/admin/usuarios/criar` deve carregar sem erros 500. O formulário deve permitir a criação de um novo usuário com sucesso, exibindo mensagens de feedback (sucesso/erro) e redirecionando para a lista de usuários.
- [ ] **Consistência:** Todas as rotas de cliente que exibem informações do usuário devem funcionar corretamente.
- [ ] **Logs Limpos:** O log do servidor (`server.log`) não deve apresentar os erros `UndefinedError: 'user' is undefined` ou `500 Internal Server Error` relacionados a essas rotas após as correções.

---

## 4. Próximos Passos

1. Executar as correções detalhadas nas Soluções Propostas.
2. Reiniciar o servidor Flask.
3. Realizar os testes de aceitação para cada correção.
4. Documentar as alterações no GitHub com um novo commit.
