import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

COMPANY_NAME = "TechCorp"
SUPPORT_EMAIL = "support@techcorp.com"
SUPPORT_PHONE = "1-800-555-0123"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_stores")

PRODUCT_A_DIR = os.path.join(DATA_DIR, "product_a")
PRODUCT_B_DIR = os.path.join(DATA_DIR, "product_b")
PRODUCT_C_DIR = os.path.join(DATA_DIR, "product_c")
PRODUCT_D_DIR = os.path.join(DATA_DIR, "product_d")

LLM_TEMPERATURE = 0.1
MAX_TOKENS = 1024
RETRIEVER_K = 4
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
