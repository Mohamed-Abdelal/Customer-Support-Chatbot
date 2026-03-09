# response_formatter.py

from datetime import datetime


class ResponseFormatter:

    def __init__(self, company_name: str, support_email: str, support_phone: str):
        self.company_name = company_name
        self.support_email = support_email
        self.support_phone = support_phone

    def format_response(self, response_content: str, knowledge_base: str = None) -> str:
        lines = []
        if knowledge_base:
            lines.append(f"[Source: {knowledge_base}]")
        lines.append("")
        lines.append(response_content)
        lines.append("")
        lines.append(f"— {self.company_name} Support")
        return "\n".join(lines)

    def format_error_response(self, error_type: str) -> str:
        messages = {
            "api_error": (
                "We're experiencing a temporary service issue. "
                "Please try again in a moment or contact us directly."
            ),
            "empty_query": "It looks like your message was empty. How can I help you today?",
            "out_of_scope": (
                "I'm not sure I can help with that topic. I specialise in "
                "CloudStore Pro, SecureVault AI, DataFlow Analytics, and TeamFlow Pro."
            ),
            "hallucination_guard": (
                "I want to make sure I give you accurate information. "
                "Let me connect you with a specialist who can help."
            ),
        }
        body = messages.get(error_type, "Something went wrong. Please try again.")
        return (
            f"{body}\n\n"
            f"Contact us: {self.support_email} | {self.support_phone}"
        )

    def format_escalation_response(self, reason: str = "") -> str:
        return (
            "This issue requires attention from our specialist team.\n\n"
            f"{'Reason: ' + reason + chr(10) if reason else ''}"
            "Next steps:\n"
            f"  1. Email: {self.support_email}\n"
            f"  2. Phone: {self.support_phone} (24/7)\n"
            f"  3. Use the callback scheduler to book a support call.\n\n"
            f"— {self.company_name} Support"
        )

    def filter_response(self, response: str) -> str:
        blocked_phrases = [
            "i don't know",
            "i dont know",
            "as an ai language model",
            "i cannot provide medical",
            "i cannot provide legal",
            "i'm not sure",
            "im not sure",
        ]
        lower = response.lower()
        for phrase in blocked_phrases:
            if phrase.lower() in lower:
                return self.format_error_response("hallucination_guard")
        return response
