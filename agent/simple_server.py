#!/usr/bin/env python3
"""
Servidor FastAPI básico para teste
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI(title="Open Gemini Canvas Backend")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Open Gemini Canvas Backend is running!"}

@app.get("/healthz")
async def health_check():
    return {
        "status": "healthy",
        "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "model": os.getenv("OPENROUTER_MODEL", "not-configured")
    }

@app.get("/test")
async def test_openrouter():
    """Teste básico de conectividade com OpenRouter"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {"error": "OpenRouter API key not configured"}
    
    try:
        import requests
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Teste simples de conectividade
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            models_data = response.json()
            return {
                "status": "connected",
                "total_models": len(models_data.get("data", [])),
                "configured_model": os.getenv("OPENROUTER_MODEL")
            }
        else:
            return {
                "status": "error",
                "code": response.status_code,
                "message": "Failed to connect to OpenRouter"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    print("Iniciando servidor básico na porta 8000...")
    print("Frontend: http://localhost:3000")
    print("Backend: http://localhost:8000")
    print("Health Check: http://localhost:8000/healthz")
    print("Test OpenRouter: http://localhost:8000/test")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)