# HackDataV2: Synthetic Data Platform (CyberSynth Core)

A high-performance, schema-aware synthetic dataset generation engine and AI layer engineered for **HackDataV2**. Solves data privacy, scarcity, and testing bottlenecks by generating statistically faithful tabular datasets, relational schemas with strict referential integrity, and mathematically reconciled financial documents.

---

## ⚡ Core Capabilities

1. **Tabular Generation Engine (`/api/generate/tabular`)**
   - Configurable row counts, seeds, missing data rates (`null_rate`), and outlier rates (`outlier_rate`).
   - Statistical numeric distributions via **NumPy** (Uniform, Normal/Gaussian, Exponential, Lognormal).
   - Column-level privacy controls:
     - **Email Masking**: `s***@domain.com`
     - **Cryptographic Hashing**: SHA-256 for IDs, IPs, and sensitive tokens
     - **Redaction**: Full `[REDACTED]` masking

2. **Relational Generation Engine (`/api/generate/relational`)**
   - Automatic DAG dependency discovery & topological sorting.
   - Enforces 100% referential integrity across multi-table relationships (e.g. `Customers` $\to$ `Orders` $\to$ `Order Items`).
   - Dynamic cross-table mathematical consistency:
     - `Line Total = Quantity * Unit Price`
     - Parent `Order Total = sum(Line Totals)`

3. **Document Generation Engine (`/api/generate/document`)**
   - **Invoices**: Realistic line items, regional currencies (`USD`, `EUR`, `CYBER_CRED ₡`), tax rates, and mathematically reconciled subtotals and grand totals.
   - **Bank Statements**: Chronological transaction histories with merchants, debits, credits, and continuous running balance reconciliation:
     $$\text{Balance}_i = \text{Balance}_{i-1} + \text{Credit}_i - \text{Debit}_i$$
   - Export formats: **JSON**, styled Cyberpunk **HTML**, and flattened **CSV**.

4. **AI Layer (`/api/schema/infer`)**
   - Natural language to JSON Schema inference powered by **OpenRouter API** (`openai/gpt-4o-mini` or `z-ai/glm-5.3-flash`).
   - Translates prompts like *"Generate a cyber banking ledger with anomalous transfers"* into validated relational or document schemas.
   - Intelligent offline fallback synthesizer for uninterrupted demos without API keys.

5. **Presets & Demo Data (Sadia's Track)**
   - Pre-built demo schemas in `presets/`:
     - `fintech_ledger.json` (Accounts, Transactions with Debits/Credits, Fraud Alerts)
     - `cyber_ecommerce.json` (Customers, Orders, Order Items with price*quantity math)
     - `invoice_sample.json` (Hacker defense contract invoice with `CYBER_CRED`)

6. **Full CORS Support**
   - Pre-configured `CORSMiddleware` with `allow_origins=["*"]` to connect with Next.js frontend (`http://localhost:3000`).

---

## 📁 Project Structure

```text
synthetic-data-platform/
├── backend/
│   ├── ai/
│   │   ├── __init__.py
│   │   └── inference.py          # OpenRouter client & heuristic fallback
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── privacy.py            # Email masking & SHA-256 hashing
│   │   ├── tabular.py            # Faker + NumPy tabular generator
│   │   ├── relational.py         # Referential integrity & cross-table math
│   │   └── document.py           # Invoices, bank statements, HTML/CSV
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Unified schema contract & Pydantic models
│   ├── config.py                 # Environment configuration
│   ├── main.py                   # FastAPI service & route handlers
│   └── __init__.py
├── presets/
│   ├── fintech_ledger.json       # Sadia Preset 1
│   ├── cyber_ecommerce.json      # Sadia Preset 2
│   └── invoice_sample.json       # Sadia Preset 3
├── tests/
│   ├── __init__.py
│   └── test_engines.py           # Unit and integration test suite
├── Dockerfile                    # Production containerization
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── README.md
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(If `OPENROUTER_API_KEY` is not provided, the platform automatically activates the offline heuristic synthesizer).*

### 3. Run FastAPI Backend
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger UI is live at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Run Automated Tests

Execute the comprehensive test suite verifying privacy masking, relational referential integrity, mathematical reconciliations, and document generation:

```bash
python -m unittest tests/test_engines.py
```

---

## 📡 API Reference & Examples

### 1. Tabular Generation (`POST /api/generate/tabular`)
```json
{
  "table_name": "operatives",
  "row_count": 25,
  "seed": 1337,
  "null_rate": 0.05,
  "outlier_rate": 0.02,
  "fields": [
    {"name": "agent_id", "type": "uuid", "is_primary": true},
    {"name": "codename", "type": "name"},
    {"name": "secure_email", "type": "email", "privacy": "mask"},
    {"name": "clearance_level", "type": "category", "options": ["ALPHA", "BETA", "OMEGA"]},
    {"name": "credits", "type": "currency", "min": 500, "max": 25000},
    {"name": "terminal_ip", "type": "ipv4", "privacy": "hash"}
  ]
}
```

### 2. Relational Generation (`POST /api/generate/relational`)
```json
{
  "tables": [
    {
      "name": "customers",
      "row_count": 10,
      "fields": [
        {"name": "customer_id", "type": "uuid", "is_primary": true},
        {"name": "email", "type": "email", "privacy": "mask"}
      ]
    },
    {
      "name": "orders",
      "row_count": 20,
      "fields": [
        {"name": "order_id", "type": "uuid", "is_primary": true},
        {"name": "customer_id", "type": "foreign_key", "references": "customers.customer_id"},
        {"name": "total_amount", "type": "currency"}
      ]
    },
    {
      "name": "order_items",
      "row_count": 50,
      "fields": [
        {"name": "item_id", "type": "uuid", "is_primary": true},
        {"name": "order_id", "type": "foreign_key", "references": "orders.order_id"},
        {"name": "quantity", "type": "integer", "min": 1, "max": 5},
        {"name": "unit_price", "type": "currency", "min": 20, "max": 200},
        {"name": "line_total", "type": "currency"}
      ]
    }
  ]
}
```
*Guarantees: All `customer_id` and `order_id` values match existing primary keys, and each `order.total_amount` equals the exact sum of its items' `quantity * unit_price`.*

### 3. Document Generation (`POST /api/generate/document`)
```json
{
  "type": "invoice",
  "currency": "CYBER_CRED",
  "tax_rate": 0.08,
  "item_count": 5,
  "format": "all"
}
```
*Returns structured JSON, styled Cyberpunk HTML document, and exportable CSV.*

### 4. AI Schema Inference (`POST /api/schema/infer`)
```json
{
  "prompt": "Generate a cyber banking ledger with anomalous transfers and money laundering alerts"
}
```

### 5. Presets Loading & Execution
- List presets: `GET /api/presets`
- Get preset schema: `GET /api/presets/fintech_ledger`
- Instant generation: `POST /api/presets/fintech_ledger/generate`

---

## 🐳 Docker Deployment

Build and run with Docker:
```bash
docker build -t synth-platform-backend .
docker run -p 8000:8000 synth-platform-backend
```
Deployable directly on Render, Railway, or Fly.io.
