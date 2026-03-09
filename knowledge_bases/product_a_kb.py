# product_a_kb.py - CloudStore Pro

from utils.document_processor import DocumentProcessor
from knowledge_bases.kb_manager import KnowledgeBase
import config


def build_cloud_services_kb(llm=None) -> KnowledgeBase:
    processor = DocumentProcessor()
    vector_store = processor.get_or_create_vector_store(
        config.PRODUCT_A_DIR, "cloud_services"
    )
    return KnowledgeBase(vector_store, "CloudStore Pro", llm=llm)
