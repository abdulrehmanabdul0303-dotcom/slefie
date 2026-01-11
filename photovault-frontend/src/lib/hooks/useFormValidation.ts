import { useState, useCallback } from 'react';

export interface ValidationError {
  [key: string]: string;
}

export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: string | number | boolean) => string | undefined;
}

export interface ValidationRules {
  [key: string]: ValidationRule;
}

/**
 * Hook for form validation
 * Provides error tracking and validation logic
 */
export const useFormValidation = (rules: ValidationRules) => {
  const [errors, setErrors] = useState<ValidationError>({});

  const validate = useCallback(
    (formData: Record<string, string | number | boolean>): boolean => {
      const newErrors: ValidationError = {};

      Object.keys(rules).forEach((field) => {
        const rule = rules[field];
        const value = formData[field];

        // Required validation
        if (rule.required && (!value || value.toString().trim() === '')) {
          newErrors[field] = `${field} is required`;
          return;
        }

        if (!value) return;

        // Min length validation
        if (rule.minLength && value.toString().length < rule.minLength) {
          newErrors[field] = `${field} must be at least ${rule.minLength} characters`;
          return;
        }

        // Max length validation
        if (rule.maxLength && value.toString().length > rule.maxLength) {
          newErrors[field] = `${field} must not exceed ${rule.maxLength} characters`;
          return;
        }

        // Pattern validation
        if (rule.pattern && !rule.pattern.test(value.toString())) {
          newErrors[field] = `${field} format is invalid`;
          return;
        }

        // Custom validation
        if (rule.custom) {
          const customError = rule.custom(value);
          if (customError) {
            newErrors[field] = customError;
          }
        }
      });

      setErrors(newErrors);
      return Object.keys(newErrors).length === 0;
    },
    [rules]
  );

  const clearErrors = useCallback((field?: string) => {
    if (field) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    } else {
      setErrors({});
    }
  }, []);

  const setFieldError = useCallback((field: string, error: string) => {
    setErrors((prev) => ({ ...prev, [field]: error }));
  }, []);

  return { errors, validate, clearErrors, setFieldError };
};

/**
 * Common validation patterns
 */
export const ValidationPatterns = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/,
  username: /^[a-zA-Z0-9_-]{3,20}$/,
  phone: /^\+?[\d\s-()]{10,}$/,
};
