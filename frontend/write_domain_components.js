const fs = require('fs');

// src/components/nyayacheck/ComplianceChart.tsx
fs.writeFileSync('src/components/nyayacheck/ComplianceChart.tsx', `'use client';

import React, { useState } from 'react';
import { MONTHLY_TRENDS } from '@/data/mockData';

export const ComplianceChart: React.FC = () => {
  const [range, setRange] = useState<'6m' | 'fy'>('6m');

  return (
    <div className="w-full bg-surface rounded-lg p-space-md border border-outline-variant/30 flex flex-col">
      <div className="flex w-full h-64">
        {/* Y Axis */}
        <div className="w-12 flex flex-col justify-between items-end pr-3 pb-8 text-on-surface-variant/70 font-label-code text-[11px]">
          <span>100%</span>
          <span>75%</span>
          <span>50%</span>
          <span>25%</span>
          <span>0%</span>
        </div>

        {/* Chart Area */}
        <div className="flex-1 relative flex flex-col justify-between pb-8">
          <div className="absolute inset-0 bottom-8 flex flex-col justify-between pointer-events-none">
            <div className="w-full border-b border-outline-variant/30 border-dashed"></div>
            <div className="w-full border-b border-outline-variant/30 border-dashed"></div>
            <div className="w-full border-b border-outline-variant/30 border-dashed"></div>
            <div className="w-full border-b border-outline-variant/30 border-dashed"></div>
            <div className="w-full border-b border-outline-variant/50"></div>
          </div>

          <div className="relative h-full flex items-end justify-around px-2 z-10">
            {MONTHLY_TRENDS.map((item, index) => {
              const isLast = index === MONTHLY_TRENDS.length - 1;
              const compliantHeight = Math.round((item.passRate / 100) * 160);
              const deficitHeight = Math.round((item.deficitRate / 100) * 160);

              return (
                <div
                  key={item.month}
                  className="group relative flex flex-col items-center h-full justify-end w-14 cursor-pointer"
                >
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-11 z-30 bg-primary text-on-primary text-[11px] font-label-code px-2 py-1 rounded shadow-md whitespace-nowrap pointer-events-none flex flex-col items-center">
                    <span>Pass: {item.passRate}% · Deficit: {item.deficitRate}%</span>
                    <span className="text-[10px] text-on-primary/70">{item.total} total</span>
                  </div>

                  <span
                    className={
                      isLast
                        ? 'mb-1.5 font-label-code text-[11px] text-primary font-bold'
                        : 'mb-1.5 font-label-code text-[11px] text-on-surface-variant/80 font-medium group-hover:text-primary transition-colors'
                    }
                  >
                    {item.passRate}%
                  </span>

                  <div
                    className={
                      isLast
                        ? 'w-7 flex flex-col items-center rounded-t overflow-hidden shadow-sm ring-2 ring-primary/30 transition-all'
                        : 'w-7 flex flex-col items-center rounded-t overflow-hidden shadow-xs group-hover:ring-2 group-hover:ring-primary/20 transition-all'
                    }
                  >
                    <div
                      className="w-full bg-error transition-all group-hover:brightness-95"
                      style={{ height: `${deficitHeight}px` }}
                    />
                    <div
                      className="w-full bg-secondary transition-all group-hover:brightness-105"
                      style={{ height: `${compliantHeight}px` }}
                    />
                  </div>

                  <div className="absolute bottom-[-24px] flex flex-col items-center">
                    <span
                      className={
                        isLast
                          ? 'font-body-sm text-body-sm font-semibold text-primary'
                          : 'font-body-sm text-body-sm text-on-surface-variant group-hover:text-primary transition-colors'
                      }
                    >
                      {item.month}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
`);

// src/components/nyayacheck/DeficitCategoryCard.tsx
fs.writeFileSync('src/components/nyayacheck/DeficitCategoryCard.tsx', `import React from 'react';
import { DeficitCategory } from '@/types';
import { cn } from '@/lib/utils';

interface DeficitCategoryCardProps {
  categories: DeficitCategory[];
}

export const DeficitCategoryCard: React.FC<DeficitCategoryCardProps> = ({ categories }) => {
  return (
    <div className="space-y-2.5">
      {categories.map((cat) => (
        <div
          key={cat.id}
          className="p-3 rounded-lg bg-surface border border-outline-variant/30 flex items-center justify-between hover:border-outline-variant/60 transition-colors"
        >
          <div className="min-w-0 pr-2">
            <p className="font-body-sm text-body-sm font-semibold text-on-surface truncate">
              {cat.title}
            </p>
            <p className="font-label-meta text-label-meta text-on-surface-variant">
              {cat.rule}
            </p>
          </div>
          <span
            className={cn(
              'px-2 py-1 rounded font-body-sm text-body-sm font-semibold whitespace-nowrap',
              cat.severity === 'high'
                ? 'text-error bg-error-container/60'
                : 'text-on-surface-variant bg-surface-container-highest'
            )}
          >
            {cat.packCount}
          </span>
        </div>
      ))}
    </div>
  );
};
`);

// src/components/nyayacheck/RegionalTable.tsx
fs.writeFileSync('src/components/nyayacheck/RegionalTable.tsx', `'use client';

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
`);

// src/components/nyayacheck/ReportDetailDrawer.tsx
fs.writeFileSync('src/components/nyayacheck/ReportDetailDrawer.tsx', `'use client';

import React from 'react';
import { InspectionReport } from '@/types';
import { Badge } from '@/components/ui/Badge';

interface ReportDetailDrawerProps {
  report: InspectionReport | null;
  onClose: () => void;
}

export const ReportDetailDrawer: React.FC<ReportDetailDrawerProps> = ({ report, onClose }) => {
  if (!report) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-space-md bg-primary/40 backdrop-blur-sm">
      <div className="bg-surface rounded-xl border border-outline-variant/40 shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="p-space-lg bg-surface-container-low border-b border-outline-variant/40 flex items-start justify-between">
          <div className="flex flex-col">
            <div className="flex items-center gap-space-xs mb-1">
              <span className="px-2 py-0.5 rounded bg-primary text-on-primary font-label-code text-label-code font-semibold">
                {report.reportCode}
              </span>
              <Badge status={report.status} />
            </div>
            <h3 className="font-headline-md text-headline-md text-on-surface font-semibold">
              Inspection Dossier Summary
            </h3>
            <p className="font-label-meta text-label-meta text-on-surface-variant mt-0.5">
              Statutory Record DEL-LM-2025-{report.reportCode.replace('#REP-', '')} • {report.timestamp}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <div className="p-space-lg overflow-y-auto flex flex-col gap-space-md font-body-sm">
          <div className="grid grid-cols-2 gap-space-md p-space-md rounded-lg bg-surface-container-low border border-outline-variant/30">
            <div>
              <span className="font-label-meta text-label-meta uppercase text-on-surface-variant block">
                Product
              </span>
              <span className="font-semibold text-on-surface block mt-0.5">
                {report.productName}
              </span>
              <span className="font-label-code text-label-code text-on-surface-variant">
                {report.sku}
              </span>
            </div>
            <div>
              <span className="font-label-meta text-label-meta uppercase text-on-surface-variant block">
                Location
              </span>
              <span className="font-semibold text-on-surface block mt-0.5">
                {report.location}
              </span>
              <span className="font-label-code text-label-code text-on-surface-variant">
                {report.zone}
              </span>
            </div>
            <div>
              <span className="font-label-meta text-label-meta uppercase text-on-surface-variant block">
                Inspecting Officer
              </span>
              <span className="font-semibold text-on-surface block mt-0.5">
                {report.officerName}
              </span>
              <span className="font-label-code text-label-code text-on-surface-variant">
                Badge: {report.officerBadge}
              </span>
            </div>
            <div>
              <span className="font-label-meta text-label-meta uppercase text-on-surface-variant block">
                Inspection Date & Time
              </span>
              <span className="font-semibold text-on-surface block mt-0.5">
                {report.timestamp}
              </span>
              <span className="font-label-code text-label-code text-secondary font-medium">
                Digital Sig: Verified & Sealed
              </span>
            </div>
          </div>

          {report.mrp && (
            <div className="p-space-md rounded-lg bg-surface border border-outline-variant/30 grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div>
                <span className="font-label-meta text-label-meta text-on-surface-variant uppercase">Declared MRP</span>
                <span className="font-body-md font-semibold text-primary block mt-0.5">{report.mrp}</span>
              </div>
              <div>
                <span className="font-label-meta text-label-meta text-on-surface-variant uppercase">Net Quantity</span>
                <span className="font-body-md font-semibold text-primary block mt-0.5">{report.netQty}</span>
              </div>
              <div>
                <span className="font-label-meta text-label-meta text-on-surface-variant uppercase">Packing Date</span>
                <span className="font-body-md font-semibold text-primary block mt-0.5">{report.mfgDate}</span>
              </div>
            </div>
          )}

          <div
            className={
              report.status === 'deficit'
                ? 'p-space-md rounded-lg bg-error-container/30 border border-error/20 flex flex-col gap-1'
                : 'p-space-md rounded-lg bg-secondary-container/30 border border-secondary/20 flex flex-col gap-1'
            }
          >
            <div
              className={
                report.status === 'deficit'
                  ? 'flex items-center gap-1.5 text-error font-semibold font-body-sm'
                  : 'flex items-center gap-1.5 text-secondary font-semibold font-body-sm'
              }
            >
              <span className="material-symbols-outlined text-[18px]">
                {report.status === 'deficit' ? 'error' : 'verified'}
              </span>
              <span>
                {report.status === 'deficit'
                  ? 'Findings & Verdict: Statutory Non-Compliance'
                  : 'Findings & Verdict: Statutory Compliance Certified'}
              </span>
            </div>
            <p className="text-on-surface-variant leading-relaxed text-body-sm">
              {report.findings}
            </p>
          </div>

          <div className="p-space-md rounded-lg bg-surface-container-low border border-outline-variant/30 flex items-center justify-between">
            <div>
              <span className="font-label-meta text-label-meta uppercase text-on-surface-variant block">
                Cryptographic Hash & Panchnama Memo
              </span>
              <span className="font-label-code text-label-code text-primary block mt-0.5">
                {report.digitalSignature}
              </span>
            </div>
            <span className="font-label-code text-label-code px-2 py-1 rounded bg-secondary-container text-on-secondary-container font-semibold">
              e-Sign Validated
            </span>
          </div>
        </div>

        <div className="p-space-md bg-surface-container-low border-t border-outline-variant/40 flex items-center justify-between gap-space-sm">
          <button
            onClick={onClose}
            className="px-space-md py-2 rounded-lg border border-outline-variant/60 text-on-surface hover:bg-surface-container-high transition-colors font-body-sm cursor-pointer"
          >
            Close
          </button>
          <div className="flex items-center gap-space-xs">
            <button
              onClick={() => alert('Printing Notice...')}
              className="inline-flex items-center gap-1.5 px-space-md py-2 rounded-lg bg-surface border border-outline-variant/60 text-on-surface hover:bg-surface-container-high transition-colors shadow-sm font-body-sm cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">print</span>
              <span>Print Notice</span>
            </button>
            <button
              onClick={() => alert('Downloading PDF Panchnama dossier...')}
              className="inline-flex items-center gap-1.5 px-space-md py-2 rounded-lg bg-primary text-on-primary hover:bg-primary-container transition-colors shadow-sm font-body-sm font-semibold cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
              <span>Download PDF Panchnama</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
`);

console.log('Domain components created');
