import hashlib
import random
import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from faker import Faker
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from ai.openrouter_client import infer_schema_from_prompt

app = FastAPI(title="CYBER_SYNTH_API", version="1.0.0")
fake = Faker()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AIInferRequest(BaseModel):
    prompt: str

class TabularField(BaseModel):
    name: str
    type: str  # uuid, name, email, currency, category, date
    privacy: Optional[str] = "none" # mask, hash, none
    options: Optional[List[str]] = None
    min_val: Optional[float] = 100.0
    max_val: Optional[float] = 5000.0

class TabularRequest(BaseModel):
    row_count: int = 25
    seed: Optional[int] = 42
    null_rate: float = 0.0
    outlier_rate: float = 0.0
    fields: List[TabularField]

@app.post("/api/schema/infer")
def infer_schema(req: AIInferRequest):
    return infer_schema_from_prompt(req.prompt)

@app.post("/api/generate/tabular")
def generate_tabular(req: TabularRequest):
    if req.seed is not None:
        Faker.seed(req.seed)
        random.seed(req.seed)

    rows = []
    for _ in range(req.row_count):
        row = {}
        for f in req.fields:
            if random.random() < req.null_rate:
                row[f.name] = None
                continue

            # Core Type Generation
            if f.type == "uuid":
                val = str(uuid.uuid4())[:8]
            elif f.type == "name":
                val = fake.name()
            elif f.type == "email":
                val = fake.safe_email()
            elif f.type == "currency":
                val = round(random.uniform(f.min_val, f.max_val), 2)
                if random.random() < req.outlier_rate:
                    val = round(val * 10, 2)
            elif f.type == "category" and f.options:
                val = random.choice(f.options)
            elif f.type == "date":
                val = fake.date_this_year().isoformat()
            else:
                val = fake.word()

            # Privacy Rules (Slide 5)
            if f.privacy == "mask" and isinstance(val, str) and "@" in val:
                user_part, domain = val.split("@", 1)
                val = f"{user_part[:1]}***@{domain}"
            elif f.privacy == "hash" and val is not None:
                val = hashlib.sha256(str(val).encode()).hexdigest()[:12]

            row[f.name] = val
        rows.append(row)
    return {"status": "SUCCESS", "count": len(rows), "data": rows}

@app.post("/api/generate/relational")
def generate_relational(seed: int = 42, cust_count: int = 10, orders_count: int = 25):
    random.seed(seed)
    Faker.seed(seed)

    # 1. Customers (Parent Table)
    customers = [
        {"customer_id": f"CUST-{i:03d}", "name": fake.name(), "email": f"{fake.user_name()}@cyber.net"}
        for i in range(1, cust_count + 1)
    ]

    # 2. Orders (Child Table with FK)
    orders = []
    order_items = []
    item_id_counter = 1

    skus = [
        {"sku": "NEURAL-LINK-V2", "price": 450.0},
        {"sku": "CYBER-DECK-PORTABLE", "price": 1200.0},
        {"sku": "QUANTUM-KEY-DONGLE", "price": 85.0}
    ]

    for o_idx in range(1, orders_count + 1):
        cust = random.choice(customers)
        ord_id = f"ORD-{o_idx:04d}"
        
        # 3. Order Items with Mathematical Reconciliation (Slide 6)
        num_items = random.randint(1, 3)
        order_total = 0.0
        
        for _ in range(num_items):
            chosen = random.choice(skus)
            qty = random.randint(1, 4)
            line_amount = round(chosen["price"] * qty, 2)
            order_total += line_amount
            
            order_items.append({
                "item_id": f"ITEM-{item_id_counter:05d}",
                "order_id": ord_id,
                "sku": chosen["sku"],
                "qty": qty,
                "unit_price": chosen["price"],
                "total_amount": line_amount
            })
            item_id_counter += 1

        orders.append({
            "order_id": ord_id,
            "customer_id": cust["customer_id"],
            "order_date": (datetime.now() - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d"),
            "order_total": round(order_total, 2)
        })

    return {
        "status": "SUCCESS",
        "tables": {
            "customers": customers,
            "orders": orders,
            "order_items": order_items
        }
    }

@app.post("/api/generate/document")
def generate_document(doc_type: str = "invoice"):
    if doc_type == "invoice":
        # Slide 7 Reconciled Invoice Spec
        items = [
            {"item": "API access — Pro tier", "qty": 1, "unit_price": 1100.00, "amount": 1100.00},
            {"item": "Onboarding support", "qty": 1, "unit_price": 140.00, "amount": 140.00}
        ]
        subtotal = sum(i["amount"] for i in items)
        tax = round(subtotal * 0.08, 2)
        total = round(subtotal + tax, 2)
        return {
            "type": "invoice",
            "invoice_number": f"INV-{random.randint(10000, 99999)}",
            "billed_to": fake.company(),
            "from_entity": "Synth Data Co.",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "items": items,
            "subtotal": subtotal,
            "tax": tax,
            "total": total
        }
    else:
        # Slide 8 Reconciled Bank Statement Spec
        balance = 1204.30
        records = [
            {"date": "08-14", "description": "Greenleaf Market", "debit": 42.10, "credit": None, "balance": round(balance, 2)},
            {"date": "08-15", "description": "Payroll deposit", "debit": None, "credit": 2150.00, "balance": round(balance - 42.10 + 2150.00, 2)},
            {"date": "08-17", "description": "Riverside Utilities", "debit": 96.40, "credit": None, "balance": round(balance - 42.10 + 2150.00 - 96.40, 2)}
        ]
        return {
            "type": "bank_statement",
            "account_holder": fake.name(),
            "account_number": f"CYB-****{random.randint(1000, 9999)}",
            "transactions": records
        }