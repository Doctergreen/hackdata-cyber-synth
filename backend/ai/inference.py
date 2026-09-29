import json
import logging
import re
from typing import Any, Dict, Optional, Tuple

import httpx

from backend.config import settings
from backend.models.schemas import UnifiedSchema, TableDefinition, FieldDefinition, DocumentConfig

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Synthetic Data Architect for HackDataV2.
Your task is to translate natural language user prompts into a structured schema specification in strict JSON format.

The JSON schema must adhere to this contract:
{
  "project_name": "PROJECT_NAME",
  "mode": "tabular" | "relational" | "document",
  "locale": "en_US",
  "seed": 1337,
  "tables": [
    {
      "name": "table_name",
      "row_count": 25,
      "fields": [
        {
          "name": "field_name",
          "type": "uuid" | "name" | "email" | "currency" | "category" | "datetime" | "date" | "ipv4" | "foreign_key" | "integer" | "float" | "boolean" | "ai_context",
          "is_primary": true | false,
          "privacy": "none" | "mask" | "hash" | "redact",
          "options": ["opt1", "opt2"], // only for category
          "null_rate": 0.05, // 0.0 to 1.0 edge case injection
          "outlier_rate": 0.02, // 0.0 to 1.0 statistical anomaly injection
          "min": 100, // for numeric
          "max": 5000,
          "references": "parent_table.primary_key" // required if type == foreign_key
        }
      ]
    }
  ],
  "documents": {
    "type": "invoice" | "bank_statement",
    "template": "hacker_receipt",
    "currency": "USD",
    "tax_rate": 0.08
  }
}

Rules:
1. Always enforce primary keys (uuid or int) and foreign keys with references (e.g. "customers.customer_id").
2. Include privacy controls: use 'mask' for emails, 'hash' for IPs or secret tokens.
3. Include realistic edge cases (null_rate 0.02 - 0.10, outlier_rate 0.01 - 0.05) if anomalies or edge cases are requested.
4. Output RAW JSON ONLY. No markdown wrappers or preamble.
"""

def generate_heuristic_schema(prompt: str) -> UnifiedSchema:
    """
    Intelligent heuristic fallback when OpenRouter is unreachable or API key is absent.
    Parses key concepts from prompt to build high-fidelity schemas.
    """
    p = prompt.lower()

    if any(k in p for k in ["invoice", "receipt", "billing"]):
        return UnifiedSchema(
            project_name="CYBER_BILLING_SUITE",
            mode="document",
            locale="en_US",
            seed=1337,
            documents=DocumentConfig(
                type="invoice",
                template="hacker_receipt",
                currency="CYBER_CRED" if "cyber" in p else "USD",
                tax_rate=0.08,
                item_count=6
            )
        )

    if any(k in p for k in ["statement", "bank statement"]):
        return UnifiedSchema(
            project_name="FINANCIAL_LEDGER_RUNNER",
            mode="document",
            locale="en_US",
            seed=1337,
            documents=DocumentConfig(
                type="bank_statement",
                template="hacker_receipt",
                currency="USD",
                initial_balance=12500.0,
                item_count=15
            )
        )

    if any(k in p for k in ["ecommerce", "e-commerce", "shop", "store", "order"]):
        return UnifiedSchema(
            project_name="CYBER_ECOMMERCE_PLATFORM",
            mode="relational",
            locale="en_US",
            seed=1337,
            tables=[
                TableDefinition(
                    name="customers",
                    row_count=15,
                    fields=[
                        FieldDefinition(name="customer_id", type="uuid", is_primary=True),
                        FieldDefinition(name="full_name", type="name", privacy="none"),
                        FieldDefinition(name="email", type="email", privacy="mask"),
                        FieldDefinition(name="tier", type="category", options=["STANDARD", "PRO", "CYBER_ELITE"]),
                        FieldDefinition(name="signup_date", type="date", start="2025-01-01", end="2026-06-30")
                    ]
                ),
                TableDefinition(
                    name="orders",
                    row_count=35,
                    fields=[
                        FieldDefinition(name="order_id", type="uuid", is_primary=True),
                        FieldDefinition(name="customer_id", type="foreign_key", references="customers.customer_id"),
                        FieldDefinition(name="order_date", type="datetime", start="2026-01-01", end="2026-09-30"),
                        FieldDefinition(name="order_status", type="category", options=["COMPLETED", "PROCESSING", "SHIPPED", "DISPUTED"]),
                        FieldDefinition(name="total_amount", type="currency", min=50.0, max=5000.0, outlier_rate=0.03)
                    ]
                ),
                TableDefinition(
                    name="order_items",
                    row_count=80,
                    fields=[
                        FieldDefinition(name="item_id", type="uuid", is_primary=True),
                        FieldDefinition(name="order_id", type="foreign_key", references="orders.order_id"),
                        FieldDefinition(name="product_name", type="category", options=["Quantum Neural Link", "Zero-Day Exploit Shield", "Cold Storage Ledger", "Bionic Interface Cable"]),
                        FieldDefinition(name="quantity", type="integer", min=1, max=5),
                        FieldDefinition(name="unit_price", type="currency", min=45.0, max=1200.0),
                        FieldDefinition(name="line_total", type="currency", min=45.0, max=6000.0)
                    ]
                )
            ]
        )

    # Banking / Ledger / Cyber Anomaly Default
    if any(k in p for k in ["bank", "ledger", "fraud", "transfer", "laundering"]):
        return UnifiedSchema(
            project_name="CYBER_BANKING_LEDGER",
            mode="relational",
            locale="en_US",
            seed=1337,
            tables=[
                TableDefinition(
                    name="accounts",
                    row_count=20,
                    fields=[
                        FieldDefinition(name="account_id", type="uuid", is_primary=True),
                        FieldDefinition(name="account_holder", type="name", privacy="none"),
                        FieldDefinition(name="account_email", type="email", privacy="mask"),
                        FieldDefinition(name="account_type", type="category", options=["CHECKING", "SAVINGS", "OFFSHORE_VAULT"]),
                        FieldDefinition(name="balance", type="currency", min=1000.0, max=50000.0, outlier_rate=0.05)
                    ]
                ),
                TableDefinition(
                    name="transactions",
                    row_count=60,
                    fields=[
                        FieldDefinition(name="tx_id", type="uuid", is_primary=True),
                        FieldDefinition(name="account_id", type="foreign_key", references="accounts.account_id"),
                        FieldDefinition(name="timestamp", type="datetime", start="2026-06-01", end="2026-09-30"),
                        FieldDefinition(name="type", type="category", options=["DEBIT", "CREDIT"]),
                        FieldDefinition(name="amount", type="currency", min=15.0, max=15000.0, outlier_rate=0.08),
                        FieldDefinition(name="terminal_ip", type="ipv4", privacy="hash"),
                        FieldDefinition(name="action_summary", type="ai_context", prompt="cyber banking wire transfers and anomalous structuring")
                    ]
                ),
                TableDefinition(
                    name="fraud_alerts",
                    row_count=15,
                    fields=[
                        FieldDefinition(name="alert_id", type="uuid", is_primary=True),
                        FieldDefinition(name="tx_id", type="foreign_key", references="transactions.tx_id"),
                        FieldDefinition(name="risk_score", type="float", min=0.75, max=0.99, distribution="uniform"),
                        FieldDefinition(name="detection_rule", type="category", options=["RAPID_TRANSFER_VELOCITY", "GEO_IMPOSSIBLE_TRAVEL", "STRUCTURING_CEILING_EVASION"]),
                        FieldDefinition(name="flagged_anomalous", type="boolean")
                    ]
                )
            ]
        )

    # General Cyber Operatives & Access Logs
    return UnifiedSchema(
        project_name="CYBER_SYNTH_V1",
        mode="relational",
        locale="en_US",
        seed=1337,
        tables=[
            TableDefinition(
                name="operatives",
                row_count=25,
                fields=[
                    FieldDefinition(name="agent_id", type="uuid", is_primary=True),
                    FieldDefinition(name="codename", type="name", privacy="none"),
                    FieldDefinition(name="secure_email", type="email", privacy="mask"),
                    FieldDefinition(name="clearance_level", type="category", options=["ALPHA", "BETA", "OMEGA"], null_rate=0.05),
                    FieldDefinition(name="credits", type="currency", min=500.0, max=25000.0, outlier_rate=0.02)
                ]
            ),
            TableDefinition(
                name="access_logs",
                row_count=75,
                fields=[
                    FieldDefinition(name="log_id", type="uuid", is_primary=True),
                    FieldDefinition(name="agent_id", type="foreign_key", references="operatives.agent_id"),
                    FieldDefinition(name="timestamp", type="datetime", start="2026-01-01", end="2026-09-30"),
                    FieldDefinition(name="terminal_ip", type="ipv4", privacy="hash"),
                    FieldDefinition(name="action_summary", type="ai_context", prompt="cyberpunk terminal operations like breach detection or mainframe ping")
                ]
            )
        ]
    )

async def infer_schema_from_prompt(prompt: str, model: Optional[str] = None) -> Tuple[UnifiedSchema, str, str]:
    """
    Calls OpenRouter API to infer schema. Falls back cleanly to heuristic synthesizer if unavailable.
    """
    chosen_model = model or settings.DEFAULT_MODEL
    api_key = settings.OPENROUTER_API_KEY.strip()

    if not api_key:
        logger.info("No OPENROUTER_API_KEY detected. Using intelligent heuristic synthesis engine.")
        schema = generate_heuristic_schema(prompt)
        return schema, "heuristic-offline-synthesizer", "Synthesized using built-in deterministic schema architect."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://hackdatav2.synthetics.dev",
        "X-Title": "HackDataV2 Synthetic Data Platform",
        "Content-Type": "application/json"
    }

    payload = {
        "model": chosen_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Infer synthetic data schema for: {prompt}"}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )

            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                
                # Clean potential markdown wrapping
                cleaned = re.sub(r"^```(?:json)?\s*", "", content.strip())
                cleaned = re.sub(r"\s*```$", "", cleaned)

                parsed_json = json.loads(cleaned)
                schema = UnifiedSchema.model_validate(parsed_json)
                return schema, chosen_model, "Inferred successfully via OpenRouter."
            else:
                logger.warning(f"OpenRouter returned status {resp.status_code}: {resp.text}")
                schema = generate_heuristic_schema(prompt)
                return schema, f"{chosen_model}-fallback", f"Fell back to heuristic engine (OpenRouter HTTP {resp.status_code})"

    except Exception as exc:
        logger.error(f"Error connecting to OpenRouter: {exc}")
        schema = generate_heuristic_schema(prompt)
        return schema, "heuristic-synthesizer", f"Fell back to heuristic engine: {str(exc)}"
