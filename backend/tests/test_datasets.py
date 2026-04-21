from __future__ import annotations

import csv
import io
from pathlib import Path

from fastapi.testclient import TestClient

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_upload_valid_json_dataset_persists_records(client: TestClient) -> None:
    with (FIXTURE_DIR / "dataset_valid.json").open("rb") as handle:
        response = client.post(
            "/api/v1/datasets",
            files={"file": ("dataset_valid.json", handle, "application/json")},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["dataset"]["dataset_id"] == "dataset_support_faq_v1"
    assert body["dataset"]["item_count"] == 20
    assert body["snapshot_id"] == "dataset_support_faq_v1__snapshot_001"
    assert len(body["preview_items"]) == 5

    dataset_list = client.get("/api/v1/datasets")
    assert dataset_list.status_code == 200
    assert dataset_list.json()[0]["dataset_id"] == "dataset_support_faq_v1"

    items = client.get("/api/v1/datasets/dataset_support_faq_v1/items")
    assert items.status_code == 200
    assert items.json()["snapshot_id"] == "dataset_support_faq_v1__snapshot_001"
    assert items.json()["total_count"] == 20


def test_upload_invalid_json_dataset_returns_row_errors(client: TestClient) -> None:
    with (FIXTURE_DIR / "dataset_invalid.json").open("rb") as handle:
        response = client.post(
            "/api/v1/datasets",
            files={"file": ("dataset_invalid.json", handle, "application/json")},
        )

    assert response.status_code == 422
    detail = response.json()
    assert detail["message"] == "Dataset import validation failed."
    assert any(error["field"] == "input_text" for error in detail["errors"])
    assert any(error["field"] == "category" for error in detail["errors"])


def test_upload_csv_dataset_uses_form_metadata(client: TestClient) -> None:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "dataset_item_id",
            "input_text",
            "category",
            "expected_output",
            "metadata_json",
        ],
    )
    writer.writeheader()
    writer.writerow(
        {
            "dataset_item_id": "csv_item_001",
            "input_text": "What is the billing cycle?",
            "category": "billing",
            "expected_output": "Monthly.",
            "metadata_json": '{"locale": "en-US"}',
        }
    )
    writer.writerow(
        {
            "dataset_item_id": "csv_item_002",
            "input_text": "Can admins export reports?",
            "category": "admin",
            "expected_output": "Yes.",
            "metadata_json": '{"tier": "enterprise"}',
        }
    )

    response = client.post(
        "/api/v1/datasets",
        data={"dataset_id": "dataset_csv_demo", "name": "CSV Demo Dataset"},
        files={"file": ("dataset.csv", buffer.getvalue().encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["dataset"]["dataset_id"] == "dataset_csv_demo"
    assert body["dataset"]["source_type"] == "csv"
    assert body["dataset"]["item_count"] == 2


def test_duplicate_dataset_id_creates_new_snapshot(client: TestClient) -> None:
    with (FIXTURE_DIR / "dataset_valid.json").open("rb") as handle:
        first = client.post(
            "/api/v1/datasets",
            files={"file": ("dataset_valid.json", handle, "application/json")},
        )

    assert first.status_code == 201
    assert first.json()["snapshot_id"] == "dataset_support_faq_v1__snapshot_001"

    with (FIXTURE_DIR / "dataset_valid.json").open("rb") as handle:
        second = client.post(
            "/api/v1/datasets",
            files={"file": ("dataset_valid.json", handle, "application/json")},
        )

    assert second.status_code == 201
    assert second.json()["snapshot_id"] == "dataset_support_faq_v1__snapshot_002"

    dataset = client.get("/api/v1/datasets/dataset_support_faq_v1")
    assert dataset.status_code == 200
    assert dataset.json()["latest_snapshot_id"] == "dataset_support_faq_v1__snapshot_002"
    assert dataset.json()["snapshot_count"] == 2


def test_uploading_multiple_csv_datasets_without_item_ids_generates_unique_ids(
    client: TestClient,
) -> None:
    csv_body = b"input_text,category\nQuestion one,billing\nQuestion two,admin\n"

    first = client.post(
        "/api/v1/datasets",
        data={"dataset_id": "dataset_one", "name": "Dataset One"},
        files={"file": ("first.csv", csv_body, "text/csv")},
    )
    assert first.status_code == 201
    first_preview_ids = [item["dataset_item_id"] for item in first.json()["preview_items"]]
    assert first_preview_ids == ["dataset_one__item_001", "dataset_one__item_002"]

    second = client.post(
        "/api/v1/datasets",
        data={"dataset_id": "dataset_two", "name": "Dataset Two"},
        files={"file": ("second.csv", csv_body, "text/csv")},
    )
    assert second.status_code == 201
    second_preview_ids = [item["dataset_item_id"] for item in second.json()["preview_items"]]
    assert second_preview_ids == ["dataset_two__item_001", "dataset_two__item_002"]
