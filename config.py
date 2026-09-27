import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in the project root
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_college_library_key_2026')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'

    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_NAME = os.getenv('DB_NAME', 'library_db')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Business Rules
    MAX_ISSUED_BOOKS = 3
    LOAN_PERIOD_DAYS = 14
    DAILY_FINE_RATE = 5.00  # Rs. 5.00 per day overdue
