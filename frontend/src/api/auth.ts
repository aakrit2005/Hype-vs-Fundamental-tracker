import { apiFetch } from "./client";
import type { TokenResponse, User } from "../types";

export function register(email: string, password: string) {
  return apiFetch<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
    }),
  });
}

export function login(email: string, password: string) {
  // FastAPI's OAuth2 password flow expects a form body.
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body,
  });
}