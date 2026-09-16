'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { resetPassword } from '@/lib/api';

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tokenParam = searchParams.get('token') || '';

  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (tokenParam) {
      setToken(tokenParam);
    }
  }, [tokenParam]);

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!token.trim()) {
      setErrorMessage('Please enter your reset token.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    if (newPassword.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.');
      return;
    }

    setIsLoading(true);

    try {
      await resetPassword(token.trim(), newPassword);
      setIsLoading(false);
      setSuccessMessage('Password reset successfully! Redirecting to sign in...');
      setTimeout(() => {
        router.push('/login');
      }, 1200);
    } catch (err: any) {
      setIsLoading(false);
      setErrorMessage(err.message || 'Invalid or expired token. Please try again.');
    }
  };

  return (
    <div className="w-full max-w-[440px] flex flex-col items-center">
      {/* Title */}
      <div className="flex flex-col items-center text-center mb-space-lg">
        <div className="w-12 h-12 rounded-full bg-surface-container flex items-center justify-center mb-space-sm border border-outline-variant/30">
          <span className="material-symbols-outlined text-on-surface text-[24px]">
            key
          </span>
        </div>
        <h1 className="font-headline-md text-headline-md text-on-surface tracking-tight font-semibold">
          Reset Password
        </h1>
        <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
          Enter your reset token and your new password
        </p>
      </div>

      {/* Form Card */}
      <div className="w-full bg-surface-container-lowest rounded-xl p-space-xl shadow-sm relative border border-outline-variant/40">
        <form className="flex flex-col gap-space-md" onSubmit={handleReset}>
          {/* Token */}
          <div className="flex flex-col gap-space-xs">
            <label className="font-body-sm text-body-sm text-on-surface font-medium" htmlFor="token">
              Reset Token
            </label>
            <input
              className="w-full bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/45 font-body-md text-body-md rounded-lg px-space-md py-2.5 transition-colors focus:bg-surface focus:outline-none border border-transparent focus:border-outline-variant/60"
              id="token"
              name="token"
              placeholder="Paste your reset token"
              required
              type="text"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
          </div>

          {/* New Password */}
          <div className="flex flex-col gap-space-xs">
            <label className="font-body-sm text-body-sm text-on-surface font-medium" htmlFor="newPassword">
              New Password
            </label>
            <div className="relative flex items-center">
              <input
                autoComplete="new-password"
                className="w-full bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/45 font-body-md text-body-md rounded-lg px-space-md py-2.5 pr-10 transition-colors focus:bg-surface focus:outline-none border border-transparent focus:border-outline-variant/60"
                id="newPassword"
                name="newPassword"
                placeholder="At least 6 characters"
                required
                type={showPassword ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              <button
                aria-label="Toggle password visibility"
                className="absolute right-3 p-1 flex items-center justify-center text-on-surface-variant hover:text-on-surface transition-colors focus:outline-none cursor-pointer"
                onClick={() => setShowPassword(!showPassword)}
                type="button"
              >
                <span className="material-symbols-outlined text-[18px]">
                  {showPassword ? 'visibility' : 'visibility_off'}
                </span>
              </button>
            </div>
          </div>

          {/* Confirm Password */}
          <div className="flex flex-col gap-space-xs">
            <label className="font-body-sm text-body-sm text-on-surface font-medium" htmlFor="confirmPassword">
              Confirm New Password
            </label>
            <input
              autoComplete="new-password"
              className="w-full bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/45 font-body-md text-body-md rounded-lg px-space-md py-2.5 transition-colors focus:bg-surface focus:outline-none border border-transparent focus:border-outline-variant/60"
              id="confirmPassword"
              name="confirmPassword"
              placeholder="Re-enter new password"
              required
              type={showPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>

          {/* Messages */}
          {errorMessage && (
            <div className="p-3 rounded-lg bg-error-container/30 border border-error/40 text-error font-body-sm text-body-sm text-center">
              {errorMessage}
            </div>
          )}
          {successMessage && (
            <div className="p-3 rounded-lg bg-secondary-container/30 border border-secondary/40 text-secondary font-body-sm text-body-sm text-center">
              {successMessage}
            </div>
          )}

          {/* Submit Button */}
          <div className="pt-space-xs flex flex-col gap-space-md">
            <button
              className={`w-full font-headline-sm text-headline-sm text-[0.9375rem] rounded-lg py-3 px-space-lg flex items-center justify-center gap-space-sm transition-all cursor-pointer shadow-sm ${
                isLoading
                  ? 'bg-primary text-on-primary opacity-75 pointer-events-none'
                  : 'bg-primary text-on-primary hover:bg-inverse-surface active:scale-[0.99]'
              }`}
              type="submit"
            >
              <span>{isLoading ? 'Resetting Password...' : 'Reset Password'}</span>
            </button>

            <div className="flex justify-center text-center">
              <Link
                href="/login"
                className="font-body-sm text-body-sm text-on-surface-variant hover:text-primary transition-colors underline"
              >
                Back to Sign In
              </Link>
            </div>
          </div>
        </form>
      </div>

      {/* Footer */}
      <div className="mt-space-lg text-center">
        <span className="font-label-meta text-label-meta text-on-surface-variant/75">
          © 2025 NyayaCheck
        </span>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface min-h-screen flex flex-col justify-between">
      {/* Header */}
      <header className="fixed top-0 w-full z-50 bg-surface/90 backdrop-blur-xl shadow-xs border-b border-outline-variant/30">
        <div className="h-16 w-full px-gutter md:px-margin flex items-center justify-between max-w-[1600px] mx-auto">
          <Link href="/" className="flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-primary text-[24px]">gavel</span>
            <span className="font-headline-sm text-headline-sm text-on-surface leading-tight tracking-tight font-bold">
              NyayaCheck
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-on-surface-variant hover:text-on-surface text-body-sm font-medium transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="w-full pt-16 bg-surface flex-1 flex items-center justify-center">
        <div className="flex flex-col w-full min-h-[calc(100vh-4rem)] items-center justify-center px-gutter-mobile md:px-gutter py-space-xl">
          <Suspense fallback={<div>Loading...</div>}>
            <ResetPasswordForm />
          </Suspense>
        </div>
      </main>
    </div>
  );
}
