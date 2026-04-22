from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import DatasetItemRecord, DatasetRecord, DatasetSnapshotRecord, EvalTaskRunRecord
from app.schemas.contracts import (
    DatasetApprovalStatus,
    DatasetItemSchema,
    DatasetLifecycleStatus,
    DatasetSchema,
    DatasetSnapshotSchema,
    DatasetSourceOrigin,
    SourceType,
)
from app.schemas.datasets import (
    DatasetApprovalRequestSchema,
    DatasetChangedItemSchema,
    DatasetDetailSchema,
    DatasetDiffSchema,
    DatasetDraftGenerateRequestSchema,
    DatasetDraftListSchema,
    DatasetImportItemSchema,
    DatasetImportPayloadSchema,
    DatasetItemListSchema,
    DatasetPromotionRequestSchema,
    DatasetPromotionResultSchema,
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


def _utc_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat()


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return cleaned or "dataset"


def _generated_dataset_id(seed: str) -> str:
    return f"dataset_{_slugify(seed)}_{uuid4().hex[:8]}"


def _generated_item_id(dataset_id: str, index: int) -> str:
    return f"{dataset_id}__item_{index:03d}"


def _normalise_tags(raw_value: object | None) -> list[str]:
    if raw_value is None or raw_value == "":
        return []
    if isinstance(raw_value, list):
        values = raw_value
    elif isinstance(raw_value, str):
        values = [part.strip() for part in raw_value.split(",")]
    else:
        values = [str(raw_value)]

    seen: set[str] = set()
    tags: list[str] = []
    for raw_tag in values:
        tag = str(raw_tag).strip().lower()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


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
    transformed["tags"] = _normalise_tags(transformed.get("tags"))

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
                source_origin=item.source_origin,
                source_task_run_id=item.source_task_run_id,
                tags=item.tags,
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


def _next_snapshot_version(session: Session, dataset_id: str) -> int:
    current_max_version = session.scalar(
        select(func.max(DatasetSnapshotRecord.version_number)).where(
            DatasetSnapshotRecord.dataset_id == dataset_id
        )
    )
    return int(current_max_version or 0) + 1


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
        source_origin=DatasetSourceOrigin(record.source_origin),
        source_task_run_id=record.source_task_run_id,
        tags=list(record.tag_list_json or []),
        metadata_json=record.metadata_json,
    )


def _persist_snapshot_items(
    session: Session,
    *,
    dataset_id: str,
    snapshot_id: str,
    items: list[DatasetItemSchema],
) -> None:
    for index, item in enumerate(items, start=1):
        session.add(
            DatasetItemRecord(
                dataset_item_id=item.dataset_item_id,
                dataset_id=dataset_id,
                dataset_snapshot_id=snapshot_id,
                sort_index=index,
                input_text=item.input_text,
                category=item.category,
                difficulty=item.difficulty,
                expected_output=item.expected_output,
                rubric_json=item.rubric_json,
                reference_context=item.reference_context,
                source_origin=item.source_origin.value,
                source_task_run_id=item.source_task_run_id,
                tag_list_json=list(item.tags),
                metadata_json=item.metadata_json,
            )
        )


def create_dataset(
    session: Session,
    normalized: NormalizedDatasetImport,
    *,
    source_origin: DatasetSourceOrigin = DatasetSourceOrigin.manual,
    lifecycle_status: DatasetLifecycleStatus = DatasetLifecycleStatus.published,
    approval_status: DatasetApprovalStatus = DatasetApprovalStatus.approved,
    generated_prompt: str | None = None,
    approved_by: str | None = None,
    approved_at: datetime | None = None,
    parent_snapshot_id: str | None = None,
) -> DatasetDetailSchema:
    dataset_record = session.get(DatasetRecord, normalized.dataset.dataset_id)
    if dataset_record is None:
        dataset_record = DatasetRecord(
            dataset_id=normalized.dataset.dataset_id,
            name=normalized.dataset.name,
            description=normalized.dataset.description,
            schema_version=normalized.dataset.schema_version,
            source_type=normalized.dataset.source_type.value,
            source_origin=source_origin.value,
            lifecycle_status=lifecycle_status.value,
            approval_status=approval_status.value,
            generated_prompt=generated_prompt,
            approved_by=approved_by,
            approved_at=approved_at,
        )
        session.add(dataset_record)
    else:
        dataset_record.name = normalized.dataset.name
        dataset_record.description = normalized.dataset.description
        dataset_record.schema_version = normalized.dataset.schema_version
        dataset_record.source_type = normalized.dataset.source_type.value
        dataset_record.source_origin = source_origin.value
        dataset_record.lifecycle_status = lifecycle_status.value
        dataset_record.approval_status = approval_status.value
        dataset_record.generated_prompt = generated_prompt
        dataset_record.approved_by = approved_by
        dataset_record.approved_at = approved_at

    version_number = _next_snapshot_version(session, normalized.dataset.dataset_id)

    snapshot_record = DatasetSnapshotRecord(
        dataset_snapshot_id=_snapshot_id(normalized.dataset.dataset_id, version_number),
        dataset_id=normalized.dataset.dataset_id,
        version_number=version_number,
        checksum=_snapshot_checksum(normalized.items),
        parent_snapshot_id=parent_snapshot_id,
    )
    session.add(snapshot_record)
    _persist_snapshot_items(
        session,
        dataset_id=normalized.dataset.dataset_id,
        snapshot_id=snapshot_record.dataset_snapshot_id,
        items=normalized.items,
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


def list_datasets(
    session: Session,
    *,
    include_drafts: bool = False,
) -> list[DatasetSummarySchema]:
    datasets = session.execute(
        select(DatasetRecord).order_by(DatasetRecord.created_at.desc())
    ).scalars()
    summaries: list[DatasetSummarySchema] = []
    for dataset in datasets:
        if not include_drafts and dataset.lifecycle_status == DatasetLifecycleStatus.draft.value:
            continue
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
                source_origin=DatasetSourceOrigin(dataset.source_origin),
                lifecycle_status=DatasetLifecycleStatus(dataset.lifecycle_status),
                approval_status=DatasetApprovalStatus(dataset.approval_status),
                generated_prompt=dataset.generated_prompt,
                approved_by=dataset.approved_by,
                approved_at=_utc_iso(dataset.approved_at),
                latest_snapshot_id=dataset.latest_snapshot_id,
                item_count=item_count,
            )
        )
    return summaries


def list_dataset_drafts(session: Session) -> DatasetDraftListSchema:
    drafts = [
        dataset
        for dataset in list_datasets(session, include_drafts=True)
        if dataset.lifecycle_status == DatasetLifecycleStatus.draft
    ]
    return DatasetDraftListSchema(total_count=len(drafts), items=drafts)


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
        source_origin=DatasetSourceOrigin(dataset.source_origin),
        lifecycle_status=DatasetLifecycleStatus(dataset.lifecycle_status),
        approval_status=DatasetApprovalStatus(dataset.approval_status),
        generated_prompt=dataset.generated_prompt,
        approved_by=dataset.approved_by,
        approved_at=_utc_iso(dataset.approved_at),
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
                parent_snapshot_id=record.parent_snapshot_id,
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


def generate_dataset_draft(
    session: Session,
    payload: DatasetDraftGenerateRequestSchema,
) -> DatasetDetailSchema:
    dataset_id = _generated_dataset_id(payload.name)
    prompt_tags = _normalise_tags(payload.tags)
    prompt_terms = _normalise_tags(payload.prompt)
    effective_tags = prompt_tags or prompt_terms[:3] or ["generated"]

    items: list[DatasetItemSchema] = []
    for index in range(1, payload.item_count + 1):
        category = effective_tags[(index - 1) % len(effective_tags)]
        items.append(
            DatasetItemSchema(
                dataset_item_id=f"{dataset_id}__draft_{index:03d}",
                dataset_id=dataset_id,
                input_text=(
                    f"{payload.prompt.strip()} Scenario {index}: "
                    "describe the correct agent response."
                ),
                category=category,
                difficulty="medium",
                expected_output=f"Draft benchmark answer {index} for {payload.name}.",
                rubric_json={"max_steps": 2, "quality_focus": effective_tags[:2]},
                source_origin=DatasetSourceOrigin.generated,
                tags=list(dict.fromkeys(["generated", category, *effective_tags])),
                metadata_json={
                    "generation_prompt": payload.prompt,
                    "draft_index": index,
                },
            )
        )

    normalized = NormalizedDatasetImport(
        dataset=DatasetSchema(
            dataset_id=dataset_id,
            name=payload.name,
            description=payload.description,
            schema_version="1.0",
            source_type=SourceType.prompt,
            source_origin=DatasetSourceOrigin.generated,
            lifecycle_status=DatasetLifecycleStatus.draft,
            approval_status=DatasetApprovalStatus.pending_review,
            generated_prompt=payload.prompt,
        ),
        items=items,
    )
    return create_dataset(
        session,
        normalized,
        source_origin=DatasetSourceOrigin.generated,
        lifecycle_status=DatasetLifecycleStatus.draft,
        approval_status=DatasetApprovalStatus.pending_review,
        generated_prompt=payload.prompt,
    )


def approve_dataset_draft(
    session: Session,
    dataset_id: str,
    payload: DatasetApprovalRequestSchema,
) -> DatasetDetailSchema:
    dataset = session.get(DatasetRecord, dataset_id)
    if dataset is None:
        raise LookupError(dataset_id)
    if dataset.lifecycle_status != DatasetLifecycleStatus.draft.value:
        raise ValueError("Only draft datasets can be approved.")
    if dataset.latest_snapshot_id is None:
        raise LookupError("Draft dataset has no snapshot to approve.")

    latest_snapshot = session.get(DatasetSnapshotRecord, dataset.latest_snapshot_id)
    if latest_snapshot is None:
        raise LookupError("Draft snapshot not found.")

    normalized = NormalizedDatasetImport(
        dataset=DatasetSchema(
            dataset_id=dataset.dataset_id,
            name=dataset.name,
            description=dataset.description,
            schema_version=dataset.schema_version,
            source_type=SourceType(dataset.source_type),
            source_origin=DatasetSourceOrigin(dataset.source_origin),
            lifecycle_status=DatasetLifecycleStatus.published,
            approval_status=DatasetApprovalStatus.approved,
            generated_prompt=dataset.generated_prompt,
        ),
        items=[
            _item_schema(record)
            for record in _snapshot_items(session, latest_snapshot.dataset_snapshot_id)
        ],
    )
    approved_detail = create_dataset(
        session,
        normalized,
        source_origin=DatasetSourceOrigin(dataset.source_origin),
        lifecycle_status=DatasetLifecycleStatus.published,
        approval_status=DatasetApprovalStatus.approved,
        generated_prompt=dataset.generated_prompt,
        approved_by=payload.reviewer_id,
        approved_at=datetime.now(UTC),
        parent_snapshot_id=latest_snapshot.dataset_snapshot_id,
    )
    if payload.note:
        approved_snapshot = session.get(DatasetSnapshotRecord, approved_detail.snapshot_id)
        if approved_snapshot is not None:
            for item in session.execute(
                select(DatasetItemRecord).where(
                    DatasetItemRecord.dataset_snapshot_id == approved_snapshot.dataset_snapshot_id
                )
            ).scalars():
                metadata = dict(item.metadata_json or {})
                metadata["approval_note"] = payload.note
                item.metadata_json = metadata
            session.commit()
    return get_dataset_detail(session, dataset_id)


def promote_failed_case(
    session: Session,
    task_run_id: str,
    payload: DatasetPromotionRequestSchema,
) -> DatasetPromotionResultSchema:
    statement = (
        select(EvalTaskRunRecord)
        .where(EvalTaskRunRecord.task_run_id == task_run_id)
        .options(selectinload(EvalTaskRunRecord.review))
        .options(selectinload(EvalTaskRunRecord.trace))
    )
    task_run = session.execute(statement).scalar_one_or_none()
    if task_run is None:
        raise LookupError("Task run not found.")
    if task_run.review is None or not task_run.review.verdict:
        raise ValueError("Failed-case promotion requires an existing reviewer verdict.")

    dataset_id = payload.target_dataset_id or "dataset_regression_promoted"
    dataset_name = payload.target_dataset_name or "Promoted Regression Dataset"
    dataset = session.get(DatasetRecord, dataset_id)
    existing_items: list[DatasetItemSchema] = []
    parent_snapshot_id: str | None = None
    if dataset is not None and dataset.latest_snapshot_id:
        parent_snapshot_id = dataset.latest_snapshot_id
        existing_items = [
            _item_schema(record) for record in _snapshot_items(session, dataset.latest_snapshot_id)
        ]

    tag_candidates = _normalise_tags(
        [
            "regression",
            task_run.category,
            task_run.review.failure_label or "",
            *(payload.tags or []),
        ]
    )
    promoted_item = DatasetItemSchema(
        dataset_item_id=f"{dataset_id}__promoted_{len(existing_items) + 1:03d}",
        dataset_id=dataset_id,
        input_text=task_run.input_text,
        category=task_run.category,
        difficulty=task_run.difficulty,
        expected_output=task_run.expected_output,
        source_origin=DatasetSourceOrigin.promoted_from_failure,
        source_task_run_id=task_run.task_run_id,
        tags=tag_candidates,
        metadata_json={
            **(task_run.metadata_json or {}),
            "source_run_id": task_run.run_id,
            "source_review_id": task_run.review.review_id,
            "promoted_from_task_run_id": task_run.task_run_id,
            "promotion_failure_label": task_run.review.failure_label,
        },
    )
    normalized = NormalizedDatasetImport(
        dataset=DatasetSchema(
            dataset_id=dataset_id,
            name=dataset_name,
            description="Regression cases promoted from reviewed task failures.",
            schema_version="1.0",
            source_type=SourceType.promotion,
            source_origin=DatasetSourceOrigin.promoted_from_failure,
            lifecycle_status=(
                DatasetLifecycleStatus.draft
                if payload.create_as_draft
                else DatasetLifecycleStatus.published
            ),
            approval_status=(
                DatasetApprovalStatus.pending_review
                if payload.create_as_draft
                else DatasetApprovalStatus.approved
            ),
        ),
        items=[*existing_items, promoted_item],
    )
    detail = create_dataset(
        session,
        normalized,
        source_origin=DatasetSourceOrigin.promoted_from_failure,
        lifecycle_status=normalized.dataset.lifecycle_status,
        approval_status=normalized.dataset.approval_status,
        parent_snapshot_id=parent_snapshot_id,
    )
    return DatasetPromotionResultSchema(
        dataset=detail,
        snapshot_id=detail.snapshot_id,
        promoted_item=promoted_item,
    )
