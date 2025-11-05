# PROCESSO DE MUDANÇAS RIGOROSO (PDR) - COMBINADO

## 1. Visão Geral

Este documento estabelece o processo formal para implementar quaisquer mudanças, correções ou novas funcionalidades no sistema "Combinado". O objetivo é garantir a estabilidade, segurança e integridade do sistema, minimizando o risco de regressões e falhas inesperadas.

## 2. Etapas Obrigatórias

Toda e qualquer alteração no código-fonte ou na infraestrutura do sistema deve seguir as 7 etapas abaixo, sem exceção.

### Etapa 1: Investigação e Definição do Problema/Requisito
- **Descrição:** Análise detalhada do problema a ser resolvido ou do requisito a ser implementado.
- **Entregável:** Um ticket ou issue em um sistema de rastreamento com a descrição clara, passos para reproduzir (se for um bug) e o resultado esperado.

### Etapa 2: Mapeamento de Ocorrências e Impacto
- **Descrição:** Identificar todas as partes do sistema que são afetadas pela mudança proposta. Isso inclui frontend, backend, banco de dados, APIs, etc.
- **Entregável:** Uma lista de arquivos, módulos, e componentes que serão modificados, e uma análise de impacto potencial em outras áreas do sistema.

### Etapa 3: Identificação da Causa Raiz / Proposta de Solução
- **Descrição:** Para bugs, identificar a causa fundamental do problema. Para novas funcionalidades, desenhar uma solução técnica detalhada.
- **Entregável:** Documentação da causa raiz ou o rascunho da arquitetura da nova funcionalidade.

### Etapa 4: Implementação e Correção do Fluxo
- **Descrição:** Escrever ou modificar o código para implementar a solução proposta. O código deve seguir os padrões de estilo e as melhores práticas definidas para o projeto.
- **Entregável:** Um branch separado no sistema de controle de versão (Git) com as alterações implementadas.

### Etapa 5: Desenvolvimento de Testes Automatizados
- **Descrição:** Criar testes unitários e de integração que cubram a nova funcionalidade ou a correção do bug. Os testes devem validar o comportamento esperado e garantir que a mudança não introduziu novos problemas.
- **Entregável:** Arquivos de teste no diretório `/tests` que validam a mudança.

### Etapa 6: Revisão de Código (Code Review)
- **Descrição:** Outro desenvolvedor (ou o arquiteto do sistema) deve revisar as alterações propostas. A revisão deve focar na correção da lógica, qualidade do código, cobertura de testes e aderência à arquitetura.
- **Entregável:** Aprovação formal do Pull Request ou Merge Request.

### Etapa 7: Validação em Ambiente de Testes e Deploy
- **Descrição:** As alterações aprovadas são mescladas na branch principal e implantadas em um ambiente de homologação (staging) para testes manuais e validação final.
- **Entregável:** Confirmação de que a funcionalidade está operando como esperado no ambiente de testes, seguida pelo deploy em produção.

## 3. Documentação

Toda mudança deve ser acompanhada da atualização da documentação relevante, incluindo a Planta Arquitetônica, guias de usuário e a própria documentação do código.


## 4. Diretrizes de Interface e Terminologia

### 4.1. Terminologia por Tipo de Usuário

Toda implementação deve respeitar a diferenciação de terminologia conforme o tipo de usuário:

**Administradores:** Utilizam terminologia técnica "tokens" para controle interno do sistema.

**Usuários (Clientes e Prestadores):** Visualizam apenas "saldo" em reais brasileiros (R$), sem conhecimento da existência de tokens internos.

### 4.2. Validação de Interface

Antes de qualquer deploy ou atualização, verificar se:
- Interfaces administrativas utilizam corretamente a terminologia "tokens"
- Interfaces de usuários apresentam apenas valores em "R$" e "saldo"
- Não há vazamento de terminologia técnica para usuários finais
