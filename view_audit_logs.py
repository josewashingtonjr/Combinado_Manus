#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Visualizador de Logs de Auditoria
Ferramenta para consultar e analisar logs de auditoria do sistema
"""

import json
import sys
from datetime import datetime
from typing import List, Dict, Optional

def read_audit_logs(log_file: str = 'logs/audit.log') -> List[Dict]:
    """Lê e parseia os logs de auditoria"""
    logs = []
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Extrair JSON da linha de log
                # Formato: timestamp - AUDIT - {json}
                if ' - AUDIT - ' in line:
                    json_part = line.split(' - AUDIT - ', 1)[1].strip()
                    try:
                        log_entry = json.loads(json_part)
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
    except FileNotFoundError:
        print(f"⚠️  Arquivo {log_file} não encontrado")
    
    return logs

def filter_logs(
    logs: List[Dict],
    operation: Optional[str] = None,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict]:
    """Filtra logs por critérios"""
    filtered = logs
    
    if operation:
        filtered = [log for log in filtered if log.get('operation') == operation]
    
    if entity_id is not None:
        filtered = [log for log in filtered if log.get('entity_id') == entity_id]
    
    if user_id is not None:
        filtered = [log for log in filtered if log.get('user_id') == user_id]
    
    if start_date:
        filtered = [log for log in filtered if log.get('timestamp', '') >= start_date]
    
    if end_date:
        filtered = [log for log in filtered if log.get('timestamp', '') <= end_date]
    
    return filtered

def display_log(log: Dict, detailed: bool = False):
    """Exibe um log de auditoria formatado"""
    timestamp = log.get('timestamp', 'N/A')
    operation = log.get('operation', 'N/A')
    entity_type = log.get('entity_type', 'N/A')
    entity_id = log.get('entity_id', 'N/A')
    user_id = log.get('user_id', 'N/A')
    audit_id = log.get('audit_id', 'N/A')
    
    print(f"\n{'=' * 80}")
    print(f"🔍 Audit ID: {audit_id}")
    print(f"📅 Timestamp: {timestamp}")
    print(f"⚙️  Operação: {operation}")
    print(f"📦 Entidade: {entity_type} #{entity_id}")
    print(f"👤 Usuário: {user_id}")
    
    if detailed:
        print(f"\n📋 Detalhes:")
        details = log.get('details', {})
        for key, value in details.items():
            print(f"   • {key}: {value}")
    
    print('=' * 80)

def show_statistics(logs: List[Dict]):
    """Mostra estatísticas dos logs"""
    if not logs:
        print("⚠️  Nenhum log encontrado")
        return
    
    print(f"\n{'=' * 80}")
    print("📊 ESTATÍSTICAS DE AUDITORIA")
    print('=' * 80)
    
    # Total de logs
    print(f"\n📈 Total de registros: {len(logs)}")
    
    # Operações mais comuns
    operations = {}
    for log in logs:
        op = log.get('operation', 'UNKNOWN')
        operations[op] = operations.get(op, 0) + 1
    
    print("\n🔧 Operações registradas:")
    for op, count in sorted(operations.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {op}: {count}")
    
    # Usuários mais ativos
    users = {}
    for log in logs:
        user = log.get('user_id')
        if user:
            users[user] = users.get(user, 0) + 1
    
    if users:
        print("\n👥 Usuários mais ativos:")
        for user, count in sorted(users.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • Usuário #{user}: {count} operações")
    
    # Período dos logs
    if logs:
        timestamps = [log.get('timestamp') for log in logs if log.get('timestamp')]
        if timestamps:
            print(f"\n📅 Período:")
            print(f"   • Primeiro registro: {min(timestamps)}")
            print(f"   • Último registro: {max(timestamps)}")
    
    print('=' * 80)

def trace_order(logs: List[Dict], order_id: int):
    """Rastreia todas as operações de uma ordem específica"""
    order_logs = filter_logs(logs, entity_id=order_id)
    
    if not order_logs:
        print(f"⚠️  Nenhum log encontrado para a ordem #{order_id}")
        return
    
    print(f"\n{'=' * 80}")
    print(f"🔍 RASTREAMENTO DA ORDEM #{order_id}")
    print('=' * 80)
    print(f"\nTotal de eventos: {len(order_logs)}")
    
    # Ordenar por timestamp
    order_logs.sort(key=lambda x: x.get('timestamp', ''))
    
    print("\n📜 Histórico de eventos:")
    for i, log in enumerate(order_logs, 1):
        timestamp = log.get('timestamp', 'N/A')
        operation = log.get('operation', 'N/A')
        user_id = log.get('user_id', 'N/A')
        
        print(f"\n{i}. {timestamp}")
        print(f"   Operação: {operation}")
        print(f"   Usuário: {user_id}")
        
        # Mostrar detalhes relevantes
        details = log.get('details', {})
        if 'old_status' in details and 'new_status' in details:
            print(f"   Status: {details['old_status']} → {details['new_status']}")
        if 'value' in details:
            print(f"   Valor: R$ {details['value']:.2f}")
        if 'reason' in details:
            print(f"   Motivo: {details['reason'][:100]}")
    
    print('=' * 80)

def main():
    """Menu principal"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        # Ler logs
        logs = read_audit_logs()
        
        if command == 'stats':
            show_statistics(logs)
        
        elif command == 'trace' and len(sys.argv) > 2:
            order_id = int(sys.argv[2])
            trace_order(logs, order_id)
        
        elif command == 'operation' and len(sys.argv) > 2:
            operation = sys.argv[2]
            filtered = filter_logs(logs, operation=operation)
            print(f"\n📋 Logs da operação '{operation}': {len(filtered)} registros")
            for log in filtered[:10]:  # Mostrar primeiros 10
                display_log(log, detailed=True)
        
        elif command == 'user' and len(sys.argv) > 2:
            user_id = int(sys.argv[2])
            filtered = filter_logs(logs, user_id=user_id)
            print(f"\n👤 Logs do usuário #{user_id}: {len(filtered)} registros")
            for log in filtered[:10]:  # Mostrar primeiros 10
                display_log(log)
        
        elif command == 'recent':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            recent = sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
            print(f"\n🕐 Últimos {limit} registros:")
            for log in recent:
                display_log(log)
        
        else:
            print("❌ Comando inválido")
            show_help()
    
    else:
        show_help()

def show_help():
    """Mostra ajuda de uso"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║              VISUALIZADOR DE LOGS DE AUDITORIA                       ║
╚══════════════════════════════════════════════════════════════════════╝

Uso: python3.11 view_audit_logs.py [comando] [argumentos]

Comandos disponíveis:

  stats
    Mostra estatísticas gerais dos logs de auditoria
    Exemplo: python3.11 view_audit_logs.py stats

  trace <order_id>
    Rastreia todas as operações de uma ordem específica
    Exemplo: python3.11 view_audit_logs.py trace 123

  operation <operation_name>
    Filtra logs por tipo de operação
    Exemplo: python3.11 view_audit_logs.py operation ORDER_CREATED

  user <user_id>
    Filtra logs por usuário
    Exemplo: python3.11 view_audit_logs.py user 456

  recent [limit]
    Mostra os registros mais recentes (padrão: 10)
    Exemplo: python3.11 view_audit_logs.py recent 20

Operações disponíveis:
  • ORDER_CREATED - Criação de ordem
  • STATUS_CHANGED - Mudança de status
  • SERVICE_COMPLETED - Serviço concluído
  • ORDER_CONFIRMED_MANUAL - Confirmação manual
  • ORDER_CONFIRMED_AUTO - Confirmação automática
  • ORDER_CANCELLED - Cancelamento
  • DISPUTE_OPENED - Abertura de contestação
  • DISPUTE_RESOLVED - Resolução de disputa
  • FINANCIAL_TRANSACTION - Transação financeira
  • ERROR_* - Erros em operações

╚══════════════════════════════════════════════════════════════════════╝
""")

if __name__ == '__main__':
    main()
