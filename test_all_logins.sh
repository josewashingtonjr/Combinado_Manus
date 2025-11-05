#!/bin/bash

echo "=========================================="
echo "TESTE DE LOGIN - TODOS OS USUÁRIOS"
echo "=========================================="

sleep 2

echo -e "\n1. Testando Cliente..."
curl -s -X POST http://127.0.0.1:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"cliente@teste.com","password":"cliente123"}' | python3.11 -m json.tool

echo -e "\n2. Testando Prestador..."
curl -s -X POST http://127.0.0.1:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"prestador@teste.com","password":"prestador123"}' | python3.11 -m json.tool

echo -e "\n3. Testando Usuário Dual..."
curl -s -X POST http://127.0.0.1:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"dual@teste.com","password":"dual12345"}' | python3.11 -m json.tool

echo -e "\n4. Testando Admin..."
curl -s -X POST http://127.0.0.1:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@combinado.com","password":"admin12345"}' | python3.11 -m json.tool

echo -e "\n=========================================="
echo "TESTES CONCLUÍDOS"
echo "=========================================="
