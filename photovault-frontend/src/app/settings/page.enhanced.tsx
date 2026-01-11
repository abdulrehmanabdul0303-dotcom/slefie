'use client';

import { useState } from 'react';
import { Button, Input } from '@/components/ui';
import { useToast } from '@/lib/hooks/useToast';
import { useFormValidation, ValidationPatterns, ValidationRules } from '@/lib/hooks/useFormValidation';
import { useAsyncOperation } from '@/lib/hooks/useAsyncOperation';
import { Mail, Lock, User } from 'lucide-react';

/**
 * Example: Settings/Profile Form with Full Validation
 * Demonstrates useFormValidation and useToast integration
 */
export default function ExampleFormPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    currentPassword: '',
    newPassword: '',
  });

  const { success, error: toastError } = useToast();
  const { isLoading, execute } = useAsyncOperation();

  // Define validation rules
  const validationRules: ValidationRules = {
    name: {
      required: true,
      minLength: 2,
      maxLength: 50,
    },
    email: {
      required: true,
      pattern: ValidationPatterns.email,
    },
    currentPassword: {
      required: true,
      minLength: 6,
    },
    newPassword: {
      required: true,
      minLength: 8,
      custom: (value) => {
        const strValue = String(value);
        if (!/[A-Z]/.test(strValue))
          return 'Must contain at least one uppercase letter';
        if (!/[a-z]/.test(strValue))
          return 'Must contain at least one lowercase letter';
        if (!/\d/.test(strValue)) return 'Must contain at least one number';
        return undefined;
      },
    },
  };

  const { errors, validate, clearErrors, setFieldError } =
    useFormValidation(validationRules);

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    clearErrors(field);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate all fields
    if (!validate(formData)) {
      toastError('Please fix validation errors');
      return;
    }

    try {
      await execute(async () => {
        // Simulate API call
        await new Promise((resolve) => setTimeout(resolve, 2000));

        // Check if password matches
        if (formData.newPassword === formData.currentPassword) {
          setFieldError(
            'newPassword',
            'New password must be different from current'
          );
          throw new Error('Password validation failed');
        }

        success('Profile updated successfully!');
      });
    } catch (err) {
      if (!(err instanceof Error && err.message.includes('validation'))) {
        toastError(
          err instanceof Error ? err.message : 'Update failed'
        );
      }
    }
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Profile Settings
          </h1>
          <p className="text-white/60">Update your account information</p>
        </div>

        {/* Form Card */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name Field */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                <User className="inline w-4 h-4 mr-2" />
                Full Name
              </label>
              <Input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="John Doe"
                disabled={isLoading}
              />
              {errors.name && (
                <p className="text-red-400 text-xs mt-2">{errors.name}</p>
              )}
              {!errors.name && formData.name && (
                <p className="text-green-400 text-xs mt-2">✓ Valid</p>
              )}
            </div>

            {/* Email Field */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                <Mail className="inline w-4 h-4 mr-2" />
                Email Address
              </label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="john@example.com"
                disabled={isLoading}
              />
              {errors.email && (
                <p className="text-red-400 text-xs mt-2">{errors.email}</p>
              )}
              {!errors.email && formData.email && (
                <p className="text-green-400 text-xs mt-2">✓ Valid</p>
              )}
            </div>

            {/* Divider */}
            <div className="border-t border-white/10 pt-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                Change Password
              </h3>
            </div>

            {/* Current Password */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                <Lock className="inline w-4 h-4 mr-2" />
                Current Password
              </label>
              <Input
                type="password"
                value={formData.currentPassword}
                onChange={(e) =>
                  handleChange('currentPassword', e.target.value)
                }
                placeholder="••••••••"
                disabled={isLoading}
              />
              {errors.currentPassword && (
                <p className="text-red-400 text-xs mt-2">
                  {errors.currentPassword}
                </p>
              )}
            </div>

            {/* New Password */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                <Lock className="inline w-4 h-4 mr-2" />
                New Password
              </label>
              <Input
                type="password"
                value={formData.newPassword}
                onChange={(e) => handleChange('newPassword', e.target.value)}
                placeholder="••••••••"
                disabled={isLoading}
              />
              {errors.newPassword && (
                <p className="text-red-400 text-xs mt-2">
                  {errors.newPassword}
                </p>
              )}
              {!errors.newPassword && formData.newPassword && (
                <div className="text-green-400 text-xs mt-2">
                  <p>✓ Uppercase letter</p>
                  <p>✓ Lowercase letter</p>
                  <p>✓ Number</p>
                  <p>✓ 8+ characters</p>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <div className="flex gap-3 pt-4">
              <Button
                type="submit"
                variant="primary"
                disabled={isLoading}
                fullWidth
              >
                {isLoading ? 'Saving...' : 'Save Changes'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setFormData({
                    name: '',
                    email: '',
                    currentPassword: '',
                    newPassword: '',
                  });
                  clearErrors();
                }}
                disabled={isLoading}
              >
                Cancel
              </Button>
            </div>
          </form>
        </div>

        {/* Info Box */}
        <div className="mt-8 bg-blue-500/20 border border-blue-500/50 rounded-xl p-4">
          <p className="text-blue-200 text-sm">
            💡 <strong>Tip:</strong> Passwords must contain uppercase, lowercase,
            and numbers. This is an example page showing form validation in action.
          </p>
        </div>
      </div>
    </div>
  );
}
