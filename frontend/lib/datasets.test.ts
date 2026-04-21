import { describe, expect, it } from "vitest";

import { formatDatasetImportError } from "./datasets";

describe("formatDatasetImportError", () => {
  it("renders row and field context for dataset import errors", () => {
    const formatted = formatDatasetImportError({
      message: "Dataset import validation failed.",
      errors: [{ row_number: 2, field: "category", message: "Field required" }],
    });

    expect(formatted[0]).toBe("Row 2 - category: Field required");
  });
});
