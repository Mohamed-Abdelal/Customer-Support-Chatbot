# diagnostics.py

import json
from langchain_classic.tools import BaseTool


STATUS_DB = {
    "CloudStore Pro": {
        "overall": "Operational",
        "api": "Operational",
        "sync": "Operational",
        "web_console": "Operational",
        "uptime_30d": "99.97%",
    },
    "SecureVault AI": {
        "overall": "Operational",
        "api": "Operational",
        "browser_ext": "Degraded",
        "breach_monitor": "Operational",
        "uptime_30d": "99.99%",
        "incident": "Extension auto-fill intermittent on Chrome 122 — fix releasing 2024-03-10",
    },
    "DataFlow Analytics": {
        "overall": "Operational",
        "api": "Operational",
        "dashboards": "Operational",
        "reports": "Operational",
        "uptime_30d": "99.95%",
    },
    "TeamFlow Pro": {
        "overall": "Operational",
        "api": "Operational",
        "video_calls": "Operational",
        "notifications": "Operational",
        "uptime_30d": "99.98%",
    },
}


class DiagnosticsTool(BaseTool):
    name: str = "system_diagnostics"
    description: str = (
        "Check the real-time operational status of a TechCorp product. "
        "Input the product name, e.g. 'SecureVault AI'."
    )

    def _run(self, product: str) -> str:
        product = product.strip()
        result = STATUS_DB.get(product)
        if result is None:
            for key in STATUS_DB:
                if key.lower() in product.lower() or product.lower() in key.lower():
                    result = STATUS_DB[key]
                    product = key
                    break
        if result is None:
            return json.dumps({
                "error": f"Unknown product: {product}",
                "available": list(STATUS_DB.keys()),
            })
        return json.dumps({"product": product, **result}, indent=2)

    async def _arun(self, product: str) -> str:
        return self._run(product)
