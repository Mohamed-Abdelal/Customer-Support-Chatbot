# main.py - CLI entry point for customer support

import sys
import re
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_groq import ChatGroq

import config
from utils.document_processor import DocumentProcessor
from knowledge_bases.kb_manager import KnowledgeBase, KnowledgeBaseRouter
from conversation.memory_manager import ConversationManager
from utils.response_formatter import ResponseFormatter
from tools.compatibility_checker import CompatibilityChecker
from tools.diagnostics import DiagnosticsTool
from tools.order_lookup import OrderLookupTool
from tools.ticket_manager import TicketManager
from tools.callback_scheduler import CallbackScheduler
from tools.plan_upgrade import PlanUpgradeCalculator


class CustomerSupportSystem:

    def __init__(self):
        print("\n[INFO] Initializing Customer Support System...")

        if not config.GROQ_API_KEY:
            print("[ERROR] Please set GROQ_API_KEY in .env or environment.")
            sys.exit(1)

        self.llm = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.GROQ_MODEL,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.MAX_TOKENS,
        )

        print("[INFO] Loading knowledge bases...")
        self.processor = DocumentProcessor()
        self.knowledge_bases = self._build_knowledge_bases()
        self.router = KnowledgeBaseRouter(self.knowledge_bases, llm=self.llm)

        self.memory_manager = ConversationManager(memory_type="buffer")

        self.formatter = ResponseFormatter(
            company_name=config.COMPANY_NAME,
            support_email=config.SUPPORT_EMAIL,
            support_phone=config.SUPPORT_PHONE,
        )

        self.tools = [
            CompatibilityChecker(),
            DiagnosticsTool(),
            OrderLookupTool(),
            TicketManager(),
            CallbackScheduler(),
            PlanUpgradeCalculator(),
        ]

        print("[INFO] System ready.\n")

    def _build_knowledge_bases(self) -> dict:
        product_map = {
            "cloud_services": (config.PRODUCT_A_DIR, "CloudStore Pro"),
            "security_products": (config.PRODUCT_B_DIR, "SecureVault AI"),
            "analytics_platform": (config.PRODUCT_C_DIR, "DataFlow Analytics"),
            "project_management": (config.PRODUCT_D_DIR, "TeamFlow Pro"),
        }
        kbs = {}
        for kb_name, (directory, display_name) in product_map.items():
            print(f"  Processing: {display_name}")
            vector_store = self.processor.get_or_create_vector_store(directory, kb_name)
            kbs[kb_name] = KnowledgeBase(vector_store, display_name, llm=self.llm)
        return kbs

    def process_query(self, user_query: str) -> str:
        user_query = user_query.strip()
        if not user_query:
            return self.formatter.format_error_response("empty_query")

        self.memory_manager.add_user_message(user_query)

        try:
            tool_result = self._try_tool(user_query)
            if tool_result:
                self.memory_manager.add_ai_message(tool_result)
                return self.formatter.format_response(tool_result, "Specialized Tool")

            result = self._query_with_memory(user_query)
            answer = self.formatter.filter_response(result["answer"])
            self.memory_manager.add_ai_message(answer)
            return self.formatter.format_response(answer, result.get("product", "Knowledge Base"))

        except Exception as e:
            self.memory_manager.add_ai_message(f"[Error] {e}")
            return self.formatter.format_error_response("api_error")

    def _try_tool(self, query: str):
        lower = query.lower()
        if any(w in lower for w in ["compatible", "compatibility"]):
            return CompatibilityChecker().run(query)
        if any(w in lower for w in ["diagnos", "status check", "system status"]):
            return DiagnosticsTool().run(query)
        match = re.search(r"(TKT-\d+)", query.upper())
        if match:
            return OrderLookupTool().run(match.group(1))
        if "upgrade" in lower and ("plan" in lower or "->" in query):
            return PlanUpgradeCalculator().run(query)
        return None

    def _query_with_memory(self, user_query: str) -> dict:
        history = self.memory_manager.get_formatted_history()
        kb = self.router.route_query(user_query)

        if history and self.memory_manager.turn_count() > 1:
            context_query = f"Conversation so far:\n{history}\n\nLatest question: {user_query}"
        else:
            context_query = user_query

        return kb.query(context_query)

    def run_interactive(self) -> None:
        print("=" * 60)
        print(f"  Welcome to {config.COMPANY_NAME} Support")
        print("=" * 60)
        print("Type your question. Commands: 'clear' | 'history' | 'quit'\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[Session ended]")
                break

            if not user_input:
                continue
            if user_input.lower() == "quit":
                print("Thank you for contacting TechCorp Support. Goodbye!")
                break
            if user_input.lower() == "clear":
                self.memory_manager.clear()
                print("[Conversation history cleared]\n")
                continue
            if user_input.lower() == "history":
                print("\n--- Conversation History ---")
                print(self.memory_manager.get_formatted_history() or "(empty)")
                print("----------------------------\n")
                continue

            response = self.process_query(user_input)
            print(f"\n{response}\n")


if __name__ == "__main__":
    system = CustomerSupportSystem()
    system.run_interactive()
