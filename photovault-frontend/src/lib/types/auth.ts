/**
 * Authentication Types & Interfaces
 */

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  verified: boolean;
  created_at?: string;
}

export interface AuthCredentials {
  email: string;
  password: string;
}

export interface SignupData {
  name: string;
  email: string;
  password: string;
  password_confirm?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type?: string;
  user?: AuthUser;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordReset {
  token: string;
  password: string;
  password_confirm: string;
}

export interface EmailVerification {
  token: string;
}

export interface AuthSession {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  expiresAt?: number;
}

export interface AuthError {
  message: string;
  code?: string;
  field?: string;
}
