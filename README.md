# Cyber Synth — AI-Powered Synthetic Data Platform
> Built for HackDataV2. An enterprise-grade, schema-aware synthetic dataset generation engine across Tabular, Relational, and Document architectures.

## 🌐 Live Deployments
- **Web Application**: [https://hackdata-cyber-synth.vercel.app](https://hackdata-cyber-synth.vercel.app)
- **Interactive Swagger API Docs**: [https://cyber-synth-api.onrender.com/docs](https://cyber-synth-api.onrender.com/docs)

---

## 📁 Repository Structure

```text
cyber-synth/
├── backend/
│   ├── ai/
│   │   └── openrouter_client.py    # OpenRouter API client & heuristic schema fallback
│   ├── Dockerfile                  # Production container config
│   ├── main.py                     # Unified FastAPI engine (Tabular, Relational, Documents)
│   └── requirements.txt            # Python dependencies (FastAPI, Faker, NumPy, Pandas)
├── frontend/
│   ├── app/
│   │   ├── layout.tsx              # Cyberpunk terminal styling & fonts
│   │   └── page.tsx                # 3-rail reactive generation workspace
│   ├── public/                     # Static assets & icons
│   ├── package.json                # Next.js 15 & UI dependencies
│   ├── tailwind.config.ts          # Phosphor green palette & UI theme
│   └── tsconfig.json
├── docker-compose.yml              # Local multi-service orchestration
└── README.md                       # Platform documentation & live URLs
```

## ⚡ Core Capabilities

### 1. Tabular Generation Engine (`POST /api/generate/tabular`)
- Configurable volume (`row_count`), reproducible distributions (`seed`), missing data rates (`null_rate`), and anomaly injection (`outlier_rate`).
- Dynamic privacy controls:
  - **PII Masking**: Replaces sensitive strings with privacy patterns (e.g., `s***@domain.com`).
  - **Cryptographic Hashing**: SHA-256 encoding for account IDs, IPs, and user identifiers.

### 2. Relational Generation Engine (`POST /api/generate/relational`)
- Multi-table schema coordination across `Customers` → `Orders` → `Order Items`.
- Strict foreign-key referential integrity across parent-child dependencies.
- Dynamic cross-table mathematical consistency:
  - Line Item Total = Quantity × Unit Price
  - Parent Order Total = sum(Line Totals)

### 3. Business Document Engine (`POST /api/generate/document`)
- **Invoices**: Procedural service catalog items with dynamic quantities, currency units, automated 8% tax calculations, and mathematically reconciled grand totals.
- **Bank Statements**: 30-day transaction logs with debits, payroll credits, continuous running balance reconciliation, and SHA-256 hashed account tokens.

### 4. AI Schema Inference Layer (`POST /api/schema/infer`)
- Translates natural language requests into structured, validated schema definitions using OpenRouter.
- Built-in heuristic synthesizer fallback to ensure continuous local and demo operation without active API credentials.

---

## 🛠 Tech Stack
- **Frontend**: Next.js 15, React, Tailwind CSS, TypeScript (Deployed on Vercel)
- **Backend**: FastAPI, Pydantic, Faker, NumPy, Python 3.11 (Deployed on Render)
- **Containerization**: Docker Compose (`docker-compose.yml`)
