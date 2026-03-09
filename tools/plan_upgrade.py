# plan_upgrade.py

import json
from langchain_classic.tools import BaseTool


UPGRADE_CATALOG = {
    "CloudStore Pro": {
        "Starter->Business": {"monthly_increase": "$40", "annual_savings": "$96", "benefits": ["20x more storage (2 TB)", "22 additional users", "Priority email support", "API access", "90-day version history"]},
        "Business->Enterprise": {"monthly_increase": "$150", "annual_savings": "$240", "benefits": ["Unlimited storage", "Unlimited users", "Dedicated CSM", "365-day history", "SLA guarantee", "HIPAA compliance"]},
    },
    "SecureVault AI": {
        "Free->Premium": {"monthly_increase": "$3", "annual_savings": "$12", "benefits": ["Unlimited passwords", "Priority support", "Advanced MFA", "Emergency access", "Dark-web monitoring"]},
        "Premium->Teams": {"monthly_increase": "$2/user", "annual_savings": "", "benefits": ["Admin console", "Shared vaults", "Activity log", "Usage reports"]},
        "Teams->Business": {"monthly_increase": "$3/user", "annual_savings": "", "benefits": ["SSO (SAML/OIDC)", "SCIM provisioning", "Advanced policies", "Audit trail"]},
    },
    "DataFlow Analytics": {
        "Analyst->Professional": {"monthly_increase": "$70", "annual_savings": "$120", "benefits": ["Unlimited dashboards", "Up to 20 data sources", "AutoML", "20 team members", "Streaming analytics"]},
        "Professional->Enterprise": {"monthly_increase": "$300", "annual_savings": "$480", "benefits": ["Unlimited sources", "Unlimited users", "Dedicated support", "Row-level security", "On-prem option", "Custom SLA"]},
    },
    "TeamFlow Pro": {
        "Free->Starter": {"monthly_increase": "$8/user", "annual_savings": "", "benefits": ["Unlimited projects", "20 GB storage", "Basic automations", "Priority support"]},
        "Starter->Business": {"monthly_increase": "$8/user", "annual_savings": "", "benefits": ["Advanced automations", "Time tracking & invoicing", "OKR tracking", "Resource management"]},
        "Business->Enterprise": {"monthly_increase": "$12/user", "annual_savings": "", "benefits": ["SSO", "Audit log", "Advanced security", "Dedicated CSM", "SLA guarantee"]},
    },
}


class PlanUpgradeCalculator(BaseTool):
    name: str = "plan_upgrade_calculator"
    description: str = (
        "Show upgrade cost and benefits for a product plan change. "
        "Input format: 'product_name | current->target'. "
        "Example: 'CloudStore Pro | Starter->Business'"
    )

    def _run(self, query: str) -> str:
        parts = [p.strip() for p in query.split("|")]
        if len(parts) < 2:
            return json.dumps({"error": "Format: 'product | plan_path' (e.g. 'CloudStore Pro | Starter->Business')"})

        product, plan_path = parts[0], parts[1]
        catalog = UPGRADE_CATALOG.get(product, {})
        result = catalog.get(plan_path)
        if result:
            return json.dumps({"product": product, "upgrade": plan_path, **result}, indent=2)
        return json.dumps({
            "info": "Plan path not found. Contact sales@techcorp.com",
            "available_upgrades": list(catalog.keys()) if catalog else [],
            "known_products": list(UPGRADE_CATALOG.keys()),
        })

    async def _arun(self, query: str) -> str:
        return self._run(query)
