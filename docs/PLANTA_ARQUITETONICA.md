# Planta Arquitetônica Detalhada - Sistema Combinado v2.0

## 1. Visão Geral da Arquitetura

O sistema "Combinado" é uma aplicação web baseada em Flask, projetada para gerenciar transações de tokens próprios (1 token = 1 real) entre clientes e prestadores de serviços, com um administrador centralizado para controle de tokenomics e configurações. O sistema implementa um modelo conceitual de blockchain internamente, sem usar blockchain real, para garantir rastreabilidade, auditabilidade e segurança das transações, evitando taxas de transação externa.

- **Framework Principal:** Flask (Python)
- **Banco de Dados:** SQLAlchemy com SQLite para desenvolvimento e PostgreSQL para produção.
- **Modelo Blockchain Interno:** O sistema segue o modelo conceitual de blockchain (carteiras, escrow, rastreabilidade, auditabilidade) mas implementado internamente no banco de dados, sem usar blockchain real para evitar taxas de transação. Todas as transações são rastreáveis e auditáveis através de logs internos.
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



## 5. Modelo Blockchain Interno

O sistema implementa um modelo conceitual de blockchain sem usar tecnologia blockchain real, proporcionando os benefícios de segurança, rastreabilidade e auditabilidade sem as desvantagens de taxas de transação externa.

### 5.1. Características do Modelo Interno

- **Carteiras Virtuais:** Cada usuário possui carteiras virtuais armazenadas no banco de dados com saldos controlados rigorosamente.
- **Sistema de Escrow:** Carteiras especiais para garantias de transações, liberadas apenas após confirmação de conclusão de serviços.
- **Rastreabilidade Total:** Cada transação possui ID único, timestamp e histórico completo de origem e destino.
- **Auditabilidade:** Logs imutáveis de todas as operações para fins de auditoria e compliance.
- **Integridade de Dados:** Validações rigorosas para garantir que saldos nunca fiquem inconsistentes.
- **Atomicidade:** Transações são processadas de forma atômica, garantindo que não ocorram estados intermediários inválidos.

### 5.2. Benefícios do Modelo

- **Custo Zero de Transação:** Sem taxas de blockchain externa.
- **Performance Superior:** Transações instantâneas sem dependência de rede externa.
- **Controle Total:** Administração completa do sistema de tokens e carteiras.
- **Flexibilidade:** Possibilidade de implementar regras de negócio específicas.
- **Segurança:** Controle total sobre a segurança e validação das transações.

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

### 8.3. Próximas Implementações

**Banco de Dados:**
- [ ] Modelo `Contestacao` com campos completos
- [ ] Modelo `Contrato` com status e histórico
- [ ] Modelo `ConfiguracaoSistema` para persistência
- [ ] Modelo `HistoricoContestacao` para auditoria

**Lógica de Negócio:**
- [ ] Implementar decisões de contestação
- [ ] Sistema de notificações em tempo real
- [ ] Cálculo automático de multas
- [ ] Bloqueio/liberação de valores em escrow

**Relatórios:**
- [ ] Relatório de contestações por período
- [ ] Taxa de resolução favorável
- [ ] Tempo médio de análise
- [ ] Usuários com mais contestações

---

**Última Atualização:** 05 de Outubro de 2025  
**Versão do Sistema:** 1.1.0  
**Status:** Em Desenvolvimento Ativo
