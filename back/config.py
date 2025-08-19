import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Constantes generales
API_KEY = os.getenv("TWELVEDATA_API_KEY") 
SYMBOL = os.getenv("SYMBOL")
INTERVAL = os.getenv("INTERVAL")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Brevo (correo)
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")



# WhatsApp CallMeBot
CALLMEBOT_PHONE = os.getenv("CALLMEBOT_PHONE")
CALLMEBOT_APIKEY = os.getenv("CALLMEBOT_APIKEY")

# Bybit Trading
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

# Debug: verificar que las variables se carguen
print(f"🔍 Config Debug - BYBIT_API_KEY: {'✅ Configurada' if BYBIT_API_KEY else '❌ No encontrada'}")
print(f"🔍 Config Debug - BYBIT_API_SECRET: {'✅ Configurada' if BYBIT_API_SECRET else '❌ No encontrada'}")

