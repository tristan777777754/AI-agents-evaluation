from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.datasets import (
    DatasetDetailSchema,
    DatasetImportErrorSchema,
    DatasetItemListSchema,
    DatasetSummarySchema,
    DatasetUploadResultSchema,
)
from app.services.datasets import (
    DatasetImportValidationException,
    create_dataset,
    get_dataset_detail,
    get_dataset_items,
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

    return DatasetUploadResultSchema(dataset=dataset, preview_items=normalized.items[:5])


@router.get("", response_model=list[DatasetSummarySchema])
def get_datasets(session: DatasetSession) -> list[DatasetSummarySchema]:
    return list_datasets(session)

@router.get("/{dataset_id}", response_model=DatasetDetailSchema)
def get_dataset(dataset_id: str, session: DatasetSession) -> DatasetDetailSchema:
    try:
        return get_dataset_detail(session, dataset_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        ) from exc


@router.get("/{dataset_id}/items", response_model=DatasetItemListSchema)
def get_dataset_item_list(
    dataset_id: str,
    session: DatasetSession,
) -> DatasetItemListSchema:
    try:
        items = get_dataset_items(session, dataset_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        ) from exc

    return DatasetItemListSchema(dataset_id=dataset_id, total_count=len(items), items=items)
