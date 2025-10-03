#!/usr/bin/env python3
"""
Script simples para testar o servidor FastAPI
"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

print("=== Teste do Servidor Backend ===")
print(f"OpenRouter API Key: {os.getenv('OPENROUTER_API_KEY')[:10]}...")
print(f"OpenRouter Model: {os.getenv('OPENROUTER_MODEL')}")
print(f"OpenRouter Base URL: {os.getenv('OPENROUTER_BASE_URL')}")
print(f"LangGraph URL: {os.getenv('NEXT_PUBLIC_LANGGRAPH_URL')}")

try:
    import fastapi
    print("✅ FastAPI instalado")
except ImportError:
    print("❌ FastAPI não instalado")

try:
    import uvicorn
    print("✅ Uvicorn instalado")
except ImportError:
    print("❌ Uvicorn não instalado")

try:
    import openai
    print("✅ OpenAI instalado")
except ImportError:
    print("❌ OpenAI não instalado")

try:
    from langchain_openai import ChatOpenAI
    print("✅ LangChain OpenAI instalado")
except ImportError:
    print("❌ LangChain OpenAI não instalado")

try:
    import langgraph
    print("✅ LangGraph instalado")
except ImportError:
    print("❌ LangGraph não instalado")

try:
    import copilotkit
    print("✅ CopilotKit instalado")
except ImportError:
    print("❌ CopilotKit não instalado")

print("\n=== Teste de Conectividade OpenRouter ===")
try:
    import requests
    
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ Conectividade com OpenRouter funcionando")
        models = response.json()
        print(f"Total de modelos disponíveis: {len(models.get('data', []))}")
    else:
        print(f"❌ Erro na conectividade: {response.status_code}")
        
except Exception as e:
    print(f"❌ Erro ao testar conectividade: {e}")

print("\n=== Status Final ===")
print("Frontend: http://localhost:3000 (rodando)")
print("Backend: Aguardando configuração completa")