import math
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from faker import Faker

from backend.models.schemas import (
    DistributionType,
    FieldDefinition,
    PrivacyType,
    TableDefinition,
)
from backend.engines.privacy import apply_privacy

CYBER_AI_CONTEXT_SAMPLES = [
    "Quantum entanglement ping verified at node-delta",
    "Mainframe unauthorized handshake attempt mitigated",
    "Synapse protocol sync established with Subnet-49",
    "Encrypted ledger packet routed through zero-knowledge relay",
    "Anomaly score threshold exceeded on neural core gateway",
    "Biometric authorization token refreshed",
    "Dark pool high-frequency liquidity routing active",
    "Bypassed edge firewall port 8083 via authenticated proxy",
    "Autonomous sentinel script executed: memory dump clean",
    "Neural cluster memory utilization spike: 94.2%"
]

def get_faker_instance(locale: str = "en_US", seed: Optional[int] = None) -> Faker:
    fake = Faker(locale)
    if seed is not None:
        fake.seed_instance(seed)
    return fake

class TabularEngine:
    def __init__(self, seed: Optional[int] = 1337, locale: str = "en_US"):
        self.seed = seed
        self.locale = locale
        self.fake = get_faker_instance(locale, seed)
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

    def generate_numeric_series(
        self,
        field: FieldDefinition,
        row_count: int,
        is_float: bool = True
    ) -> np.ndarray:
        min_val = field.min if field.min is not None else (10.0 if is_float else 1)
        max_val = field.max if field.max is not None else (1000.0 if is_float else 100)
        dist = field.distribution or DistributionType.UNIFORM

        if dist == DistributionType.NORMAL:
            mean = field.mean if field.mean is not None else (min_val + max_val) / 2.0
            std = field.std_dev if field.std_dev is not None else (max_val - min_val) / 6.0
            data = np.random.normal(loc=mean, scale=std, size=row_count)
            data = np.clip(data, min_val, max_val)
        elif dist == DistributionType.EXPONENTIAL:
            scale = field.mean if field.mean is not None else (max_val - min_val) / 3.0
            data = min_val + np.random.exponential(scale=scale, size=row_count)
            data = np.clip(data, min_val, max_val * 1.5)
        elif dist == DistributionType.LOGNORMAL:
            data = min_val + np.random.lognormal(mean=2.0, sigma=0.75, size=row_count)
            data = np.clip(data, min_val, max_val * 2.0)
        else:  # UNIFORM
            data = np.random.uniform(low=min_val, high=max_val, size=row_count)

        # Inject outliers if specified
        outlier_rate = field.outlier_rate if field.outlier_rate and field.outlier_rate > 0 else 0.0
        if outlier_rate > 0:
            num_outliers = max(1, int(round(row_count * outlier_rate)))
            outlier_indices = np.random.choice(row_count, size=num_outliers, replace=False)
            for idx in outlier_indices:
                direction = 1 if np.random.rand() > 0.3 else -1
                factor = np.random.uniform(3.0, 8.0)
                if direction > 0:
                    data[idx] = max_val * factor
                else:
                    data[idx] = min_val / factor if min_val > 0 else -abs(max_val * factor * 0.2)

        if not is_float:
            data = np.round(data).astype(int)
        else:
            data = np.round(data, 2)

        return data

    def generate_datetime_series(
        self,
        field: FieldDefinition,
        row_count: int,
        date_only: bool = False
    ) -> List[str]:
        try:
            start_dt = datetime.fromisoformat(field.start) if field.start else datetime(2026, 1, 1)
        except Exception:
            start_dt = datetime(2026, 1, 1)

        try:
            end_dt = datetime.fromisoformat(field.end) if field.end else datetime(2026, 9, 30, 23, 59, 59)
        except Exception:
            end_dt = datetime(2026, 9, 30, 23, 59, 59)

        if end_dt <= start_dt:
            end_dt = start_dt + timedelta(days=365)

        total_seconds = int((end_dt - start_dt).total_seconds())
        # Sort or randomize timestamps
        random_offsets = np.random.randint(0, max(1, total_seconds), size=row_count)
        # To make time series look realistic, we can either sort or leave as logs
        timestamps = [start_dt + timedelta(seconds=int(offset)) for offset in random_offsets]

        if date_only:
            return [dt.strftime("%Y-%m-%d") for dt in timestamps]
        return [dt.isoformat() for dt in timestamps]

    def generate_field_values(
        self,
        field: FieldDefinition,
        row_count: int,
        global_null_rate: float = 0.0,
        global_outlier_rate: float = 0.0
    ) -> List[Any]:
        ftype = field.type.lower().strip()
        effective_outlier_rate = max(field.outlier_rate or 0.0, global_outlier_rate)
        
        # Clone field with effective outlier rate for generation
        working_field = field.model_copy(update={"outlier_rate": effective_outlier_rate})

        values: List[Any] = []

        if ftype == "uuid":
            values = [str(uuid.uuid4()) for _ in range(row_count)]
        elif ftype in ("name", "full_name"):
            values = [self.fake.name() for _ in range(row_count)]
        elif ftype == "first_name":
            values = [self.fake.first_name() for _ in range(row_count)]
        elif ftype == "last_name":
            values = [self.fake.last_name() for _ in range(row_count)]
        elif ftype == "email":
            values = [self.fake.email() for _ in range(row_count)]
        elif ftype in ("currency", "money", "balance", "price"):
            series = self.generate_numeric_series(working_field, row_count, is_float=True)
            values = series.tolist()
        elif ftype in ("int", "integer", "quantity", "count"):
            series = self.generate_numeric_series(working_field, row_count, is_float=False)
            values = series.tolist()
        elif ftype in ("float", "numeric", "score", "rate"):
            series = self.generate_numeric_series(working_field, row_count, is_float=True)
            values = series.tolist()
        elif ftype in ("category", "enum", "status"):
            opts = working_field.options if working_field.options else ["ALPHA", "BETA", "GAMMA"]
            values = [str(np.random.choice(opts)) for _ in range(row_count)]
        elif ftype in ("datetime", "timestamp"):
            values = self.generate_datetime_series(working_field, row_count, date_only=False)
        elif ftype == "date":
            values = self.generate_datetime_series(working_field, row_count, date_only=True)
        elif ftype == "ipv4":
            values = [self.fake.ipv4() for _ in range(row_count)]
        elif ftype == "ipv6":
            values = [self.fake.ipv6() for _ in range(row_count)]
        elif ftype == "boolean":
            values = [bool(np.random.rand() > 0.5) for _ in range(row_count)]
        elif ftype in ("phone", "phone_number"):
            values = [self.fake.phone_number() for _ in range(row_count)]
        elif ftype == "company":
            values = [self.fake.company() for _ in range(row_count)]
        elif ftype == "address":
            values = [self.fake.address().replace("\n", ", ") for _ in range(row_count)]
        elif ftype == "job":
            values = [self.fake.job() for _ in range(row_count)]
        elif ftype == "ai_context":
            prompt = working_field.prompt or ""
            # Contextual synthesis from bank/cyber/ecommerce
            if "bank" in prompt.lower() or "ledger" in prompt.lower():
                bank_contexts = [
                    "High-frequency offshore wire transfer flagged",
                    "Automated ACH clearing batch completed",
                    "Suspicious struct split below reporting ceiling",
                    "Multi-signature cold storage dispersal",
                    "Card verification token regenerated after 3 retries"
                ]
                values = [random.choice(bank_contexts) for _ in range(row_count)]
            else:
                values = [random.choice(CYBER_AI_CONTEXT_SAMPLES) for _ in range(row_count)]
        elif ftype == "foreign_key":
            # For tabular engine alone, provide synthetic surrogate keys if not resolved
            values = [f"FK_{i+1:04d}" for i in range(row_count)]
        else:
            # Default text/string
            values = [self.fake.word() for _ in range(row_count)]

        # Apply privacy controls (masking, hashing, redaction)
        privacy = working_field.privacy or PrivacyType.NONE
        if privacy != PrivacyType.NONE:
            values = [apply_privacy(v, ftype, privacy.value) for v in values]

        # Apply null rate injection
        effective_null_rate = max(working_field.null_rate or 0.0, global_null_rate)
        if effective_null_rate > 0 and not working_field.is_primary:
            num_nulls = max(1, int(round(row_count * effective_null_rate)))
            null_indices = np.random.choice(row_count, size=min(num_nulls, row_count), replace=False)
            for idx in null_indices:
                values[idx] = None

        return values

    def generate_table(
        self,
        table_def: TableDefinition,
        global_null_rate: float = 0.0,
        global_outlier_rate: float = 0.0
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        row_count = table_def.row_count
        columns = [field.name for field in table_def.fields]
        column_data: Dict[str, List[Any]] = {}

        for field in table_def.fields:
            column_data[field.name] = self.generate_field_values(
                field,
                row_count=row_count,
                global_null_rate=global_null_rate,
                global_outlier_rate=global_outlier_rate
            )

        # Assemble into list of dict rows
        rows: List[Dict[str, Any]] = []
        for i in range(row_count):
            row = {col: column_data[col][i] for col in columns}
            rows.append(row)

        metadata = {
            "table_name": table_def.name,
            "row_count": row_count,
            "column_count": len(columns),
            "columns": columns,
            "seed": self.seed,
            "locale": self.locale,
            "null_rate_applied": global_null_rate,
            "outlier_rate_applied": global_outlier_rate
        }

        return rows, metadata
