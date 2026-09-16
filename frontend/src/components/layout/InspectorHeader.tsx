'use client';

import React from 'react';

export const InspectorHeader: React.FC = () => {
  return (
    <header className="fixed top-0 left-72 right-0 h-16 bg-surface/85 backdrop-blur-xl z-40 shadow-[0_1px_8px_rgba(0,0,0,0.04)] border-b border-outline-variant/40">
      <div className="w-full h-16 px-space-lg flex items-center justify-between">
        <div className="flex items-center gap-space-md min-w-0">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary text-[20px]">verified_user</span>
            <span className="font-body-md text-body-md font-semibold text-primary truncate">
              Officer S.K. Ranganathan
            </span>
            <span className="font-label-code text-label-code text-on-surface-variant px-1.5 py-0.5 rounded bg-surface-container-high">
              Badge LM-DL-88392
            </span>
          </div>
          <div className="hidden xl:flex items-center gap-2 pl-3">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-secondary"></span>
            <span className="font-body-sm text-body-sm text-on-surface-variant">Zonal Unit: North Delhi</span>
          </div>
        </div>

        <div className="flex items-center gap-space-md">
          <div className="hidden md:inline-flex items-center gap-2 px-2.5 py-1 rounded bg-secondary-container">
            <span className="material-symbols-outlined text-on-secondary-container text-[16px]">tune</span>
            <span className="font-label-code text-label-code text-on-secondary-container font-medium">
              NABL Calibrated Terminal
            </span>
          </div>
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
            <span className="material-symbols-outlined text-on-primary text-[18px]">person</span>
          </div>
        </div>
      </div>
    </header>
  );
};
