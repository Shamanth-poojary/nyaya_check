'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { registerUser } from '@/lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleRegister = async (event: React.FormEvent) => {
    event.preventDefault();
    setErrorMessage(null);

    if (!name || !email || !password) {
      setErrorMessage('Please fill in all required fields.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.');
      return;
    }

    setIsLoading(true);

    try {
      const res = await registerUser({
        name,
        email,
        password
      });

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

      router.push('/inspector/new-scan');
    } catch (err: any) {
      setIsLoading(false);
      setErrorMessage(err.message || 'Registration failed. Please check your details.');
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
              href="/login"
              className="text-primary hover:text-primary-container text-body-sm font-semibold transition-colors"
            >
              Sign In
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
                  person_add
                </span>
              </div>
              <h1 className="font-headline-md text-headline-md text-on-surface tracking-tight font-semibold">
                Create Account
              </h1>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                Enter your details to register a new account
              </p>
            </div>

            {/* Form Card */}
            <div className="w-full bg-surface-container-lowest rounded-xl p-space-xl shadow-sm relative border border-outline-variant/40">
              <form className="flex flex-col gap-space-md" onSubmit={handleRegister}>
                {/* Full Name */}
                <div className="flex flex-col gap-space-xs">
                  <label className="font-body-sm text-body-sm text-on-surface font-medium" htmlFor="fullName">
                    Full Name
                  </label>
                  <div className="relative flex items-center">
                    <input
                      className="w-full bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/45 font-body-md text-body-md rounded-lg px-space-md py-2.5 transition-colors focus:bg-surface focus:outline-none border border-transparent focus:border-outline-variant/60"
                      id="fullName"
                      name="name"
                      placeholder="e.g. Rajesh Kumar"
                      required
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                    <span className="material-symbols-outlined absolute right-3 text-on-surface-variant text-[20px] pointer-events-none">
                      person
                    </span>
                  </div>
                </div>

                {/* Email */}
                <div className="flex flex-col gap-space-xs">
                  <label className="font-body-sm text-body-sm text-on-surface font-medium" htmlFor="officialEmail">
                    Email Address
                  </label>
                  <div className="relative flex items-center">
                    <input
                      autoComplete="email"
                      className="w-full bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/45 font-body-md text-body-md rounded-lg px-space-md py-2.5 transition-colors focus:bg-surface focus:outline-none border border-transparent focus:border-outline-variant/60"
                      id="officialEmail"
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
                  <label className="font-body-sm text-body-sm text-on-surface font-medium" htmlFor="password">
                    Password
                  </label>
                  <div className="relative flex items-center">
                    <input
                      autoComplete="new-password"
                      className="w-full bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/45 font-body-md text-body-md rounded-lg px-space-md py-2.5 pr-10 transition-colors focus:bg-surface focus:outline-none border border-transparent focus:border-outline-variant/60"
                      id="password"
                      name="password"
                      placeholder="Minimum 6 characters"
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

                {/* Confirm Password */}
                <div className="flex flex-col gap-space-xs">
                  <label className="font-body-sm text-body-sm text-on-surface font-medium" htmlFor="confirmPassword">
                    Confirm Password
                  </label>
                  <input
                    autoComplete="new-password"
                    className="w-full bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/45 font-body-md text-body-md rounded-lg px-space-md py-2.5 transition-colors focus:bg-surface focus:outline-none border border-transparent focus:border-outline-variant/60"
                    id="confirmPassword"
                    name="confirmPassword"
                    placeholder="Re-enter password"
                    required
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                </div>

                {/* Error Banner */}
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
                    <span>{isLoading ? 'Creating Account...' : 'Create Account'}</span>
                  </button>

                  <div className="flex items-center justify-between text-center pt-1 font-body-sm text-body-sm">
                    <Link
                      href="/login"
                      className="text-on-surface-variant hover:text-primary transition-colors"
                    >
                      Already have an account? <span className="text-primary font-semibold underline">Sign In</span>
                    </Link>
                    <Link
                      href="/forgot-password"
                      className="text-on-surface-variant hover:text-primary transition-colors underline"
                    >
                      Forgot password?
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
