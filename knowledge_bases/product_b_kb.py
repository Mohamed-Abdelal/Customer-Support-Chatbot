# product_b_kb.py - SecureVault AI

from utils.document_processor import DocumentProcessor
from knowledge_bases.kb_manager import KnowledgeBase
import config


def build_security_kb(llm=None) -> KnowledgeBase:
    processor = DocumentProcessor()
    vector_store = processor.get_or_create_vector_store(
        config.PRODUCT_B_DIR, "security_products"
    )
    return KnowledgeBase(vector_store, "SecureVault AI", llm=llm)
