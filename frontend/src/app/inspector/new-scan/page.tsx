'use client';

import React from 'react';
import { ScanViewfinder } from '@/components/nyayacheck/ScanViewfinder';

export default function InspectorNewScanPage() {
  return (
    <div className="flex flex-col w-full pb-space-xl">
      {/* Top Statutory Protocol Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-md mb-space-lg">
        <div className="flex flex-col">
          {/* <div className="flex items-center gap-2 text-secondary font-label-meta text-label-meta uppercase tracking-wider mb-1">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
            <span>Legal Metrology Inspection</span>
          </div> */}
          <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight font-bold">
            Package Verification Scan
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl mt-1">
            Align product package inside camera view to extract compliance declarations automatically.
          </p>
        </div>
      </div>

      {/* Industrial Camera Viewfinder & Real-time Findings */}
      <ScanViewfinder />
    </div>
  );
}
