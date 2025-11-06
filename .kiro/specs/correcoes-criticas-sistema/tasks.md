# Plano de Implementação - Correções Críticas do Sistema

- [x] 1. Implementar migração de tipos monetários Float para Numeric
  - Criar script de migração SQL para converter campos Float para Numeric(18,2)
  - Implementar MonetaryMigrationService para validar integridade dos dados
  - Modificar modelos Wallet, Transaction, Order, TokenRequest para usar Numeric(18,2)
  - _Requisitos: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Implementar constraints de banco para integridade financeira
  - Adicionar constraints CHECK para prevenir saldo negativo em wallets
  - Criar constraints para validar valores positivos em orders e amounts não-zero em transactions
  - Implementar índices para otimizar consultas financeiras frequentes
  - _Requisitos: 3.1, 3.2, 3.3_

- [x] 3. Implementar sistema de transações atômicas
- [x] 3.1 Criar AtomicTransactionManager com context manager para operações financeiras
  - Implementar context manager para transações atômicas
  - Adicionar sistema de retry com backoff exponencial para deadlocks
  - Criar tratamento de exceções específicas para integridade financeira
  - _Requisitos: 2.1, 2.2, 2.3_

- [x] 3.2 Refatorar WalletService para usar transações atômicas
  - Modificar credit_wallet, debit_wallet para usar transações atômicas
  - Refatorar transfer_to_escrow e release_from_escrow para atomicidade completa
  - Implementar validação de saldo dentro da mesma transação do débito
  - _Requisitos: 2.1, 2.2, 2.3, 2.4, 3.4_

- [ ] 4. Implementar sistema de identificação única de transações
- [x] 4.1 Criar TransactionIdGenerator para IDs únicos
  - Implementar gerador de transaction_id no formato TXN-YYYYMMDD-HHMMSS-UUID8
  - Adicionar validação de unicidade de transaction_id
  - Criar índice único para transaction_id no banco
  - _Requisitos: 6.1, 6.2, 6.3_

- [x] 4.2 Modificar modelo Transaction para incluir transaction_id único
  - Adicionar campo transaction_id como String(50) unique not null
  - Implementar geração automática de transaction_id no __init__
  - Atualizar todas as criações de Transaction para incluir transaction_id
  - _Requisitos: 6.1, 6.2, 6.4_

- [x] 5. Implementar sistema de timeout de sessão
- [x] 5.1 Criar SessionTimeoutManager para controle de expiração
  - Implementar verificação de timeout de 30 minutos de inatividade
  - Criar sistema de aviso 5 minutos antes da expiração
  - Implementar limpeza automática de sessões expiradas
  - _Requisitos: 4.1, 4.2, 4.3, 4.4_

- [x] 5.2 Integrar timeout de sessão no middleware da aplicação
  - Adicionar verificação de timeout em before_request
  - Implementar redirecionamento automático para login após expiração
  - Criar endpoints para extensão de sessão e verificação de status
  - _Requisitos: 4.1, 4.2, 4.3_

- [x] 6. Implementar proteção CSRF completa
- [x] 6.1 Habilitar CSRFProtect para toda a aplicação
  - Ativar CSRFProtect globalmente no app.py
  - Configurar geração de tokens CSRF únicos por sessão
  - Implementar validação automática em todas as requisições POST/PUT/DELETE/PATCH
  - _Requisitos: 5.1, 5.2, 5.4_

- [x] 6.2 Adicionar tokens CSRF em todos os templates
  - Atualizar todos os formulários em templates/admin/ com {{ csrf_token() }}
  - Adicionar proteção CSRF em templates/cliente/ e templates/prestador/
  - Modificar formulários de autenticação para incluir tokens CSRF
  - _Requisitos: 5.1, 5.3_

- [x] 7. Implementar validação de transições de status de pedidos
- [x] 7.1 Criar OrderStatusValidator com regras de transição
  - Definir matriz de transições válidas entre status de orders
  - Implementar validação de transições antes de mudanças de status
  - Criar logs de auditoria para todas as tentativas de mudança de status
  - _Requisitos: 7.1, 7.2, 7.3_

- [x] 7.2 Integrar validação de status nos serviços de order
  - Modificar OrderService para usar OrderStatusValidator
  - Implementar rejeição de transições inválidas com mensagens claras
  - Adicionar histórico de mudanças de status para cada order
  - _Requisitos: 7.1, 7.2, 7.4_

- [x] 8. Implementar sistema de soft delete
- [x] 8.1 Modificar modelos User e AdminUser para soft delete
  - Adicionar campos deleted_at e deleted_by nos modelos
  - Implementar propriedade is_deleted para verificação de status
  - Criar métodos para soft delete e restore de usuários
  - _Requisitos: 8.1, 8.2, 8.4_

- [x] 8.2 Criar SoftDeleteService para gerenciar exclusões
  - Implementar soft_delete_user que marca como deletado sem remover
  - Criar restore_user para reativar usuários deletados
  - Modificar consultas para filtrar usuários deletados por padrão
  - _Requisitos: 8.1, 8.2, 8.3, 8.4_

- [x] 9. Implementar controle de criação de tokens
- [x] 9.1 Criar modelo TokenCreationLimit para limites por admin
  - Implementar modelo com limites diários e mensais por administrador
  - Adicionar campos para controle de criação de tokens
  - Criar relacionamento com AdminUser para rastreamento
  - _Requisitos: 9.1, 9.3_

- [x] 9.2 Implementar TokenCreationControlService
  - Criar verificação de limites diários e mensais antes da criação
  - Implementar sistema de aprovação para valores acima do limite
  - Adicionar logs detalhados de todas as criações de tokens
  - _Requisitos: 9.1, 9.2, 9.3, 9.4_

- [ ]* 10. Criar testes de integridade para todas as correções
  - Escrever testes para migração de dados Float→Numeric
  - Criar testes de atomicidade para operações financeiras concorrentes
  - Implementar testes de race condition e constraints de saldo
  - _Requisitos: 1.1, 2.1, 3.1_

- [ ]* 11. Criar testes de segurança para validar correções
  - Escrever testes para proteção CSRF em todos os formulários
  - Criar testes de timeout de sessão e limpeza automática
  - Implementar testes de validação de transições de status
  - _Requisitos: 4.1, 5.1, 7.1_

- [ ]* 12. Implementar monitoramento e alertas para sistema corrigido
  - Criar alertas para tentativas de saldo negativo
  - Implementar monitoramento de transações com falha de atomicidade
  - Adicionar logs de auditoria para todas as operações críticas
  - _Requisitos: 2.1, 3.1, 6.1_