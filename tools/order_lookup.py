# order_lookup.py

import json
from langchain_classic.tools import BaseTool


TICKET_DB = {
    "TKT-001": {"status": "Resolved", "product": "CloudStore Pro", "issue": "Sync not working", "resolved_at": "2024-03-01", "notes": "Fixed by clearing cache."},
    "TKT-002": {"status": "In Progress", "product": "SecureVault AI", "issue": "Browser extension bug", "assigned_to": "Platform Team", "eta": "2024-03-10"},
    "TKT-003": {"status": "Pending", "product": "DataFlow Analytics", "issue": "Slow dashboard", "eta": "Within 24 hours"},
    "TKT-004": {"status": "Resolved", "product": "CloudStore Pro", "issue": "API rate limiting", "resolved_at": "2024-03-02"},
    "TKT-005": {"status": "Escalated", "product": "TeamFlow Pro", "issue": "SSO configuration", "assigned_to": "Enterprise Team", "eta": "4 hours"},
    "TKT-006": {"status": "In Progress", "product": "SecureVault AI", "issue": "Breach alert false positive", "assigned_to": "Security Team", "eta": "2 hours"},
}


class OrderLookupTool(BaseTool):
    name: str = "ticket_status_lookup"
    description: str = (
        "Look up the status of a support ticket by its ID (e.g. TKT-001). "
        "Input should be the ticket ID."
    )

    def _run(self, ticket_id: str) -> str:
        tid = ticket_id.strip().upper()
        result = TICKET_DB.get(tid)
        if result is None:
            return json.dumps({
                "error": f"Ticket '{tid}' not found.",
                "valid_ids": list(TICKET_DB.keys()),
            })
        return json.dumps({"ticket_id": tid, **result}, indent=2)

    async def _arun(self, ticket_id: str) -> str:
        return self._run(ticket_id)
