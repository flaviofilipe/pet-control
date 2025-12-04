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

# Database configuration (PostgreSQL)
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://pet_control_user:pet_control_pass@localhost:5432/pet_control"
)

# Pool de conexões
DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.environ.get("DB_POOL_RECYCLE", "3600"))

# Auto migrations/seeds
AUTO_RUN_MIGRATIONS = os.environ.get("AUTO_RUN_MIGRATIONS", "false").lower() == "true"
AUTO_RUN_SEEDS = os.environ.get("AUTO_RUN_SEEDS", "false").lower() == "true"

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
