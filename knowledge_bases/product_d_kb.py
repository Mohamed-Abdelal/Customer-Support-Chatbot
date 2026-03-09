# product_d_kb.py - TeamFlow Pro

from utils.document_processor import DocumentProcessor
from knowledge_bases.kb_manager import KnowledgeBase
import config


def build_project_management_kb(llm=None) -> KnowledgeBase:
    processor = DocumentProcessor()
    vector_store = processor.get_or_create_vector_store(
        config.PRODUCT_D_DIR, "project_management"
    )
    return KnowledgeBase(vector_store, "TeamFlow Pro", llm=llm)
