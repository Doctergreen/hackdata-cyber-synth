import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Fast, ultra-cheap model to conserve your $10 balance
MODEL = "openai/gpt-4o-mini"

SYSTEM_PROMPT = """
You are an expert database architect and synthetic data engine for HackDataV2.
Convert the user's natural language request into a clean, valid JSON schema.
Output ONLY raw JSON with this exact structure:
{
  "mode": "tabular" | "relational" | "document",
  "project_name": "string",
  "tables": [
    {
      "name": "string",
      "row_count": 25,
      "fields": [
        {"name": "string", "type": "uuid"|"name"|"email"|"currency"|"date"|"category"|"foreign_key", "privacy": "none"|"mask"|"hash", "references": "table.col"}
      ]
    }
  ],
  "document_config": {
    "doc_type": "invoice" | "bank_statement",
    "currency": "$",
    "tax_rate": 0.08
  }
}
"""

def infer_schema_from_prompt(prompt: str) -> dict:
    if not OPENROUTER_API_KEY:
        # Fallback preset if key is missing
        return {
            "mode": "tabular",
            "project_name": "FALLBACK_CORP",
            "tables": [{
                "name": "operatives",
                "row_count": 20,
                "fields": [
                    {"name": "id", "type": "uuid", "privacy": "none"},
                    {"name": "codename", "type": "name", "privacy": "none"},
                    {"name": "comm_link", "type": "email", "privacy": "mask"},
                    {"name": "bounty", "type": "currency", "min": 1000, "max": 50000}
                ]
            }]
        }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "CyberSynth Platform"
    }
    payload = {
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    res = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
    data = res.json()
    return json.loads(data["choices"][0]["message"]["content"])