import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse

from backend.config import settings
from backend.models.schemas import (
    DocumentConfig,
    DocumentGenerateRequest,
    DocumentGenerateResponse,
    InferSchemaRequest,
    InferSchemaResponse,
    RelationalGenerateRequest,
    RelationalGenerateResponse,
    TableDefinition,
    TabularGenerateRequest,
    TabularGenerateResponse,
    UnifiedSchema,
)
from backend.engines.tabular import TabularEngine
from backend.engines.relational import RelationalEngine
from backend.engines.document import DocumentEngine
from backend.ai.inference import infer_schema_from_prompt

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Schema-aware synthetic data generation engine and AI layer for HackDataV2.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 6. Configure CORS middleware for all origins ("*") so Next.js on localhost:3000 can communicate seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PRESETS_DIR = Path(__file__).resolve().parent.parent / "presets"


@app.get("/", tags=["General"])
async def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "endpoints": {
            "tabular": "/api/generate/tabular",
            "relational": "/api/generate/relational",
            "document": "/api/generate/document",
            "infer": "/api/schema/infer",
            "presets": "/api/presets",
            "health": "/api/health"
        },
        "system_ping": "24ms",
        "message": "CYBER_SYNTH_CORE ONLINE"
    }


@app.get("/api/health", tags=["General"])
async def health_check():
    has_api_key = bool(settings.OPENROUTER_API_KEY.strip())
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "openrouter_configured": has_api_key,
        "active_model": settings.DEFAULT_MODEL,
        "timestamp": time.time()
    }


# 1. Tabular Generation Engine (/api/generate/tabular)
@app.post("/api/generate/tabular", response_model=TabularGenerateResponse, tags=["Engines"])
async def generate_tabular(request: TabularGenerateRequest):
    start_time = time.time()
    try:
        # Determine table definition
        if request.schema_def:
            table_def = request.schema_def
            if request.row_count and request.row_count != 25:
                table_def.row_count = request.row_count
        elif request.fields:
            table_def = TableDefinition(
                name=request.table_name or "dataset",
                row_count=request.row_count or 25,
                fields=request.fields
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'schema_def' or 'fields' must be provided in the request body."
            )

        engine = TabularEngine(seed=request.seed, locale=request.locale or "en_US")
        rows, meta = engine.generate_table(
            table_def=table_def,
            global_null_rate=request.null_rate or 0.0,
            global_outlier_rate=request.outlier_rate or 0.0
        )

        columns = [f.name for f in table_def.fields]
        meta["generation_time_ms"] = round((time.time() - start_time) * 1000, 2)

        return TabularGenerateResponse(
            status="success",
            table_name=table_def.name,
            row_count=len(rows),
            data=rows,
            columns=columns,
            metadata=meta
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tabular generation failed: {str(e)}"
        )


# 2. Relational Generation Engine (/api/generate/relational)
@app.post("/api/generate/relational", response_model=RelationalGenerateResponse, tags=["Engines"])
async def generate_relational(request: RelationalGenerateRequest):
    start_time = time.time()
    try:
        if not request.tables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one table definition must be provided."
            )

        engine = RelationalEngine(seed=request.seed, locale=request.locale or "en_US")
        dataset, relationships, meta = engine.generate_relational(request.tables)

        meta["generation_time_ms"] = round((time.time() - start_time) * 1000, 2)
        row_counts = {t_name: len(rows) for t_name, rows in dataset.items()}

        return RelationalGenerateResponse(
            status="success",
            tables=dataset,
            table_names=list(dataset.keys()),
            row_counts=row_counts,
            relationships=relationships,
            metadata=meta
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Relational generation failed: {str(e)}"
        )


# 3. Document Generation Engine (/api/generate/document)
@app.post("/api/generate/document", response_model=DocumentGenerateResponse, tags=["Engines"])
async def generate_document(request: DocumentGenerateRequest):
    start_time = time.time()
    try:
        # Build DocumentConfig
        if request.config:
            doc_config = request.config
        else:
            doc_config = DocumentConfig(
                type=request.type or "invoice",
                template=request.template or "hacker_receipt",
                currency=request.currency or "USD",
                tax_rate=request.tax_rate if request.tax_rate is not None else 0.08,
                item_count=request.item_count or 5,
                initial_balance=request.initial_balance if request.initial_balance is not None else 5000.0,
                account_holder=request.account_holder,
                account_number=request.account_number,
                format=request.format or "all"
            )

        engine = DocumentEngine(seed=request.seed, locale=request.locale or "en_US")
        doc_data, html_out, csv_out = engine.generate(doc_config)

        metadata = {
            "generation_time_ms": round((time.time() - start_time) * 1000, 2),
            "seed": request.seed,
            "format": doc_config.format,
            "currency": doc_config.currency
        }

        return DocumentGenerateResponse(
            status="success",
            document_type=doc_config.type,
            data=doc_data,
            html=html_out,
            csv=csv_out,
            metadata=metadata
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document generation failed: {str(e)}"
        )


# 4. AI Layer (/api/schema/infer)
@app.post("/api/schema/infer", response_model=InferSchemaResponse, tags=["AI Layer"])
async def infer_schema(request: InferSchemaRequest):
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User prompt cannot be empty."
        )

    try:
        schema, model_used, explanation = await infer_schema_from_prompt(
            prompt=request.prompt,
            model=request.model
        )

        return InferSchemaResponse(
            status="success",
            inferred_schema=schema,
            model_used=model_used,
            explanation=explanation
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema inference failed: {str(e)}"
        )


# 5. Presets & Demo Data (Sadia's track)
@app.get("/api/presets", tags=["Presets"])
async def list_presets():
    preset_files = ["fintech_ledger.json", "cyber_ecommerce.json", "invoice_sample.json"]
    results = {}

    for fname in preset_files:
        fpath = PRESETS_DIR / fname
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                key = fname.replace(".json", "")
                results[key] = json.load(f)

    return {
        "status": "success",
        "count": len(results),
        "presets": results
    }


@app.get("/api/presets/{preset_name}", tags=["Presets"])
async def get_preset(preset_name: str):
    clean_name = preset_name.replace(".json", "")
    fpath = PRESETS_DIR / f"{clean_name}.json"
    if not fpath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{preset_name}' not found. Available presets: fintech_ledger, cyber_ecommerce, invoice_sample"
        )

    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "status": "success",
        "preset_name": clean_name,
        "schema": data
    }


@app.post("/api/presets/{preset_name}/generate", tags=["Presets"])
async def generate_from_preset(preset_name: str):
    clean_name = preset_name.replace(".json", "")
    fpath = PRESETS_DIR / f"{clean_name}.json"
    if not fpath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{preset_name}' not found."
        )

    with open(fpath, "r", encoding="utf-8") as f:
        raw_schema = json.load(f)

    unified = UnifiedSchema.model_validate(raw_schema)

    if unified.mode == "document" and unified.documents:
        engine = DocumentEngine(seed=unified.seed or 1337, locale=unified.locale or "en_US")
        doc_data, html_out, csv_out = engine.generate(unified.documents)
        return {
            "status": "success",
            "mode": "document",
            "preset": clean_name,
            "data": doc_data,
            "html": html_out,
            "csv": csv_out
        }
    elif unified.tables:
        if len(unified.tables) > 1:
            rel_engine = RelationalEngine(seed=unified.seed or 1337, locale=unified.locale or "en_US")
            dataset, relationships, meta = rel_engine.generate_relational(unified.tables)
            return {
                "status": "success",
                "mode": "relational",
                "preset": clean_name,
                "tables": dataset,
                "relationships": relationships,
                "metadata": meta
            }
        else:
            tab_engine = TabularEngine(seed=unified.seed or 1337, locale=unified.locale or "en_US")
            rows, meta = tab_engine.generate_table(unified.tables[0])
            return {
                "status": "success",
                "mode": "tabular",
                "preset": clean_name,
                "table_name": unified.tables[0].name,
                "data": rows,
                "metadata": meta
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preset has no executable tables or document specifications."
        )
