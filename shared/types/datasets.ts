import type { Dataset, DatasetItem } from "./contracts";

export type DatasetSummary = Dataset & {
  item_count: number;
};

export type DatasetDetail = DatasetSummary & {
  categories: string[];
};

export type DatasetItemList = {
  dataset_id: string;
  total_count: number;
  items: DatasetItem[];
};

export type DatasetUploadResult = {
  dataset: DatasetDetail;
  preview_items: DatasetItem[];
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
