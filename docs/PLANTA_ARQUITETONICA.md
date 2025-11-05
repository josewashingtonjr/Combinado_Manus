# Planta Arquitetônica Detalhada - Sistema Combinado v2.0

## 1. Visão Geral da Arquitetura

O sistema "Combinado" é uma aplicação web baseada em Flask, projetada para gerenciar transações de tokens próprios (1 token = 1 real) entre clientes e prestadores de serviços, com um administrador centralizado para controle de tokenomics e configurações. 

**IMPORTANTE:** O sistema **NÃO utiliza blockchain**. Ele funciona com um **modelo interno próprio** inspirado em conceitos de rastreabilidade e auditabilidade, mas implementado totalmente no banco de dados relacional, sem qualquer dependência de tecnologia blockchain.

- **Framework Principal:** Flask (Python)
- **Banco de Dados:** SQLAlchemy com PostgreSQL para produção e SQLite para desenvolvimento.
- **Modelo de Transações Interno:** Sistema próprio de carteiras virtuais, escrow e transações rastreáveis implementado totalmente no banco de dados relacional (PostgreSQL). Todas as transações são registradas com IDs únicos, timestamps e histórico completo para rastreabilidade e auditoria. **NÃO utiliza blockchain.**
- **Tokenomics:** Tokens próprios (1:1 com BRL), gerenciamento de compra e venda pelo administrador, dedução automática de taxas.
- **Papéis de Usuário:** Administrador, Cliente, Prestador (um usuário pode ter múltiplos papéis).
- **Implantação:** Código versionado no GitHub, backend hospedado em serviço de deploy para aplicações Flask.
- **Prototipagem:** Inicialmente web-based, com transição futura para integração com a API oficial do WhatsApp Business.

## 2. Estrutura de Arquivos e Módulos

O projeto deve seguir uma estrutura modular e organizada para facilitar a manutenção e o entendimento:

- `app.py`: Ponto de entrada da aplicação Flask, inicialização, configuração de extensões (DB, Migrações, etc.).
- `config.py`: Armazena configurações da aplicação, como chaves secretas, URI do banco de dados, configurações de ambiente (desenvolvimento, teste, produção).
- `routes/`: Diretório para Blueprints que definem as rotas da aplicação.
  - `admin_routes.py`: Rotas da área administrativa.
  - `auth_routes.py`: Rotas de autenticação.
  - `cliente_routes.py`: Rotas da área do cliente.
  - `prestador_routes.py`: Rotas da área do prestador.
- `models/`: Diretório para os modelos de dados (SQLAlchemy).
  - `user.py`, `wallet.py`, `transaction.py`, etc.
- `forms/`: Diretório para os formulários (WTForms).
- `services/`: Módulo para encapsular a lógica de negócio e funções utilitárias.
- `templates/`: Diretório para arquivos HTML (Jinja2).
- `static/`: Diretório para arquivos estáticos (CSS, JavaScript, imagens, fontes).
- `tests/`: Diretório para testes automatizados.
- `docs/`: Diretório para documentação do projeto.

## 3. Lógica de Funcionamento e Relacionamentos

- **Autenticação e Autorização:**
  - Usuários se autenticam via `auth_routes.py` e `auth_service.py`.
  - Decoradores (`@login_required`, `@admin_required`) controlam o acesso às rotas.
  - Tokens CSRF são gerados e validados em todos os formulários.
- **Gestão de Usuários:**
  - O administrador gerencia usuários através da área administrativa.
- **Tokenomics e Fluxo de Transações:**
  - A lógica de compra, venda e transferência de tokens é encapsulada em `services/token_service.py`.
  - O sistema de carteiras e escrow interno é gerenciado através de `services/wallet_service.py`.
  - Todas as transações são registradas com IDs únicos e timestamps para auditabilidade completa.

## 4. Conexões e Segurança

- **Conexão com Banco de Dados:** Utilizar SQLAlchemy para prevenir SQL Injection.
- **Sistema de Carteiras Interno:** Implementação de carteiras virtuais no banco de dados com controles rigorosos de integridade e validação de saldos.
- **HTTPS:** Todas as comunicações devem ser criptografadas.
- **Validação de Entrada:** Validação robusta no backend e frontend.
- **Logs de Auditoria:** Todas as ações críticas devem ser logadas.



## 5. Modelo de Transações Interno

**IMPORTANTE:** O sistema **NÃO utiliza blockchain**. Ele implementa um **modelo próprio de transações** no banco de dados relacional que se inspira em conceitos de rastreabilidade e auditabilidade, mas **sem usar qualquer tecnologia blockchain real**. Isso proporciona os benefícios de segurança e controle sem as desvantagens de taxas externas e complexidade.

### 5.1. Características do Modelo Interno

- **Carteiras Virtuais:** Cada usuário possui carteiras virtuais armazenadas no banco de dados com saldos controlados rigorosamente.
- **Sistema de Escrow:** Carteiras especiais para garantias de transações, liberadas apenas após confirmação de conclusão de serviços.
- **Rastreabilidade Total:** Cada transação possui ID único, timestamp e histórico completo de origem e destino.
- **Auditabilidade:** Logs imutáveis de todas as operações para fins de auditoria e compliance.
- **Integridade de Dados:** Validações rigorosas para garantir que saldos nunca fiquem inconsistentes.
- **Atomicidade:** Transações são processadas de forma atômica, garantindo que não ocorram estados intermediários inválidos.

### 5.2. Benefícios do Modelo Próprio

- **Custo Zero de Transação:** Sem taxas de rede externa, todas as operações são internas.
- **Performance Superior:** Transações instantâneas processadas diretamente no banco de dados.
- **Controle Total:** Administração completa do sistema de tokens e carteiras sem dependências externas.
- **Flexibilidade:** Possibilidade de implementar regras de negócio específicas sem limitações externas.
- **Segurança:** Controle total sobre a segurança, validação e auditoria das transações.
- **Simplicidade:** Sem complexidade de contratos inteligentes, wallets externas ou redes descentralizadas.

## 6. Terminologia e Interface do Usuário

### 6.1. Diferenciação de Terminologia por Papel

O sistema utiliza terminologias diferentes dependendo do tipo de usuário para melhor experiência e compreensão:

**Para Administradores:**
- Utilizam a terminologia técnica "tokens" para gerenciamento interno
- Têm acesso a informações sobre tokenomics e configurações do sistema
- Visualizam relatórios técnicos com métricas de tokens

**Para Usuários (Clientes e Prestadores):**
- Visualizam apenas "saldo" em reais brasileiros (R$)
- Não têm conhecimento da existência de tokens internos
- Todas as transações são apresentadas em valores monetários (R$)
- Interface simplificada focada na experiência do usuário

### 6.2. Apresentação de Valores

- **Administradores:** "1000 tokens" ou "1000 TKN"
- **Usuários:** "R$ 1.000,00" ou "Saldo: R$ 1.000,00"

### 6.3. Benefícios da Abordagem

Esta diferenciação permite que os usuários finais tenham uma experiência mais familiar e intuitiva, trabalhando diretamente com valores em reais, enquanto o sistema mantém internamente a lógica de tokens para controle técnico e auditabilidade.


---

## 7. Interface de Usuário e Design (Atualizado em 05/10/2025)

### 7.1. Princípios de Design

O sistema segue princípios modernos de UI/UX para garantir usabilidade e eficiência:

- **Minimalismo:** Textos concisos nos cards e elementos visuais
- **Hierarquia Visual:** Uso de cores e ícones para comunicação rápida
- **Acessibilidade:** Navegação clara com menu lateral expansível
- **Responsividade:** Adaptação para desktop e mobile

### 7.2. Dashboard Administrativo

**Layout:**
- Menu lateral expansível (coluna esquerda, 2/12)
- Conteúdo principal (coluna direita, 10/12)
- Cards de estatísticas na primeira linha

**Cards de Métricas (Primeira Linha):**

| Card | Cor | Ícone | Texto | Métrica |
|------|-----|-------|-------|---------|
| 1º | Azul (`bg-primary`) | `fa-users` | "Usuários" | Total de usuários |
| 2º | Verde (`bg-success`) | `fa-user-check` | "Ativos" | Usuários ativos |
| 3º | Vermelho (`bg-danger`) | `fa-exclamation-triangle` | "Contestações" | Contestações abertas |
| 4º | Amarelo (`bg-warning`) | `fa-file-contract` | "Contratos" | Contratos ativos |
| 5º | Azul claro (`bg-info`) | `fa-check-circle` | "Finalizados" | Contratos finalizados |

**Observações:**
- Textos curtos e objetivos (ex: "Contestações" ao invés de "Contestações em Aberto")
- Card de contestações possui link "Ver Todas" no rodapé
- Cores seguem convenção semântica (vermelho = urgente, verde = ok)

### 7.3. Menu Lateral (Sidebar)

**Estrutura:**
- Header azul com título "Acesso Rápido" e ícone de raio
- Categorias principais expansíveis/colapsáveis
- Subcategorias com indentação visual
- Ícones coloridos para identificação rápida

**Categorias e Subcategorias:**

1. **Dashboard** (link direto)
   - Ícone: `fa-tachometer-alt` (azul)

2. **Usuários** (expansível)
   - Ícone: `fa-users` (verde)
   - Subcategorias:
     - Listar Todos
     - Criar Novo

3. **Tokens** (expansível)
   - Ícone: `fa-coins` (amarelo)
   - Subcategorias:
     - Gerenciar
     - Adicionar

4. **Contestações** (expansível)
   - Ícone: `fa-exclamation-triangle` (vermelho)
   - Subcategorias:
     - Todas
     - Pendentes
     - Em Análise

5. **Contratos** (expansível)
   - Ícone: `fa-file-contract` (azul claro)
   - Subcategorias:
     - Todos
     - Ativos
     - Finalizados

6. **Configurações** (expansível)
   - Ícone: `fa-cogs` (cinza)
   - Subcategorias:
     - Taxas e Multas
     - Segurança

7. **Relatórios** (expansível)
   - Ícone: `fa-chart-bar` (azul)
   - Subcategorias:
     - Financeiro
     - Usuários
     - Contratos

8. **Logs** (link direto)
   - Ícone: `fa-list-alt` (cinza)

**Funcionalidades:**
- Clique na categoria → Expande/colapsa subcategorias
- Animação suave com Bootstrap Collapse
- Visível apenas em telas médias/grandes (desktop)
- Em mobile, usa navbar superior

### 7.4. Sistema de Contestações

**Fluxo de Contestação:**
1. Usuário (cliente ou prestador) abre contestação
2. Valor do contrato é bloqueado em escrow
3. Admin recebe notificação (card vermelho no dashboard)
4. Admin analisa evidências e histórico
5. Admin toma decisão com justificativa obrigatória
6. Sistema distribui valores conforme decisão
7. Ambas as partes são notificadas

**Opções de Decisão:**
- Aprovar - Favor do Cliente (Reembolso Total)
- Aprovar - Favor do Prestador (Pagamento Total)
- Dividir 50/50
- Divisão Personalizada (% customizado)
- Rejeitar Contestação

**Status de Contestação:**
- `pendente` - Aguardando análise (vermelho)
- `em_analise` - Admin analisando (amarelo)
- `resolvida` - Decisão tomada (verde)
- `rejeitada` - Contestação indevida (cinza)

### 7.5. Configurações do Sistema

**Taxas Configuráveis:**
- Taxa de Transação (%)
- Taxa de Saque (R$)
- Taxa de Depósito (R$)
- Valor Mínimo de Saque (R$)

**Multas e Penalidades:**
- Multa por Cancelamento de Contrato (%)
- Multa por Atraso (% por dia)
- Multa Máxima por Atraso (%)
- Multa por Contestação Indevida (R$)
- Prazo para Contestação (dias)

**Segurança:**
- Tamanho Mínimo de Senha
- Autenticação de Dois Fatores (2FA)

### 7.6. Padrões de Cores

**Cores Semânticas:**
- Azul (`primary`) - Informação geral, navegação
- Verde (`success`) - Status positivo, ativo
- Vermelho (`danger`) - Alerta, urgente, contestações
- Amarelo (`warning`) - Atenção, em progresso
- Azul claro (`info`) - Informação complementar
- Cinza (`secondary`) - Neutro, configurações

**Aplicação:**
- Cards seguem cores semânticas
- Badges de status usam as mesmas cores
- Ícones do menu lateral coloridos para identificação

### 7.7. Responsividade

**Desktop (≥768px):**
- Menu lateral visível
- Cards em linha (4-5 cards por linha)
- Conteúdo em 10 colunas

**Mobile (<768px):**
- Menu lateral oculto
- Navbar superior com menu hambúrguer
- Cards empilhados verticalmente
- Conteúdo em largura total

---

## 8. Atualizações Recentes (05/10/2025)

### 8.1. Melhorias de UI/UX

✅ **Cards do Dashboard:**
- Textos reduzidos para visual mais limpo
- "Contestações em Aberto" → "Contestações"
- "Contratos Ativos" → "Contratos"
- "Contratos Finalizados" → "Finalizados"
- "Usuários Ativos" → "Ativos"

✅ **Menu Lateral Moderno:**
- Implementado menu expansível com subcategorias
- 8 categorias principais com 20+ subcategorias
- Ícones coloridos para identificação rápida
- Acesso direto a funcionalidades específicas

✅ **Sistema de Contestações:**
- Card vermelho no dashboard para visibilidade
- Templates completos de listagem e análise
- Formulário de decisão com 5 opções
- Integração com sistema de escrow

✅ **Configurações Completas:**
- Gestão de taxas (transação, saque, depósito)
- Configuração de multas e penalidades
- Parâmetros de contestação
- Interface intuitiva com formulários separados

### 8.2. Arquivos Modificados

**Templates:**
- `/templates/admin/dashboard.html` - Cards atualizados
- `/templates/admin/base_admin.html` - Menu lateral moderno
- `/templates/admin/contestacoes.html` - Lista de contestações
- `/templates/admin/analisar_contestacao.html` - Análise individual
- `/templates/admin/configuracoes.html` - Taxas e multas

**Backend:**
- `/routes/admin_routes.py` - Rotas de contestações e configurações
- `/services/admin_service.py` - Stats atualizadas

**Documentação:**
- `/docs/MELHORIAS_DASHBOARD_CONFIG.md` - Documentação de melhorias
- `/docs/MELHORIAS_MENU_LATERAL.md` - Documentação do menu
- `/docs/PLANTA_ARQUITETONICA.md` - Esta atualização

### 8.3. Sistema de Convites (Atualização 06/10/2025)

**Funcionalidades Implementadas:**

**Criação de Convites por Clientes:**
- Cliente pode convidar prestadores específicos por email
- Especificação de serviço, valor, data e descrição detalhada
- Validação de saldo: cliente deve ter valor do serviço + taxa de contestação
- Geração de token único para acesso seguro ao convite

**Gestão de Convites por Prestadores:**
- Visualização de convites recebidos com detalhes completos
- Possibilidade de aceitar, recusar ou propor alterações
- Alteração de valor e data de entrega antes da aceitação
- Validação de saldo: prestador deve ter taxa de contestação

**Fluxo de Conversão:**
- Convite aceito automaticamente vira ordem de serviço
- Convite recusado expira e notifica o cliente
- Sistema de notificações automáticas para todas as ações

**Cadastro via Convite:**
- Usuários não cadastrados podem se registrar via link do convite
- Usuários existentes fazem login direto pelo convite
- Redirecionamento automático para análise do convite

### 8.4. Sistema de Segurança Administrativo (Atualização 06/10/2025)

**Funcionalidades de Segurança Implementadas:**

**Troca de Senha para Administradores:**
- Interface segura para alteração de senha administrativa
- Validação de senha atual obrigatória
- Validação de força da nova senha (mínimo 6 caracteres)
- Confirmação de senha com validação em tempo real
- Logs de auditoria para mudanças de senha
- Acesso via dropdown do usuário e menu lateral de configurações

**Recursos de Segurança:**
- Validação dupla de senha (atual + nova)
- Feedback visual em tempo real para confirmação de senha
- Prevenção de senhas fracas
- Confirmação obrigatória antes da alteração
- Redirecionamento seguro após alteração bem-sucedida

**Interface de Segurança:**
- Template responsivo com design consistente
- Dicas de segurança integradas
- Validação JavaScript para melhor UX
- Tratamento de erros robusto

### 8.5. Correções de Sistema (Atualização 06/10/2025)

**Problemas Corrigidos:**

**Erro 500 na Criação de Usuários:**
- Criados templates faltantes: `criar_usuario.html` e `editar_usuario.html`
- Implementada criação automática de carteira para novos usuários
- Adicionado tratamento de erro robusto na criação de carteiras
- Validações de formulário com máscaras para CPF e telefone
- Interface responsiva com feedback visual em tempo real

**Templates de Gestão de Usuários:**
- Template de criação com validações completas
- Template de edição com informações do usuário
- Máscaras automáticas para CPF e telefone
- Validação de senhas em tempo real
- Ações perigosas com confirmação obrigatória

**Melhorias de UX:**
- Breadcrumbs para navegação
- Cards informativos com dicas
- Feedback visual para ações do usuário
- Validação JavaScript para melhor experiência

### 8.6. Sistema de Copyright e Versionamento (Atualização 06/10/2025)

**Funcionalidades Implementadas:**

**Sistema de Versionamento:**
- Arquivo `version.py` centralizado com informações de versão
- Versão atual: 1.2.1 (Sistema Combinado)
- Build number automático com data
- Contexto global de templates para informações de versão

**Informações de Copyright:**
- Copyright: © 2025 W-jr (89) 98137-5841
- Informações de contato integradas
- Footer atualizado em todos os templates
- Página "Sobre" com informações completas do desenvolvedor

**Implementação Técnica:**
- Context processor para injeção automática de variáveis
- Template base atualizado com footer informativo
- Rota `/sobre` funcional com informações detalhadas
- Integração com página inicial (link no menu)

**Informações Exibidas:**
- Nome do sistema e versão
- Data e número do build
- Informações de copyright e desenvolvedor
- Telefone de contato: (89) 98137-5841
- Link para WhatsApp integrado

### 8.5. Próximas Implementações

**Banco de Dados:**
- [x] Modelo `Invite` com campos completos (implementado)
- [ ] Modelo `Contestacao` com campos completos
- [ ] Modelo `Contrato` com status e histórico
- [ ] Modelo `ConfiguracaoSistema` para persistência
- [ ] Modelo `HistoricoContestacao` para auditoria

**Lógica de Negócio:**
- [x] Sistema de convites completo (implementado)
- [ ] Implementar decisões de contestação
- [ ] Sistema de notificações em tempo real
- [ ] Cálculo automático de multas
- [ ] Bloqueio/liberação de valores em escrow

**Relatórios:**
- [x] Relatório de contratos/ordens com dados reais (implementado)
- [x] Relatório de usuários com estatísticas de carteira (implementado)
- [x] Relatório financeiro com transações e receitas (implementado)
- [x] Relatório de convites com taxas de conversão (implementado)
- [x] Sistema de filtros por data, status e tipo (implementado)
- [x] Exportação para Excel e PDF (implementado)
- [ ] Relatório de contestações por período
- [ ] Taxa de resolução favorável
- [ ] Tempo médio de análise
- [ ] Usuários com mais contestações

---

## 9. Padrões de Templates e Interface

### 9.1. Estrutura Hierárquica de Templates

O sistema segue uma estrutura hierárquica rigorosa para garantir consistência visual e funcional:

**Template Base (`templates/base.html`):**
- Estrutura HTML5 com Bootstrap 5.1.3 e Font Awesome 6.0.0
- Sistema de mensagens flash padronizado
- Blocos principais: `title`, `navbar`, `content`, `footer`, `extra_css`, `extra_js`

**Templates Base por Papel:**
- **Admin** (`base_admin.html`): Cor azul, terminologia "tokens", sidebar expansível
- **Cliente** (`base_cliente.html`): Cor verde, terminologia "R$", sidebar simples
- **Prestador** (`base_prestador.html`): Cor amarelo, terminologia "R$", cards de oportunidades

### 9.2. Padrões de Design por Papel

| Papel | Cor Principal | Ícone | Terminologia | Layout |
|-------|---------------|-------|--------------|--------|
| Admin | Azul (`bg-primary`) | `fas fa-cog` | "Tokens" | Sidebar expansível + subcategorias |
| Cliente | Verde (`bg-success`) | `fas fa-user-tie` | "Saldo em R$" | Sidebar + cards informativos |
| Prestador | Amarelo (`bg-warning`) | `fas fa-user-cog` | "Saldo em R$" | Sidebar + cards de oportunidades |

### 9.3. Cores Semânticas Padronizadas

| Contexto | Cor | Classe Bootstrap | Uso Específico |
|----------|-----|------------------|----------------|
| Admin/Informação | Azul | `bg-primary` | Navegação admin, cards informativos |
| Cliente/Sucesso | Verde | `bg-success` | Navegação cliente, status positivo |
| Prestador/Atenção | Amarelo | `bg-warning` | Navegação prestador, alertas |
| Erro/Urgente | Vermelho | `bg-danger` | Contestações, erros críticos |
| Informação Complementar | Azul claro | `bg-info` | Dados secundários |
| Neutro/Configurações | Cinza | `bg-secondary` | Configurações, logs |

### 9.4. Ícones Padronizados (Font Awesome)

**Funcionalidades Principais:**
- Dashboard: `fas fa-tachometer-alt`
- Usuários: `fas fa-users`
- Carteira/Saldo: `fas fa-wallet`
- Tokens (Admin): `fas fa-coins`
- Ordens: `fas fa-clipboard-list`
- Contestações: `fas fa-exclamation-triangle`
- Configurações: `fas fa-cogs`
- Relatórios: `fas fa-chart-bar`
- Convites: `fas fa-envelope-open-text`
- Notificações: `fas fa-bell`

### 9.5. Componentes Reutilizáveis

**Cards de Métricas (Padrão):**
```html
<div class="col-md-3 mb-4">
    <div class="card border-0 shadow-sm">
        <div class="card-body text-center">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="card-title text-muted mb-1">TÍTULO</h6>
                    <h3 class="mb-0 text-CONTEXTO">VALOR</h3>
                </div>
                <div class="text-CONTEXTO">
                    <i class="fas fa-ICONE fa-2x"></i>
                </div>
            </div>
        </div>
    </div>
</div>
```

**Formulários Padronizados:**
```html
<div class="mb-3">
    <label for="campo" class="form-label">Label</label>
    <input type="text" class="form-control" id="campo" name="campo" required>
    <div class="form-text">Texto de ajuda (opcional)</div>
</div>
```

### 9.6. Terminologia Diferenciada por Papel

**Implementação Obrigatória:**
- **Administradores:** Veem "1000 tokens", "Tokenomics", métricas técnicas
- **Usuários (Cliente/Prestador):** Veem "R$ 1.000,00", "Saldo", interface simplificada
- **Filtro Obrigatório:** `|format_currency` para conversão automática

**Exemplo de Uso:**
```html
<!-- Admin -->
<span>{{ valor }} tokens</span>

<!-- Cliente/Prestador -->
<span>{{ valor|format_currency }}</span>
```

### 9.7. Layout Responsivo

**Desktop (≥768px):**
- Sidebar visível (2/12 colunas)
- Conteúdo principal (10/12 colunas)
- Menu lateral expansível (admin)

**Mobile (<768px):**
- Sidebar oculta
- Navbar superior com menu hambúrguer
- Conteúdo em largura total
- Cards empilhados verticalmente

### 9.8. Padrões de Acessibilidade

**Obrigatórios em Todos os Templates:**
- `alt` em todas as imagens
- `aria-label` em botões sem texto
- `role` em elementos interativos
- Contraste adequado (WCAG 2.1)
- Navegação por teclado funcional
- Estrutura semântica (h1, h2, etc.)

### 9.9. Estrutura de Arquivos de Templates

```
templates/
├── base.html                    # Template base principal
├── admin/
│   ├── base_admin.html         # Base para admin (azul, tokens)
│   ├── dashboard.html          # Dashboard com cards coloridos
│   ├── convites.html           # Gestão de convites (admin)
│   └── ...                     # Outras páginas admin
├── cliente/
│   ├── base_cliente.html       # Base para cliente (verde, R$)
│   ├── dashboard.html          # Dashboard com saldo
│   ├── convites.html           # Criar/gerenciar convites
│   └── ...                     # Outras páginas cliente
├── prestador/
│   ├── base_prestador.html     # Base para prestador (amarelo, R$)
│   ├── dashboard.html          # Dashboard com oportunidades
│   ├── convites.html           # Responder convites
│   └── ...                     # Outras páginas prestador
├── auth/
│   ├── admin_login.html        # Login admin
│   ├── user_login.html         # Login usuário
│   └── convite_cadastro.html   # Cadastro via convite
├── errors/
│   ├── 404.html               # Página não encontrada
│   ├── 500.html               # Erro interno
│   └── ...                    # Outros erros
└── shared/
    ├── convite_detalhes.html  # Componente de detalhes do convite
    └── ...                    # Outros componentes compartilhados
```

### 9.10. Convenções de Nomenclatura

**Arquivos de Template:**
- Snake_case: `base_admin.html`, `criar_convite.html`
- Descritivo e agrupado por funcionalidade
- Prefixo por papel quando necessário

**Classes CSS Customizadas:**
- Prefixo `sc-` para classes do Sistema Combinado
- BEM methodology para componentes complexos
- Bootstrap padrão sempre que possível

### 9.11. Validação e Checklist de Templates

**Checklist Obrigatório para Novos Templates:**
- [ ] Herda do template base correto (admin/cliente/prestador)
- [ ] Usa terminologia apropriada ao papel
- [ ] Implementa responsividade (desktop/mobile)
- [ ] Segue padrões de cores definidos
- [ ] Inclui ícones padronizados Font Awesome
- [ ] Atende critérios de acessibilidade WCAG 2.1
- [ ] Funciona em Chrome, Firefox, Safari
- [ ] Validação HTML5 sem erros
- [ ] Navegação por teclado funcional

### 9.12. Sistema de Convites - Padrões Específicos

**Templates Específicos para Convites:**
- `cliente/criar_convite.html`: Formulário de criação
- `cliente/meus_convites.html`: Lista de convites enviados
- `prestador/convites_recebidos.html`: Lista de convites recebidos
- `prestador/responder_convite.html`: Interface de resposta
- `auth/convite_cadastro.html`: Cadastro via token de convite
- `shared/convite_card.html`: Componente reutilizável de convite

**Padrões de Interface para Convites:**
- Cards com status colorido (pendente: amarelo, aceito: verde, recusado: vermelho)
- Ícone padrão: `fas fa-envelope-open-text`
- Terminologia: "Convite de Serviço", "Proposta", "Solicitação"
- Valores sempre em R$ para usuários (cliente/prestador)

---

## 10. Dashboard Financeiro Avançado (Implementado em 06/10/2025)

### 10.1. Funcionalidades Implementadas

**Cards de Taxas Recebidas no Dashboard Principal:**
- Card "Taxas Totais" - Receita histórica completa em tokens
- Card "Receita do Mês" - Receita mensal com número de transações
- Card "Taxa Média" - Taxa média por transação mensal
- Card "% do Volume" - Percentual de taxas sobre volume total de transações

**Seção Financeira Completa no Menu Admin:**
- **Dashboard Financeiro** (`/admin/financeiro/dashboard`)
  - Gráfico de evolução das receitas (6 meses)
  - Top 10 usuários geradores de taxa
  - Previsões baseadas em tendências históricas
  - Resumo completo de tokens e distribuição
- **Receitas** (`/admin/financeiro/receitas`)
  - Detalhamento de todas as transações de taxa
  - Filtros por período (7, 30, 90, 365 dias)
  - Estatísticas de receita diária
- **Configuração de Taxas** (`/admin/financeiro/taxas`)
  - Interface para configurar taxa do sistema (%)
  - Configuração de taxas de saque e depósito
  - Simulador de impacto em tempo real
  - Validações de segurança para alterações
- **Previsões** (`/admin/financeiro/previsoes`)
  - Análise de tendências baseada em 12 meses
  - Cálculo de crescimento percentual
  - Previsões mensais, trimestrais e anuais
- **Relatórios Financeiros** (`/admin/financeiro/relatorios`)
  - Relatórios consolidados por período
  - Análise de lucratividade e margem
  - Integração com ReportService existente

**Card de Distribuição de Tokens:**
- Visualização detalhada de tokens disponíveis vs em escrow
- Percentuais de distribuição em tempo real
- Barra de progresso visual da distribuição
- Métricas de circulação avançadas

### 10.2. Arquivos Implementados

**Backend:**
- `services/admin_service.py` - Métricas financeiras expandidas
- `routes/admin_routes.py` - 5 novas rotas financeiras

**Frontend:**
- `templates/admin/dashboard.html` - Cards de taxas e distribuição
- `templates/admin/base_admin.html` - Menu financeiro expandido
- `templates/admin/financeiro_dashboard.html` - Dashboard financeiro completo
- `templates/admin/financeiro_taxas.html` - Configuração de taxas

**Funcionalidades Técnicas:**
- Integração com Chart.js para gráficos interativos
- Simulador de impacto de taxas em tempo real
- Cálculos de previsão baseados em tendências
- Terminologia técnica "tokens" para administradores
- Tratamento de erros robusto com fallbacks

### 10.3. Correções Críticas Implementadas

**Erro de Template Corrigido:**
- **Problema:** `url_for('sobre')` causando erro 500 na página inicial
- **Solução:** Corrigido para `url_for('home.about')` 
- **Impacto:** Sistema agora funciona sem erros críticos

### 10.4. Métricas Adicionadas ao AdminService

**Novas Estatísticas Financeiras:**
- `taxas_totais` - Total histórico de taxas arrecadadas
- `transacoes_com_taxa_mes` - Número de transações que geraram taxa no mês
- `taxa_media_mes` - Taxa média por transação mensal
- `tokens_em_escrow` - Tokens bloqueados em transações
- `tokens_disponiveis_usuarios` - Tokens livres com usuários
- `percentual_escrow` - Percentual de tokens em escrow

**Integração com WalletService:**
- Cálculos baseados em dados reais do sistema de tokenomics
- Validações de integridade matemática
- Fallbacks para casos de erro nos cálculos

---

**Última Atualização:** 06 de Outubro de 2025  
**Versão do Sistema:** 1.2.1  
**Status:** Dashboard Financeiro Avançado Implementado
