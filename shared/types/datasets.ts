import type { Dataset, DatasetItem, DatasetSnapshot } from "./contracts";

export type DatasetSummary = Dataset & {
  item_count: number;
};

export type DatasetDetail = DatasetSummary & {
  snapshot_id: string;
  snapshot_version: number;
  snapshot_count: number;
  categories: string[];
};

export type DatasetItemList = {
  dataset_id: string;
  snapshot_id: string;
  total_count: number;
  items: DatasetItem[];
};

export type DatasetUploadResult = {
  dataset: DatasetDetail;
  snapshot_id: string;
  preview_items: DatasetItem[];
};

export type DatasetDraftGenerateRequest = {
  name: string;
  prompt: string;
  description?: string | null;
  item_count?: number;
  tags?: string[];
};

export type DatasetDraftList = {
  total_count: number;
  items: DatasetSummary[];
};

export type DatasetApprovalRequest = {
  reviewer_id: string;
  note?: string | null;
};

export type DatasetPromotionRequest = {
  target_dataset_id?: string | null;
  target_dataset_name?: string | null;
  create_as_draft?: boolean;
  tags?: string[];
};

export type DatasetPromotionResult = {
  dataset: DatasetDetail;
  snapshot_id: string;
  promoted_item: DatasetItem;
};

export type DatasetSnapshotList = {
  dataset_id: string;
  snapshots: DatasetSnapshot[];
};

export type DatasetChangedItem = {
  dataset_item_id: string;
  from_item: DatasetItem;
  to_item: DatasetItem;
};

export type DatasetDiff = {
  dataset_id: string;
  from_snapshot_id: string;
  to_snapshot_id: string;
  added_count: number;
  removed_count: number;
  changed_count: number;
  added: DatasetItem[];
  removed: DatasetItem[];
  changed: DatasetChangedItem[];
};

export type DatasetValidationError = {
  row_number: number | null;
  field: string | null;
  message: string;
};

export type DatasetImportError = {
  message: string;
  errors: DatasetValidationError[];
};
