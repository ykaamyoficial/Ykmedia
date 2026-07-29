import { ValidationError } from "@/shared/errors";
import { httpClient } from "@/shared/services";
import {
  dashboardOverviewSchema,
  type DashboardOverview,
} from "@/features/dashboard/types";

export async function fetchDashboardOverview(): Promise<DashboardOverview> {
  const payload = await httpClient.getJson<unknown>("/dashboard/overview");
  const parsed = dashboardOverviewSchema.safeParse(payload);

  if (!parsed.success) {
    throw new ValidationError("Dashboard overview payload is invalid.", parsed.error);
  }

  return parsed.data;
}
