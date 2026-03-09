# product_c_kb.py - DataFlow Analytics

from utils.document_processor import DocumentProcessor
from knowledge_bases.kb_manager import KnowledgeBase
import config


def build_analytics_kb(llm=None) -> KnowledgeBase:
    processor = DocumentProcessor()
    vector_store = processor.get_or_create_vector_store(
        config.PRODUCT_C_DIR, "analytics_platform"
    )
    return KnowledgeBase(vector_store, "DataFlow Analytics", llm=llm)
