import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment configuration
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()

# Validate environment
VALID_ENVIRONMENTS = ["development", "testing", "production"]
if ENVIRONMENT not in VALID_ENVIRONMENTS:
    raise ValueError(f"ENVIRONMENT must be one of: {', '.join(VALID_ENVIRONMENTS)}")

# Environment helpers
IS_DEVELOPMENT = ENVIRONMENT == "development"
IS_TESTING = ENVIRONMENT == "testing"
IS_PRODUCTION = ENVIRONMENT == "production"

# Logging configuration
log_level = logging.INFO if IS_PRODUCTION else logging.WARNING
logging.basicConfig(level=log_level)

# Auth0 configuration
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
AUTH0_API_AUDIENCE = os.environ.get("AUTH0_API_AUDIENCE", "")
CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET", "")
AUTH0_CALLBACK_URI = os.environ.get("AUTH0_CALLBACK_URI", "http://localhost:8000/callback")

# Validate Auth0 configuration
if not all([AUTH0_DOMAIN, AUTH0_API_AUDIENCE, CLIENT_ID, CLIENT_SECRET, AUTH0_CALLBACK_URI]):
    raise ValueError("All Auth0 environment variables must be set.")

# Session configuration
SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "your-super-secret-key-here")

# Validate SESSION_SECRET_KEY in production
if IS_PRODUCTION and SESSION_SECRET_KEY == "your-super-secret-key-here":
    raise ValueError("SESSION_SECRET_KEY must be set to a secure value in production")

# CORS configuration
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8000")

# Database configuration
DB_NAME = os.environ.get("DB_NAME", "pet_control")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "profiles")
PETS_COLLECTION_NAME = os.environ.get("PETS_COLLECTION_NAME", "pets")
VACCINES_COLLECTION_NAME = os.environ.get("VACCINES_COLLECTION_NAME", "vaccines")
ECTOPARASITES_COLLECTION_NAME = os.environ.get("ECTOPARASITES_COLLECTION_NAME", "ectoparasites")
VERMIFUGOS_COLLECTION_NAME = os.environ.get("VERMIFUGOS_COLLECTION_NAME", "vermifugos")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")

# File upload configuration
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Request timeout
REQUEST_TIMEOUT = 10

# Gmail configuration for daily notifications
GMAIL_EMAIL = os.environ.get("GMAIL_EMAIL", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD", "")
GMAIL_SMTP_SERVER = os.environ.get("GMAIL_SMTP_SERVER", "smtp.gmail.com")
GMAIL_SMTP_PORT = int(os.environ.get("GMAIL_SMTP_PORT", "587"))

# Validate Gmail configuration for notifications (only if being used)
def validate_gmail_config():
    """Valida configuração do Gmail apenas quando necessário"""
    if not GMAIL_EMAIL or not GMAIL_PASSWORD:
        return False, "GMAIL_EMAIL e GMAIL_PASSWORD devem ser configurados no .env"
    return True, "Gmail configurado corretamente"
