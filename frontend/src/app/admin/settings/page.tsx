'use client';

import React, { useState } from 'react';
import { Toast } from '@/components/ui/Toast';
import { changePassword } from '@/lib/api';

export default function AdminSettingsPage() {
  const [showToast, setShowToast] = useState(false);
  const [toastTitle, setToastTitle] = useState('Configuration Synchronized');
  const [toastDesc, setToastDesc] = useState('Changes applied to statutory database instance.');
  const [twoFactor, setTwoFactor] = useState(true);
  const [deficitAlerts, setDeficitAlerts] = useState(true);
  const [weeklyDigest, setWeeklyDigest] = useState(true);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword || currentPassword) {
      if (!currentPassword) {
        setToastTitle('Password Error');
        setToastDesc('Please enter your current password.');
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3500);
        return;
      }
      if (newPassword !== confirmPassword) {
        setToastTitle('Password Error');
        setToastDesc('New password and confirmation do not match.');
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3500);
        return;
      }
      try {
        await changePassword(currentPassword, newPassword);
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setToastTitle('Password Updated');
        setToastDesc('Security credentials successfully synchronized.');
      } catch (err: any) {
        setToastTitle('Update Failed');
        setToastDesc(err.message || 'Failed to update password.');
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3500);
        return;
      }
    } else {
      setToastTitle('Configuration Synchronized');
      setToastDesc('Changes applied to statutory database instance.');
    }
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3500);
  };

  return (
    <div className="flex flex-col w-full p-margin max-w-[1500px] mx-auto space-y-space-xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-md pb-space-md border-b border-outline-variant/40">
        <div className="space-y-1">
          <h2 className="font-headline-lg text-headline-lg text-on-surface tracking-tight font-semibold">
            Organization Settings
          </h2>
          <p className="font-body-md text-body-md text-on-surface-variant">
            Manage organization profile, security credentials, and department notifications.
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-space-lg max-w-4xl">
        {/* Card 1: Org Profile */}
        <section className="bg-surface-container-low rounded-xl border border-outline-variant/40 p-space-lg space-y-space-md shadow-sm">
          <div className="border-b border-outline-variant/30 pb-space-sm">
            <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
              Organization Profile
            </h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Department details and jurisdictional registration.
            </p>
          </div>
          <div className="space-y-space-md">
            <div className="space-y-1.5">
              <label className="block font-body-sm text-body-sm font-medium text-on-surface">
                Organization Name
              </label>
              <input
                className="w-full px-space-md py-2.5 rounded-lg bg-surface border border-outline-variant/60 focus:border-primary focus:outline-none font-body-md text-body-md text-on-surface transition-all"
                type="text"
                defaultValue="Directorate of Legal Metrology & Standards — Northern Zonal Division"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
              <div className="space-y-1.5">
                <label className="block font-body-sm text-body-sm font-medium text-on-surface">
                  Statutory Order No.
                </label>
                <input
                  className="w-full px-space-md py-2.5 rounded-lg bg-surface border border-outline-variant/60 focus:border-primary focus:outline-none font-label-code text-label-code text-on-surface transition-all"
                  type="text"
                  defaultValue="DLM-DEL-2021-REG-0994"
                />
              </div>
              <div className="space-y-1.5">
                <label className="block font-body-sm text-body-sm font-medium text-on-surface">
                  Jurisdiction / Region
                </label>
                <select className="w-full px-space-md py-2.5 rounded-lg bg-surface border border-outline-variant/60 focus:border-primary focus:outline-none font-body-md text-body-md text-on-surface appearance-none transition-all cursor-pointer">
                  <option>National Capital Territory of Delhi (All Districts)</option>
                  <option>NCR Zonal Corridor (Gurugram, Faridabad, Noida)</option>
                  <option>Inter-State Transit Corridor Hub</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
              <div className="space-y-1.5">
                <label className="block font-body-sm text-body-sm font-medium text-on-surface">
                  Official Email
                </label>
                <input
                  className="w-full px-space-md py-2.5 rounded-lg bg-surface border border-outline-variant/60 focus:border-primary focus:outline-none font-body-md text-body-md text-on-surface transition-all"
                  type="email"
                  defaultValue="controller.delhi@legalmetrology.gov.in"
                />
              </div>
              <div className="space-y-1.5">
                <label className="block font-body-sm text-body-sm font-medium text-on-surface">
                  Contact Phone
                </label>
                <input
                  className="w-full px-space-md py-2.5 rounded-lg bg-surface border border-outline-variant/60 focus:border-primary focus:outline-none font-body-md text-body-md text-on-surface transition-all"
                  type="text"
                  defaultValue="+91 11 2338 4821"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Card 2: Official Seal */}
        <section className="bg-surface-container-low rounded-xl border border-outline-variant/40 p-space-lg space-y-space-md shadow-sm">
          <div className="border-b border-outline-variant/30 pb-space-sm">
            <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
              Official Seal & Logo
            </h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Display logo applied to official digital certificates and summons.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row items-center gap-space-lg p-space-md rounded-lg bg-surface border border-outline-variant/40">
            <div className="w-24 h-24 rounded-full bg-surface-container-lowest border-2 border-primary/80 flex items-center justify-center p-1.5 shrink-0 shadow-xs">
              <div className="w-full h-full rounded-full border border-dashed border-outline/60 flex flex-col items-center justify-center text-center bg-surface-container-low/30">
                <span className="material-symbols-outlined text-primary text-[28px]">balance</span>
                <span className="font-label-meta text-[7px] font-bold uppercase tracking-wider text-primary mt-0.5">
                  Legal Metrology
                </span>
              </div>
            </div>
            <div className="flex-1 space-y-2 text-center sm:text-left">
              <div>
                <span className="font-body-sm text-body-sm font-medium text-on-surface block">
                  delhi_zonal_emblem.svg
                </span>
                <span className="font-label-meta text-label-meta text-on-surface-variant">
                  Recommended SVG or PNG with transparent background.
                </span>
              </div>
              <div className="flex items-center justify-center sm:justify-start gap-space-sm">
                <button
                  type="button"
                  onClick={() => alert('Seal upload file selector triggered')}
                  className="px-space-md py-2 rounded-lg bg-surface border border-outline-variant/80 hover:bg-surface-container-high text-on-surface font-body-sm text-body-sm font-medium transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">upload</span>
                  <span>Upload New Seal</span>
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Card 3: Security & Access */}
        <section className="bg-surface-container-low rounded-xl border border-outline-variant/40 p-space-lg space-y-space-md shadow-sm">
          <div className="border-b border-outline-variant/30 pb-space-sm">
            <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
              Security & Access
            </h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Update administrator password and configure authentication settings.
            </p>
          </div>
          <div className="space-y-space-md">
            <div className="space-y-1.5">
              <label className="block font-body-sm text-body-sm font-medium text-on-surface">
                Current Password
              </label>
              <input
                className="w-full px-space-md py-2.5 rounded-lg bg-surface border border-outline-variant/60 focus:border-primary focus:outline-none font-body-md text-body-md text-on-surface transition-all"
                placeholder="••••••••••••"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
              <div className="space-y-1.5">
                <label className="block font-body-sm text-body-sm font-medium text-on-surface">
                  New Password
                </label>
                <input
                  className="w-full px-space-md py-2.5 rounded-lg bg-surface border border-outline-variant/60 focus:border-primary focus:outline-none font-body-md text-body-md text-on-surface transition-all"
                  placeholder="Enter new password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label className="block font-body-sm text-body-sm font-medium text-on-surface">
                  Confirm New Password
                </label>
                <input
                  className="w-full px-space-md py-2.5 rounded-lg bg-surface border border-outline-variant/60 focus:border-primary focus:outline-none font-body-md text-body-md text-on-surface transition-all"
                  placeholder="Confirm new password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
            </div>

            <div className="pt-space-xs">
              <div className="p-space-md rounded-lg bg-surface border border-outline-variant/50 flex items-center justify-between gap-space-md">
                <div className="space-y-0.5">
                  <span className="font-body-sm text-body-sm font-medium text-on-surface block">
                    Require Two-Factor Authentication (2FA)
                  </span>
                  <p className="font-label-meta text-label-meta text-on-surface-variant">
                    Mandate TOTP or authentication codes for all inspector accounts.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={twoFactor}
                  onChange={(e) => setTwoFactor(e.target.checked)}
                  className="w-5 h-5 accent-primary cursor-pointer"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Card 4: Notifications */}
        <section className="bg-surface-container-low rounded-xl border border-outline-variant/40 p-space-lg space-y-space-md shadow-sm">
          <div className="border-b border-outline-variant/30 pb-space-sm">
            <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
              Notifications & Dispatches
            </h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Configure operational alerts and automated reports.
            </p>
          </div>
          <div className="space-y-space-sm">
            <label className="flex items-start gap-space-sm p-space-sm rounded-lg hover:bg-surface transition-colors cursor-pointer border border-transparent hover:border-outline-variant/40">
              <input
                type="checkbox"
                checked={deficitAlerts}
                onChange={(e) => setDeficitAlerts(e.target.checked)}
                className="w-4 h-4 mt-1 accent-primary"
              />
              <div className="space-y-0.5">
                <span className="font-body-sm text-body-sm font-medium text-on-surface block leading-tight">
                  Immediate Deficit Alerts
                </span>
                <p className="font-label-meta text-label-meta text-on-surface-variant">
                  Instant notification when critical tolerance discrepancies are logged during inspection.
                </p>
              </div>
            </label>

            <label className="flex items-start gap-space-sm p-space-sm rounded-lg hover:bg-surface transition-colors cursor-pointer border border-transparent hover:border-outline-variant/40">
              <input
                type="checkbox"
                checked={weeklyDigest}
                onChange={(e) => setWeeklyDigest(e.target.checked)}
                className="w-4 h-4 mt-1 accent-primary"
              />
              <div className="space-y-0.5">
                <span className="font-body-sm text-body-sm font-medium text-on-surface block leading-tight">
                  Weekly Compliance Digest
                </span>
                <p className="font-label-meta text-label-meta text-on-surface-variant">
                  Weekly summary report detailing field verifications, notices, and compounded resolutions.
                </p>
              </div>
            </label>
          </div>
        </section>

        {/* Bottom Actions */}
        <div className="flex items-center justify-end gap-space-sm pt-space-sm pb-space-lg">
          <button
            type="button"
            className="px-space-lg py-2.5 rounded-lg border border-outline-variant/60 text-on-surface-variant hover:bg-surface-container-high transition-colors font-body-sm text-body-sm font-medium cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-space-lg py-2.5 rounded-lg bg-primary text-on-primary hover:bg-primary-container font-body-sm text-body-sm font-semibold tracking-wide transition-all shadow-sm active:scale-[0.99] cursor-pointer"
          >
            Save Changes
          </button>
        </div>
      </form>

      <Toast
        show={showToast}
        title={toastTitle}
        description={toastDesc}
      />
    </div>
  );
}
