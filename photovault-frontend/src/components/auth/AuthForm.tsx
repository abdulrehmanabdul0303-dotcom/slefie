'use client';

import { useState } from 'react';
import { Button, Input } from '@/components/ui';
import { useToast } from '@/lib/hooks/useToast';
import { useFormValidation, ValidationPatterns, ValidationRules } from '@/lib/hooks/useFormValidation';
import { useAsyncOperation } from '@/lib/hooks/useAsyncOperation';
import { Eye, EyeOff } from 'lucide-react';

interface AuthFormProps {
  mode: 'login' | 'signup';
  onSubmit: (data: LoginData | SignupData) => Promise<void>;
  isSubmitting?: boolean;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface SignupData extends LoginData {
  name: string;
  confirmPassword?: string;
}

/**
 * Enhanced Auth Form Component
 * Features:
 * - Form validation with useFormValidation
 * - Loading states with useAsyncOperation
 * - Toast notifications with useToast
 * - Password visibility toggle
 */
export const AuthForm: React.FC<AuthFormProps> = ({
  mode,
  onSubmit,
  isSubmitting = false,
}) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const { success, error: toastError } = useToast();
  const { isLoading, error, execute } = useAsyncOperation();

  const signupValidationRules: ValidationRules = {
    name: { required: true, minLength: 2, maxLength: 50 },
    email: {
      required: true,
      pattern: ValidationPatterns.email,
    },
    password: {
      required: true,
      minLength: 8,
      custom: (value) => {
        const strValue = String(value);
        if (!/[a-z]/.test(strValue)) return 'Must contain lowercase letters';
        if (!/[A-Z]/.test(strValue)) return 'Must contain uppercase letters';
        if (!/\d/.test(strValue)) return 'Must contain numbers';
        return undefined;
      },
    },
    confirmPassword: {
      required: true,
      custom: (value) => {
        if (String(value) !== password) return 'Passwords do not match';
        return undefined;
      },
    },
  };

  const loginValidationRules: ValidationRules = {
    email: {
      required: true,
      pattern: ValidationPatterns.email,
    },
    password: {
      required: true,
      minLength: 6,
    },
  };

  const validationRules = mode === 'signup' ? signupValidationRules : loginValidationRules;

  const { errors, validate, clearErrors } = useFormValidation(validationRules);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const formData: Record<string, string> =
      mode === 'signup'
        ? { email, password, name, confirmPassword }
        : { email, password };

    // Validate form
    if (!validate(formData)) {
      toastError('Please fix the errors below');
      return;
    }

    try {
      clearErrors();
      await execute(async () => {
        const submitData = mode === 'signup' 
          ? {
              email,
              password,
              name,
              confirmPassword,
            } as SignupData
          : {
              email,
              password,
            } as LoginData;
        await onSubmit(submitData);
        success(mode === 'login' ? 'Login successful!' : 'Signup successful!');
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'An error occurred';
      toastError(errorMessage);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Name Field (Signup only) */}
      {mode === 'signup' && (
        <div>
          <Input
            label="Full Name"
            type="text"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              clearErrors('name');
            }}
            placeholder="John Doe"
            disabled={isLoading || isSubmitting}
            error={errors.name}
          />
          {errors.name && (
            <p className="text-red-400 text-xs mt-1">{errors.name}</p>
          )}
        </div>
      )}

      {/* Email Field */}
      <div>
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            clearErrors('email');
          }}
          placeholder="you@example.com"
          disabled={isLoading || isSubmitting}
          error={errors.email}
        />
        {errors.email && (
          <p className="text-red-400 text-xs mt-1">{errors.email}</p>
        )}
      </div>

      {/* Password Field */}
      <div>
        <div className="relative">
          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              clearErrors('password');
            }}
            placeholder="••••••••"
            disabled={isLoading || isSubmitting}
            error={errors.password}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-4 top-10 text-white/60 hover:text-white"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
        {errors.password && (
          <p className="text-red-400 text-xs mt-1">{errors.password}</p>
        )}
      </div>

      {/* Confirm Password Field (Signup only) */}
      {mode === 'signup' && (
        <div>
          <div className="relative">
            <Input
              label="Confirm Password"
              type={showConfirmPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                clearErrors('confirmPassword');
              }}
              placeholder="••••••••"
              disabled={isLoading || isSubmitting}
              error={errors.confirmPassword}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-4 top-10 text-white/60 hover:text-white"
            >
              {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          {errors.confirmPassword && (
            <p className="text-red-400 text-xs mt-1">{errors.confirmPassword}</p>
          )}
        </div>
      )}

      {/* Server Error Display */}
      {error && (
        <div className="p-4 rounded-lg bg-red-500/20 border border-red-500/50 text-red-200 text-sm">
          {error.message}
        </div>
      )}

      {/* Submit Button */}
      <Button
        type="submit"
        variant="primary"
        fullWidth
        disabled={isLoading || isSubmitting}
      >
        {isLoading || isSubmitting
          ? 'Loading...'
          : mode === 'login'
            ? 'Sign In'
            : 'Create Account'}
      </Button>
    </form>
  );
};
