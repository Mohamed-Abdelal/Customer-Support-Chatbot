# callback_scheduler.py

import json
from datetime import datetime
from langchain_classic.tools import BaseTool


class CallbackScheduler(BaseTool):
    name: str = "schedule_callback"
    description: str = (
        "Schedule a callback from a support engineer. Input format: "
        "'name | email | preferred_time | issue_brief'. "
        "Example: 'Jane Doe | jane@example.com | 2024-03-10 14:00 UTC | SSO setup help'"
    )

    def _run(self, query: str) -> str:
        parts = [p.strip() for p in query.split("|")]
        if len(parts) < 4:
            return json.dumps({"error": "Format: 'name | email | time | issue'"})

        name, email, time, issue = parts[0], parts[1], parts[2], parts[3]
        return json.dumps({
            "confirmation": "Callback scheduled",
            "name": name,
            "email": email,
            "scheduled_time": time,
            "issue": issue,
            "meeting_link": f"https://meet.techcorp.com/support-{datetime.now().strftime('%H%M%S')}",
            "note": "A calendar invite will be sent to your email within 5 minutes.",
        }, indent=2)

    async def _arun(self, query: str) -> str:
        return self._run(query)
