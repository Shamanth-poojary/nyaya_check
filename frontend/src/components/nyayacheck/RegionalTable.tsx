'use client';

import React, { useState } from 'react';
import { REGIONAL_RECORDS } from '@/data/mockData';
import { cn } from '@/lib/utils';

export const RegionalTable: React.FC = () => {
  const [filter, setFilter] = useState('');

  const filtered = REGIONAL_RECORDS.filter((r) =>
    r.zone.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="bg-surface-container-low rounded-xl p-space-lg border border-outline-variant/30 space-y-space-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm">
        <div className="space-y-0.5">
          <h3 className="font-headline-sm text-headline-sm text-primary font-semibold">
            Regional Overview
          </h3>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Audit and compliance statistics across active zonal jurisdictions
          </p>
        </div>
        <div className="relative">
          <span className="material-symbols-outlined absolute left-2.5 top-2 text-on-surface-variant text-[18px]">
            search
          </span>
          <input
            className="pl-8 pr-3 py-1.5 rounded-lg bg-surface border border-outline-variant/40 text-on-surface font-body-sm text-body-sm placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-1 focus:ring-primary w-64 shadow-xs"
            placeholder="Filter zones..."
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
      </div>

      <div className="overflow-x-auto w-full">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-outline-variant/30 text-on-surface-variant font-label-meta text-label-meta uppercase tracking-wider">
              <th className="py-3 px-4">Zone / Region</th>
              <th className="py-3 px-4 text-right">Total Packages</th>
              <th className="py-3 px-4 text-right">Violations</th>
              <th className="py-3 px-4 text-right">Deficit Rate</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/20 text-on-surface font-body-sm text-body-sm">
            {filtered.map((item) => (
              <tr key={item.id} className="hover:bg-surface transition-colors">
                <td className="py-3 px-4 font-semibold text-on-surface">{item.zone}</td>
                <td className="py-3 px-4 text-right font-label-code text-label-code">
                  {item.totalPackages}
                </td>
                <td
                  className={cn(
                    'py-3 px-4 text-right font-label-code text-label-code',
                    item.isHighDeficit ? 'font-semibold text-error' : 'text-on-surface-variant'
                  )}
                >
                  {item.violations}
                </td>
                <td
                  className={cn(
                    'py-3 px-4 text-right font-semibold font-label-code text-label-code',
                    item.isHighDeficit ? 'text-error' : 'text-secondary'
                  )}
                >
                  {item.deficitRate}
                </td>
                <td className="py-3 px-4 text-right">
                  <button className="px-3 py-1 rounded border border-outline-variant/40 bg-surface hover:bg-surface-container-highest text-primary font-body-sm text-body-sm transition-colors cursor-pointer">
                    Inspect
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between pt-space-xs font-body-sm text-body-sm text-on-surface-variant">
        <span>Showing {filtered.length} monitored regional divisions</span>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1 rounded border border-outline-variant/40 bg-surface hover:bg-surface-container-highest transition-colors cursor-pointer">
            Previous
          </button>
          <button className="px-3 py-1 rounded border border-outline-variant/40 bg-surface hover:bg-surface-container-highest transition-colors cursor-pointer">
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
