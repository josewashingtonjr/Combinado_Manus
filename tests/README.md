# Testes Automatizados do Projeto Combinado

Este diretório contém a suíte de testes automatizados para o sistema Combinado, desenvolvida para garantir a qualidade, estabilidade e segurança da aplicação.

## Estrutura dos Testes

### Arquivos de Teste

1. **`test_auth.py`** - Testes de Autenticação e Autorização (22 testes)
   - Login/logout de usuários e administradores
   - Controle de acesso e autorização
   - Gerenciamento de papéis
   - Segurança de senha
   - Gerenciamento de sessão

2. **`test_cliente_prestador.py`** - Testes de Funcionalidades de Cliente e Prestador (30+ testes)
   - Carteira do cliente
   - Ordens de serviço
   - Convites
   - Dashboard do prestador
   - Transações e histórico
   - Serviços de carteira

3. **`test_admin.py`** - Testes de Funcionalidades Administrativas (25+ testes)
   - Dashboard administrativo
   - Gerenciamento de usuários
   - Gerenciamento de tokens
   - Configurações do sistema
   - Monitoramento de transações
   - Gerenciamento de ordens e disputas
   - Relatórios
   - Segurança administrativa

### Arquivos de Configuração

- **`conftest.py`** - Configuração base e fixtures para todos os testes
- **`__init__.py`** - Inicialização do pacote de testes

## Fixtures Disponíveis

As seguintes fixtures estão disponíveis para uso nos testes:

- `app` - Instância da aplicação Flask configurada para testes
- `client` - Cliente de teste para fazer requisições HTTP
- `db_session` - Sessão de banco de dados limpa para cada teste
- `test_user` - Usuário de teste com papel de cliente
- `test_admin` - Administrador de teste
- `test_provider` - Prestador de teste
- `authenticated_client` - Cliente autenticado como usuário
- `authenticated_admin_client` - Cliente autenticado como administrador

## Executando os Testes

### Pré-requisitos

Instale as dependências de teste:

```bash
pip3 install pytest pytest-cov
```

### Executar Todos os Testes

```bash
cd /home/ubuntu/projeto
pytest tests/
```

### Executar Testes Específicos

```bash
# Apenas testes de autenticação
pytest tests/test_auth.py

# Apenas testes de cliente e prestador
pytest tests/test_cliente_prestador.py

# Apenas testes administrativos
pytest tests/test_admin.py
```

### Executar com Cobertura de Código

```bash
pytest tests/ --cov=. --cov-report=html
```

O relatório de cobertura será gerado em `htmlcov/index.html`.

### Executar com Saída Detalhada

```bash
pytest tests/ -v
```

### Executar Testes Específicos por Nome

```bash
# Executar apenas testes de login
pytest tests/ -k "login"

# Executar apenas testes de carteira
pytest tests/ -k "wallet"
```

## Estrutura de um Teste

Exemplo de estrutura de um teste:

```python
def test_example(client, test_user, db_session):
    """Descrição do que o teste faz"""
    # Arrange - Preparar dados de teste
    data = {'key': 'value'}
    
    # Act - Executar a ação
    response = client.post('/route', data=data)
    
    # Assert - Verificar o resultado
    assert response.status_code == 200
    assert b'expected' in response.data
```

## Boas Práticas

1. **Isolamento de Testes**: Cada teste deve ser independente e não depender do estado de outros testes.

2. **Limpeza de Dados**: Use fixtures que limpam o banco de dados antes de cada teste.

3. **Nomenclatura Clara**: Use nomes descritivos para os testes que indiquem claramente o que está sendo testado.

4. **Documentação**: Adicione docstrings aos testes explicando o comportamento esperado.

5. **Cobertura**: Busque uma cobertura de código de pelo menos 80% para funcionalidades críticas.

## Categorias de Testes

### Testes Unitários
Testam funções e métodos isoladamente, sem dependências externas.

### Testes de Integração
Testam a interação entre diferentes componentes do sistema (rotas, serviços, banco de dados).

### Testes de Segurança
Verificam controle de acesso, autenticação, autorização e proteção contra ataques.

### Testes de Lógica de Negócio
Validam regras de negócio específicas do sistema (tokenomics, transações, taxas).

## Problemas Conhecidos

Alguns testes podem falhar devido a:

1. **Dependências de Serviços**: Alguns serviços podem não estar implementados completamente.
2. **Rotas Ausentes**: Algumas rotas referenciadas nos testes podem não existir ainda.
3. **Modelos Incompletos**: Alguns modelos podem não ter todos os campos esperados.

Esses problemas devem ser corrigidos durante a fase de execução e correção de testes.

## Contribuindo

Ao adicionar novos testes:

1. Siga a estrutura existente
2. Use fixtures apropriadas
3. Documente o comportamento esperado
4. Execute todos os testes antes de fazer commit
5. Mantenha a cobertura de código alta

## Próximos Passos

1. Executar a suíte de testes completa
2. Corrigir falhas identificadas
3. Aumentar cobertura de código
4. Adicionar testes para funcionalidades faltantes
5. Implementar testes de performance
6. Adicionar testes end-to-end

---

**Última atualização:** 26 de outubro de 2025  
**Autor:** Manus AI

