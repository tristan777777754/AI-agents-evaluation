from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import DatasetItemRecord, DatasetRecord, DatasetSnapshotRecord
from app.schemas.contracts import (
    DatasetItemSchema,
    DatasetSchema,
    DatasetSnapshotSchema,
    SourceType,
)
from app.schemas.datasets import (
    DatasetChangedItemSchema,
    DatasetDetailSchema,
    DatasetDiffSchema,
    DatasetImportItemSchema,
    DatasetImportPayloadSchema,
    DatasetItemListSchema,
    DatasetSnapshotListSchema,
    DatasetSummarySchema,
    DatasetValidationErrorSchema,
)


class DatasetImportValidationException(Exception):
    def __init__(self, errors: list[DatasetValidationErrorSchema]):
        super().__init__("Dataset import validation failed.")
        self.errors = errors


@dataclass(frozen=True)
class NormalizedDatasetImport:
    dataset: DatasetSchema
    items: list[DatasetItemSchema]


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return cleaned or "dataset"


def _generated_dataset_id(seed: str) -> str:
    return f"dataset_{_slugify(seed)}_{uuid4().hex[:8]}"


def _generated_item_id(dataset_id: str, index: int) -> str:
    return f"{dataset_id}__item_{index:03d}"


def _normalise_optional_json_field(
    raw_value: object | None,
    *,
    row_number: int,
    field: str,
    errors: list[DatasetValidationErrorSchema],
) -> dict[str, object] | None:
    if raw_value is None or raw_value == "":
        return None
    if isinstance(raw_value, dict):
        return raw_value
    if not isinstance(raw_value, str):
        errors.append(
            DatasetValidationErrorSchema(
                row_number=row_number,
                field=field,
                message="Must be either empty, a JSON object, or JSON object text.",
            )
        )
        return None

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        errors.append(
            DatasetValidationErrorSchema(
                row_number=row_number,
                field=field,
                message="Must be valid JSON object text.",
            )
        )
        return None

    if not isinstance(parsed, dict):
        errors.append(
            DatasetValidationErrorSchema(
                row_number=row_number,
                field=field,
                message="Must decode to a JSON object.",
            )
        )
        return None

    return parsed


def _collect_validation_errors(
    row_number: int | None,
    exc: ValidationError,
) -> list[DatasetValidationErrorSchema]:
    collected: list[DatasetValidationErrorSchema] = []
    for error in exc.errors():
        location = error["loc"][0] if error["loc"] else None
        collected.append(
            DatasetValidationErrorSchema(
                row_number=row_number,
                field=str(location) if location is not None else None,
                message=error["msg"],
            )
        )
    return collected


def _build_item(
    raw_item: dict[str, object],
    *,
    row_number: int,
    default_dataset_item_id: str,
) -> tuple[DatasetImportItemSchema | None, list[DatasetValidationErrorSchema]]:
    errors: list[DatasetValidationErrorSchema] = []
    transformed = dict(raw_item)
    transformed["dataset_item_id"] = transformed.get("dataset_item_id") or default_dataset_item_id
    transformed["rubric_json"] = _normalise_optional_json_field(
        transformed.get("rubric_json"), row_number=row_number, field="rubric_json", errors=errors
    )
    transformed["metadata_json"] = _normalise_optional_json_field(
        transformed.get("metadata_json"),
        row_number=row_number,
        field="metadata_json",
        errors=errors,
    )

    try:
        item = DatasetImportItemSchema.model_validate(transformed)
    except ValidationError as exc:
        errors.extend(_collect_validation_errors(row_number, exc))
        return None, errors

    if not item.input_text.strip():
        errors.append(
            DatasetValidationErrorSchema(
                row_number=row_number,
                field="input_text",
                message="Input text must not be empty.",
            )
        )
    if not item.category.strip():
        errors.append(
            DatasetValidationErrorSchema(
                row_number=row_number,
                field="category",
                message="Category must not be empty.",
            )
        )

    return item, errors


def parse_dataset_upload(
    *,
    filename: str,
    content: bytes,
    dataset_id: str | None,
    name: str | None,
    description: str | None,
) -> NormalizedDatasetImport:
    suffix = Path(filename).suffix.lower()
    if suffix == ".json":
        return _parse_json_upload(
            content,
            dataset_id=dataset_id,
            name=name,
            description=description,
        )
    if suffix == ".csv":
        return _parse_csv_upload(
            content,
            filename=filename,
            dataset_id=dataset_id,
            name=name,
            description=description,
        )

    raise DatasetImportValidationException(
        [
            DatasetValidationErrorSchema(
                field="file",
                message="Unsupported file type. Upload a .json or .csv dataset file.",
            )
        ]
    )


def _parse_json_upload(
    content: bytes,
    *,
    dataset_id: str | None,
    name: str | None,
    description: str | None,
) -> NormalizedDatasetImport:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DatasetImportValidationException(
            [
                DatasetValidationErrorSchema(
                    field="file",
                    message=f"JSON dataset could not be decoded: {exc}",
                )
            ]
        ) from exc

    try:
        parsed = DatasetImportPayloadSchema.model_validate(payload)
    except ValidationError as exc:
        raise DatasetImportValidationException(_collect_validation_errors(None, exc)) from exc

    resolved_name = name or parsed.name
    resolved_dataset_id = dataset_id or parsed.dataset_id or _generated_dataset_id(resolved_name)
    resolved_description = description if description is not None else parsed.description

    return _normalise_import(
        dataset_schema=DatasetSchema(
            dataset_id=resolved_dataset_id,
            name=resolved_name,
            description=resolved_description,
            schema_version=parsed.schema_version,
            source_type=parsed.source_type,
        ),
        raw_items=parsed.items,
    )


def _parse_csv_upload(
    content: bytes,
    *,
    filename: str,
    dataset_id: str | None,
    name: str | None,
    description: str | None,
) -> NormalizedDatasetImport:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DatasetImportValidationException(
            [
                DatasetValidationErrorSchema(
                    field="file",
                    message=f"CSV dataset could not be decoded: {exc}",
                )
            ]
        ) from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise DatasetImportValidationException(
            [DatasetValidationErrorSchema(field="file", message="CSV header row is required.")]
        )

    resolved_name = name or Path(filename).stem.replace("_", " ").strip() or "Dataset Upload"
    resolved_dataset_id = dataset_id or _generated_dataset_id(resolved_name)

    return _normalise_import(
        dataset_schema=DatasetSchema(
            dataset_id=resolved_dataset_id,
            name=resolved_name,
            description=description,
            schema_version="1.0",
            source_type=SourceType.csv,
        ),
        raw_items=[dict(row) for row in reader],
    )


def _normalise_import(
    *,
    dataset_schema: DatasetSchema,
    raw_items: list[dict[str, object]],
) -> NormalizedDatasetImport:
    if not raw_items:
        raise DatasetImportValidationException(
            [
                DatasetValidationErrorSchema(
                    field="items",
                    message="At least one dataset item is required.",
                )
            ]
        )

    errors: list[DatasetValidationErrorSchema] = []
    items: list[DatasetItemSchema] = []
    seen_ids: set[str] = set()

    for index, raw_item in enumerate(raw_items, start=1):
        row_number = index if dataset_schema.source_type is SourceType.json else index + 1
        item, row_errors = _build_item(
            raw_item,
            row_number=row_number,
            default_dataset_item_id=_generated_item_id(dataset_schema.dataset_id, index),
        )
        errors.extend(row_errors)
        if item is None:
            continue
        if item.dataset_item_id in seen_ids:
            errors.append(
                DatasetValidationErrorSchema(
                    row_number=row_number,
                    field="dataset_item_id",
                    message="Dataset item ids must be unique within a dataset upload.",
                )
            )
            continue

        assert item.dataset_item_id is not None
        seen_ids.add(item.dataset_item_id)
        items.append(
            DatasetItemSchema(
                dataset_item_id=item.dataset_item_id,
                dataset_id=dataset_schema.dataset_id,
                input_text=item.input_text.strip(),
                category=item.category.strip(),
                difficulty=item.difficulty,
                expected_output=item.expected_output,
                rubric_json=item.rubric_json,
                reference_context=item.reference_context,
                metadata_json=item.metadata_json,
            )
        )

    if errors:
        raise DatasetImportValidationException(errors)

    return NormalizedDatasetImport(dataset=dataset_schema, items=items)


def _snapshot_checksum(items: list[DatasetItemSchema]) -> str:
    serialized = json.dumps(
        [item.model_dump(mode="json") for item in items],
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _snapshot_id(dataset_id: str, version_number: int) -> str:
    return f"{dataset_id}__snapshot_{version_number:03d}"


def _get_snapshot(
    session: Session,
    dataset_id: str,
    snapshot_id: str | None,
) -> tuple[DatasetRecord, DatasetSnapshotRecord]:
    dataset = session.get(DatasetRecord, dataset_id)
    if dataset is None:
        raise LookupError(dataset_id)

    resolved_snapshot_id = snapshot_id or dataset.latest_snapshot_id
    if resolved_snapshot_id is None:
        raise LookupError(f"No snapshots found for dataset '{dataset_id}'.")

    snapshot = session.get(DatasetSnapshotRecord, resolved_snapshot_id)
    if snapshot is None or snapshot.dataset_id != dataset_id:
        raise LookupError(resolved_snapshot_id)

    return dataset, snapshot


def _snapshot_items(session: Session, snapshot_id: str) -> list[DatasetItemRecord]:
    statement = (
        select(DatasetItemRecord)
        .where(DatasetItemRecord.dataset_snapshot_id == snapshot_id)
        .order_by(DatasetItemRecord.sort_index.asc())
    )
    return list(session.execute(statement).scalars().all())


def _item_schema(record: DatasetItemRecord) -> DatasetItemSchema:
    return DatasetItemSchema(
        dataset_item_id=record.dataset_item_id,
        dataset_id=record.dataset_id,
        input_text=record.input_text,
        category=record.category,
        difficulty=record.difficulty,
        expected_output=record.expected_output,
        rubric_json=record.rubric_json,
        reference_context=record.reference_context,
        metadata_json=record.metadata_json,
    )


def create_dataset(session: Session, normalized: NormalizedDatasetImport) -> DatasetDetailSchema:
    dataset_record = session.get(DatasetRecord, normalized.dataset.dataset_id)
    if dataset_record is None:
        dataset_record = DatasetRecord(
            dataset_id=normalized.dataset.dataset_id,
            name=normalized.dataset.name,
            description=normalized.dataset.description,
            schema_version=normalized.dataset.schema_version,
            source_type=normalized.dataset.source_type.value,
        )
        session.add(dataset_record)
        version_number = 1
    else:
        dataset_record.name = normalized.dataset.name
        dataset_record.description = normalized.dataset.description
        dataset_record.schema_version = normalized.dataset.schema_version
        dataset_record.source_type = normalized.dataset.source_type.value
        current_max_version = session.scalar(
            select(func.max(DatasetSnapshotRecord.version_number)).where(
                DatasetSnapshotRecord.dataset_id == normalized.dataset.dataset_id
            )
        )
        version_number = int(current_max_version or 0) + 1

    snapshot_record = DatasetSnapshotRecord(
        dataset_snapshot_id=_snapshot_id(normalized.dataset.dataset_id, version_number),
        dataset_id=normalized.dataset.dataset_id,
        version_number=version_number,
        checksum=_snapshot_checksum(normalized.items),
    )
    session.add(snapshot_record)

    for index, item in enumerate(normalized.items, start=1):
        session.add(
            DatasetItemRecord(
                dataset_item_id=item.dataset_item_id,
                dataset_id=normalized.dataset.dataset_id,
                dataset_snapshot_id=snapshot_record.dataset_snapshot_id,
                sort_index=index,
                input_text=item.input_text,
                category=item.category,
                difficulty=item.difficulty,
                expected_output=item.expected_output,
                rubric_json=item.rubric_json,
                reference_context=item.reference_context,
                metadata_json=item.metadata_json,
            )
        )

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError(
            "Dataset import failed because one or more record ids already exist."
        ) from exc

    dataset_record.latest_snapshot_id = snapshot_record.dataset_snapshot_id
    session.commit()

    return get_dataset_detail(
        session,
        normalized.dataset.dataset_id,
        snapshot_id=snapshot_record.dataset_snapshot_id,
    )


def list_datasets(session: Session) -> list[DatasetSummarySchema]:
    datasets = session.execute(
        select(DatasetRecord).order_by(DatasetRecord.created_at.desc())
    ).scalars()
    summaries: list[DatasetSummarySchema] = []
    for dataset in datasets:
        item_count = 0
        if dataset.latest_snapshot_id is not None:
            item_count = int(
                session.scalar(
                    select(func.count(DatasetItemRecord.dataset_item_record_id)).where(
                        DatasetItemRecord.dataset_snapshot_id == dataset.latest_snapshot_id
                    )
                )
                or 0
            )
        summaries.append(
            DatasetSummarySchema(
                dataset_id=dataset.dataset_id,
                name=dataset.name,
                description=dataset.description,
                schema_version=dataset.schema_version,
                source_type=SourceType(dataset.source_type),
                latest_snapshot_id=dataset.latest_snapshot_id,
                item_count=item_count,
            )
        )
    return summaries


def get_dataset_detail(
    session: Session,
    dataset_id: str,
    *,
    snapshot_id: str | None = None,
) -> DatasetDetailSchema:
    dataset, snapshot = _get_snapshot(session, dataset_id, snapshot_id)

    item_count = session.scalar(
        select(func.count(DatasetItemRecord.dataset_item_record_id)).where(
            DatasetItemRecord.dataset_snapshot_id == snapshot.dataset_snapshot_id
        )
    )
    categories = session.execute(
        select(DatasetItemRecord.category)
        .where(DatasetItemRecord.dataset_snapshot_id == snapshot.dataset_snapshot_id)
        .distinct()
        .order_by(DatasetItemRecord.category.asc())
    ).scalars()
    snapshot_count = session.scalar(
        select(func.count(DatasetSnapshotRecord.dataset_snapshot_id)).where(
            DatasetSnapshotRecord.dataset_id == dataset_id
        )
    )

    return DatasetDetailSchema(
        dataset_id=dataset.dataset_id,
        name=dataset.name,
        description=dataset.description,
        schema_version=dataset.schema_version,
        source_type=SourceType(dataset.source_type),
        latest_snapshot_id=dataset.latest_snapshot_id,
        snapshot_id=snapshot.dataset_snapshot_id,
        snapshot_version=snapshot.version_number,
        snapshot_count=int(snapshot_count or 0),
        item_count=item_count or 0,
        categories=list(categories),
    )


def get_dataset_items(
    session: Session,
    dataset_id: str,
    *,
    snapshot_id: str | None = None,
) -> DatasetItemListSchema:
    _, snapshot = _get_snapshot(session, dataset_id, snapshot_id)
    records = _snapshot_items(session, snapshot.dataset_snapshot_id)
    return DatasetItemListSchema(
        dataset_id=dataset_id,
        snapshot_id=snapshot.dataset_snapshot_id,
        total_count=len(records),
        items=[_item_schema(record) for record in records],
    )


def list_dataset_snapshots(session: Session, dataset_id: str) -> DatasetSnapshotListSchema:
    dataset = session.get(DatasetRecord, dataset_id)
    if dataset is None:
        raise LookupError(dataset_id)

    records = session.execute(
        select(DatasetSnapshotRecord)
        .where(DatasetSnapshotRecord.dataset_id == dataset_id)
        .order_by(DatasetSnapshotRecord.version_number.asc())
    ).scalars()
    return DatasetSnapshotListSchema(
        dataset_id=dataset_id,
        snapshots=[
            DatasetSnapshotSchema(
                dataset_snapshot_id=record.dataset_snapshot_id,
                dataset_id=record.dataset_id,
                version_number=record.version_number,
                checksum=record.checksum,
                created_at=record.created_at.isoformat() if record.created_at else None,
            )
            for record in records
        ],
    )


def get_dataset_diff(
    session: Session,
    dataset_id: str,
    *,
    from_snapshot_id: str,
    to_snapshot_id: str,
) -> DatasetDiffSchema:
    _, from_snapshot = _get_snapshot(session, dataset_id, from_snapshot_id)
    _, to_snapshot = _get_snapshot(session, dataset_id, to_snapshot_id)

    from_items = {
        record.dataset_item_id: _item_schema(record)
        for record in _snapshot_items(session, from_snapshot.dataset_snapshot_id)
    }
    to_items = {
        record.dataset_item_id: _item_schema(record)
        for record in _snapshot_items(session, to_snapshot.dataset_snapshot_id)
    }

    from_ids = set(from_items)
    to_ids = set(to_items)
    added = [to_items[item_id] for item_id in sorted(to_ids - from_ids)]
    removed = [from_items[item_id] for item_id in sorted(from_ids - to_ids)]

    changed: list[DatasetChangedItemSchema] = []
    for item_id in sorted(from_ids & to_ids):
        if from_items[item_id].model_dump(mode="json") == to_items[item_id].model_dump(mode="json"):
            continue
        changed.append(
            DatasetChangedItemSchema(
                dataset_item_id=item_id,
                from_item=from_items[item_id],
                to_item=to_items[item_id],
            )
        )

    return DatasetDiffSchema(
        dataset_id=dataset_id,
        from_snapshot_id=from_snapshot.dataset_snapshot_id,
        to_snapshot_id=to_snapshot.dataset_snapshot_id,
        added_count=len(added),
        removed_count=len(removed),
        changed_count=len(changed),
        added=added,
        removed=removed,
        changed=changed,
    )
