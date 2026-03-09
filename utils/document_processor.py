# document_processor.py
# Loads docs from files, splits them into chunks, and stores in FAISS

import os
from typing import List, Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader

import config


class DocumentProcessor:

    LOADER_MAP = {
        ".txt": TextLoader,
        ".pdf": PyPDFLoader,
        ".csv": CSVLoader,
    }

    def __init__(self, embedding_model: Optional[str] = None):
        model_name = embedding_model or config.EMBEDDING_MODEL
        self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def load_documents(self, file_path: str) -> List[Document]:
        ext = os.path.splitext(file_path)[1].lower()
        loader_cls = self.LOADER_MAP.get(ext)
        if loader_cls is None:
            raise ValueError(f"Unsupported file type: {ext}")
        loader = loader_cls(file_path, encoding="utf-8") if ext == ".txt" else loader_cls(file_path)
        return loader.load()

    def load_directory(self, directory: str) -> List[Document]:
        documents = []
        if not os.path.isdir(directory):
            return documents
        for filename in sorted(os.listdir(directory)):
            ext = os.path.splitext(filename)[1].lower()
            if ext in self.LOADER_MAP:
                path = os.path.join(directory, filename)
                try:
                    documents.extend(self.load_documents(path))
                except Exception as e:
                    print(f"  [WARN] Could not load {path}: {e}")
        return documents

    def process_documents(self, documents: List[Document]) -> List[Document]:
        return self.text_splitter.split_documents(documents)

    def create_vector_store(self, documents: List[Document], store_name: str) -> FAISS:
        chunks = self.process_documents(documents)
        if not chunks:
            raise ValueError("No document chunks to index.")
        vector_store = FAISS.from_documents(chunks, self.embedding_model)
        save_path = os.path.join(config.VECTOR_STORE_DIR, store_name)
        os.makedirs(save_path, exist_ok=True)
        vector_store.save_local(save_path)
        return vector_store

    def load_vector_store(self, store_name: str) -> Optional[FAISS]:
        save_path = os.path.join(config.VECTOR_STORE_DIR, store_name)
        index_file = os.path.join(save_path, "index.faiss")
        if os.path.exists(index_file):
            return FAISS.load_local(
                save_path,
                self.embedding_model,
                allow_dangerous_deserialization=True,
            )
        return None

    def get_or_create_vector_store(self, directory: str, store_name: str) -> FAISS:
        existing = self.load_vector_store(store_name)
        if existing is not None:
            return existing
        documents = self.load_directory(directory)
        if not documents:
            raise FileNotFoundError(f"No loadable documents in {directory}")
        return self.create_vector_store(documents, store_name)
