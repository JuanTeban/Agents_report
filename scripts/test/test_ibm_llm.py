#!/usr/bin/env python3
"""
Script de prueba para IBM Watson LLM
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from app.core.ia.llm.ibm_provider import IBMWatsonProvider

async def test_ibm_simple():
    print("\n" + "="*80)
    print("TEST: IBM WATSON LLM - PRUEBA SIMPLE")
    print("="*80)
    
    try:
        provider = IBMWatsonProvider()
        
        prompt = "¿Cuál es la capital de Colombia? Responde en una sola línea."
        
        print(f"\nPrompt: {prompt}")
        print("Generando respuesta...\n")
        
        response = await provider.generate_async(prompt, temperature=0.3)
        
        print("RESPUESTA:")
        print("-"*80)
        print(response.content)
        print("-"*80)
        print(f"\nModelo: {response.model}")
        print(f"Tokens: {response.usage}")
        print(f"Metadata: {response.metadata}")
        
        print("\n✅ Test completado exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(test_ibm_simple())
    sys.exit(exit_code)