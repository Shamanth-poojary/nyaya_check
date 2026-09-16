'use client';

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
