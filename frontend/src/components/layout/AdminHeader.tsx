'use client';

import React from 'react';

export const AdminHeader: React.FC = () => {
  return (
    <header className="fixed top-0 left-72 right-0 h-16 bg-surface/90 backdrop-blur-md border-b border-outline-variant/40 z-40 px-space-lg flex items-center justify-between shadow-[0_1px_4px_rgba(0,0,0,0.02)]">
      <div className="flex items-center gap-space-md min-w-0">
        <h1 className="font-headline-sm text-headline-sm text-on-surface truncate tracking-tight">
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
        <div className="flex items-center gap-space-sm">
          <div className="flex flex-col text-right hidden sm:flex">
            <span className="font-body-sm text-body-sm font-semibold text-on-surface leading-tight">
              Rohit S. Verma
            </span>
            <span className="font-label-meta text-label-meta text-on-surface-variant">
              Chief Compliance Officer
            </span>
          </div>
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shadow-sm">
            <span className="material-symbols-outlined text-on-primary text-[18px]">person</span>
          </div>
        </div>
      </div>
    </header>
  );
};
