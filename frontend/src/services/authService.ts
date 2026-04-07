import { apiPost } from "./api";

export type AuthRole = "manufacturer" | "driver" | "retailer";

export interface LoginPayload {
  name: string;
  email: string;
  role: AuthRole;
}

export interface AuthUser {
  id: number;
  name: string;
  email: string;
  role: AuthRole;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export async function loginUser(payload: LoginPayload): Promise<AuthResponse> {
  return apiPost<AuthResponse, LoginPayload>("/api/auth/login", payload);
}
