# kb_manager.py

from typing import Dict, Optional

from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA, LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS

import config


class KnowledgeBase:

    def __init__(self, vector_store: FAISS, product_name: str, llm=None):
        self.vector_store = vector_store
        self.product_name = product_name
        self.llm = llm or ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.GROQ_MODEL,
            temperature=config.LLM_TEMPERATURE,
        )
        self.retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": config.RETRIEVER_K},
        )
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
        )

    def query(self, question: str) -> dict:
        result = self.qa_chain.invoke({"query": question})
        return {
            "answer": result.get("result", ""),
            "source_documents": result.get("source_documents", []),
            "product": self.product_name,
        }


class KnowledgeBaseRouter:

    ROUTING_TEMPLATE = PromptTemplate(
        template=(
            "You are a query router for a tech company with these products:\n"
            "{product_list}\n\n"
            "Given the customer query below, respond with ONLY the product key "
            "(e.g. 'cloud_services') that best matches. If the query spans multiple "
            "products or is unclear, respond with 'general'.\n\n"
            "Query: {query}\n\n"
            "Product key:"
        ),
        input_variables=["product_list", "query"],
    )

    def __init__(self, knowledge_bases: Dict[str, KnowledgeBase], llm=None):
        self.knowledge_bases = knowledge_bases
        self.llm = llm or ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.GROQ_MODEL,
            temperature=0,
        )
        self.routing_chain = LLMChain(llm=self.llm, prompt=self.ROUTING_TEMPLATE)

        self.product_list_str = "\n".join(
            f"  - {key}: {kb.product_name}"
            for key, kb in self.knowledge_bases.items()
        )

    def route_query(self, query: str) -> KnowledgeBase:
        try:
            result = self.routing_chain.run(
                product_list=self.product_list_str,
                query=query,
            ).strip().lower()

            for key in self.knowledge_bases:
                if key in result:
                    return self.knowledge_bases[key]

        except Exception:
            pass

        return self._fallback_route(query)

    def _fallback_route(self, query: str) -> KnowledgeBase:
        keywords = {
            "cloud_services": ["cloudstore", "cloud", "storage", "sync", "upload", "s3"],
            "security_products": ["securevault", "password", "vault", "breach", "sso", "mfa"],
            "analytics_platform": ["dataflow", "analytics", "dashboard", "report", "automl", "bi"],
            "project_management": ["teamflow", "project", "kanban", "scrum", "gantt", "okr"],
        }
        lower_query = query.lower()
        for key, words in keywords.items():
            if key in self.knowledge_bases and any(w in lower_query for w in words):
                return self.knowledge_bases[key]

        first_key = next(iter(self.knowledge_bases))
        return self.knowledge_bases[first_key]
