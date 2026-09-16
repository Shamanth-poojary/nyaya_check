'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { logoutUser } from '@/lib/api';

const navItems = [
  { label: 'New Scan', href: '/inspector/new-scan', icon: 'photo_camera' },
  { label: 'Reports', href: '/inspector/reports', icon: 'folder' },
  { label: 'Settings', href: '/inspector/settings', icon: 'settings' },
];

export const InspectorSidebar: React.FC = () => {
  const pathname = usePathname();

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch {
      // proceed with client navigation to /login
    }
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-72 bg-surface-container-low z-50 flex flex-col justify-between shadow-[0_1px_8px_rgba(0,0,0,0.04)] border-r border-outline-variant/40">
      <div className="flex flex-col">
        <Link href="/" className="px-space-lg pt-space-lg pb-space-md hover:bg-surface-container/50 transition-colors block">
          <div className="flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-primary text-[26px]">balance</span>
            <span className="font-headline-md text-headline-md text-primary tracking-tight font-bold">
              NyayaCheck
            </span>
          </div>
          <div className="mt-space-xs inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-container-high">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
            <span className="font-label-meta text-label-meta text-on-surface-variant uppercase tracking-wider">
              Field Inspector Portal
            </span>
          </div>
          <div className="mt-1">
            <span className="font-label-meta text-label-meta text-outline uppercase tracking-widest">
              Statutory Enforcement
            </span>
          </div>
        </Link>

        <div className="px-space-md my-space-xs">
          <div className="h-[1px] bg-surface-container-highest w-full"></div>
        </div>

        <div className="px-space-md pt-space-sm">
          <div className="px-3 pb-2 font-label-meta text-label-meta text-outline uppercase tracking-wider">
            Field Operations
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors font-body-sm text-body-sm',
                    isActive
                      ? 'bg-primary-container text-on-primary font-semibold shadow-sm'
                      : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
                  )}
                >
                  <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="p-space-md">
        <div className="p-space-md rounded-lg bg-surface-container flex flex-col gap-space-sm border border-outline-variant/30">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-primary-container text-on-primary flex items-center justify-center font-label-code text-label-code font-bold">
              SR
            </div>
            <div className="flex flex-col min-w-0 flex-1">
              <span className="font-body-sm text-body-sm font-semibold text-on-surface truncate">
                S.K. Ranganathan
              </span>
              <span className="font-label-code text-label-code text-outline truncate">
                LM-DL-88392
              </span>
            </div>
          </div>
          <div className="pt-2">
            <Link
              href="/login"
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded bg-surface-container-high hover:bg-surface-container-highest text-on-surface transition-colors font-body-sm text-body-sm font-medium"
            >
              <span className="material-symbols-outlined text-[18px]">logout</span>
              <span>Log Out</span>
            </Link>
          </div>
        </div>
      </div>
    </aside>
  );
};
