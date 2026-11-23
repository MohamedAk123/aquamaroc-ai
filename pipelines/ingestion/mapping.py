from pathlib import Path
from typing import Literal
from uuid import UUID

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ColumnMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["demo", "official"]
    sheet: str
    header_row: int = Field(ge=1)
    columns: dict[str, str]
    units: dict[str, str]
    reservoirs: dict[str, UUID]
    max_bytes: int = Field(default=10_000_000, gt=0, le=50_000_000)
    max_uncompressed_bytes: int = Field(default=50_000_000, gt=0, le=200_000_000)

    @model_validator(mode="after")
    def validate_mapping(self):
        required = {"reservoir_name", "observation_date", "storage_mm3", "filling_rate_pct"}
        if set(self.columns) != required or len(set(self.columns.values())) != len(required):
            raise ValueError("Le mapping exige quatre colonnes distinctes et explicites")
        if self.units != {"storage_mm3": "Mm3", "filling_rate_pct": "%"}:
            raise ValueError("Unités attendues : Mm3 et % ; conversion à auditer explicitement")
        return self


def load_mapping(path: Path) -> ColumnMapping:
    return ColumnMapping.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
