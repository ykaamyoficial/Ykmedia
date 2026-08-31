import { ValidationError } from "@/shared/errors";
import { appTimeouts } from "@/shared/constants/app";
import { httpClient } from "@/shared/services";
import {
  appSettingsSchema,
  diagnosticReportSchema,
  evolutionLicenseSchema,
  evolutionSessionSchema,
  saveAppSettingsSchema,
  setupProgressSchema,
  setupReportSchema,
  type AppSettings,
  type DiagnosticReport,
  type EvolutionLicense,
  type EvolutionSession,
  type SetupProgress,
  type SetupReport,
} from "@/features/settings/types";

export async function fetchSettings(): Promise<AppSettings> {
  const payload = await httpClient.getJson<unknown>("/settings");
  const parsed = appSettingsSchema.safeParse(payload);
  if (!parsed.success) {
    throw new ValidationError("Settings payload is invalid.", parsed.error);
  }
  return parsed.data;
}

export async function saveSettings(settings: AppSettings): Promise<AppSettings> {
  const payload = await httpClient.requestJson<unknown>("/settings", {
    method: "PUT",
    body: {
      downloads_root: settings.downloads_root,
      ffmpeg_path: settings.ffmpeg_path,
      sqlite_database: settings.sqlite_database,
      whatsapp_instance: settings.whatsapp_instance,
    },
  });
  const parsed = saveAppSettingsSchema.safeParse(payload);
  if (!parsed.success) {
    throw new ValidationError("Save settings payload is invalid.", parsed.error);
  }
  return parsed.data;
}

export async function fetchEvolutionSession(): Promise<EvolutionSession> {
  const payload = await httpClient.getJson<unknown>("/settings/evolution");
  const parsed = evolutionSessionSchema.safeParse(payload);
  if (!parsed.success) {
    throw new ValidationError("Evolution payload is invalid.", parsed.error);
  }
  return parsed.data;
}

export async function connectEvolutionSession(): Promise<EvolutionSession> {
  const payload = await httpClient.requestJson<unknown>("/settings/evolution/connect", {
    method: "POST",
  });
  const parsed = evolutionSessionSchema.safeParse(payload);
  if (!parsed.success) {
    throw new ValidationError("Connect evolution payload is invalid.", parsed.error);
  }
  return parsed.data;
}

export async function disconnectEvolutionSession(): Promise<EvolutionSession> {
  const payload = await httpClient.requestJson<unknown>("/settings/evolution/disconnect", {
    method: "POST",
  });
  const parsed = evolutionSessionSchema.safeParse(payload);
  if (!parsed.success) {
    throw new ValidationError("Disconnect evolution payload is invalid.", parsed.error);
  }
  return parsed.data;
}

export async function prepareSystem(): Promise<SetupReport> {
  const payload = await httpClient.requestJson<unknown>("/settings/prepare", {
    method: "POST",
    timeoutMs: appTimeouts.systemPrepareMs,
  });
  const parsed = setupReportSchema.safeParse(payload);
  if (!parsed.success) {
    throw new ValidationError("Setup payload is invalid.", parsed.error);
  }
  return parsed.data;
}

export async function runDiagnostics(): Promise<DiagnosticReport> {
  const payload = await httpClient.getJson<unknown>("/settings/diagnostics");
  const parsed = diagnosticReportSchema.safeParse(payload);
  if (!parsed.success) {
    throw new ValidationError("Diagnostics payload is invalid.", parsed.error);
  }
  return parsed.data;
}

export async function fetchEvolutionLicense(): Promise<EvolutionLicense> {
  const payload = await httpClient.getJson<unknown>("/settings/evolution/license");
  const parsed = evolutionLicenseSchema.safeParse(payload);
  if (!parsed.success) {
    throw new ValidationError("License payload is invalid.", parsed.error);
  }
  return parsed.data;
}

export async function startEvolutionLicenseRegistration(): Promise<EvolutionLicense> {
  const payload = await httpClient.requestJson<unknown>("/settings/evolution/license/register", {
    method: "POST",
  });
  const parsed = evolutionLicenseSchema.safeParse(payload);
  if (!parsed.success) {
    throw new ValidationError("License registration payload is invalid.", parsed.error);
  }
  return parsed.data;
}

export async function fetchSetupProgress(): Promise<SetupProgress> {
  const payload = await httpClient.getJson<unknown>("/settings/prepare/status");
  const parsed = setupProgressSchema.safeParse(payload);
  if (!parsed.success) {
    throw new ValidationError("Setup progress payload is invalid.", parsed.error);
  }
  return parsed.data;
}
