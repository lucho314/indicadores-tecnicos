#!/usr/bin/env python3

"""
Script de prueba para verificar el cliente OpenAI
"""

import os
from openai import OpenAI

def test_openai_client():
    print("🧪 Probando cliente OpenAI...")
    
    # Verificar API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY no encontrada")
        return False
    
    print(f"🔑 API Key encontrada: {api_key[:10]}...")
    
    try:
        # Crear cliente OpenAI básico (sin parámetros adicionales)
        print("🚀 Creando cliente OpenAI...")
        client = OpenAI(api_key=api_key)
        print("✅ Cliente OpenAI creado exitosamente")
        
        # Hacer una llamada simple
        print("📞 Haciendo llamada de prueba...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Di 'Hola mundo'"}],
            max_tokens=10
        )
        
        content = response.choices[0].message.content
        print(f"✅ Respuesta: {content}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_openai_client()
