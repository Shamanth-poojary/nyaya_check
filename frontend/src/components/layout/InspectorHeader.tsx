'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useOfficerProfile } from '@/lib/userProfile';
import { logoutUser } from '@/lib/api';

export const InspectorHeader: React.FC = () => {
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
      if (event.key === 'Escape') {
        setDropdownOpen(false);
      }
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
      // Proceed with client navigation
    }
    localStorage.removeItem('auth_user');
    router.push('/login');
  };

  const handleSettings = () => {
    setDropdownOpen(false);
    router.push('/inspector/settings');
  };

  return (
    <header className="fixed top-0 left-72 right-0 h-16 bg-surface/85 backdrop-blur-xl z-40 shadow-[0_1px_8px_rgba(0,0,0,0.04)] border-b border-outline-variant/40">
      <div className="w-full h-16 px-space-lg flex items-center justify-between">
        {/* Left: Officer Identification details */}
        <div className="flex items-center gap-space-md min-w-0">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary text-[20px]">verified_user</span>
            <span className="font-body-md text-body-md font-semibold text-primary truncate">
              Officer {profile.name}
            </span>
            <span className="font-label-code text-label-code text-on-surface-variant px-1.5 py-0.5 rounded bg-surface-container-high">
              Badge {profile.badge || 'LM-DL-88392'}
            </span>
          </div>
          <div className="hidden xl:flex items-center gap-2 pl-3">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-secondary"></span>
            <span className="font-body-sm text-body-sm text-on-surface-variant">
              Zonal Unit: {profile.zonalUnit || 'North Delhi'}
            </span>
          </div>
        </div>

        {/* Right: Profile button */}
        <div className="flex items-center gap-space-md">
          {/* Profile Button with Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen((prev) => !prev)}
              aria-expanded={dropdownOpen}
              aria-haspopup="true"
              className="flex items-center gap-2 p-1 rounded-full hover:ring-2 hover:ring-primary/40 focus:outline-none focus:ring-2 focus:ring-primary transition-all cursor-pointer"
              title="Officer Profile Menu"
            >
              <div className="w-9 h-9 rounded-full bg-primary overflow-hidden flex items-center justify-center border border-outline-variant/50 shadow-xs relative">
                {profile.avatar ? (
                  <img
                    src={profile.avatar}
                    alt={profile.name}
                    className="w-full h-full object-cover object-top"
                  />
                ) : (
                  <span className="material-symbols-outlined text-on-primary text-[20px]">person</span>
                )}
              </div>
            </button>

            {/* Dropdown Menu */}
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl bg-surface-container-lowest border border-outline-variant/50 shadow-xl py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                {/* Officer Summary */}
                <div className="px-4 py-3 border-b border-surface-container-high flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary-container overflow-hidden flex-shrink-0 flex items-center justify-center border border-outline-variant/40">
                    {profile.avatar ? (
                      <img
                        src={profile.avatar}
                        alt={profile.name}
                        className="w-full h-full object-cover object-top"
                      />
                    ) : (
                      <span className="material-symbols-outlined text-on-primary text-[22px]">person</span>
                    )}
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="font-body-md text-body-md font-semibold text-on-surface truncate">
                      {profile.name}
                    </span>
                    <span className="font-label-meta text-label-meta text-on-surface-variant truncate">
                      {profile.email}
                    </span>
                    <span className="font-label-code text-[11px] text-primary font-medium mt-0.5">
                      {profile.badge || 'LM-DL-88392'}
                    </span>
                  </div>
                </div>

                {/* Actions: Settings & Logout */}
                <div className="p-1 space-y-0.5">
                  <button
                    onClick={handleSettings}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-on-surface hover:bg-surface-container hover:text-primary transition-colors text-left font-body-sm text-body-sm font-medium cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[20px] text-on-surface-variant">
                      settings
                    </span>
                    <span>Settings</span>
                  </button>

                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-error hover:bg-error-container/20 hover:text-error transition-colors text-left font-body-sm text-body-sm font-medium cursor-pointer"
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
      </div>
    </header>
  );
};
