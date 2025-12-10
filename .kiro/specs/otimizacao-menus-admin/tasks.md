# Plano de Implementação - Otimização de Menus do Painel Administrativo

- [x] 1. Auditar e documentar estrutura atual dos menus
  - Identificar todas as duplicações e problemas no menu lateral do base_admin.html
  - Listar todos os submenus e suas rotas correspondentes
  - Documentar quais submenus apontam para a mesma URL
  - Identificar botões sem função ou rotas inexistentes
  - _Requisitos: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1_

- [x] 2. Corrigir menu de Configurações
- [x] 2.1 Separar rotas de Taxas e Segurança
  - Criar rota específica para configurações de taxas: `/admin/configuracoes/taxas`
  - Criar rota específica para configurações de segurança: `/admin/configuracoes/seguranca`
  - Implementar lógica de salvamento separada para cada seção
  - Adicionar validação de dados específica para cada tipo de configuração
  - _Requisitos: 1.1, 1.2_

- [x] 2.2 Atualizar template configuracoes.html
  - Adicionar IDs de âncora para seções (#taxas, #seguranca)
  - Separar formulários de taxas e segurança em cards distintos
  - Atualizar actions dos formulários para rotas específicas
  - Garantir que cada seção tenha título e descrição clara
  - _Requisitos: 1.3, 1.4_

- [x] 2.3 Atualizar menu lateral para Configurações
  - Modificar submenu de Configurações no base_admin.html
  - Criar link para "Taxas do Sistema" apontando para rota específica
  - Criar link para "Segurança" usando âncora (#seguranca)
  - Remover duplicações de submenus
  - Validar que cada submenu aponta para funcionalidade única
  - _Requisitos: 1.3, 1.5_

- [x] 3. Implementar sistema de abas para Relatórios
- [x] 3.1 Criar estrutura de abas no template relatorios.html
  - Implementar nav-tabs do Bootstrap com 3 abas (Financeiro, Usuários, Contratos)
  - Criar tab-panes correspondentes com IDs únicos (#financeiro, #usuarios, #contratos)
  - Adicionar conteúdo específico para cada aba
  - Implementar filtros específicos dentro de cada aba
  - _Requisitos: 2.1, 2.3_

- [x] 3.2 Implementar JavaScript para navegação por âncoras
  - Criar script para detectar hash na URL ao carregar página
  - Ativar aba correspondente ao hash automaticamente
  - Atualizar hash da URL ao trocar de aba
  - Garantir fallback para primeira aba se hash inválido
  - _Requisitos: 2.2, 2.5_

- [x] 3.3 Atualizar menu lateral para Relatórios
  - Modificar submenus de Relatórios no base_admin.html
  - Criar links com âncoras para cada tipo de relatório
  - Garantir que cada submenu navega para aba correta
  - Remover submenus duplicados
  - _Requisitos: 2.2, 2.4_

- [x] 4. Corrigir visibilidade do menu lateral em Convites
- [x] 4.1 Diagnosticar problema de CSS/JavaScript
  - Inspecionar template convites.html para identificar causa do desaparecimento
  - Verificar se template estende corretamente base_admin.html
  - Identificar conflitos de CSS que possam ocultar menu
  - Verificar se há JavaScript que remove menu lateral
  - _Requisitos: 3.1, 3.2_

- [x] 4.2 Corrigir template e estilos
  - Garantir que convites.html estende base_admin.html corretamente
  - Adicionar CSS para forçar visibilidade do menu se necessário
  - Remover código JavaScript que possa estar ocultando menu
  - Testar visibilidade em diferentes resoluções de tela
  - _Requisitos: 3.1, 3.2_

- [x] 4.3 Implementar filtros por status em Convites
  - Modificar rota `/admin/convites` para aceitar parâmetro `status` via query string
  - Implementar lógica de filtro na query do banco de dados
  - Atualizar template para mostrar filtro ativo
  - Adicionar validação de valores de status permitidos
  - _Requisitos: 3.3, 3.5_

- [x] 4.4 Atualizar menu lateral para Convites
  - Criar submenus com filtros: Todos, Pendentes, Aceitos, Recusados
  - Garantir que cada submenu usa query string diferente
  - Remover submenus duplicados
  - Validar que filtros funcionam corretamente
  - _Requisitos: 3.3, 3.4, 3.5_

- [x] 5. Otimizar menu de Contestações
- [x] 5.1 Implementar filtros por status em Contestações
  - Modificar rota `/admin/contestacoes` para aceitar parâmetro `status`
  - Implementar filtro para: Todas, Pendentes, Em Análise
  - Atualizar query do banco para filtrar por status
  - Adicionar validação de valores de status
  - _Requisitos: 4.2, 4.4_

- [x] 5.2 Atualizar menu lateral para Contestações
  - Criar submenus únicos: Todas, Pendentes, Em Análise
  - Garantir que cada submenu aplica filtro diferente via query string
  - Remover submenus duplicados ou sem função
  - Validar que não há redundâncias
  - _Requisitos: 4.1, 4.3, 4.5_

- [x] 6. Otimizar menu de Ordens
- [x] 6.1 Validar e otimizar filtros de status em Ordens
  - Verificar se rota `/admin/ordens` já suporta filtro por status
  - Garantir que todos os status possíveis têm filtro funcional
  - Validar filtros: Todas, Aguardando, Executadas, Concluídas, Contestadas
  - Adicionar tratamento de erro para status inválidos
  - _Requisitos: 5.2, 5.4_

- [x] 6.2 Atualizar menu lateral para Ordens
  - Revisar submenus existentes no base_admin.html
  - Remover submenus duplicados
  - Garantir que cada submenu aplica filtro único
  - Consolidar submenus redundantes
  - _Requisitos: 5.1, 5.3, 5.5_

- [x] 7. Auditoria geral e remoção de elementos sem função
- [x] 7.1 Identificar e remover botões sem função
  - Auditar todos os botões em templates do admin
  - Verificar se cada botão tem rota ou ação JavaScript associada
  - Remover botões que não fazem nada
  - Documentar botões removidos
  - _Requisitos: 6.2, 6.6_

- [x] 7.2 Consolidar funcionalidades duplicadas
  - Identificar funcionalidades acessíveis por múltiplos caminhos
  - Manter apenas o caminho mais intuitivo
  - Remover links/botões redundantes
  - Documentar consolidações realizadas
  - _Requisitos: 6.3, 6.6_

- [x] 7.3 Validar todas as rotas referenciadas
  - Listar todas as rotas usadas em url_for() nos templates
  - Verificar se cada rota existe em admin_routes.py
  - Corrigir ou remover referências a rotas inexistentes
  - Adicionar tratamento de erro para rotas inválidas
  - _Requisitos: 6.4_

- [x] 8. Garantir consistência de navegação
- [x] 8.1 Padronizar estrutura do menu lateral
  - Aplicar mesmo padrão HTML para todos os menus colapsáveis
  - Garantir mesma estrutura de classes CSS
  - Padronizar ícones e espaçamentos
  - Validar que todos os menus colapsam/expandem corretamente
  - _Requisitos: 7.1, 7.3_

- [x] 8.2 Validar navbar superior em todas as páginas
  - Verificar que navbar é consistente em todos os templates admin
  - Garantir que links da navbar funcionam em todas as páginas
  - Validar que badges de notificação aparecem corretamente
  - Testar dropdown de usuário em todas as páginas
  - _Requisitos: 7.2_

- [x] 8.3 Aplicar estilos CSS uniformes
  - Criar ou atualizar arquivo CSS específico para menus admin
  - Garantir que menus colapsáveis têm estilo consistente
  - Padronizar cores, fontes e espaçamentos
  - Adicionar estados hover e active para todos os links
  - _Requisitos: 7.3, 7.5_

- [x] 8.4 Testar funcionalidade de menus colapsáveis
  - Verificar que todos os menus expandem/colapsam corretamente
  - Testar em diferentes navegadores (Chrome, Firefox, Safari)
  - Validar que estado do menu persiste ao navegar entre páginas
  - Garantir que funciona sem JavaScript (fallback)
  - _Requisitos: 7.4_

- [x] 9. Testes de integração e validação final
- [x] 9.1 Executar testes manuais de navegação
  - Clicar em cada item do menu lateral e verificar página carregada
  - Testar todos os filtros de status em convites, ordens e contestações
  - Validar navegação por abas em relatórios
  - Confirmar que âncoras na URL funcionam corretamente
  - _Requisitos: Todos_

- [x] 9.2 Testar responsividade
  - Testar menu em desktop (1920x1080, 1366x768)
  - Testar menu em tablet (768x1024)
  - Testar menu em mobile (375x667)
  - Validar que menu colapsa corretamente em telas pequenas
  - _Requisitos: 7.1, 7.2_

- [x] 9.3 Validar acessibilidade
  - Verificar que todos os links têm texto descritivo
  - Garantir que navegação por teclado funciona
  - Validar contraste de cores para legibilidade
  - Testar com leitor de tela (se possível)
  - _Requisitos: 7.1, 7.2, 7.3_

- [x] 9.4 Documentar alterações realizadas
  - Criar documento listando todas as mudanças nos menus
  - Documentar rotas criadas, modificadas ou removidas
  - Listar submenus removidos e justificativa
  - Criar guia de navegação atualizado para administradores
  - _Requisitos: 6.5_
