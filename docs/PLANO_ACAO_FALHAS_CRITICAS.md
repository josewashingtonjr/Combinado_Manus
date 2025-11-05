# Plano de Ação para Correção das Falhas Críticas

**Data:** 29 de outubro de 2025  
**Autor:** Manus AI  
**Objetivo:** Fornecer um plano de ação detalhado e priorizado para a correção das 18 falhas de severidade crítica identificadas na auditoria completa do sistema Combinado.

---

## 1. Visão Geral

Este documento apresenta um plano de ação estruturado para corrigir as **18 falhas críticas** identificadas na auditoria do sistema. As falhas foram priorizadas com base em três critérios principais:

1. **Impacto no Sistema:** Gravidade das consequências se a falha não for corrigida
2. **Risco de Segurança:** Potencial de exploração maliciosa ou perda de dados
3. **Complexidade de Correção:** Esforço técnico necessário para implementar a solução

As correções estão organizadas em **3 ondas de implementação**, permitindo uma abordagem incremental e gerenciável.

---

## 2. Plano de Ação Detalhado

### Onda 1: Correções Emergenciais (Prioridade Máxima)

Estas correções devem ser implementadas **imediatamente** devido ao alto risco de perda de dados financeiros e vulnerabilidades de segurança críticas.

| ID | Problema | Severidade | Arquivo(s) Afetado(s) | Descrição da Correção | Esforço | Prazo | Responsável | Status |
|---|---|---|---|---|---|---|---|---|
| **C-01** | Uso de Float para valores monetários | CRÍTICA | `models.py` (Wallet, Transaction, Order) | Migrar campos `balance`, `escrow_balance`, `amount` e `value` de `db.Float` para `db.Numeric(18, 2)`. Criar migração Alembic e atualizar todos os serviços para usar `Decimal`. | Alto | 2 dias | Backend Dev | ⬜ Pendente |
| **C-02** | Operações financeiras não-atômicas | CRÍTICA | `wallet_service.py`, `order_service.py` | Envolver todas as operações que modificam saldos em blocos `try/except` com `db.session.begin_nested()` e `db.session.commit()`/`db.session.rollback()`. | Médio | 1 dia | Backend Dev | ⬜ Pendente |
| **C-03** | Race condition em validação de saldo | CRÍTICA | `wallet_service.py` | Implementar `SELECT FOR UPDATE` ou mover validação de saldo para dentro da transação atômica. Usar `with_for_update()` ao consultar carteiras. | Médio | 1 dia | Backend Dev | ⬜ Pendente |
| **C-04** | Criação de ordem sem validação atômica | CRÍTICA | `order_service.py`, `cliente_routes.py` | Integrar validação de saldo na mesma transação da criação da ordem. Garantir que débito e criação sejam atômicos. | Médio | 1 dia | Backend Dev | ⬜ Pendente |
| **C-05** | Falta de proteção CSRF | CRÍTICA | `templates/**/*.html`, `auth_routes.py` | Auditar todos os templates com formulários e adicionar `{{ form.hidden_tag() }}`. Implementar validação CSRF em rotas POST. | Alto | 2 dias | Frontend + Backend | ⬜ Pendente |
| **C-06** | Elevação de privilégios em `role_routes.py` | CRÍTICA | `role_routes.py` | Adicionar validação rigorosa na rota `set_role` para verificar se o usuário possui o papel solicitado antes de permitir a troca. | Baixo | 4 horas | Backend Dev | ⬜ Pendente |

**Total Onda 1:** 6 correções | Prazo estimado: **5 dias úteis**

---

### Onda 2: Correções de Alta Prioridade

Estas correções devem ser implementadas **logo após a Onda 1** para mitigar riscos de segurança e integridade de dados.

| ID | Problema | Severidade | Arquivo(s) Afetado(s) | Descrição da Correção | Esforço | Prazo | Responsável | Status |
|---|---|---|---|---|---|---|---|---|
| **C-07** | Exposição de stack traces em produção | CRÍTICA | `app.py`, `templates/errors/500.html` | Garantir que `DEBUG=False` em produção. Configurar handler de erro 500 genérico que não exponha detalhes técnicos. | Baixo | 2 horas | DevOps + Backend | ⬜ Pendente |
| **C-08** | Texto malformado em `admin_routes.py` | CRÍTICA | `admin_routes.py` (linha 495) | Remover o texto `acoes.html')` solto no final do arquivo que causa erro de sintaxe. | Baixo | 15 min | Backend Dev | ⬜ Pendente |
| **C-09** | Duplicação de rota `contestacoes` | CRÍTICA | `admin_routes.py` (linhas 319 e 490) | Remover a segunda definição da rota `/admin/contestacoes` e consolidar funcionalidade na primeira. | Baixo | 1 hora | Backend Dev | ⬜ Pendente |
| **C-10** | Redirecionamento inseguro | ALTA | `role_routes.py` | Validar `request.referrer` contra whitelist de domínios permitidos antes de redirecionar. Usar `url_for()` como fallback. | Médio | 4 horas | Backend Dev | ⬜ Pendente |
| **C-11** | Falta de proteção contra brute force | ALTA | `auth_routes.py`, `auth_service.py` | Implementar rate limiting usando modelo `LoginAttempt`. Bloquear temporariamente após 5 tentativas falhas. | Médio | 1 dia | Backend Dev | ⬜ Pendente |
| **C-12** | Validação de saldo insuficiente em transações | ALTA | `cliente_routes.py`, `prestador_routes.py` | Implementar validação atômica de saldo em todas as rotas de criação de ordem e saque. | Médio | 1 dia | Backend Dev | ⬜ Pendente |

**Total Onda 2:** 6 correções | Prazo estimado: **3 dias úteis**

---

### Onda 3: Correções Complementares Críticas

Estas correções completam a mitigação dos riscos críticos e devem ser implementadas **após as Ondas 1 e 2**.

| ID | Problema | Severidade | Arquivo(s) Afetado(s) | Descrição da Correção | Esforço | Prazo | Responsável | Status |
|---|---|---|---|---|---|---|---|---|
| **C-13** | Saldo negativo possível | ALTA | `models.py` (Wallet) | Adicionar constraint CHECK no banco de dados: `CHECK (balance >= 0 AND escrow_balance >= 0)`. Criar migração. | Baixo | 2 horas | Backend Dev + DBA | ⬜ Pendente |
| **C-14** | Transição de status inválida em Order | ALTA | `models.py`, `order_service.py` | Implementar máquina de estados ou validação de transições. Criar enum `OrderStatus` e método `can_transition_to()`. | Alto | 2 dias | Backend Dev | ⬜ Pendente |
| **C-15** | Cascade delete agressivo | ALTA | `models.py` (Wallet) | Remover `cascade="all, delete-orphan"` e implementar soft delete. Adicionar campo `deleted_at` em User e Wallet. | Médio | 1 dia | Backend Dev | ⬜ Pendente |
| **C-16** | Criação ilimitada de tokens | ALTA | `admin_routes.py`, `admin_service.py` | Implementar limite diário de criação de tokens (ex: 100.000) ou aprovação em duas etapas para valores acima de threshold. | Médio | 1 dia | Backend Dev | ⬜ Pendente |
| **C-17** | Sessão sem timeout | ALTA | `auth_service.py`, `config.py` | Implementar timeout de sessão de 24 horas. Adicionar `PERMANENT_SESSION_LIFETIME` em config. | Baixo | 2 horas | Backend Dev | ⬜ Pendente |
| **C-18** | Falta de campo `transaction_id` único | ALTA | `models.py` (Transaction) | Adicionar campo `transaction_id` único gerado por `generate_transaction_id()`. Criar índice único. Migração. | Médio | 4 horas | Backend Dev | ⬜ Pendente |

**Total Onda 3:** 6 correções | Prazo estimado: **5 dias úteis**

---

## 3. Cronograma de Implementação

### Semana 1: Onda 1 (Dias 1-5)

| Dia | Correções | Atividades |
|---|---|---|
| **Dia 1** | C-01 (início) | Criar branch `fix/critical-financial-integrity`. Criar migração para alterar tipos de Float para Numeric. |
| **Dia 2** | C-01 (conclusão), C-02 | Atualizar serviços para usar Decimal. Implementar transações atômicas em wallet_service.py. |
| **Dia 3** | C-03, C-04 | Implementar SELECT FOR UPDATE. Integrar validação atômica em order_service.py. |
| **Dia 4** | C-05 (início) | Auditar todos os templates. Adicionar CSRF tokens em formulários. |
| **Dia 5** | C-05 (conclusão), C-06 | Validar CSRF em rotas POST. Implementar validação de papéis em role_routes.py. Testes. |

### Semana 2: Onda 2 (Dias 6-8)

| Dia | Correções | Atividades |
|---|---|---|
| **Dia 6** | C-07, C-08, C-09 | Configurar modo produção. Remover texto malformado. Consolidar rota duplicada. |
| **Dia 7** | C-10, C-11 (início) | Implementar validação de redirecionamento. Criar modelo LoginAttempt. |
| **Dia 8** | C-11 (conclusão), C-12 | Implementar rate limiting. Validação atômica de saldo em rotas. Testes. |

### Semana 3: Onda 3 (Dias 9-13)

| Dia | Correções | Atividades |
|---|---|---|
| **Dia 9** | C-13, C-17, C-18 | Adicionar constraints CHECK. Implementar timeout de sessão. Adicionar transaction_id. |
| **Dia 10** | C-14 (início) | Criar enum OrderStatus. Implementar máquina de estados. |
| **Dia 11** | C-14 (conclusão), C-15 | Validar transições de status. Implementar soft delete. |
| **Dia 12** | C-16 | Implementar limite de criação de tokens. Testes integrados. |
| **Dia 13** | Revisão e Deploy | Code review. Executar suíte de testes completa. Deploy em staging. |

---

## 4. Recursos Necessários

### Equipe

| Papel | Responsabilidades | Alocação |
|---|---|---|
| **Backend Developer** | Implementar correções em serviços, modelos e rotas | 100% (13 dias) |
| **Frontend Developer** | Adicionar CSRF tokens em templates | 50% (2 dias) |
| **DBA** | Criar e revisar migrações de banco de dados | 25% (1 dia) |
| **DevOps** | Configurar ambiente de produção, deploy | 25% (1 dia) |
| **QA/Tester** | Executar testes, validar correções | 50% (3 dias) |

### Ferramentas

- **Alembic:** Para migrações de banco de dados
- **pytest:** Para executar suíte de testes automatizados
- **Git:** Para versionamento e controle de branches
- **GitHub:** Para code review e pull requests

---

## 5. Critérios de Aceitação

Cada correção deve atender aos seguintes critérios antes de ser considerada concluída:

1. **Implementação Completa:** Código implementado conforme especificação
2. **Testes Passando:** Todos os testes automatizados relacionados passando
3. **Code Review:** Aprovação de pelo menos um revisor
4. **Documentação:** Atualização de documentação técnica quando aplicável
5. **Migração Testada:** Migrações de banco de dados testadas em ambiente de staging

---

## 6. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Migração de Float para Numeric causa perda de dados | Baixa | Alto | Backup completo antes da migração. Testar em staging primeiro. |
| Transações atômicas causam deadlocks | Média | Médio | Implementar timeout de transação. Monitorar logs de deadlock. |
| CSRF tokens quebram funcionalidades existentes | Média | Médio | Testar todas as funcionalidades após implementação. |
| Rate limiting bloqueia usuários legítimos | Baixa | Médio | Configurar threshold adequado (5 tentativas). Implementar reset manual. |
| Soft delete causa inconsistências | Baixa | Alto | Implementar queries que sempre filtram por `deleted_at IS NULL`. |

---

## 7. Métricas de Sucesso

Após a implementação de todas as correções, as seguintes métricas devem ser atingidas:

| Métrica | Meta | Como Medir |
|---|---|---|
| **Falhas Críticas Resolvidas** | 100% (18/18) | Auditoria de código |
| **Cobertura de Testes** | ≥ 80% | pytest --cov |
| **Testes Passando** | 100% | pytest |
| **Vulnerabilidades de Segurança** | 0 críticas | Análise de segurança |
| **Inconsistências Financeiras** | 0 | Auditoria de transações |

---

## 8. Próximos Passos Após Correções

Após a conclusão das correções críticas:

1. **Implementar Correções de Alta Severidade:** Abordar os 31 problemas de alta severidade identificados na auditoria
2. **Monitoramento Contínuo:** Implementar monitoramento de logs e alertas para detectar problemas proativamente
3. **Auditoria de Segurança:** Realizar auditoria de segurança externa
4. **Testes de Carga:** Executar testes de performance e carga
5. **Documentação de API:** Criar documentação completa da API para integrações futuras

---

## 9. Aprovação e Acompanhamento

### Aprovação

| Stakeholder | Papel | Assinatura | Data |
|---|---|---|---|
| Product Owner | Aprovação do plano | _____________ | ___/___/_____ |
| Tech Lead | Revisão técnica | _____________ | ___/___/_____ |
| Security Officer | Validação de segurança | _____________ | ___/___/_____ |

### Acompanhamento

- **Reuniões Diárias:** Stand-up de 15 minutos para acompanhamento de progresso
- **Revisão Semanal:** Revisão de progresso e ajuste de prioridades
- **Relatório Final:** Relatório de conclusão com métricas e lições aprendidas

---

## 10. Conclusão

Este plano de ação fornece um roteiro claro e estruturado para a correção das 18 falhas críticas identificadas na auditoria. A implementação em 3 ondas permite uma abordagem incremental, minimizando riscos e permitindo validação contínua.

A execução rigorosa deste plano é essencial para garantir a **integridade financeira**, a **segurança** e a **estabilidade** do sistema Combinado. O sucesso depende do comprometimento da equipe, da alocação adequada de recursos e do acompanhamento contínuo do progresso.

---

**Documento preparado por:** Manus AI  
**Data de criação:** 29 de outubro de 2025  
**Versão:** 1.0

