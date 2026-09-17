'use client';

import React, { useState, useEffect } from 'react';
import { Toast } from '@/components/ui/Toast';
import { changePassword } from '@/lib/api';
import { useOfficerProfile } from '@/lib/userProfile';

export default function InspectorSettingsPage() {
  const { profile, updateProfile } = useOfficerProfile();

  const [showToast, setShowToast] = useState(false);
  const [toastTitle, setToastTitle] = useState('Parameters Synchronised');
  const [toastDesc, setToastDesc] = useState('Officer profile & device parameters written to cryptographic ledger.');
  
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [avatar, setAvatar] = useState('');
  const [offlineSync, setOfflineSync] = useState(true);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    if (profile) {
      setName(profile.name || '');
      setEmail(profile.email || '');
      setPhone(profile.phone || '+91 98402 11983');
      setAvatar(profile.avatar || '');
    }
  }, [profile]);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          const newAvatar = event.target.result as string;
          setAvatar(newAvatar);
          updateProfile({ avatar: newAvatar });
          setToastTitle('Portrait Updated');
          setToastDesc('New officer portrait has been saved and applied across your terminal.');
          setShowToast(true);
          setTimeout(() => setShowToast(false), 3500);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 1. Update Officer profile details
    updateProfile({
      name: name.trim() || profile.name,
      email: email.trim() || profile.email,
      phone: phone.trim() || profile.phone,
      avatar: avatar || profile.avatar,
    });

    // 2. Handle Password change if requested
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
        setToastTitle('Profile & Password Updated');
        setToastDesc('Officer profile and security credentials have been updated.');
      } catch (err: any) {
        setToastTitle('Password Update Failed');
        setToastDesc(err.message || 'Failed to update password.');
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3500);
        return;
      }
    } else {
      setToastTitle('Profile Synchronised');
      setToastDesc('Officer name, portrait, and terminal parameters saved.');
    }

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
          Manage your officer profile, portrait photo, contact details, and account security.
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
                <div className="w-24 h-24 rounded-xl overflow-hidden bg-surface-container-highest flex-shrink-0 border-2 border-primary/20 shadow-sm flex items-center justify-center">
                  {avatar ? (
                    <img
                      src={avatar}
                      alt="Officer portrait"
                      className="w-full h-full object-cover object-top"
                    />
                  ) : (
                    <span className="material-symbols-outlined text-[48px] text-outline">person</span>
                  )}
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
                  Front-facing portrait displayed in the terminal navigation, header, and inspection memos.
                </p>
                <div className="flex flex-wrap items-center gap-3 mt-1">
                  <label className="cursor-pointer inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container-highest transition-colors font-body-sm text-body-sm font-medium text-on-surface shadow-xs">
                    <span className="material-symbols-outlined text-[18px]">upload_file</span>
                    <span>Upload New Photo</span>
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
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter officer full name"
                  />
                  <span className="material-symbols-outlined absolute right-3 top-2.5 text-[20px] text-secondary">
                    verified
                  </span>
                </div>
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  Displayed as "Officer {name || profile.name}" across the portal.
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
                  value={profile.badge || 'LM-DL-88392'}
                />
                <span className="font-body-sm text-body-sm text-outline">
                  Statutory ID bound to {profile.zonalUnit || 'North Delhi'} Zonal Registry.
                </span>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-meta text-label-meta uppercase tracking-wider text-outline">
                  Encrypted Terminal Mobile
                </label>
                <input
                  className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 XXXXX XXXXX"
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
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@nic.in"
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
                    Assigned Jurisdiction: {profile.jurisdiction || 'North Delhi Zone II'}
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
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
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
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
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
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
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
            type="submit"
            className="px-6 py-2.5 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-body-md text-body-md font-semibold transition-all shadow-sm cursor-pointer"
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
