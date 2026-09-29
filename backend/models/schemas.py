from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

class PrivacyType(str, Enum):
    NONE = "none"
    MASK = "mask"
    HASH = "hash"
    REDACT = "redact"

class DistributionType(str, Enum):
    UNIFORM = "uniform"
    NORMAL = "normal"
    EXPONENTIAL = "exponential"
    LOGNORMAL = "lognormal"

class FieldDefinition(BaseModel):
    name: str
    type: str  # uuid, name, email, currency, category, datetime, date, ipv4, integer, float, boolean, foreign_key, ai_context, etc.
    is_primary: Optional[bool] = False
    privacy: Optional[PrivacyType] = PrivacyType.NONE
    options: Optional[List[Any]] = None
    null_rate: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    outlier_rate: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std_dev: Optional[float] = None
    distribution: Optional[DistributionType] = DistributionType.UNIFORM
    references: Optional[str] = None  # e.g. "operatives.agent_id" or "customers.id"
    start: Optional[str] = None  # For datetime / date
    end: Optional[str] = None
    prompt: Optional[str] = None  # For ai_context
    description: Optional[str] = None
    reconcile_with: Optional[str] = None  # e.g., for relational arithmetic like "order_items:sum(quantity*unit_price)"

class TableDefinition(BaseModel):
    name: str
    row_count: int = Field(default=25, ge=1, le=10000)
    fields: List[FieldDefinition]

class DocumentConfig(BaseModel):
    type: str = "invoice"  # "invoice" or "bank_statement"
    template: Optional[str] = "hacker_receipt"
    currency: Optional[str] = "USD"
    tax_rate: Optional[float] = 0.08
    date_start: Optional[str] = "2026-01-01"
    date_end: Optional[str] = "2026-09-30"
    item_count: Optional[int] = 5
    initial_balance: Optional[float] = 5000.0
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    format: Optional[str] = "all"  # "json", "html", "csv", "all"

class UnifiedSchema(BaseModel):
    project_name: Optional[str] = "CYBER_SYNTH_V1"
    mode: Optional[str] = "tabular"  # tabular, relational, document
    locale: Optional[str] = "en_US"
    seed: Optional[int] = 1337
    tables: Optional[List[TableDefinition]] = None
    documents: Optional[DocumentConfig] = None

# Request / Response Schemas
class TabularGenerateRequest(BaseModel):
    schema_def: Optional[TableDefinition] = None
    fields: Optional[List[FieldDefinition]] = None
    table_name: Optional[str] = "dataset"
    row_count: Optional[int] = 25
    seed: Optional[int] = 1337
    null_rate: Optional[float] = 0.0
    outlier_rate: Optional[float] = 0.0
    locale: Optional[str] = "en_US"

class RelationalGenerateRequest(BaseModel):
    tables: List[TableDefinition]
    seed: Optional[int] = 1337
    locale: Optional[str] = "en_US"

class DocumentGenerateRequest(BaseModel):
    config: Optional[DocumentConfig] = None
    type: Optional[str] = "invoice"
    template: Optional[str] = "hacker_receipt"
    currency: Optional[str] = "USD"
    tax_rate: Optional[float] = 0.08
    item_count: Optional[int] = 5
    initial_balance: Optional[float] = 5000.0
    account_holder: Optional[str] = None
    account_number: Optional[str] = None
    format: Optional[str] = "all"
    seed: Optional[int] = 1337
    locale: Optional[str] = "en_US"

class InferSchemaRequest(BaseModel):
    prompt: str
    model: Optional[str] = None

class TabularGenerateResponse(BaseModel):
    status: str = "success"
    table_name: str
    row_count: int
    data: List[Dict[str, Any]]
    columns: List[str]
    metadata: Dict[str, Any]

class RelationalGenerateResponse(BaseModel):
    status: str = "success"
    tables: Dict[str, List[Dict[str, Any]]]
    table_names: List[str]
    row_counts: Dict[str, int]
    relationships: List[Dict[str, str]]
    metadata: Dict[str, Any]

class DocumentGenerateResponse(BaseModel):
    status: str = "success"
    document_type: str
    data: Dict[str, Any]
    html: Optional[str] = None
    csv: Optional[str] = None
    metadata: Dict[str, Any]

class InferSchemaResponse(BaseModel):
    status: str = "success"
    inferred_schema: UnifiedSchema
    model_used: str
    explanation: Optional[str] = None
