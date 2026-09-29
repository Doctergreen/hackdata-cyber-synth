import json
import re
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main_platform import app
from backend.models.schemas import (
    FieldDefinition,
    PrivacyType,
    TableDefinition,
    DocumentConfig,
    UnifiedSchema,
    DistributionType
)
from backend.engines.tabular import TabularEngine
from backend.engines.relational import RelationalEngine
from backend.engines.document import DocumentEngine
from backend.engines.privacy import mask_email, hash_value
from backend.ai.inference import generate_heuristic_schema

class TestSyntheticDataEngines(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.seed = 1337

    def test_privacy_controls(self):
        # Email masking test: s***@domain.com
        raw_email = "sarah.connor@cyberdyne.io"
        masked = mask_email(raw_email)
        self.assertTrue(masked.startswith("s***@cyberdyne.io"))

        # Single char username
        masked_short = mask_email("a@example.com")
        self.assertEqual(masked_short, "a***@example.com")

        # SHA-256 ID/IP hashing
        ip_addr = "192.168.1.105"
        hashed = hash_value(ip_addr)
        self.assertEqual(len(hashed), 64)
        self.assertTrue(re.match(r"^[0-9a-f]{64}$", hashed))
        # Hash repeatability
        self.assertEqual(hashed, hash_value(ip_addr))

    def test_tabular_engine_generation_and_distributions(self):
        engine = TabularEngine(seed=self.seed)

        table_def = TableDefinition(
            name="operatives",
            row_count=30,
            fields=[
                FieldDefinition(name="agent_id", type="uuid", is_primary=True),
                FieldDefinition(name="codename", type="name", privacy=PrivacyType.NONE),
                FieldDefinition(name="secure_email", type="email", privacy=PrivacyType.MASK),
                FieldDefinition(name="clearance_level", type="category", options=["ALPHA", "BETA", "OMEGA"], null_rate=0.10),
                FieldDefinition(name="credits", type="currency", min=500.0, max=25000.0, outlier_rate=0.05),
                FieldDefinition(name="terminal_ip", type="ipv4", privacy=PrivacyType.HASH)
            ]
        )

        rows, meta = engine.generate_table(table_def)
        self.assertEqual(len(rows), 30)
        self.assertEqual(meta["column_count"], 6)

        # Verify email masking
        for row in rows:
            email = row["secure_email"]
            if email:
                self.assertIn("***@", email)

        # Verify IP hashing
        for row in rows:
            hashed_ip = row["terminal_ip"]
            if hashed_ip:
                self.assertEqual(len(hashed_ip), 64)

        # Verify null rate injection
        null_count = sum(1 for r in rows if r["clearance_level"] is None)
        self.assertGreater(null_count, 0)

        # Verify outlier injection
        credits_values = [r["credits"] for r in rows if r["credits"] is not None]
        # At least one extreme credit value or normal values within range
        self.assertTrue(any(c > 25000.0 for c in credits_values) or any(c < 500.0 for c in credits_values))

    def test_relational_engine_referential_integrity_and_reconciliation(self):
        engine = RelationalEngine(seed=self.seed)

        customers_table = TableDefinition(
            name="customers",
            row_count=5,
            fields=[
                FieldDefinition(name="customer_id", type="uuid", is_primary=True),
                FieldDefinition(name="name", type="name")
            ]
        )

        orders_table = TableDefinition(
            name="orders",
            row_count=10,
            fields=[
                FieldDefinition(name="order_id", type="uuid", is_primary=True),
                FieldDefinition(name="customer_id", type="foreign_key", references="customers.customer_id"),
                FieldDefinition(name="total_amount", type="currency", min=10.0, max=100.0)
            ]
        )

        order_items_table = TableDefinition(
            name="order_items",
            row_count=25,
            fields=[
                FieldDefinition(name="item_id", type="uuid", is_primary=True),
                FieldDefinition(name="order_id", type="foreign_key", references="orders.order_id"),
                FieldDefinition(name="quantity", type="integer", min=1, max=4),
                FieldDefinition(name="unit_price", type="currency", min=15.0, max=150.0),
                FieldDefinition(name="line_total", type="currency")
            ]
        )

        dataset, relationships, meta = engine.generate_relational([
            order_items_table, customers_table, orders_table  # Given in random order to test topological sort
        ])

        # Verify topological sort and output presence
        self.assertIn("customers", dataset)
        self.assertIn("orders", dataset)
        self.assertIn("order_items", dataset)

        customer_ids = {c["customer_id"] for c in dataset["customers"]}
        order_ids = {o["order_id"] for o in dataset["orders"]}

        # 1. Enforce referential integrity: Orders -> Customers
        for order in dataset["orders"]:
            self.assertIn(order["customer_id"], customer_ids)

        # 2. Enforce referential integrity: Order Items -> Orders
        for item in dataset["order_items"]:
            self.assertIn(item["order_id"], order_ids)

        # 3. Dynamic Cross-table consistency: Order total must reconcile dynamically with item quantity * unit price
        item_sums = {}
        for item in dataset["order_items"]:
            # item line total = quantity * unit_price
            expected_line = round(item["quantity"] * item["unit_price"], 2)
            self.assertAlmostEqual(item["line_total"], expected_line, places=2)
            
            oid = item["order_id"]
            item_sums[oid] = item_sums.get(oid, 0.0) + item["line_total"]

        for order in dataset["orders"]:
            oid = order["order_id"]
            expected_order_total = round(item_sums.get(oid, 0.0), 2)
            self.assertAlmostEqual(order["total_amount"], expected_order_total, places=2)

    def test_document_engine_invoice_reconciliation(self):
        engine = DocumentEngine(seed=self.seed)
        config = DocumentConfig(
            type="invoice",
            currency="CYBER_CRED",
            tax_rate=0.10,
            item_count=5
        )

        doc_data, html_out, csv_out = engine.generate(config)

        self.assertEqual(doc_data["type"], "invoice")
        self.assertEqual(doc_data["currency"], "CYBER_CRED")

        # Verify mathematical consistency
        items = doc_data["items"]
        computed_subtotal = round(sum(it["amount"] for it in items), 2)
        fin = doc_data["financial_summary"]
        self.assertAlmostEqual(fin["subtotal"], computed_subtotal, places=2)

        expected_grand_total = round(fin["taxable_amount"] + fin["tax_amount"], 2)
        self.assertAlmostEqual(fin["grand_total"], expected_grand_total, places=2)
        self.assertTrue(fin["reconciliation_verified"])

        # Verify HTML and CSV
        self.assertIn("[SYSTEM // INVOICE]", html_out)
        self.assertIn("CYBER_CRED", csv_out)

    def test_document_engine_bank_statement_running_balance(self):
        engine = DocumentEngine(seed=self.seed)
        config = DocumentConfig(
            type="bank_statement",
            initial_balance=10000.0,
            item_count=12
        )

        doc_data, html_out, csv_out = engine.generate(config)
        self.assertEqual(doc_data["type"], "bank_statement")

        # Verify continuous running balance invariant
        running = doc_data["summary"]["opening_balance"]
        for tx in doc_data["transactions"]:
            if tx["type"] == "CREDIT":
                running = round(running + tx["credit"], 2)
            else:
                running = round(running - tx["debit"], 2)
            self.assertAlmostEqual(tx["running_balance"], running, places=2)

        self.assertAlmostEqual(doc_data["summary"]["closing_balance"], running, places=2)
        self.assertTrue(doc_data["summary"]["reconciliation_verified"])

        # Check HTML and CSV
        self.assertIn("RUNNING BALANCE", html_out)
        self.assertIn("Transaction ID", csv_out)

    def test_ai_heuristic_schema_inference(self):
        # Banking ledger prompt
        banking_prompt = "Generate a cyber banking ledger with anomalous transfers and money laundering"
        schema_banking = generate_heuristic_schema(banking_prompt)
        self.assertEqual(schema_banking.mode, "relational")
        table_names = [t.name for t in schema_banking.tables]
        self.assertIn("accounts", table_names)
        self.assertIn("transactions", table_names)
        self.assertIn("fraud_alerts", table_names)

        # Invoice prompt
        invoice_prompt = "Generate a cyber defense contract invoice with 8% tax"
        schema_inv = generate_heuristic_schema(invoice_prompt)
        self.assertEqual(schema_inv.mode, "document")
        self.assertEqual(schema_inv.documents.type, "invoice")

    def test_presets_loading_and_execution(self):
        presets_dir = Path(__file__).resolve().parent.parent / "presets"
        files = ["fintech_ledger.json", "cyber_ecommerce.json", "invoice_sample.json"]

        for fname in files:
            path = presets_dir / fname
            self.assertTrue(path.exists(), f"Preset {fname} missing")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            validated = UnifiedSchema.model_validate(data)
            self.assertIsNotNone(validated.project_name)

    def test_fastapi_endpoints_integration(self):
        # 1. Health
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

        # 2. Tabular endpoint
        tab_req = {
            "table_name": "users",
            "row_count": 10,
            "seed": 42,
            "fields": [
                {"name": "id", "type": "uuid", "is_primary": True},
                {"name": "email", "type": "email", "privacy": "mask"},
                {"name": "ip", "type": "ipv4", "privacy": "hash"}
            ]
        }
        res = self.client.post("/api/generate/tabular", json=tab_req)
        self.assertEqual(res.status_code, 200)
        resp_data = res.json()
        self.assertEqual(resp_data["row_count"], 10)
        self.assertEqual(len(resp_data["data"]), 10)
        self.assertIn("***@", resp_data["data"][0]["email"])

        # 3. Document endpoint
        doc_req = {
            "type": "invoice",
            "currency": "EUR",
            "tax_rate": 0.20,
            "item_count": 4,
            "format": "all"
        }
        res = self.client.post("/api/generate/document", json=doc_req)
        self.assertEqual(res.status_code, 200)
        doc_resp = res.json()
        self.assertEqual(doc_resp["data"]["currency"], "EUR")
        self.assertIsNotNone(doc_resp["html"])
        self.assertIsNotNone(doc_resp["csv"])

        # 4. Schema infer endpoint
        infer_req = {"prompt": "Create an e-commerce database with customers, orders and order items"}
        res = self.client.post("/api/schema/infer", json=infer_req)
        self.assertEqual(res.status_code, 200)
        infer_resp = res.json()
        self.assertEqual(infer_resp["status"], "success")
        self.assertIn("inferred_schema", infer_resp)

        # 5. Presets endpoint
        res = self.client.get("/api/presets")
        self.assertEqual(res.status_code, 200)
        presets_data = res.json()
        self.assertIn("fintech_ledger", presets_data["presets"])
        self.assertIn("cyber_ecommerce", presets_data["presets"])
        self.assertIn("invoice_sample", presets_data["presets"])

        # 6. Presets instant generate endpoint
        res = self.client.post("/api/presets/cyber_ecommerce/generate")
        self.assertEqual(res.status_code, 200)
        gen_data = res.json()
        self.assertEqual(gen_data["mode"], "relational")
        self.assertIn("customers", gen_data["tables"])
        self.assertIn("orders", gen_data["tables"])
        self.assertIn("order_items", gen_data["tables"])

if __name__ == "__main__":
    unittest.main()
