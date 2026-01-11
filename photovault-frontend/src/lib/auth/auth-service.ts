/**
 * Authentication Service
 * Handles all auth-related API calls and token management
 */

import { api } from '../api/client';
import { authStore } from './auth-store';
import type {
  AuthCredentials,
  SignupData,
  AuthResponse,
  AuthUser,
  PasswordResetRequest,
  PasswordReset,
  EmailVerification,
  AuthError,
} from '@/lib/types/auth';

class AuthService {
  /**
   * Login with email and password
   */
  async login(credentials: AuthCredentials): Promise<{ user: AuthUser; token: string }> {
    try {
      // Login
      const response = await api.post<AuthResponse>('/api/auth/login/', credentials);

      const token = response.data?.access_token;
      if (!token) {
        throw new Error('No token received from server');
      }

      // Store token
      authStore.setToken(token);

      // Fetch user profile
      const userResponse = await api.get<AuthUser>('/api/auth/me/');
      return {
        user: userResponse.data,
        token,
      };
    } catch (error: any) {
      throw this.handleError(error, 'Login failed');
    }
  }

  /**
   * Sign up new user
   */
  async signup(data: SignupData): Promise<{ user: AuthUser; token: string }> {
    try {
      // Add password_confirm field for Django backend
      const signupData = {
        ...data,
        password_confirm: data.password
      };

      const response = await api.post<AuthResponse>('/api/auth/register/', signupData);

      // Registration doesn't return tokens, just creates account
      // User needs to verify email before logging in
      if (response.status === 201) {
        // For now, return a placeholder since registration is successful
        // but user needs to verify email before getting actual tokens
        return {
          user: {
            id: 'pending',
            email: data.email,
            name: data.name,
            verified: false
          },
          token: 'pending-verification'
        };
      }

      throw new Error('Registration failed');
    } catch (error: any) {
      throw this.handleError(error, 'Signup failed');
    }
  }

  /**
   * Logout
   */
  async logout(): Promise<void> {
    try {
      // Call logout endpoint (optional)
      await api.post('/api/auth/logout/').catch(() => {
        // Logout endpoint might not exist, continue anyway
      });
    } finally {
      // Clear tokens regardless of API response
      authStore.clear();
    }
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(data: PasswordResetRequest): Promise<void> {
    try {
      await api.post('/api/auth/password/reset/', data);
    } catch (error: any) {
      throw this.handleError(error, 'Password reset request failed');
    }
  }

  /**
   * Reset password with token
   */
  async resetPassword(data: PasswordReset): Promise<void> {
    try {
      await api.post('/api/auth/password/reset/confirm/', data);
    } catch (error: any) {
      throw this.handleError(error, 'Password reset failed');
    }
  }

  /**
   * Verify email
   */
  async verifyEmail(data: EmailVerification): Promise<void> {
    try {
      await api.post('/api/auth/verify/', data);
    } catch (error: any) {
      throw this.handleError(error, 'Email verification failed');
    }
  }

  /**
   * Get current user session
   */
  async getSession(): Promise<AuthUser | null> {
    try {
      const token = authStore.getToken();
      if (!token) return null;

      const response = await api.get<AuthUser>('/api/auth/me/');
      return response.data;
    } catch {
      // Token invalid or expired
      authStore.clear();
      return null;
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<string> {
    try {
      const response = await api.post<AuthResponse>('/api/auth/refresh/');

      const token = response.data?.access_token;
      if (!token) {
        throw new Error('No token received from refresh');
      }

      authStore.setToken(token);

      return token;
    } catch (error) {
      authStore.clear();
      throw error;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!authStore.getToken();
  }

  /**
   * Unified error handling
   */
  private handleError(error: any, defaultMessage: string): AuthError {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.response?.data?.error ||
      error.message ||
      defaultMessage;

    const code = error.response?.status?.toString();
    const field = error.response?.data?.field;

    return { message, code, field };
  }
}

export const authService = new AuthService();
