import { ValidationError } from "@/shared/errors";
import { httpClient } from "@/shared/services";
import {
  fileLibraryResponseSchema,
  type FileLibraryResponse,
} from "@/features/files/types";

export async function fetchFiles(): Promise<FileLibraryResponse> {
  const payload = await httpClient.getJson<unknown>("/files");
  const parsed = fileLibraryResponseSchema.safeParse(payload);

  if (!parsed.success) {
    throw new ValidationError("Files payload is invalid.", parsed.error);
  }

  return parsed.data;
}
