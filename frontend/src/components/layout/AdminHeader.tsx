'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { logoutUser } from '@/lib/api';
import { useOfficerProfile } from '@/lib/userProfile';

export const AdminHeader: React.FC = () => {
  const router = useRouter();
  const { profile } = useOfficerProfile();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setDropdownOpen(false);
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const handleLogout = async () => {
    setDropdownOpen(false);
    try {
      await logoutUser();
    } catch {
      // Proceed with navigation
    }
    localStorage.removeItem('auth_user');
    router.push('/login');
  };

  const handleSettings = () => {
    setDropdownOpen(false);
    router.push('/admin/settings');
  };

  return (
    <header className="fixed top-0 left-72 right-0 h-16 bg-surface/90 backdrop-blur-md border-b border-outline-variant/40 z-40 px-space-lg flex items-center justify-between shadow-[0_1px_4px_rgba(0,0,0,0.02)]">
      <div className="flex items-center gap-space-md min-w-0">
        <h1 className="font-headline-sm text-headline-sm text-on-surface truncate tracking-tight font-semibold">
          NyayaCheck Legal Metrology — Org Admin
        </h1>
        <div className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-secondary-container/60 border border-secondary/20 text-on-secondary-container">
          <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
          <span className="font-label-code text-label-code font-medium">IN-DL • Enforced</span>
        </div>
      </div>

      <div className="flex items-center gap-space-md">
        <button
          className="relative p-1.5 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors cursor-pointer"
          title="Notifications"
        >
          <span className="material-symbols-outlined text-[22px]">notifications</span>
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-error ring-2 ring-surface"></span>
        </button>

        <div className="h-5 w-[1px] bg-outline-variant/50"></div>

        {/* Profile with Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen((prev) => !prev)}
            aria-expanded={dropdownOpen}
            className="flex items-center gap-space-sm p-1 rounded-lg hover:bg-surface-container/60 transition-colors cursor-pointer text-left"
          >
            <div className="flex flex-col text-right hidden sm:flex">
              <span className="font-body-sm text-body-sm font-semibold text-on-surface leading-tight">
                {profile.name || 'Admin User'}
              </span>
              <span className="font-label-meta text-label-meta text-on-surface-variant">
                {profile.role === 'admin' ? 'Administrator' : 'Compliance Officer'}
              </span>
            </div>
            <div className="w-9 h-9 rounded-full bg-primary overflow-hidden flex items-center justify-center shadow-sm border border-outline-variant/50">
              {profile.avatar ? (
                <img
                  src={profile.avatar}
                  alt={profile.name}
                  className="w-full h-full object-cover object-top"
                />
              ) : (
                <span className="material-symbols-outlined text-on-primary text-[18px]">person</span>
              )}
            </div>
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-60 rounded-xl bg-surface-container-lowest border border-outline-variant/50 shadow-xl py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="px-4 py-3 border-b border-surface-container-high">
                <p className="font-body-sm text-body-sm font-semibold text-on-surface truncate">
                  {profile.name}
                </p>
                <p className="font-label-meta text-label-meta text-on-surface-variant truncate">
                  {profile.email}
                </p>
              </div>

              <div className="p-1 space-y-0.5">
                <button
                  onClick={handleSettings}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface hover:bg-surface-container hover:text-primary transition-colors text-left font-body-sm text-body-sm font-medium cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px] text-on-surface-variant">
                    settings
                  </span>
                  <span>Settings</span>
                </button>

                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-error hover:bg-error-container/20 hover:text-error transition-colors text-left font-body-sm text-body-sm font-medium cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px] text-error">
                    logout
                  </span>
                  <span>Log Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
