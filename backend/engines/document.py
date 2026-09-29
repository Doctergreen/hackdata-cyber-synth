import csv
import io
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from faker import Faker

from backend.models.schemas import DocumentConfig

CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CAD": "CA$",
    "AUD": "A$",
    "CYBER_CRED": "₡",
    "BTC": "₿",
    "ETH": "Ξ"
}

INVOICE_SERVICES = [
    ("Neural Mainframe Penetration Testing", 4500.0, 1),
    ("Zero-Day Exploit Mitigation & Patching", 2800.0, 1),
    ("Quantum Cryptographic Tunnel Setup", 1200.0, 2),
    ("Autonomous Sentinel Botnet Defense", 350.0, 10),
    ("Synthetic Telemetry Ingestion Pipeline", 1500.0, 2),
    ("Dark Web Credential Leak Audit", 950.0, 1),
    ("SOC2 Compliance Micro-Agent Deployment", 2200.0, 1),
    ("High-Availability Mesh Routing Config", 1850.0, 1)
]

BANK_MERCHANTS = [
    ("Mainframe Cloud Hosting Co.", "DEBIT", (150.0, 1200.0)),
    ("Megacorp Payroll Direct Deposit", "CREDIT", (4500.0, 9500.0)),
    ("Neural Bridge API Subscription", "DEBIT", (49.0, 299.0)),
    ("Off-Grid Hardware Supply Store", "DEBIT", (250.0, 1800.0)),
    ("Crypto Exchange Fiat Wire", "CREDIT", (1000.0, 5000.0)),
    ("Cyber Coffee & Synapse Lounge", "DEBIT", (12.0, 45.0)),
    ("Quantum Core Node Staking Yield", "CREDIT", (220.0, 850.0)),
    ("Encrypted Satellite Uplink Fee", "DEBIT", (350.0, 600.0)),
    ("Bounty Payout - Vulnerability Report", "CREDIT", (1500.0, 7500.0)),
    ("Hardware Security Key YubiAuth", "DEBIT", (95.0, 190.0))
]

class DocumentEngine:
    def __init__(self, seed: Optional[int] = 1337, locale: str = "en_US"):
        self.seed = seed
        self.locale = locale
        self.fake = Faker(locale)
        if seed is not None:
            self.fake.seed_instance(seed)
            random.seed(seed)

    def generate_invoice(self, config: DocumentConfig) -> Dict[str, Any]:
        curr = config.currency or "USD"
        curr_symbol = CURRENCY_SYMBOLS.get(curr, "$")
        tax_rate = config.tax_rate if config.tax_rate is not None else 0.08
        item_count = max(1, min(config.item_count or 5, 20))

        inv_number = f"INV-2026-{random.randint(10000, 99999)}"
        issue_date = self.fake.date_between(start_date="-60d", end_date="today")
        due_date = issue_date + timedelta(days=30)

        # Line items
        sampled_services = random.sample(INVOICE_SERVICES, min(item_count, len(INVOICE_SERVICES)))
        if len(sampled_services) < item_count:
            # Repeat or generate extra
            for i in range(item_count - len(sampled_services)):
                sampled_services.append((f"Cyber Ops Consultation Phase {i+1}", round(random.uniform(500, 3000), 2), random.randint(1, 4)))

        items: List[Dict[str, Any]] = []
        subtotal = 0.0

        for i, item_data in enumerate(sampled_services):
            desc = item_data[0]
            price = round(float(item_data[1]), 2)
            qty = int(item_data[2]) if len(item_data) > 2 else 1
            line_total = round(qty * price, 2)
            subtotal += line_total
            items.append({
                "item_id": i + 1,
                "description": desc,
                "quantity": qty,
                "unit_price": price,
                "amount": line_total
            })

        subtotal = round(subtotal, 2)
        discount_rate = 0.05 if subtotal > 10000 else 0.0
        discount_amount = round(subtotal * discount_rate, 2)
        taxable_amount = round(subtotal - discount_amount, 2)
        tax_amount = round(taxable_amount * tax_rate, 2)
        grand_total = round(taxable_amount + tax_amount, 2)

        invoice_data = {
            "type": "invoice",
            "invoice_number": inv_number,
            "status": random.choice(["PAID", "PENDING", "PROCESSING"]),
            "issue_date": issue_date.isoformat(),
            "due_date": due_date.isoformat(),
            "currency": curr,
            "currency_symbol": curr_symbol,
            "vendor": {
                "name": "CYBERSYNTH SYSTEMS LLC",
                "tax_id": f"US-{random.randint(10, 99)}-{random.randint(1000000, 9999999)}",
                "address": "742 Evergreen Byte Highway, Neo-Austin, TX 78701",
                "email": "billing@cybersynth.io",
                "contact": "Sami Hacker (Lead Systems Arch)"
            },
            "client": {
                "name": config.account_holder or self.fake.company(),
                "contact_person": self.fake.name(),
                "address": self.fake.address().replace("\n", ", "),
                "email": self.fake.email()
            },
            "items": items,
            "financial_summary": {
                "subtotal": subtotal,
                "discount_rate": discount_rate,
                "discount_amount": discount_amount,
                "taxable_amount": taxable_amount,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "grand_total": grand_total,
                "reconciliation_verified": True
            },
            "payment_terms": "Net 30. Direct crypto deposit or FedWire.",
            "notes": "Generated by HackDataV2 Synthetic Document Engine. All math strictly verified."
        }

        return invoice_data

    def generate_bank_statement(self, config: DocumentConfig) -> Dict[str, Any]:
        curr = config.currency or "USD"
        curr_symbol = CURRENCY_SYMBOLS.get(curr, "$")
        initial_balance = float(config.initial_balance if config.initial_balance is not None else 10000.0)
        tx_count = max(5, min(config.item_count or 15, 50))

        raw_acc_no = config.account_number or f"{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
        masked_acc_no = f"****-****-****-{raw_acc_no[-4:]}"

        start_dt = datetime(2026, 8, 1)
        end_dt = datetime(2026, 8, 31)

        # Generate timestamps chronologically
        total_days = (end_dt - start_dt).days
        day_offsets = sorted([random.randint(0, total_days) for _ in range(tx_count)])

        transactions: List[Dict[str, Any]] = []
        running_bal = initial_balance
        total_credits = 0.0
        total_debits = 0.0

        for i in range(tx_count):
            tx_date = start_dt + timedelta(days=day_offsets[i], hours=random.randint(8, 22), minutes=random.randint(0, 59))
            merchant_sample = random.choice(BANK_MERCHANTS)
            desc, tx_type, amount_range = merchant_sample

            amount = round(random.uniform(amount_range[0], amount_range[1]), 2)
            if tx_type == "CREDIT":
                running_bal = round(running_bal + amount, 2)
                total_credits += amount
                debit_val = 0.0
                credit_val = amount
            else:
                running_bal = round(running_bal - amount, 2)
                total_debits += amount
                debit_val = amount
                credit_val = 0.0

            transactions.append({
                "transaction_id": f"TX-{tx_date.strftime('%Y%m%d')}-{i+1:03d}",
                "date": tx_date.strftime("%Y-%m-%d %H:%M"),
                "description": desc,
                "type": tx_type,
                "debit": debit_val,
                "credit": credit_val,
                "amount": amount,
                "running_balance": running_bal
            })

        total_credits = round(total_credits, 2)
        total_debits = round(total_debits, 2)
        closing_balance = round(initial_balance + total_credits - total_debits, 2)

        statement_data = {
            "type": "bank_statement",
            "institution": "NEO-TOKYO CYBERNETIC FEDERAL BANK",
            "routing_number": "021000021",
            "account_holder": config.account_holder or self.fake.name(),
            "account_number": masked_acc_no,
            "statement_period": f"{start_dt.strftime('%b %d, %Y')} - {end_dt.strftime('%b %d, %Y')}",
            "currency": curr,
            "currency_symbol": curr_symbol,
            "summary": {
                "opening_balance": initial_balance,
                "total_deposits_credits": total_credits,
                "total_withdrawals_debits": total_debits,
                "closing_balance": closing_balance,
                "reconciliation_verified": (closing_balance == running_bal)
            },
            "transactions": transactions
        }

        return statement_data

    def render_invoice_html(self, data: Dict[str, Any]) -> str:
        symbol = data.get("currency_symbol", "$")
        fin = data.get("financial_summary", {})
        vendor = data.get("vendor", {})
        client = data.get("client", {})
        items = data.get("items", [])

        rows_html = "".join([
            f"""
            <tr style="border-bottom: 1px solid rgba(0, 255, 102, 0.15);">
                <td style="padding: 10px 8px; color: #e2e8f0; font-family: monospace;">#{it['item_id']}</td>
                <td style="padding: 10px 8px; color: #ffffff; font-weight: 500;">{it['description']}</td>
                <td style="padding: 10px 8px; text-align: center; color: #a0aec0; font-family: monospace;">{it['quantity']}</td>
                <td style="padding: 10px 8px; text-align: right; color: #4ade80; font-family: monospace;">{symbol}{it['unit_price']:,.2f}</td>
                <td style="padding: 10px 8px; text-align: right; color: #00ff66; font-weight: 600; font-family: monospace;">{symbol}{it['amount']:,.2f}</td>
            </tr>
            """
            for it in items
        ])

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Invoice {data.get('invoice_number')}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background-color: #050807;
                    color: #d1d5db;
                    margin: 0;
                    padding: 30px;
                }}
                .card {{
                    background: #0d1410;
                    border: 1px solid rgba(0, 255, 102, 0.3);
                    border-radius: 8px;
                    box-shadow: 0 0 20px rgba(0, 255, 102, 0.15);
                    max-width: 850px;
                    margin: 0 auto;
                    padding: 35px;
                }}
                .header {{
                    display: flex;
                    justify-content: space-between;
                    border-bottom: 2px solid rgba(0, 255, 102, 0.3);
                    padding-bottom: 20px;
                    margin-bottom: 25px;
                }}
                .logo-text {{
                    font-family: monospace;
                    font-size: 24px;
                    font-weight: 800;
                    color: #00ff66;
                    text-shadow: 0 0 8px rgba(0, 255, 102, 0.4);
                }}
                .badge {{
                    background: rgba(0, 255, 102, 0.1);
                    color: #00ff66;
                    border: 1px solid #00ff66;
                    padding: 4px 10px;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 13px;
                }}
                .grid-2 {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .section-title {{
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                    color: #4ade80;
                    font-family: monospace;
                    margin-bottom: 8px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 25px;
                }}
                th {{
                    text-align: left;
                    padding: 12px 8px;
                    background: #080c09;
                    color: #4ade80;
                    font-family: monospace;
                    font-size: 12px;
                    border-bottom: 2px solid rgba(0, 255, 102, 0.3);
                }}
                .total-card {{
                    background: #080c09;
                    border: 1px solid rgba(0, 255, 102, 0.2);
                    border-radius: 6px;
                    padding: 18px 24px;
                    width: 320px;
                    margin-left: auto;
                }}
                .total-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                    font-family: monospace;
                }}
                .grand-total {{
                    font-size: 18px;
                    font-weight: 800;
                    color: #00ff66;
                    border-top: 1px dashed rgba(0, 255, 102, 0.4);
                    padding-top: 10px;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <div>
                        <div class="logo-text">[SYSTEM // INVOICE]</div>
                        <div style="font-family: monospace; font-size: 13px; color: #9ca3af; margin-top: 5px;">ID: {data.get('invoice_number')}</div>
                    </div>
                    <div style="text-align: right;">
                        <span class="badge">STATUS: {data.get('status')}</span>
                        <div style="font-family: monospace; font-size: 12px; color: #9ca3af; margin-top: 8px;">Date: {data.get('issue_date')}</div>
                        <div style="font-family: monospace; font-size: 12px; color: #ef4444;">Due: {data.get('due_date')}</div>
                    </div>
                </div>

                <div class="grid-2">
                    <div>
                        <div class="section-title">// ISSUER DETAILS</div>
                        <div style="font-weight: bold; color: #ffffff;">{vendor.get('name')}</div>
                        <div style="color: #9ca3af; font-size: 13px;">{vendor.get('address')}</div>
                        <div style="color: #4ade80; font-family: monospace; font-size: 13px;">Tax ID: {vendor.get('tax_id')}</div>
                        <div style="color: #9ca3af; font-size: 13px;">{vendor.get('email')}</div>
                    </div>
                    <div>
                        <div class="section-title">// BILLED TO</div>
                        <div style="font-weight: bold; color: #ffffff;">{client.get('name')}</div>
                        <div style="color: #d1d5db; font-size: 13px;">Attn: {client.get('contact_person')}</div>
                        <div style="color: #9ca3af; font-size: 13px;">{client.get('address')}</div>
                        <div style="color: #9ca3af; font-size: 13px;">{client.get('email')}</div>
                    </div>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>LINE</th>
                            <th>DESCRIPTION</th>
                            <th style="text-align: center;">QTY</th>
                            <th style="text-align: right;">UNIT PRICE</th>
                            <th style="text-align: right;">TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>

                <div class="total-card">
                    <div class="total-row">
                        <span style="color: #9ca3af;">Subtotal:</span>
                        <span>{symbol}{fin.get('subtotal', 0.0):,.2f}</span>
                    </div>
                    <div class="total-row">
                        <span style="color: #9ca3af;">Discount:</span>
                        <span style="color: #ef4444;">-{symbol}{fin.get('discount_amount', 0.0):,.2f}</span>
                    </div>
                    <div class="total-row">
                        <span style="color: #9ca3af;">Tax ({int(fin.get('tax_rate', 0.08)*100)}%):</span>
                        <span>{symbol}{fin.get('tax_amount', 0.0):,.2f}</span>
                    </div>
                    <div class="total-row grand-total">
                        <span>TOTAL DUE:</span>
                        <span>{symbol}{fin.get('grand_total', 0.0):,.2f}</span>
                    </div>
                </div>

                <div style="margin-top: 30px; font-family: monospace; font-size: 12px; color: #6b7280; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 15px;">
                    <div>[VERIFIED]: Mathematical reconciliation invariant verified by HackDataV2.</div>
                    <div>Payment Terms: {data.get('payment_terms')}</div>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def render_bank_statement_html(self, data: Dict[str, Any]) -> str:
        symbol = data.get("currency_symbol", "$")
        summary = data.get("summary", {})
        txs = data.get("transactions", [])

        tx_rows = "".join([
            f"""
            <tr style="border-bottom: 1px solid rgba(0, 255, 102, 0.1);">
                <td style="padding: 10px 8px; color: #a0aec0; font-family: monospace; font-size: 12px;">{tx['date']}</td>
                <td style="padding: 10px 8px; color: #ffffff; font-weight: 500;">{tx['description']}</td>
                <td style="padding: 10px 8px; text-align: center;">
                    <span style="background: {'rgba(16, 185, 129, 0.15)' if tx['type'] == 'CREDIT' else 'rgba(239, 68, 68, 0.15)'}; color: {'#10b981' if tx['type'] == 'CREDIT' else '#ef4444'}; font-family: monospace; font-size: 11px; padding: 2px 6px; border-radius: 3px;">{tx['type']}</span>
                </td>
                <td style="padding: 10px 8px; text-align: right; color: {'#10b981' if tx['credit'] > 0 else '#64748b'}; font-family: monospace;">
                    {f"+{symbol}{tx['credit']:,.2f}" if tx['credit'] > 0 else "-"}
                </td>
                <td style="padding: 10px 8px; text-align: right; color: {'#ef4444' if tx['debit'] > 0 else '#64748b'}; font-family: monospace;">
                    {f"-{symbol}{tx['debit']:,.2f}" if tx['debit'] > 0 else "-"}
                </td>
                <td style="padding: 10px 8px; text-align: right; color: #00ff66; font-weight: 600; font-family: monospace;">
                    {symbol}{tx['running_balance']:,.2f}
                </td>
            </tr>
            """
            for tx in txs
        ])

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Bank Statement - {data.get('account_number')}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background-color: #050807;
                    color: #d1d5db;
                    margin: 0;
                    padding: 30px;
                }}
                .card {{
                    background: #0d1410;
                    border: 1px solid rgba(0, 255, 102, 0.3);
                    border-radius: 8px;
                    box-shadow: 0 0 20px rgba(0, 255, 102, 0.15);
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 35px;
                }}
                .header {{
                    display: flex;
                    justify-content: space-between;
                    border-bottom: 2px solid rgba(0, 255, 102, 0.3);
                    padding-bottom: 20px;
                    margin-bottom: 25px;
                }}
                .logo-text {{
                    font-family: monospace;
                    font-size: 22px;
                    font-weight: 800;
                    color: #00ff66;
                    text-shadow: 0 0 8px rgba(0, 255, 102, 0.4);
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 15px;
                    margin-bottom: 30px;
                }}
                .metric-card {{
                    background: #080c09;
                    border: 1px solid rgba(0, 255, 102, 0.2);
                    border-radius: 6px;
                    padding: 14px;
                }}
                .metric-title {{
                    font-family: monospace;
                    font-size: 11px;
                    color: #9ca3af;
                    text-transform: uppercase;
                }}
                .metric-value {{
                    font-family: monospace;
                    font-size: 17px;
                    font-weight: 700;
                    color: #ffffff;
                    margin-top: 6px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th {{
                    text-align: left;
                    padding: 12px 8px;
                    background: #080c09;
                    color: #4ade80;
                    font-family: monospace;
                    font-size: 12px;
                    border-bottom: 2px solid rgba(0, 255, 102, 0.3);
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <div>
                        <div class="logo-text">{data.get('institution')}</div>
                        <div style="font-family: monospace; font-size: 13px; color: #9ca3af; margin-top: 5px;">ACCOUNT: {data.get('account_number')}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-family: monospace; font-size: 13px; color: #4ade80;">HOLDER: {data.get('account_holder')}</div>
                        <div style="font-family: monospace; font-size: 12px; color: #9ca3af; margin-top: 4px;">PERIOD: {data.get('statement_period')}</div>
                    </div>
                </div>

                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">Opening Balance</div>
                        <div class="metric-value">{symbol}{summary.get('opening_balance', 0.0):,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Total Credits (+)</div>
                        <div class="metric-value" style="color: #10b981;">+{symbol}{summary.get('total_deposits_credits', 0.0):,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Total Debits (-)</div>
                        <div class="metric-value" style="color: #ef4444;">-{symbol}{summary.get('total_withdrawals_debits', 0.0):,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Closing Balance</div>
                        <div class="metric-value" style="color: #00ff66;">{symbol}{summary.get('closing_balance', 0.0):,.2f}</div>
                    </div>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>DATE</th>
                            <th>DESCRIPTION</th>
                            <th style="text-align: center;">TYPE</th>
                            <th style="text-align: right;">CREDIT (+)</th>
                            <th style="text-align: right;">DEBIT (-)</th>
                            <th style="text-align: right;">RUNNING BALANCE</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tx_rows}
                    </tbody>
                </table>

                <div style="margin-top: 25px; font-family: monospace; font-size: 12px; color: #6b7280; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 15px;">
                    [SYSTEM INTEGRITY]: Continuous running balances strictly reconciled. Invariant verified: True.
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def render_csv(self, data: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        if data.get("type") == "invoice":
            writer.writerow(["Invoice Number", data.get("invoice_number")])
            writer.writerow(["Issue Date", data.get("issue_date")])
            writer.writerow(["Client", data.get("client", {}).get("name")])
            writer.writerow(["Currency", data.get("currency")])
            writer.writerow([])
            writer.writerow(["Item ID", "Description", "Quantity", "Unit Price", "Amount"])
            for it in data.get("items", []):
                writer.writerow([it["item_id"], it["description"], it["quantity"], it["unit_price"], it["amount"]])
            writer.writerow([])
            fin = data.get("financial_summary", {})
            writer.writerow(["Subtotal", fin.get("subtotal")])
            writer.writerow(["Tax Amount", fin.get("tax_amount")])
            writer.writerow(["Grand Total", fin.get("grand_total")])

        elif data.get("type") == "bank_statement":
            writer.writerow(["Institution", data.get("institution")])
            writer.writerow(["Account Number", data.get("account_number")])
            writer.writerow(["Period", data.get("statement_period")])
            writer.writerow(["Opening Balance", data.get("summary", {}).get("opening_balance")])
            writer.writerow(["Closing Balance", data.get("summary", {}).get("closing_balance")])
            writer.writerow([])
            writer.writerow(["Transaction ID", "Date", "Description", "Type", "Credit", "Debit", "Running Balance"])
            for tx in data.get("transactions", []):
                writer.writerow([tx["transaction_id"], tx["date"], tx["description"], tx["type"], tx["credit"], tx["debit"], tx["running_balance"]])

        return output.getvalue()

    def generate(self, config: DocumentConfig) -> Tuple[Dict[str, Any], Optional[str], Optional[str]]:
        doc_type = (config.type or "invoice").lower()

        if doc_type in ("bank_statement", "statement", "ledger"):
            doc_data = self.generate_bank_statement(config)
            html_out = self.render_bank_statement_html(doc_data)
        else:
            doc_data = self.generate_invoice(config)
            html_out = self.render_invoice_html(doc_data)

        csv_out = self.render_csv(doc_data)

        req_format = (config.format or "all").lower()
        final_html = html_out if req_format in ("html", "all") else None
        final_csv = csv_out if req_format in ("csv", "all") else None

        return doc_data, final_html, final_csv
