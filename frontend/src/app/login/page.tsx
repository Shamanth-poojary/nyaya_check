'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [role, setRole] = useState<'admin' | 'inspector'>('inspector');
  const [email, setEmail] = useState('sk.ranganathan@delhi.gov.in');
  const [password, setPassword] = useState('••••••••••••••••');
  const [showPassword, setShowPassword] = useState(false);
  const [btnText, setBtnText] = useState('Sign In');
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleRoleChange = (newRole: 'admin' | 'inspector') => {
    setRole(newRole);
    if (newRole === 'admin') {
      setEmail('controller.delhi@legalmetrology.gov.in');
    } else {
      setEmail('sk.ranganathan@delhi.gov.in');
    }
  };

  const handleLogin = (event: React.FormEvent) => {
    event.preventDefault();
    setBtnText('Verifying Credentials...');
    setIsAuthorizing(true);

    setTimeout(() => {
      setBtnText('Access Authorized');
      setIsSuccess(true);
      setTimeout(() => {
        if (role === 'admin') {
          router.push('/admin/dashboard');
        } else {
          router.push('/inspector/new-scan');
        }
      }, 700);
    }, 900);
  };

  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface min-h-screen flex flex-col justify-between">
      {/* Header */}
      <header className="fixed top-0 w-full z-50 bg-surface/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] border-b border-outline-variant/30">
        <div className="h-16 w-full px-gutter md:px-margin flex items-center justify-between max-w-[1600px] mx-auto">
          <Link href="/" className="flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-primary text-[24px]">gavel</span>
            <div className="flex flex-col">
              <span className="font-headline-sm text-headline-sm text-on-surface leading-tight tracking-tight font-bold">
                NyayaCheck
              </span>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-on-surface-variant hover:text-on-surface text-body-sm font-medium transition-colors"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </header>

      {/* Main Form Container */}
      <main className="w-full pt-16 bg-surface flex-1 flex items-center justify-center">
        <div className="flex flex-col w-full min-h-[calc(100vh-4rem)] items-center justify-center px-gutter-mobile md:px-gutter py-space-xl">
          <div className="w-full max-w-[460px] flex flex-col items-center">
            {/* Institutional Crest & Authority Header */}
            <div className="flex flex-col items-center text-center mb-space-lg">
              <div className="w-14 h-14 rounded-full bg-surface-container flex items-center justify-center mb-space-md shadow-sm border border-outline-variant/30">
                <span className="material-symbols-outlined text-on-surface text-[28px]">
                  assured_workload
                </span>
              </div>
              <h1 className="font-headline-md text-headline-md text-on-surface tracking-tight mb-1 font-semibold">
                Sign in to NyayaCheck
              </h1>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Statutory Regulatory &amp; Field Enforcement Gateway
              </p>
            </div>

            {/* Role Switcher Pill */}
            <div className="w-full grid grid-cols-2 gap-1 p-1 bg-surface-container-high rounded-xl border border-outline-variant/40 mb-space-md font-body-sm text-body-sm">
              <button
                type="button"
                onClick={() => handleRoleChange('inspector')}
                className={`py-2 rounded-lg font-medium transition-all cursor-pointer ${
                  role === 'inspector'
                    ? 'bg-surface text-primary shadow-xs font-semibold'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                Field Inspector
              </button>
              <button
                type="button"
                onClick={() => handleRoleChange('admin')}
                className={`py-2 rounded-lg font-medium transition-all cursor-pointer ${
                  role === 'admin'
                    ? 'bg-surface text-primary shadow-xs font-semibold'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                Org Admin
              </button>
            </div>

            {/* Paper Card Container */}
            <div className="w-full bg-surface-container-lowest rounded-xl p-space-xl shadow-sm relative border border-outline-variant/40">
              <form className="flex flex-col gap-space-lg" onSubmit={handleLogin}>
                {/* Official Email Field */}
                <div className="flex flex-col gap-space-xs">
                  <div className="flex items-center justify-between">
                    <label className="font-headline-sm text-headline-sm text-on-surface text-[0.875rem] font-medium tracking-tight" htmlFor="officialEmail">
                      Email
                    </label>
                  </div>
                  <div className="relative flex items-center">
                    <input
                      autoComplete="email"
                      className="w-full bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/45 font-body-md text-body-md rounded-lg px-space-md py-3 transition-colors focus:bg-surface focus:outline-none border border-transparent focus:border-outline-variant/60"
                      id="officialEmail"
                      name="email"
                      placeholder="officer.id@gov.in or compliance@entity.org"
                      required
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                    <span className="material-symbols-outlined absolute right-3 text-on-surface-variant text-[20px] pointer-events-none">
                      alternate_email
                    </span>
                  </div>
                </div>

                {/* Password Field */}
                <div className="flex flex-col gap-space-xs">
                  <div className="flex items-center justify-between">
                    <label className="font-headline-sm text-headline-sm text-on-surface text-[0.875rem] font-medium tracking-tight" htmlFor="officialPassword">
                      Password
                    </label>
                  </div>
                  <div className="relative flex items-center">
                    <input
                      autoComplete="current-password"
                      className="w-full bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/45 font-body-md text-body-md rounded-lg px-space-md py-3 pr-10 transition-colors focus:bg-surface focus:outline-none border border-transparent focus:border-outline-variant/60"
                      id="officialPassword"
                      name="password"
                      placeholder="••••••••••••••••"
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
                      <span className="material-symbols-outlined text-[20px]">
                        {showPassword ? 'visibility' : 'visibility_off'}
                      </span>
                    </button>
                  </div>
                </div>

                {/* Primary Submit Button */}
                <div className="pt-space-xs flex flex-col gap-space-md">
                  <button
                    className={`w-full font-headline-sm text-headline-sm text-[0.9375rem] rounded-lg py-3.5 px-space-lg flex items-center justify-center gap-space-sm active:scale-[0.99] transition-all cursor-pointer shadow-sm ${
                      isSuccess
                        ? 'bg-secondary text-on-secondary'
                        : isAuthorizing
                        ? 'bg-primary text-on-primary opacity-80 pointer-events-none'
                        : 'bg-primary text-on-primary hover:bg-inverse-surface'
                    }`}
                    type="submit"
                  >
                    <span>{btnText}</span>
                  </button>

                  {/* Password Recovery Action */}
                  <div className="flex justify-center">
                    <a
                      className="font-body-sm text-body-sm text-on-surface-variant hover:text-primary transition-colors underline decoration-outline-variant underline-offset-4 focus:outline-none"
                      href="#recovery"
                      onClick={(e) => { e.preventDefault(); alert('Password reset verification token dispatched to registered departmental mobile.'); }}
                    >
                      Forgot password?
                    </a>
                  </div>
                </div>
              </form>
            </div>

            {/* Statutory System Footer Metadata */}
            <div className="mt-space-xl flex flex-col items-center text-center gap-space-xs">
              <span className="font-label-meta text-label-meta text-on-surface-variant/75">
                © 2025 NyayaCheck • Section 65B Certified Portal
              </span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
