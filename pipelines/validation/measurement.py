from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ValidatedMeasurement(BaseModel):
    reservoir_id: UUID
    observation_date: date
    storage_mm3: Decimal | None = Field(default=None, ge=0)
    filling_rate_pct: Decimal | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def at_least_one_value(self):
        if self.storage_mm3 is None and self.filling_rate_pct is None:
            raise ValueError("Au moins une mesure est obligatoire")
        return self
