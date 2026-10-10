import { apiFetch } from "./client";
import type { Alert } from "../types";

export function getAlerts() {
  return apiFetch<Alert[]>("/alerts");
}

export function markAlertRead(id: number) {
  return apiFetch<Alert>(`/alerts/${id}/read`, {
    method: "POST",
  });
}