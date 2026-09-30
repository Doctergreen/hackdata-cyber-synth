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
            if f.privacy == "mask" and isinstance(val, str):
                if "@" in val:
                    user_part, domain = val.split("@", 1)
                    val = f"{user_part[:1]}***@{domain}"
                else:
                    parts = val.split()
                    val = " ".join([p[0] + "*" * (len(p) - 1) if len(p) > 1 else p for p in parts])
            elif f.privacy == "hash" and val is not None:
                val = hashlib.sha256(str(val).encode()).hexdigest()[:12]

            row[f.name] = val
        rows.append(row)
    return {"status": "SUCCESS", "count": len(rows), "data": rows}

@app.post("/api/generate/relational")
def generate_relational(seed: int = 42, cust_count: int = 10, orders_count: int = 25, masking: bool = False, hashing: bool = False, noise_rate: float = 0.0):
    random.seed(seed)
    Faker.seed(seed)

    # 1. Customers (Parent Table) with Privacy & Noise
    import hashlib
    customers = []
    for i in range(1, cust_count + 1):
        raw_name = fake.name()
        email_user = fake.user_name()
        domain = "cyber.net"
        
        status = "OK"
        if random.random() < noise_rate:
            status = "OUTLIER"
        
        if masking:
            name_parts = raw_name.split()
            masked_name = " ".join([p[0] + "*" * (len(p) - 1) if len(p) > 1 else p for p in name_parts])
            masked_email = f"{email_user[:1]}***@{domain}"
        else:
            masked_name = raw_name
            masked_email = f"{email_user}@{domain}"
            
        if hashing:
            masked_email = hashlib.sha256(masked_email.encode()).hexdigest()[:12] + "@hash.local"

        customers.append({
            "customer_id": f"CUST-{i:03d}",
            "name": masked_name,
            "email": masked_email,
            "status": status
        })

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
def generate_document(doc_type: str = "invoice", seed: Optional[int] = None, masking: bool = False, hashing: bool = False):
    import hashlib
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)

    def mask_text(txt: str) -> str:
        words = txt.split()
        return " ".join([w[0] + "*" * max(len(w) - 1, 2) if len(w) > 1 else w for w in words])

    if doc_type == "invoice":
        catalog = [
            ("API access — Pro tier", 1100.00),
            ("Onboarding support", 140.00),
            ("Storage add-on (TB)", 85.00),
            ("Dedicated Cloud Worker", 450.00),
            ("Security compliance audit", 750.00),
            ("Priority 24/7 SLA", 280.00),
            ("Database failover cluster", 620.00),
            ("Neural Inference Pipeline", 950.00)
        ]
        num_items = random.randint(2, 5)
        selected = random.sample(catalog, num_items)
        items = []
        for name, unit_price in selected:
            qty = random.randint(1, 4)
            amount = round(unit_price * qty, 2)
            items.append({"item": name, "qty": qty, "unit_price": unit_price, "amount": amount})
            
        subtotal = round(sum(i["amount"] for i in items), 2)
        tax = round(subtotal * 0.08, 2)
        total = round(subtotal + tax, 2)
        
        raw_company = fake.company()
        billed_to = mask_text(raw_company) if masking else raw_company

        raw_id = f"INV-{random.randint(10000, 99999)}"
        if hashing:
            inv_number = "INV-" + hashlib.sha256(raw_id.encode()).hexdigest()[:8].upper()
        else:
            inv_number = raw_id

        return {
            "type": "invoice",
            "invoice_number": inv_number,
            "billed_to": billed_to,
            "from_entity": "Synth Data Co.",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "items": items,
            "subtotal": subtotal,
            "tax": tax,
            "total": total
        }
    else:
        merchants = [
            "Greenleaf Market", "Riverside Utilities", "CyberDeck Hardware", 
            "Cloud Cluster Hosting", "Metro Transit Card", "Quantum Coffee Roasters",
            "Neural Link Subscription", "Security Gateway Service", "Vertex Data Center"
        ]
        balance = round(random.uniform(1800.0, 5000.0), 2)
        records = []
        for i in range(random.randint(7, 11)):
            day = 10 + i * 2
            date_str = f"08-{day:02d}"
            raw_desc = "Payroll deposit" if (i % 4 == 2) else random.choice(merchants)
            desc = mask_text(raw_desc) if masking else raw_desc

            if i % 4 == 2:
                credit = round(random.choice([1200.00, 2150.00, 850.00]), 2)
                balance = round(balance + credit, 2)
                records.append({"date": date_str, "description": desc, "debit": 0, "credit": credit, "balance": balance})
            else:
                debit = round(random.uniform(15.0, 180.0), 2)
                balance = round(balance - debit, 2)
                records.append({"date": date_str, "description": desc, "debit": debit, "credit": 0, "balance": balance})
                
        raw_acc = f"CYB-****{random.randint(1000, 9999)}"
        acc_num = "ACC-" + hashlib.sha256(raw_acc.encode()).hexdigest()[:8] if hashing else raw_acc

        return {
            "type": "bank_statement",
            "account": acc_num,
            "period": "Last 30 days",
            "opening": records[0]["balance"] if records else 1200.0,
            "txns": records,
            "records": records
        }