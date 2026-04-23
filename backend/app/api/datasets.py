from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.datasets import (
    DatasetApprovalRequestSchema,
    DatasetDetailSchema,
    DatasetDiffSchema,
    DatasetDraftGenerateRequestSchema,
    DatasetDraftListSchema,
    DatasetImportErrorSchema,
    DatasetItemListSchema,
    DatasetSnapshotListSchema,
    DatasetSummarySchema,
    DatasetUploadResultSchema,
)
from app.services.datasets import (
    DatasetImportValidationException,
    approve_dataset_draft,
    create_dataset,
    generate_dataset_draft,
    get_dataset_detail,
    get_dataset_diff,
    get_dataset_items,
    list_dataset_drafts,
    list_dataset_snapshots,
    list_datasets,
    parse_dataset_upload,
)

router = APIRouter()

DatasetFile = Annotated[UploadFile, File(...)]
OptionalFormField = Annotated[str | None, Form()]
DatasetSession = Annotated[Session, Depends(get_session)]


def _dataset_import_error_response(
    errors: Sequence[object],
) -> JSONResponse:
    serialized_errors = [
        error.model_dump(mode="json") if hasattr(error, "model_dump") else error for error in errors
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "message": "Dataset import validation failed.",
            "errors": serialized_errors,
        },
    )


@router.post(
    "",
    response_model=DatasetUploadResultSchema,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": DatasetImportErrorSchema}},
)
async def upload_dataset(
    file: DatasetFile,
    session: DatasetSession,
    dataset_id: OptionalFormField = None,
    name: OptionalFormField = None,
    description: OptionalFormField = None,
) -> DatasetUploadResultSchema | JSONResponse:
    try:
        normalized = parse_dataset_upload(
            filename=file.filename or "dataset_upload",
            content=await file.read(),
            dataset_id=dataset_id,
            name=name,
            description=description,
        )
    except DatasetImportValidationException as exc:
        return _dataset_import_error_response(exc.errors)

    try:
        dataset = create_dataset(session, normalized)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return DatasetUploadResultSchema(
        dataset=dataset,
        snapshot_id=dataset.snapshot_id,
        preview_items=normalized.items[:5],
    )


@router.get("/drafts", response_model=DatasetDraftListSchema)
def get_dataset_drafts(session: DatasetSession) -> DatasetDraftListSchema:
    return list_dataset_drafts(session)


@router.post(
    "/drafts/generate",
    response_model=DatasetDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_generated_dataset_draft(
    payload: DatasetDraftGenerateRequestSchema,
    session: DatasetSession,
) -> DatasetDetailSchema:
    return generate_dataset_draft(session, payload)


@router.get("", response_model=list[DatasetSummarySchema])
def get_datasets(session: DatasetSession) -> list[DatasetSummarySchema]:
    return list_datasets(session)


@router.get("/{dataset_id}", response_model=DatasetDetailSchema)
def get_dataset(
    dataset_id: str,
    session: DatasetSession,
    snapshot_id: str | None = None,
) -> DatasetDetailSchema:
    try:
        return get_dataset_detail(session, dataset_id, snapshot_id=snapshot_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        ) from exc


@router.get("/{dataset_id}/items", response_model=DatasetItemListSchema)
def get_dataset_item_list(
    dataset_id: str,
    session: DatasetSession,
    snapshot_id: str | None = None,
    page: int = 1,
    per_page: int = 25,
    tag: str | None = None,
    category: str | None = None,
) -> DatasetItemListSchema:
    try:
        return get_dataset_items(
            session,
            dataset_id,
            snapshot_id=snapshot_id,
            page=max(page, 1),
            per_page=min(max(per_page, 1), 100),
            tag=tag,
            category=category,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        ) from exc


@router.get("/{dataset_id}/snapshots", response_model=DatasetSnapshotListSchema)
def get_dataset_snapshot_list(
    dataset_id: str,
    session: DatasetSession,
) -> DatasetSnapshotListSchema:
    try:
        return list_dataset_snapshots(session, dataset_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        ) from exc


@router.get("/{dataset_id}/diff", response_model=DatasetDiffSchema)
def get_dataset_snapshot_diff(
    dataset_id: str,
    from_snapshot: str,
    to_snapshot: str,
    session: DatasetSession,
) -> DatasetDiffSchema:
    try:
        return get_dataset_diff(
            session,
            dataset_id,
            from_snapshot_id=from_snapshot,
            to_snapshot_id=to_snapshot,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset snapshot not found.",
        ) from exc


@router.post("/{dataset_id}/approve", response_model=DatasetDetailSchema)
def approve_dataset(
    dataset_id: str,
    payload: DatasetApprovalRequestSchema,
    session: DatasetSession,
) -> DatasetDetailSchema:
    try:
        return approve_dataset_draft(session, dataset_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
