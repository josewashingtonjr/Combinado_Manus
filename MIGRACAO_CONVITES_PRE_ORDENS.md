# Migração de Convites para Pré-Ordens

Este documento descreve o processo de migração de convites aceitos para o novo sistema de pré-ordens.

## Visão Geral

O script `migrate_invites_to_pre_orders.py` identifica convites com status 'aceito' que não possuem ordem associada e os converte em pré-ordens, preservando todos os dados.

## Requisitos

- Python 3.11+
- Banco de dados com as tabelas de pré-ordem já criadas (execute `apply_pre_order_migration.py` primeiro)
- Acesso ao contexto da aplicação Flask

## Uso

### Modo Dry-Run (Simulação)

Para testar a migração sem fazer alterações no banco de dados:

```bash
python migrate_invites_to_pre_orders.py --dry-run
```

Este modo:
- Identifica todos os convites elegíveis
- Simula a criação de pré-ordens
- Exibe o que seria feito sem modificar o banco
- Gera relatório JSON com estatísticas

### Modo Produção

Para executar a migração real:

```bash
python migrate_invites_to_pre_orders.py --confirm
```

**ATENÇÃO**: Este modo faz alterações permanentes no banco de dados!

## O que o Script Faz

### 1. Identificação (Requirement 16.1)

Busca convites que atendem aos critérios:
- Status: 'aceito'
- Sem `order_id` associado
- Ainda não convertidos para pré-ordem

### 2. Migração (Requirements 16.2, 16.3)

Para cada convite elegível:
- Cria uma pré-ordem preservando todos os dados:
  - Título do serviço
  - Descrição
  - Valor atual e original
  - Data de entrega
  - Categoria do serviço
  - Cliente e prestador
- Atualiza status do convite para 'convertido_pre_ordem'
- Cria registro no histórico da pré-ordem
- Define prazo de negociação (7 dias padrão)

### 3. Notificação (Requirement 16.4)

Notifica ambas as partes (cliente e prestador) sobre a criação da pré-ordem.

### 4. Relatório (Requirement 16.5)

Gera arquivo JSON com estatísticas:
- Total de convites encontrados
- Total migrado com sucesso
- Erros encontrados
- Tempo de execução
- IDs dos convites migrados

Exemplo de nome do relatório:
```
migration_report_invites_to_pre_orders_20251126_143022.json
```

## Estrutura do Relatório JSON

```json
{
  "migration_type": "invites_to_pre_orders",
  "dry_run": false,
  "start_time": "2025-11-26T14:30:22.123456",
  "end_time": "2025-11-26T14:30:25.789012",
  "execution_time_seconds": 3.67,
  "statistics": {
    "total_found": 15,
    "total_migrated": 15,
    "total_errors": 0,
    "success_rate": 100.0
  },
  "migrated_invite_ids": [1, 2, 3, 5, 7, 8, 10, 12, 15, 18, 20, 22, 25, 28, 30],
  "errors": []
}
```

## Rollback

O script implementa rollback automático em caso de erro durante a migração de um convite individual. Se ocorrer um erro:

1. A transação é revertida
2. O erro é registrado no relatório
3. A migração continua com os próximos convites

## Segurança

### Validações

- Verifica se o prestador existe no sistema (pelo telefone do convite)
- Valida que não existe pré-ordem duplicada para o mesmo convite
- Usa transações atômicas para garantir consistência

### Modo Dry-Run Obrigatório

Para evitar execuções acidentais, o script exige:
- `--dry-run` para simulação
- `--confirm` para execução real

Executar sem nenhum dos dois resulta em erro.

## Testes

O script possui testes de propriedade (Property-Based Testing) que validam:

### Property 51: Preservação de Dados

Para qualquer convite migrado, verifica que:
- Todos os campos são preservados corretamente
- Status do convite é atualizado
- Histórico é criado
- Pré-ordem tem estado inicial correto

Execute os testes com:

```bash
python -m pytest tests/test_migration_properties.py -v
```

## Exemplo de Execução

### Dry-Run

```bash
$ python migrate_invites_to_pre_orders.py --dry-run

================================================================================
INICIANDO MIGRAÇÃO: Convites → Pré-Ordens
MODO: DRY-RUN (Simulação - Nenhuma alteração será feita)
================================================================================
Início: 2025-11-26 14:30:22

Buscando convites elegíveis para migração...
✓ Encontrados 3 convites elegíveis para migração

Detalhes dos convites encontrados:
  - Convite #1: 'Serviço de Encanamento' (Cliente: 5, Valor: R$ 150.00)
  - Convite #2: 'Instalação Elétrica' (Cliente: 7, Valor: R$ 300.00)
  - Convite #3: 'Pintura de Parede' (Cliente: 5, Valor: R$ 200.00)

Iniciando migração de 3 convites...
================================================================================

[1/3] Processando convite #1...
  [DRY-RUN] Criaria pré-ordem:
    - Cliente: 5
    - Prestador: 8 (João Silva)
    - Título: Serviço de Encanamento
    - Valor atual: R$ 150.00
    - Valor original: R$ 150.00
    - Data de entrega: 2025-12-05 10:00:00
    - Expira em: 2025-12-03 14:30:22
  [DRY-RUN] Atualizaria status do convite para 'convertido_pre_ordem'
  [DRY-RUN] Criaria registro no histórico
  [DRY-RUN] Notificaria ambas as partes

[2/3] Processando convite #2...
...

================================================================================
RESUMO DA MIGRAÇÃO
================================================================================
Modo: DRY-RUN (Simulação)
Convites encontrados: 3
Convites migrados: 3
Erros: 0
Tempo de execução: 0.15 segundos

Convites migrados: [1, 2, 3]

✓ MIGRAÇÃO CONCLUÍDA COM SUCESSO!
================================================================================

✓ Relatório JSON gerado: migration_report_invites_to_pre_orders_20251126_143022.json
```

### Produção

```bash
$ python migrate_invites_to_pre_orders.py --confirm

================================================================================
INICIANDO MIGRAÇÃO: Convites → Pré-Ordens
================================================================================
Início: 2025-11-26 14:35:10

Buscando convites elegíveis para migração...
✓ Encontrados 3 convites elegíveis para migração

...

[1/3] Processando convite #1...
  ✓ Pré-ordem #45 criada
  ✓ Status do convite atualizado para 'convertido_pre_ordem'
  ✓ Registro de histórico criado
  ✓ Cliente 5 notificado
  ✓ Prestador 8 notificado
  ✓ Convite #1 migrado com sucesso para pré-ordem #45

...

================================================================================
RESUMO DA MIGRAÇÃO
================================================================================
Modo: PRODUÇÃO
Convites encontrados: 3
Convites migrados: 3
Erros: 0
Tempo de execução: 1.23 segundos

Convites migrados: [1, 2, 3]

✓ MIGRAÇÃO CONCLUÍDA COM SUCESSO!
================================================================================

✓ Relatório JSON gerado: migration_report_invites_to_pre_orders_20251126_143511.json
```

## Troubleshooting

### Erro: "Prestador não encontrado"

**Causa**: O telefone do convite não corresponde a nenhum usuário no sistema.

**Solução**: Verifique se o prestador foi cadastrado com o telefone correto.

### Erro: "Convite já possui pré-ordem associada"

**Causa**: O convite já foi migrado anteriormente.

**Solução**: Normal. O script pula convites já migrados automaticamente.

### Erro: "Nenhum convite elegível encontrado"

**Causa**: Todos os convites já foram migrados ou não há convites aceitos sem ordem.

**Solução**: Nenhuma ação necessária. A migração já foi concluída.

## Integração com Sistema Existente

Após a migração:

1. **Convites**: Ficam com status 'convertido_pre_ordem' e não podem mais ser modificados
2. **Pré-Ordens**: Entram em negociação com prazo de 7 dias
3. **Notificações**: Ambas as partes são notificadas sobre a criação da pré-ordem
4. **Histórico**: Todas as ações são registradas para auditoria

## Próximos Passos

Após executar a migração:

1. Verificar o relatório JSON gerado
2. Confirmar que todos os convites foram migrados corretamente
3. Notificar os usuários sobre o novo sistema de pré-ordens
4. Monitorar logs por 24h para identificar possíveis problemas

## Suporte

Em caso de problemas durante a migração:

1. Verifique os logs do sistema
2. Consulte o relatório JSON gerado
3. Execute em modo dry-run para diagnosticar
4. Contate o suporte técnico com o relatório JSON

## Referências

- Requirements: 16.1-16.5
- Design Document: `.kiro/specs/sistema-pre-ordem-negociacao/design.md`
- Tasks: `.kiro/specs/sistema-pre-ordem-negociacao/tasks.md`
