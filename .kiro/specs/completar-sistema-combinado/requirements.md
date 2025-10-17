# Documento de Requisitos

## Introdução

O Sistema Combinado é uma plataforma web desenvolvida em Flask que conecta clientes e prestadores de serviços com sistema de pagamentos protegidos por escrow usando tokens próprios (1 token = 1 real). O sistema utiliza um modelo interno próprio de transações (NÃO blockchain) implementado totalmente no banco de dados relacional para rastreabilidade e auditabilidade. O sistema já possui uma base sólida implementada, mas precisa ser completado, testado e corrigido seguindo rigorosamente o PDR (Processo de Mudanças Rigoroso) e respeitando a terminologia diferenciada: administradores veem "tokens", usuários finais veem apenas "saldo em R$".

## Requisitos

### Requisito 1

**User Story:** Como desenvolvedor, eu quero que o sistema rode completamente sem erros, para que possa testar e validar todas as funcionalidades implementadas.

#### Critérios de Aceitação

1. QUANDO o sistema for iniciado ENTÃO o servidor Flask DEVE rodar na porta 5001 sem erros
2. QUANDO acessar a página inicial ENTÃO o sistema DEVE carregar corretamente todos os templates
3. QUANDO tentar fazer login ENTÃO o sistema DEVE autenticar usuários corretamente
4. QUANDO navegar entre páginas ENTÃO todas as rotas DEVEM funcionar sem erro 404 ou 500

### Requisito 2

**User Story:** Como usuário do sistema, eu quero que todas as interfaces funcionem corretamente, para que possa usar o sistema sem problemas.

#### Critérios de Aceitação

1. QUANDO acessar qualquer página ENTÃO os templates HTML DEVEM renderizar corretamente
2. QUANDO fazer login como cliente ENTÃO DEVE ser redirecionado para o dashboard do cliente
3. QUANDO fazer login como prestador ENTÃO DEVE ser redirecionado para o dashboard do prestador
4. QUANDO fazer login como admin ENTÃO DEVE ser redirecionado para o painel administrativo
5. QUANDO navegar pelo menu ENTÃO todos os links DEVEM funcionar corretamente

### Requisito 3

**User Story:** Como cliente, eu quero gerenciar minha carteira de tokens, para que possa fazer pagamentos pelos serviços.

#### Critérios de Aceitação

1. QUANDO acessar minha carteira ENTÃO DEVE ver meu saldo atual em tokens
2. QUANDO fazer uma transação ENTÃO o saldo DEVE ser atualizado corretamente
3. QUANDO visualizar histórico ENTÃO DEVE ver todas as transações realizadas
4. QUANDO o saldo for insuficiente ENTÃO o sistema DEVE impedir a transação

### Requisito 4

**User Story:** Como prestador, eu quero receber pagamentos pelos serviços prestados, para que possa monetizar meu trabalho.

#### Critérios de Aceitação

1. QUANDO completar um serviço ENTÃO DEVE receber os tokens na carteira
2. QUANDO acessar minha carteira ENTÃO DEVE ver o saldo disponível
3. QUANDO visualizar histórico ENTÃO DEVE ver todos os recebimentos
4. QUANDO houver disputa ENTÃO os tokens DEVEM ficar em escrow até resolução

### Requisito 5

**User Story:** Como administrador, eu quero gerenciar todo o sistema, para que possa controlar usuários, tokens e resolver problemas.

#### Critérios de Aceitação

1. QUANDO acessar o painel admin ENTÃO DEVE ver estatísticas do sistema
2. QUANDO gerenciar usuários ENTÃO DEVE poder criar, editar e desativar contas
3. QUANDO gerenciar tokens ENTÃO DEVE poder ajustar saldos e ver transações
4. QUANDO acessar logs ENTÃO DEVE ver todas as ações importantes do sistema

### Requisito 6

**User Story:** Como usuário, eu quero que o sistema seja seguro, para que meus dados e transações estejam protegidos.

#### Critérios de Aceitação

1. QUANDO fazer login ENTÃO as senhas DEVEM estar hasheadas no banco
2. QUANDO navegar pelo sistema ENTÃO as sessões DEVEM ser seguras
3. QUANDO fazer transações ENTÃO DEVE haver logs de auditoria
4. QUANDO ocorrer erro ENTÃO informações sensíveis NÃO DEVEM ser expostas

### Requisito 7

**User Story:** Como desenvolvedor, eu quero que o sistema tenha tratamento de erros robusto, para que problemas sejam identificados e corrigidos rapidamente.

#### Critérios de Aceitação

1. QUANDO ocorrer erro 404 ENTÃO DEVE mostrar página de erro personalizada
2. QUANDO ocorrer erro 500 ENTÃO DEVE mostrar página de erro e logar o problema
3. QUANDO houver erro de validação ENTÃO DEVE mostrar mensagem clara ao usuário
4. QUANDO falhar conexão com banco ENTÃO DEVE tratar o erro graciosamente

### Requisito 8

**User Story:** Como usuário, eu quero que todas as funcionalidades do sistema de ordens funcionem, para que possa criar e gerenciar serviços.

#### Critérios de Aceitação

1. QUANDO criar uma ordem ENTÃO ela DEVE ser salva no banco de dados
2. QUANDO aceitar uma ordem ENTÃO o status DEVE ser atualizado
3. QUANDO completar uma ordem ENTÃO os tokens DEVEM ser transferidos
4. QUANDO cancelar uma ordem ENTÃO os tokens em escrow DEVEM ser devolvidos

### Requisito 9

**User Story:** Como sistema, eu quero respeitar a terminologia diferenciada por tipo de usuário, para que cada papel veja as informações adequadas ao seu contexto.

#### Critérios de Aceitação

1. QUANDO administrador acessar o sistema ENTÃO DEVE ver terminologia "tokens" em interfaces administrativas
2. QUANDO cliente ou prestador acessar o sistema ENTÃO DEVE ver apenas "saldo em R$" sem menção a tokens
3. QUANDO exibir valores ENTÃO administradores veem "1000 tokens" e usuários veem "R$ 1.000,00" usando o filtro format_currency
4. QUANDO usuário for dual (cliente+prestador) ENTÃO DEVE poder alternar entre os papéis mantendo a terminologia correta

### Requisito 10

**User Story:** Como sistema, eu quero implementar o modelo interno de transações sem blockchain, para que tenha controle total e custo zero de transação.

#### Critérios de Aceitação

1. QUANDO processar transação ENTÃO DEVE usar apenas banco de dados relacional
2. QUANDO registrar transação ENTÃO DEVE ter ID único, timestamp e rastreabilidade completa
3. QUANDO validar saldo ENTÃO DEVE garantir integridade sem estados intermediários inválidos
4. QUANDO auditar ENTÃO DEVE ter logs imutáveis de todas as operações

### Requisito 11

**User Story:** Como desenvolvedor, eu quero seguir o PDR rigorosamente, para que todas as mudanças sejam controladas e documentadas.

#### Critérios de Aceitação

1. QUANDO implementar mudança ENTÃO DEVE seguir as 7 etapas do PDR obrigatoriamente
2. QUANDO modificar código ENTÃO DEVE mapear impacto em todos os componentes afetados
3. QUANDO criar funcionalidade ENTÃO DEVE desenvolver testes automatizados correspondentes
4. QUANDO fazer deploy ENTÃO DEVE validar em ambiente de testes primeiro

### Requisito 12

**User Story:** Como administrador, eu quero um dashboard moderno com menu lateral expansível, para que possa navegar facilmente entre as funcionalidades.

#### Critérios de Aceitação

1. QUANDO acessar dashboard ENTÃO DEVE ver cards coloridos com métricas (usuários, ativos, contestações, contratos, finalizados)
2. QUANDO usar menu lateral ENTÃO DEVE ter 8 categorias principais com subcategorias expansíveis
3. QUANDO visualizar contestações ENTÃO card vermelho DEVE destacar urgência
4. QUANDO navegar ENTÃO ícones coloridos DEVEM facilitar identificação rápida

### Requisito 13

**User Story:** Como cliente, eu quero criar convites para prestadores, para que possa solicitar serviços específicos de pessoas conhecidas.

#### Critérios de Aceitação

1. QUANDO criar um convite ENTÃO DEVE especificar serviço, valor, data e dados do prestador convidado
2. QUANDO enviar convite ENTÃO o prestador DEVE receber notificação para aceitar ou recusar
3. QUANDO prestador recusar ENTÃO convite DEVE expirar e cliente ser notificado da recusa
4. QUANDO prestador aceitar ENTÃO DEVE poder alterar valor e data antes de confirmar
5. QUANDO prestador confirmar alterações ENTÃO convite DEVE se tornar uma ordem de serviço ativa

### Requisito 14

**User Story:** Como prestador, eu quero receber e gerenciar convites de clientes, para que possa aceitar trabalhos direcionados.

#### Critérios de Aceitação

1. QUANDO receber convite ENTÃO DEVE ver detalhes do serviço solicitado pelo cliente
2. QUANDO analisar convite ENTÃO DEVE poder aceitar, recusar ou propor alterações
3. QUANDO propor alterações ENTÃO DEVE poder modificar valor e data de entrega
4. QUANDO confirmar aceitação ENTÃO convite DEVE se transformar em ordem de serviço
5. QUANDO recusar convite ENTÃO cliente DEVE ser notificado automaticamente

### Requisito 15

**User Story:** Como sistema, eu quero implementar validações de saldo para convites e ordens, para que ambas as partes tenham recursos suficientes.

#### Critérios de Aceitação

1. QUANDO cliente criar convite ENTÃO DEVE ter saldo para pagar valor do serviço + taxa de contestação
2. QUANDO prestador aceitar convite ENTÃO DEVE ter saldo para pagar taxa de contestação
3. QUANDO ordem for criada ENTÃO ambos os saldos DEVEM ser validados antes do bloqueio
4. QUANDO não houver saldo suficiente ENTÃO sistema DEVE impedir criação/aceitação
5. QUANDO taxa de serviço for cobrada ENTÃO DEVE ser apenas do prestador após cliente pagar pelo serviço

### Requisito 16

**User Story:** Como usuário convidado, eu quero poder me cadastrar através de convite, para que possa participar do sistema facilmente.

#### Critérios de Aceitação

1. QUANDO receber convite por email/link ENTÃO DEVE poder acessar página de cadastro específica
2. QUANDO já tiver cadastro ENTÃO DEVE poder fazer login diretamente pelo convite
3. QUANDO não tiver cadastro ENTÃO DEVE poder se registrar mantendo dados do convite
4. QUANDO completar cadastro ENTÃO DEVE ser redirecionado para análise do convite
5. QUANDO aceitar convite após cadastro ENTÃO DEVE seguir fluxo normal de aceitação

### Requisito 17

**User Story:** Como sistema, eu quero implementar modelo de dados completo para convites, para que todas as funcionalidades sejam suportadas adequadamente.

#### Critérios de Aceitação

1. QUANDO criar modelo Invite ENTÃO DEVE ter campos: client_id, invited_email, service_title, service_description
2. QUANDO gerenciar valores ENTÃO DEVE ter original_value (cliente) e final_value (prestador após alterações)
3. QUANDO controlar status ENTÃO DEVE ter: pendente, aceito, recusado, expirado, convertido
4. QUANDO gerar acesso ENTÃO DEVE ter token único e campos de data (created_at, expires_at, responded_at)
5. QUANDO converter ENTÃO DEVE relacionar com Order criada (invite_id → order_id)

### Requisito 18

**User Story:** Como sistema, eu quero implementar InviteService com todas as operações de negócio, para que o fluxo de convites funcione completamente.

#### Critérios de Aceitação

1. QUANDO criar convite ENTÃO create_invite() DEVE validar saldo cliente (valor + taxa contestação)
2. QUANDO aceitar convite ENTÃO accept_invite() DEVE validar saldo prestador (taxa contestação)
3. QUANDO recusar convite ENTÃO reject_invite() DEVE notificar cliente automaticamente
4. QUANDO alterar termos ENTÃO update_invite_terms() DEVE permitir mudança de valor e data
5. QUANDO converter ENTÃO convert_invite_to_order() DEVE criar ordem e bloquear saldos em escrow

### Requisito 19

**User Story:** Como sistema, eu quero implementar notificações automáticas para convites, para que usuários sejam informados de todas as ações.

#### Critérios de Aceitação

1. QUANDO enviar convite ENTÃO prestador DEVE receber notificação por email/sistema
2. QUANDO aceitar convite ENTÃO cliente DEVE ser notificado da aceitação
3. QUANDO recusar convite ENTÃO cliente DEVE ser notificado da recusa
4. QUANDO alterar termos ENTÃO cliente DEVE ser notificado das alterações propostas
5. QUANDO expirar convite ENTÃO ambas as partes DEVEM ser notificadas da expiração

### Requisito 20

**User Story:** Como administrador, eu quero trocar minha senha com segurança, para que possa manter minha conta protegida.

#### Critérios de Aceitação

1. QUANDO acessar página de troca de senha ENTÃO DEVE carregar sem erro 500
2. QUANDO inserir senha atual incorreta ENTÃO DEVE mostrar erro claro
3. QUANDO inserir senhas que não coincidem ENTÃO DEVE validar antes de processar
4. QUANDO trocar senha com sucesso ENTÃO DEVE confirmar e manter sessão ativa
5. QUANDO ocorrer erro ENTÃO DEVE ser tratado graciosamente com log de auditoria

### Requisito 21

**User Story:** Como administrador, eu quero analisar contestações de ordens, para que possa resolver disputas entre usuários.

#### Critérios de Aceitação

1. QUANDO acessar lista de contestações ENTÃO DEVE mostrar disputas reais do sistema
2. QUANDO clicar em contestação específica ENTÃO DEVE carregar detalhes sem erro 500
3. QUANDO analisar disputa ENTÃO DEVE ver histórico completo da ordem
4. QUANDO tomar decisão ENTÃO DEVE processar resolução e atualizar status
5. QUANDO resolver disputa ENTÃO tokens DEVEM ser distribuídos conforme decisão

### Requisito 22

**User Story:** Como usuário, eu quero poder ser cliente E prestador simultaneamente, para que possa usar o sistema em ambos os papéis conforme necessário.

#### Critérios de Aceitação

1. QUANDO usuário tiver papéis "cliente,prestador" ENTÃO DEVE poder alternar entre eles
2. QUANDO alternar papel ENTÃO interface DEVE mudar para contexto apropriado
3. QUANDO receber convite como prestador ENTÃO DEVE poder aceitar mesmo sendo cliente
4. QUANDO criar convite como cliente ENTÃO DEVE poder convidar outros prestadores
5. QUANDO navegar pelo sistema ENTÃO DEVE manter papel ativo consistente em todas as páginas