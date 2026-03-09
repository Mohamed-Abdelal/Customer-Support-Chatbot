# ticket_manager.py

import json
from datetime import datetime
from langchain_classic.tools import BaseTool


SLA_MAP = {"Critical": "1 hour", "High": "4 hours", "Medium": "24 hours", "Low": "72 hours"}


class TicketManager(BaseTool):
    name: str = "create_support_ticket"
    description: str = (
        "Create a new support ticket. Input format: "
        "'issue_summary | product_name | severity' "
        "where severity is Critical, High, Medium, or Low. "
        "Example: 'Sync broken | CloudStore Pro | High'"
    )

    def _run(self, query: str) -> str:
        parts = [p.strip() for p in query.split("|")]
        if len(parts) < 3:
            return json.dumps({"error": "Format: 'issue | product | severity'"})

        summary, product, severity = parts[0], parts[1], parts[2]
        tid = f"TKT-{datetime.now().strftime('%H%M%S')}"
        return json.dumps({
            "ticket_id": tid,
            "status": "Created",
            "product": product,
            "summary": summary,
            "severity": severity,
            "response_sla": SLA_MAP.get(severity, "24 hours"),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "next_step": f"A support engineer will contact you within {SLA_MAP.get(severity, '24 hours')}.",
        }, indent=2)

    async def _arun(self, query: str) -> str:
        return self._run(query)
