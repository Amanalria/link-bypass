import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8725136049:AAE_36bHCVXwZJxTWzeNsGC6tQnOSgjls-k")
MAX_HOPS = int(os.getenv("MAX_HOPS", "25"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))

class Config:
    BOT_TOKEN = BOT_TOKEN
    MAX_HOPS = MAX_HOPS
    REQUEST_TIMEOUT = REQUEST_TIMEOUT
