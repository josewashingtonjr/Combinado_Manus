# Exemplos de Notificações do Sistema

## 1. Ordem Criada

### Para o Cliente:
```
✓ Ordem #123 criada com sucesso! 
Serviço: 'Instalação Elétrica'. 
Prestador: João Silva. 
Valor: R$ 500,00. 
Os valores foram bloqueados em garantia até a conclusão do serviço.
```

### Para o Prestador:
```
✓ Nova ordem #123 criada! 
Serviço: 'Instalação Elétrica'. 
Cliente: Maria Santos. 
Valor: R$ 500,00. 
Execute o serviço e marque como concluído quando finalizar.
```

---

## 2. Serviço Concluído (URGENTE)

### Para o Cliente:
```
⚠️ ATENÇÃO: Serviço concluído! 
João Silva marcou o serviço 'Instalação Elétrica' como concluído. 
Você tem 36 HORAS para confirmar ou contestar o serviço. 
Após esse prazo, a ordem será AUTOMATICAMENTE confirmada e o pagamento liberado. 
Prazo: 21/11/2025 às 14:30
```

---

## 3. Lembrete de Confirmação (12h restantes)

### Para o Cliente:
```
🔔 LEMBRETE URGENTE: Faltam apenas 12 horas para a confirmação automática! 
A ordem #123 ('Instalação Elétrica') será automaticamente confirmada em breve. 
Se houver algum problema com o serviço, conteste AGORA antes que o prazo expire. 
Prazo final: 21/11/2025 às 14:30
```

---

## 4. Confirmação Automática

### Para o Cliente:
```
ℹ️ Ordem #123 confirmada automaticamente. 
O prazo de 36 horas expirou sem contestação. 
Serviço: 'Instalação Elétrica'. 
O pagamento de R$ 500,00 foi processado e liberado para João Silva.
```

### Para o Prestador:
```
✅ Ordem #123 confirmada automaticamente! 
O cliente não contestou dentro de 36 horas. 
Serviço: 'Instalação Elétrica'. 
Você recebeu R$ 475,00 (valor líquido após taxa da plataforma).
```

---

## 5. Cancelamento de Ordem

### Para a Parte Prejudicada (Prestador):
```
⚠️ Ordem #123 foi cancelada por Maria Santos. 
Serviço: 'Instalação Elétrica'. 
Motivo: Imprevisto pessoal. 
Você receberá R$ 25,00 como compensação 
(50% da multa de cancelamento de R$ 50,00).
```

---

## 6. Contestação Aberta

### Para o Admin:
```
⚠️ Nova contestação aberta! 
Ordem #123: 'Instalação Elétrica'. 
Cliente Maria Santos contestou o serviço executado por João Silva. 
Valor: R$ 500,00. 
Motivo: O serviço não foi executado conforme combinado. Faltaram várias tomadas... 
Analise as provas e resolva a disputa.
```

### Para o Prestador:
```
⚠️ Contestação aberta na ordem #123. 
O cliente Maria Santos contestou o serviço 'Instalação Elétrica'. 
Motivo: O serviço não foi executado conforme combinado. Faltaram várias tomadas. 
O admin irá analisar o caso e tomar uma decisão. 
Aguarde a resolução da disputa.
```

---

## 7. Disputa Resolvida - Cliente Vence

### Para o Cliente (Vencedor):
```
✅ Disputa resolvida a seu favor! 
Ordem #123: 'Instalação Elétrica'. 
O admin analisou o caso e decidiu a seu favor. 
O valor de R$ 500,00 foi devolvido para sua carteira. 
Notas do admin: Após análise das provas, ficou comprovado que o serviço não foi executado adequadamente.
```

### Para o Prestador (Perdedor):
```
❌ Disputa resolvida contra você. 
Ordem #123: 'Instalação Elétrica'. 
O admin analisou o caso e decidiu a favor do cliente. 
Você não receberá o pagamento desta ordem. 
Notas do admin: Após análise das provas, ficou comprovado que o serviço não foi executado adequadamente.
```

---

## 8. Disputa Resolvida - Prestador Vence

### Para o Prestador (Vencedor):
```
✅ Disputa resolvida a seu favor! 
Ordem #123: 'Instalação Elétrica'. 
O admin analisou o caso e decidiu a seu favor. 
Você recebeu R$ 475,00 (valor líquido após taxa da plataforma). 
Notas do admin: Após análise das provas, ficou comprovado que o serviço foi executado corretamente.
```

### Para o Cliente (Perdedor):
```
❌ Disputa resolvida contra você. 
Ordem #123: 'Instalação Elétrica'. 
O admin analisou o caso e decidiu a favor do prestador. 
O pagamento foi liberado para o prestador. 
Notas do admin: Após análise das provas, ficou comprovado que o serviço foi executado corretamente.
```

---

## Cores e Categorias de Flash

- **success** (verde): Ordem criada, confirmação automática (prestador)
- **info** (azul): Confirmação automática (cliente), disputa resolvida
- **warning** (amarelo): Serviço concluído, cancelamento, contestação
- **danger** (vermelho): Lembrete urgente (12h restantes)

## Emojis Utilizados

- ⚠️ : Atenção/Alerta
- ✅ : Sucesso/Confirmação
- ❌ : Erro/Negação
- 🔔 : Lembrete/Notificação
- ℹ️ : Informação

## Características das Mensagens

1. **Clareza**: Linguagem simples e direta
2. **Completude**: Todas as informações necessárias
3. **Ação**: Indicam próximos passos quando aplicável
4. **Urgência**: Destacam prazos e ações urgentes
5. **Valores**: Sempre formatados como R$ X,XX
6. **Datas**: Formato DD/MM/YYYY às HH:MM
7. **Português**: 100% em pt-BR
