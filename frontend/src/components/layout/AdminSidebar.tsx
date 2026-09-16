'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const navItems = [
  { label: 'Dashboard', href: '/admin/dashboard', icon: 'space_dashboard' },
  { label: 'Reports', href: '/admin/reports', icon: 'description' },
  { label: 'Audit Log', href: '/admin/audit-log', icon: 'history_edu' },
  { label: 'Settings', href: '/admin/settings', icon: 'tune' },
];

export const AdminSidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-surface-container-low border-r border-outline-variant/40 z-50 flex flex-col justify-between shadow-[0_1px_8px_rgba(0,0,0,0.02)]">
      <div className="flex flex-col">
        <Link href="/" className="h-16 px-space-lg flex items-center border-b border-outline-variant/30 gap-space-sm hover:bg-surface-container/50 transition-colors">
          <div className="w-7 h-7 rounded bg-primary text-on-primary flex items-center justify-center font-headline-sm text-headline-sm font-semibold">
            §
          </div>
          <div className="flex flex-col">
            <span className="font-headline-sm text-headline-sm tracking-tight text-primary leading-none font-bold">
              NyayaCheck
            </span>
            <span className="font-label-meta text-label-meta uppercase tracking-wider text-on-surface-variant/80 mt-0.5">
              Statutory Portal
            </span>
          </div>
        </Link>

        <div className="px-space-md pt-space-lg pb-space-sm">
          <p className="font-label-meta text-label-meta uppercase text-on-surface-variant/70 tracking-wider px-space-sm mb-space-sm">
            Statutory Navigation
          </p>
          <nav className="flex flex-col gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href || (item.href === '/admin/dashboard' && pathname === '/admin');
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-space-sm px-space-sm py-2 rounded-lg transition-all duration-150',
                    isActive
                      ? 'bg-primary-container text-on-primary font-medium shadow-sm'
                      : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                  )}
                >
                  <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                  <span className="font-body-sm text-body-sm">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="p-space-md border-t border-outline-variant/40 bg-surface-container-low/60">
        <div className="p-space-sm rounded-lg bg-surface border border-outline-variant/50 mb-space-sm flex items-center justify-between">
          <div className="flex flex-col min-w-0 pr-space-xs">
            <span className="font-body-sm text-body-sm font-semibold text-on-surface truncate">
              Acme Metrology Corp
            </span>
            <span className="font-label-meta text-label-meta text-on-surface-variant truncate">
              ORG-LM-99402
            </span>
          </div>
          <span className="material-symbols-outlined text-secondary text-[18px]">verified</span>
        </div>
        <Link
          href="/login"
          className="w-full flex items-center justify-center gap-space-xs py-2 px-space-sm rounded-lg border border-outline-variant/60 text-on-surface-variant hover:text-error hover:bg-error-container/20 hover:border-error/30 transition-all font-body-sm text-body-sm"
        >
          <span className="material-symbols-outlined text-[18px]">logout</span>
          <span>Sign Out</span>
        </Link>
      </div>
    </aside>
  );
};
