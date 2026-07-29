import type { Bootstrap, Session } from "./api";
import { request } from "./http";

export function loadBootstrap(): Promise<Bootstrap> {
  return request("/api/v60/bootstrap");
}

export function loadSession(): Promise<Session> {
  return request("/api/v60/auth/me");
}

export function login(email: string, password: string): Promise<Session> {
  return request("/api/v60/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function logout(): Promise<void> {
  return request("/api/v60/auth/logout", { method: "POST" });
}
