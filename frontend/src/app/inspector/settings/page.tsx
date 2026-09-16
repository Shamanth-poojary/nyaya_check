'use client';

import React, { useState } from 'react';
import { Toast } from '@/components/ui/Toast';

export default function InspectorSettingsPage() {
  const [showToast, setShowToast] = useState(false);
  const [offlineSync, setOfflineSync] = useState(true);
  const [avatar, setAvatar] = useState(
    'https://lh3.googleusercontent.com/aida-public/AB6AXuCl76By1vtUiTeEHRzV5GW2Xa13xQiWRLhXs5XP6pvqxaaJofBodxznf0MUIRhZu3Ozw6FCKJNbV9-0CTcWfyfjnadwGG8PO7W5QCQU7B7P356qyfSCjD1BaZ9OjnLtrw2C8yJi0TwWa_e0kakumnqnV8RFNqdgIzbGQnLJ6RljUBncYzgVk3FTfT41VrEY2PH98XEBaN0cJK7BWNRmGaX6KMcfzrgdGc3JIEOk6IllLFn4akOrr5_czQ'
  );

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setAvatar(event.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3500);
  };

  return (
    <div className="flex flex-col w-full pb-16">
      {/* Header */}
      <div className="py-8 flex flex-col gap-1 border-b border-surface-container-highest">
        <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight font-semibold">
          Settings
        </h1>
        <p className="font-body-md text-body-md text-on-surface-variant">
          Manage your officer profile, contact details, and account security.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-10 mt-8">
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
          {/* Section 1: Officer Identification (7 cols) */}
          <section className="xl:col-span-7 flex flex-col gap-6 bg-surface-container-low p-6 lg:p-8 rounded-2xl shadow-sm">
            <div className="flex items-center justify-between pb-4 border-b border-surface-container-high">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-primary text-[24px]">badge</span>
                <div>
                  <h2 className="font-headline-sm text-headline-sm text-primary font-semibold">
                    Officer Official Identification
                  </h2>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">
                    Gazetted field inspector credentials under Legal Metrology Act, 2009.
                  </p>
                </div>
              </div>
              <span className="font-label-code text-label-code bg-surface-container-high px-2.5 py-1 rounded text-on-surface font-semibold">
                ENFORCER ROLE
              </span>
            </div>

            {/* Photo Identification */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 bg-surface p-4 rounded-xl border border-outline-variant/30">
              <div className="relative group">
                <div className="w-24 h-24 rounded-xl overflow-hidden bg-surface-container-highest flex-shrink-0">
                  <img
                    src={avatar}
                    alt="Officer portrait"
                    className="w-full h-full object-cover object-top"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-2 min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-body-md text-body-md font-semibold text-primary">
                    Departmental Portrait File
                  </span>
                  <span className="font-label-meta text-label-meta text-outline uppercase bg-surface-container px-1.5 py-0.5 rounded">
                    ICAO Compliant
                  </span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Front-facing portrait embedded in digital inspection memos & spot summons.
                </p>
                <div className="flex flex-wrap items-center gap-3 mt-1">
                  <label className="cursor-pointer inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container-highest transition-colors font-body-sm text-body-sm font-medium text-on-surface shadow-xs">
                    <span className="material-symbols-outlined text-[18px]">upload_file</span>
                    <span>Upload New Headshot</span>
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleImageChange}
                    />
                  </label>
                </div>
              </div>
            </div>

            {/* Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="flex flex-col gap-1.5">
                <label className="font-label-meta text-label-meta uppercase tracking-wider text-outline">
                  Gazetted Full Name
                </label>
                <div className="relative">
                  <input
                    className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                    type="text"
                    defaultValue="S.K. Ranganathan"
                  />
                  <span className="material-symbols-outlined absolute right-3 top-2.5 text-[20px] text-secondary">
                    verified
                  </span>
                </div>
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  Matches Central Gazette Reg No. #CG-2018/88392
                </span>
              </div>

              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-label-meta text-label-meta uppercase tracking-wider text-outline">
                    Zonal Badge Serial
                  </label>
                  <span className="font-label-meta text-label-meta text-error font-semibold flex items-center gap-0.5">
                    <span className="material-symbols-outlined text-[13px]">lock</span> LOCKED
                  </span>
                </div>
                <input
                  className="w-full bg-surface-container-highest/80 text-on-surface font-label-code text-label-code px-3.5 py-2.5 rounded-lg cursor-not-allowed select-none border border-outline-variant/40"
                  readOnly
                  type="text"
                  defaultValue="LM-DL-88392"
                />
                <span className="font-body-sm text-body-sm text-outline">
                  Statutory ID bound to DL Northern Zonal Registry.
                </span>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-meta text-label-meta uppercase tracking-wider text-outline">
                  Encrypted Terminal Mobile
                </label>
                <input
                  className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                  type="tel"
                  defaultValue="+91 98402 11983"
                />
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  Receives OTP challenges for seized custody receipts.
                </span>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-meta text-label-meta uppercase tracking-wider text-outline">
                  Government Directory Email
                </label>
                <input
                  className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                  type="email"
                  defaultValue="sk.ranganathan@delhi.gov.in"
                />
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  Official reports & court dockets dispatch here.
                </span>
              </div>
            </div>

            {/* Jurisdiction banner */}
            <div className="mt-2 p-4 rounded-xl bg-surface flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-outline-variant/30">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center text-primary">
                  <span className="material-symbols-outlined text-[22px]">apartment</span>
                </div>
                <div className="flex flex-col">
                  <span className="font-body-sm text-body-sm font-semibold text-primary">
                    Assigned Jurisdiction: North Delhi Zone II
                  </span>
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    Sub-divisional Magistracy: Civil Lines, Tis Hazari Complex
                  </span>
                </div>
              </div>
              <span className="font-label-code text-label-code bg-secondary-container text-on-secondary-container px-2.5 py-1 rounded font-medium">
                ACTIVE COMMISSION
              </span>
            </div>
          </section>

          {/* Section 2: Password & Offline Sync (5 cols) */}
          <section className="xl:col-span-5 flex flex-col gap-6 bg-surface-container-low p-6 lg:p-8 rounded-2xl shadow-sm self-start">
            <div className="flex items-center gap-3 pb-2 border-b border-surface-container-high">
              <span className="material-symbols-outlined text-primary text-[22px]">lock</span>
              <div>
                <h2 className="font-headline-sm text-headline-sm text-primary font-semibold">
                  Change Password
                </h2>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Update your portal access credentials.
                </p>
              </div>
            </div>

            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="font-body-sm text-body-sm font-medium text-on-surface">
                  Current Password
                </label>
                <input
                  className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                  placeholder="••••••••••••"
                  type="password"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-body-sm text-body-sm font-medium text-on-surface">
                  New Password
                </label>
                <input
                  className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                  placeholder="Enter new password"
                  type="password"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-body-sm text-body-sm font-medium text-on-surface">
                  Confirm New Password
                </label>
                <input
                  className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                  placeholder="Re-type new password"
                  type="password"
                />
              </div>
            </div>

            <div className="pt-2 border-t border-surface-container-high">
              <div className="flex items-center justify-between py-1">
                <div className="flex flex-col">
                  <span className="font-body-sm text-body-sm font-medium text-primary">
                    Auto-sync offline records
                  </span>
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    Sync inspection drafts when connection resumes
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={offlineSync}
                  onChange={(e) => setOfflineSync(e.target.checked)}
                  className="w-5 h-5 accent-primary cursor-pointer"
                />
              </div>
            </div>
          </section>
        </div>

        {/* Master Action Bar */}
        <div className="flex items-center justify-end gap-3 pt-6 border-t border-surface-container-high">
          <button
            type="button"
            className="px-5 py-2.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface font-body-md text-body-md font-medium transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-6 py-2.5 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-body-md text-body-md font-semibold transition-all shadow-sm cursor-pointer"
          >
            Save Changes
          </button>
        </div>
      </form>

      <Toast
        show={showToast}
        title="Parameters Synchronised"
        description="Officer profile & device parameters written to cryptographic ledger."
      />
    </div>
  );
}
