# Cyber Synth — AI-Powered Synthetic Data Platform
> Built for HackDataV2. Enterprise-grade, privacy-compliant synthetic data across Tabular, Relational, and Document architectures.

## Live Deployments
- **Web Platform**: [https://hackdata-cyber-synth.vercel.app](https://hackdata-cyber-synth.vercel.app)
- **FastAPI Swagger Docs**: [https://cyber-synth-api.onrender.com/docs](https://cyber-synth-api.onrender.com/docs)

## Key Features

### 1. Tabular Generation Engine
- Configurable sample volume, custom random seeds, and outlier/null rate injection.
- Statistical fidelity with column-level privacy rules: PII masking and SHA-256 cryptographic hashing.

### 2. Relational Data Structures
- Multi-table database generation (`Customers` -> `Orders` -> `Order Items`).
- Strict foreign-key referential integrity across parent and child tables.
- Automated mathematical reconciliation (item quantities x unit prices match parent order totals).

### 3. Business Document Generation
- **Invoices**: Dynamic enterprise service catalog, line-item itemization, and automated 8% tax calculation reconciling to totals.
- **Bank Statements**: 30-day corporate transaction histories with debits, payroll credits, continuous running balance calculations, and SHA-256 hashed account tokens.

### 4. AI-Powered Schema Inference
- Dedicated endpoint (`POST /api/schema/infer`) utilizing OpenRouter to convert natural language schema prompts into valid schema structures.

## Tech Stack
- **Frontend**: Next.js 15, React, Tailwind CSS, TypeScript (Deployed on Vercel)
- **Backend**: FastAPI, Pydantic, Faker, NumPy, Python 3.11 (Deployed on Render)
