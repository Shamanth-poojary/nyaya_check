const fs = require('fs');

// src/app/page.tsx - Landing Page
const landingCode = `'use client';

import React from 'react';
import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-surface flex flex-col">
      {/* Top Gazette Notice Banner */}
      <div className="bg-primary text-on-primary py-2 px-space-md border-b border-outline-variant/30 text-center">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 font-label-meta text-label-meta tracking-wider uppercase">
          <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
          <span>Legal Metrology (Packaged Commodities) Enforcement Directive 2025</span>
          <span className="hidden sm:inline text-outline-variant">•</span>
          <span className="hidden sm:inline text-outline-variant/80">Gazette Notified Regulatory Suite</span>
        </div>
      </div>

      {/* Navigation */}
      <header className="h-20 border-b border-outline-variant/30 px-space-lg max-w-7xl mx-auto w-full flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-primary text-on-primary flex items-center justify-center font-headline-sm text-headline-sm font-semibold">
            §
          </div>
          <div className="flex flex-col">
            <span className="font-headline-md text-headline-md tracking-tight text-primary font-bold">
              NyayaCheck
            </span>
            <span className="font-label-meta text-label-meta text-on-surface-variant uppercase tracking-wider">
              Legal Metrology Intelligence
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 sm:gap-space-md">
          <Link
            href="/login"
            className="px-4 py-2 text-on-surface font-body-sm text-body-sm font-medium hover:text-primary transition-colors"
          >
            Officer Sign In
          </Link>
          <Link
            href="/admin/dashboard"
            className="px-5 py-2.5 bg-primary text-on-primary rounded-xl font-body-sm text-body-sm font-semibold hover:bg-primary-container shadow-sm transition-all active:scale-[0.98]"
          >
            Access Portal
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-space-lg py-space-xl flex flex-col gap-space-xl">
        <section className="flex flex-col lg:flex-row items-center justify-between gap-space-xl pt-4">
          <div className="flex flex-col gap-space-md max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container border border-outline-variant/40 text-on-surface-variant w-fit">
              <span className="w-2 h-2 rounded-full bg-secondary"></span>
              <span className="font-label-code text-label-code font-semibold uppercase">
                Section 65B Electronic Admissibility
              </span>
            </div>

            <h1 className="font-headline-display text-4xl sm:text-5xl lg:text-6xl text-primary font-semibold tracking-tight leading-[1.1]">
              Automated Statutory Compliance for Legal Metrology
            </h1>

            <p className="font-body-lg text-body-lg text-on-surface-variant leading-relaxed">
              Verify packaged commodity label declarations, detect numeral height tolerances, and issue tamper-evident digital panchnama dossiers under the Legal Metrology Act, 2009.
            </p>

            <div className="flex flex-wrap items-center gap-space-md pt-2">
              <Link
                href="/admin/dashboard"
                className="px-6 py-3.5 rounded-xl bg-primary text-on-primary font-body-md text-body-md font-semibold hover:bg-primary-container shadow-md transition-all flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-[20px]">space_dashboard</span>
                <span>Org Admin Portal</span>
              </Link>
              <Link
                href="/inspector/new-scan"
                className="px-6 py-3.5 rounded-xl bg-surface-container-high border border-outline-variant/60 text-on-surface font-body-md text-body-md font-medium hover:bg-surface-container-highest transition-all flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-[20px]">photo_camera</span>
                <span>Field Inspector Scanner</span>
              </Link>
            </div>

            {/* Regulatory badge strip */}
            <div className="flex items-center gap-6 pt-4 text-on-surface-variant font-label-meta text-label-meta uppercase tracking-wider">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-secondary text-[16px]">verified</span>
                <span>Rule 14 Verified</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-secondary text-[16px]">gavel</span>
                <span>PCR 2011 Compliant</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-secondary text-[16px]">lock</span>
                <span>SHA-256 Merkle Ledger</span>
              </div>
            </div>
          </div>

          {/* Right Hero Graphic Card */}
          <div className="w-full lg:w-[480px] bg-surface-container-low p-space-lg rounded-2xl border border-outline-variant/40 shadow-sm flex flex-col gap-space-md">
            <div className="flex items-center justify-between border-b border-outline-variant/30 pb-space-sm">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-secondary"></span>
                <span className="font-label-code text-label-code font-bold text-primary">
                  LIVE INSPECTION DOSSIER
                </span>
              </div>
              <span className="px-2 py-0.5 rounded bg-secondary-container text-on-secondary-container font-label-code text-label-code font-semibold">
                Pass: 98.4%
              </span>
            </div>

            <div className="bg-surface p-space-md rounded-xl border border-outline-variant/30 space-y-2">
              <span className="font-label-meta text-label-meta uppercase text-on-surface-variant">Sample Verified SKU</span>
              <p className="font-headline-sm text-headline-sm font-semibold text-primary">
                Aashirvaad Superior MP Sharbati Atta 5kg
              </p>
              <span className="font-label-code text-label-code text-on-surface-variant block">
                SKU: 8901030882190 • Zone: North Delhi Z-04
              </span>
            </div>

            <div className="space-y-2 font-body-sm text-body-sm">
              <div className="flex justify-between py-1 border-b border-outline-variant/20">
                <span className="text-on-surface-variant">MRP & USP Declaration</span>
                <span className="font-semibold text-secondary flex items-center gap-1">
                  <span className="material-symbols-outlined text-[15px]">check_circle</span> ₹ 345.00 (₹ 69/kg)
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-outline-variant/20">
                <span className="text-on-surface-variant">Numeral Height (Rule 14)</span>
                <span className="font-semibold text-secondary flex items-center gap-1">
                  <span className="material-symbols-outlined text-[15px]">check_circle</span> 4.20 mm (≥ 4.0 mm)
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-outline-variant/20">
                <span className="text-on-surface-variant">Net Weight & Tolerance</span>
                <span className="font-semibold text-secondary flex items-center gap-1">
                  <span className="material-symbols-outlined text-[15px]">check_circle</span> 5.002 kg (MPE ± 15g)
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-on-surface-variant">Digital Signature Seal</span>
                <span className="font-label-code text-label-code text-on-surface">sha256:7a9e...4b1c</span>
              </div>
            </div>

            <Link
              href="/inspector/new-scan"
              className="w-full py-2.5 rounded-xl bg-primary text-on-primary text-center font-body-sm font-semibold hover:bg-primary-container transition-colors shadow-xs"
            >
              Test Live Scanner
            </Link>
          </div>
        </section>

        {/* 4-Step Statutory Protocol Grid */}
        <section className="py-space-lg border-t border-outline-variant/30 space-y-space-lg">
          <div className="space-y-1">
            <span className="font-label-meta text-label-meta uppercase tracking-wider text-secondary font-semibold">
              Statutory Architecture
            </span>
            <h2 className="font-headline-lg text-headline-lg text-primary font-semibold">
              Four-Phase Compliance Enforcement Pipeline
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Designed according to standards prescribed by the Central Directorate of Legal Metrology.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-space-md">
            <div className="bg-surface-container-low p-space-lg rounded-xl border border-outline-variant/30 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center text-primary font-bold font-headline-sm">
                01
              </div>
              <h3 className="font-headline-sm text-headline-sm font-semibold text-primary">
                Optical PDP Capture
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                High-resolution label scanning with automatic perspective correction and optical character extraction.
              </p>
            </div>

            <div className="bg-surface-container-low p-space-lg rounded-xl border border-outline-variant/30 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center text-primary font-bold font-headline-sm">
                02
              </div>
              <h3 className="font-headline-sm text-headline-sm font-semibold text-primary">
                Rule 14 Verification
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Sub-millimeter numeral height measurement and mandatory declaration presence checks against Table-I thresholds.
              </p>
            </div>

            <div className="bg-surface-container-low p-space-lg rounded-xl border border-outline-variant/30 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center text-primary font-bold font-headline-sm">
                03
              </div>
              <h3 className="font-headline-sm text-headline-sm font-semibold text-primary">
                Digital Panchnama
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Automatic generation of evidentiary inspection dossiers with timestamped geo-coordinates and inspector signature.
              </p>
            </div>

            <div className="bg-surface-container-low p-space-lg rounded-xl border border-outline-variant/30 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center text-primary font-bold font-headline-sm">
                04
              </div>
              <h3 className="font-headline-sm text-headline-sm font-semibold text-primary">
                Immutable Section 65B Log
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Cryptographic Merkle tree ledger ensuring court-admissible, tamper-evident audit logs across all zonal terminals.
              </p>
            </div>
          </div>
        </section>

        {/* Portals Quick Links */}
        <section className="bg-surface-container-low p-space-xl rounded-2xl border border-outline-variant/40 flex flex-col md:flex-row items-center justify-between gap-space-lg">
          <div className="space-y-1">
            <h3 className="font-headline-md text-headline-md text-primary font-semibold">
              Ready to access the statutory enforcement environment?
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Select your jurisdictional portal or sign in with your gazetted inspector credentials.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/admin/dashboard"
              className="px-5 py-2.5 bg-primary text-on-primary rounded-xl font-body-sm font-semibold hover:bg-primary-container shadow-sm transition-colors"
            >
              Org Admin Dashboard
            </Link>
            <Link
              href="/inspector/new-scan"
              className="px-5 py-2.5 bg-surface border border-outline-variant/60 text-on-surface rounded-xl font-body-sm font-semibold hover:bg-surface-container-high shadow-sm transition-colors"
            >
              Field Inspector Scanner
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-outline-variant/30 py-space-lg bg-surface-container-low/50">
        <div className="max-w-7xl mx-auto px-space-lg flex flex-col sm:flex-row items-center justify-between gap-4 font-body-sm text-body-sm text-on-surface-variant">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary text-[18px]">verified</span>
            <span>NyayaCheck Statutory Enforcement Portal • Legal Metrology Act, 2009</span>
          </div>
          <span className="font-label-code text-label-code">
            Release v2.5.4 • IN-DL Gazette Profile
          </span>
        </div>
      </footer>
    </div>
  );
}
`;
fs.writeFileSync('src/app/page.tsx', landingCode);

// src/app/login/page.tsx - Login Page
const loginCode = `'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [role, setRole] = useState<'admin' | 'inspector'>('admin');
  const [email, setEmail] = useState('controller.delhi@legalmetrology.gov.in');
  const [password, setPassword] = useState('••••••••••••');

  const handleRoleChange = (newRole: 'admin' | 'inspector') => {
    setRole(newRole);
    if (newRole === 'admin') {
      setEmail('controller.delhi@legalmetrology.gov.in');
    } else {
      setEmail('sk.ranganathan@delhi.gov.in');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (role === 'admin') {
      router.push('/admin/dashboard');
    } else {
      router.push('/inspector/new-scan');
    }
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-between">
      {/* Top Banner */}
      <header className="h-16 px-space-lg border-b border-outline-variant/30 flex items-center justify-between bg-surface-container-low">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-primary text-on-primary flex items-center justify-center font-headline-sm text-headline-sm font-semibold">
            §
          </div>
          <span className="font-headline-md text-headline-md font-bold text-primary tracking-tight">
            NyayaCheck
          </span>
        </Link>
        <span className="font-label-meta text-label-meta uppercase text-on-surface-variant font-medium">
          Official Enforcement Gateway
        </span>
      </header>

      {/* Main Login Card */}
      <main className="flex-1 flex items-center justify-center p-space-md">
        <div className="w-full max-w-md bg-surface-container-low p-space-xl rounded-2xl border border-outline-variant/40 shadow-sm flex flex-col gap-space-lg">
          <div className="flex flex-col items-center text-center space-y-1">
            <div className="w-12 h-12 rounded-xl bg-primary text-on-primary flex items-center justify-center mb-2 shadow-sm">
              <span className="material-symbols-outlined text-[26px]">policy</span>
            </div>
            <h1 className="font-headline-md text-headline-md font-bold text-primary">
              Official Sign In
            </h1>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Statutory Portal for Legal Metrology Officers & Org Admins
            </p>
          </div>

          {/* Role Switcher */}
          <div className="grid grid-cols-2 gap-1 p-1 bg-surface rounded-xl border border-outline-variant/40 font-body-sm text-body-sm">
            <button
              type="button"
              onClick={() => handleRoleChange('admin')}
              className={\`py-2 rounded-lg font-medium transition-all cursor-pointer \${
                role === 'admin'
                  ? 'bg-primary text-on-primary shadow-xs font-semibold'
                  : 'text-on-surface-variant hover:text-on-surface'
              }\`}
            >
              Org Admin
            </button>
            <button
              type="button"
              onClick={() => handleRoleChange('inspector')}
              className={\`py-2 rounded-lg font-medium transition-all cursor-pointer \${
                role === 'inspector'
                  ? 'bg-primary text-on-primary shadow-xs font-semibold'
                  : 'text-on-surface-variant hover:text-on-surface'
              }\`}
            >
              Field Inspector
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-space-md">
            <div className="space-y-1.5">
              <label className="block font-body-sm text-body-sm font-medium text-on-surface">
                {role === 'admin' ? 'Department Email / Official ID' : 'Inspector Email / Badge ID'}
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 rounded-lg bg-surface border border-outline-variant/60 font-body-md text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary shadow-xs"
                />
                <span className="material-symbols-outlined absolute left-3 top-3 text-on-surface-variant text-[18px]">
                  {role === 'admin' ? 'business' : 'badge'}
                </span>
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="block font-body-sm text-body-sm font-medium text-on-surface">
                  Password
                </label>
                <a href="#" className="font-label-meta text-label-meta text-on-surface-variant hover:text-primary underline">
                  Forgot?
                </a>
              </div>
              <div className="relative">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 rounded-lg bg-surface border border-outline-variant/60 font-body-md text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary shadow-xs"
                />
                <span className="material-symbols-outlined absolute left-3 top-3 text-on-surface-variant text-[18px]">
                  lock
                </span>
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-3 bg-primary text-on-primary rounded-xl font-body-md text-body-md font-semibold hover:bg-primary-container shadow-sm transition-all active:scale-[0.99] cursor-pointer"
            >
              Sign In to {role === 'admin' ? 'Org Admin Portal' : 'Field Scanner'}
            </button>
          </form>

          <div className="p-3 rounded-lg bg-surface border border-outline-variant/30 flex items-center gap-2 text-on-surface-variant font-label-meta text-label-meta">
            <span className="material-symbols-outlined text-secondary text-[16px]">verified_user</span>
            <span>Section 65B certified handshake & cryptographic session.</span>
          </div>
        </div>
      </main>

      {/* Bottom Legal Notice */}
      <footer className="py-4 text-center text-on-surface-variant font-label-meta text-label-meta border-t border-outline-variant/30 bg-surface-container-low">
        Authorized use only under the Legal Metrology Act, 2009.
      </footer>
    </div>
  );
}
`;
fs.writeFileSync('src/app/login/page.tsx', loginCode);

console.log('Landing and Login pages written');
