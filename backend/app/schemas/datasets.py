from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.contracts import DatasetItemSchema, DatasetSchema, SourceType


class DatasetSummarySchema(DatasetSchema):
    item_count: int


class DatasetDetailSchema(DatasetSummarySchema):
    categories: list[str] = Field(default_factory=list)


class DatasetItemListSchema(BaseModel):
    dataset_id: str
    total_count: int
    items: list[DatasetItemSchema]


class DatasetUploadResultSchema(BaseModel):
    dataset: DatasetDetailSchema
    preview_items: list[DatasetItemSchema] = Field(default_factory=list)


class DatasetValidationErrorSchema(BaseModel):
    row_number: int | None = None
    field: str | None = None
    message: str


class DatasetImportErrorSchema(BaseModel):
    message: str
    errors: list[DatasetValidationErrorSchema]


class DatasetImportItemSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_item_id: str | None = None
    input_text: str
    category: str
    difficulty: str | None = None
    expected_output: str | None = None
    rubric_json: dict[str, object] | None = None
    reference_context: str | None = None
    metadata_json: dict[str, object] | None = None


class DatasetImportPayloadSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str | None = None
    name: str
    description: str | None = None
    schema_version: str = "1.0"
    source_type: SourceType = SourceType.json
    items: list[dict[str, object]]
