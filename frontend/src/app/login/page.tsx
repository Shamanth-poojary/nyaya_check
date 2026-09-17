'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { loginUser } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setErrorMessage(null);

    if (!email || !password) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setIsLoading(true);

    try {
      const res = await loginUser(email, password);
      setIsLoading(false);

      if (res.user) {
        localStorage.setItem('auth_user', JSON.stringify(res.user));
        try {
          const { saveOfficerProfile } = await import('@/lib/userProfile');
          saveOfficerProfile({
            name: res.user.name,
            email: res.user.email,
            role: res.user.role,
          });
        } catch {
          // ignore
        }
      }

      if (res.user?.role === 'admin') {
        router.push('/admin/dashboard');
      } else {
        router.push('/inspector/new-scan');
      }
    } catch (err: any) {
      setIsLoading(false);
      setErrorMessage(err.message || 'Invalid email or password.');
    }
  };

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
              href="/register"
              className="text-primary hover:text-primary-container text-body-sm font-semibold transition-colors"
            >
              Register
            </Link>
            <Link
              href="/"
              className="text-on-surface-variant hover:text-on-surface text-body-sm font-medium transition-colors"
            >
              Home
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="w-full pt-16 bg-surface flex-1 flex items-center justify-center">
        <div className="flex flex-col w-full min-h-[calc(100vh-4rem)] items-center justify-center px-gutter-mobile md:px-gutter py-space-xl">
          <div className="w-full max-w-[440px] flex flex-col items-center">
            {/* Title */}
            <div className="flex flex-col items-center text-center mb-space-lg">
              <div className="w-12 h-12 rounded-full bg-surface-container flex items-center justify-center mb-space-sm border border-outline-variant/30">
                <span className="material-symbols-outlined text-on-surface text-[24px]">
                  lock
                </span>
              </div>
              <h1 className="font-headline-md text-headline-md text-on-surface tracking-tight font-semibold">
                Sign In
              </h1>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                Enter your details to sign in to your account
              </p>
            </div>

            {/* Form Card */}
            <div className="w-full bg-surface-container-lowest rounded-xl p-space-xl shadow-sm relative border border-outline-variant/40">
              <form className="flex flex-col gap-space-md" onSubmit={handleLogin}>
                {/* Email */}
                <div className="flex flex-col gap-space-xs">
                  <label className="font-body-sm text-body-sm text-on-surface font-medium" htmlFor="email">
                    Email Address
                  </label>
                  <div className="relative flex items-center">
                    <input
                      autoComplete="email"
                      className="w-full bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/45 font-body-md text-body-md rounded-lg px-space-md py-2.5 transition-colors focus:bg-surface focus:outline-none border border-transparent focus:border-outline-variant/60"
                      id="email"
                      name="email"
                      placeholder="e.g. name@example.com"
                      required
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                    <span className="material-symbols-outlined absolute right-3 text-on-surface-variant text-[20px] pointer-events-none">
                      mail
                    </span>
                  </div>
                </div>

                {/* Password */}
                <div className="flex flex-col gap-space-xs">
                  <div className="flex items-center justify-between">
                    <label className="font-body-sm text-body-sm text-on-surface font-medium" htmlFor="password">
                      Password
                    </label>
                    <Link
                      className="font-body-sm text-xs text-primary hover:underline"
                      href="/forgot-password"
                    >
                      Forgot password?
                    </Link>
                  </div>
                  <div className="relative flex items-center">
                    <input
                      autoComplete="current-password"
                      className="w-full bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/45 font-body-md text-body-md rounded-lg px-space-md py-2.5 pr-10 transition-colors focus:bg-surface focus:outline-none border border-transparent focus:border-outline-variant/60"
                      id="password"
                      name="password"
                      placeholder="Enter your password"
                      required
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
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

                {/* Error Message */}
                {errorMessage && (
                  <div className="p-3 rounded-lg bg-error-container/30 border border-error/40 text-error font-body-sm text-body-sm text-center">
                    {errorMessage}
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
                    <span>{isLoading ? 'Signing In...' : 'Sign In'}</span>
                  </button>

                  <div className="flex justify-center text-center">
                    <Link
                      href="/register"
                      className="font-body-sm text-body-sm text-on-surface-variant hover:text-primary transition-colors"
                    >
                      Don&apos;t have an account? <span className="text-primary font-semibold underline">Register</span>
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
        </div>
      </main>
    </div>
  );
}
