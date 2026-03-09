# compatibility_checker.py

import json
from langchain_classic.tools import BaseTool


COMPATIBILITY_MATRIX = {
    ("CloudStore Pro", "DataFlow Analytics"): {
        "compatible": True,
        "details": "CloudStore Pro can serve as a data source for DataFlow Analytics dashboards.",
    },
    ("CloudStore Pro", "TeamFlow Pro"): {
        "compatible": True,
        "details": "CloudStore Pro provides file attachments and shared storage for TeamFlow Pro projects.",
    },
    ("CloudStore Pro", "SecureVault AI"): {
        "compatible": False,
        "details": "No direct integration — they operate in separate security domains.",
    },
    ("SecureVault AI", "TeamFlow Pro"): {
        "compatible": True,
        "details": "SecureVault AI manages secure credentials used within TeamFlow Pro workflows.",
    },
    ("SecureVault AI", "DataFlow Analytics"): {
        "compatible": False,
        "details": "No direct integration available at this time.",
    },
    ("DataFlow Analytics", "TeamFlow Pro"): {
        "compatible": True,
        "details": "DataFlow dashboards can be embedded inside TeamFlow Pro projects.",
    },
}


class CompatibilityChecker(BaseTool):
    name: str = "compatibility_checker"
    description: str = (
        "Check if two TechCorp products are compatible. "
        "Input should be two product names separated by a comma, "
        "e.g. 'CloudStore Pro, DataFlow Analytics'."
    )

    def _run(self, query: str) -> str:
        products = [p.strip() for p in query.split(",")]
        if len(products) < 2:
            return json.dumps({"error": "Please provide two product names separated by a comma."})

        p1, p2 = products[0], products[1]
        key = (p1, p2) if (p1, p2) in COMPATIBILITY_MATRIX else (p2, p1)
        result = COMPATIBILITY_MATRIX.get(key)
        if result is None:
            return json.dumps({
                "error": f"Unknown product pair: {p1} & {p2}",
                "known_products": ["CloudStore Pro", "SecureVault AI", "DataFlow Analytics", "TeamFlow Pro"],
            })
        return json.dumps({"product_1": p1, "product_2": p2, **result}, indent=2)

    async def _arun(self, query: str) -> str:
        return self._run(query)
