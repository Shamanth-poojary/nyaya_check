import os

content = """'use client';

import React, { useState } from 'react';
import { MOCK_REPORTS } from '@/data/mockData';
import { InspectionReport, ReportStatus } from '@/types';
import { Badge } from '@/components/ui/Badge';
import { ReportDetailDrawer } from '@/components/nyayacheck/ReportDetailDrawer';

export default function AdminReportsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | ReportStatus>('all');
  const [selectedReport, setSelectedReport] = useState<InspectionReport | null>(null);

  const filteredReports = MOCK_REPORTS.filter((report) => {
    const matchesSearch =
      report.productName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.reportCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.officerName.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || report.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="flex flex-col w-full px-space-lg py-space-lg max-w-7xl mx-auto gap-space-lg">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-md border-b border-outline-variant/40 pb-space-md">
        <div className="flex flex-col">
          <div className="flex items-center gap-space-xs text-on-surface-variant mb-1">
            <span className="font-label-meta text-label-meta uppercase tracking-wider">
              Statutory Register
            </span>
            <span className="text-outline-variant font-label-meta text-label-meta">•</span>
            <span className="font-label-meta text-label-meta uppercase tracking-wider text-secondary font-semibold">
              Enforcement Records
            </span>
          </div>
          <h2 className="font-headline-lg text-headline-lg text-on-surface tracking-tight font-semibold">
            Inspection Reports
          </h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
            Chronological log of statutory inspection dossiers and compliance verification filings.
          </p>
        </div>
        <div className="flex items-center gap-space-sm">
          <button
            onClick={() => alert('Exporting inspection reports CSV...')}
            className="inline-flex items-center gap-space-xs px-space-md py-2 rounded-lg bg-surface border border-outline-variant/60 text-on-surface font-body-sm text-body-sm hover:bg-surface-container-high transition-colors shadow-sm cursor-pointer"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">table_chart</span>
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => alert('Generating bulk panchnama PDF package...')}
            className="inline-flex items-center gap-space-xs px-space-md py-2 rounded-lg bg-primary text-on-primary font-body-sm text-body-sm hover:bg-primary-container transition-colors shadow-sm cursor-pointer"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
            <span>Bulk PDF Panchnama</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Ribbon */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-space-sm items-center">
        <div className="md:col-span-6 relative">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">
            search
          </span>
          <input
            className="w-full bg-surface-container-low pl-10 pr-space-md py-2.5 rounded-lg border border-outline-variant/50 font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary shadow-xs"
            placeholder="Search by Product, Report ID, or Officer..."
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="md:col-span-3 relative">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="w-full bg-surface-container-low pl-3 pr-8 py-2.5 rounded-lg border border-outline-variant/50 font-body-sm text-body-sm text-on-surface appearance-none focus:outline-none focus:ring-2 focus:ring-primary shadow-xs cursor-pointer"
          >
            <option value="all">Filter by Status: All ({MOCK_REPORTS.length})</option>
            <option value="compliant">Compliant / Correct</option>
            <option value="deficit">Non-Compliant / Deficit</option>
            <option value="review">Review Required</option>
          </select>
          <span className="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant text-[18px]">
            expand_more
          </span>
        </div>
        <div className="md:col-span-3 flex items-center justify-end gap-space-xs">
          <span className="font-label-meta text-label-meta uppercase tracking-wider text-on-surface-variant">
            Displaying:
          </span>
          <span className="font-label-code text-label-code px-2 py-0.5 rounded bg-surface-container-high text-on-surface font-semibold">
            {filteredReports.length} of {MOCK_REPORTS.length} Reports
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="bg-surface rounded-xl border border-outline-variant/40 shadow-sm overflow-hidden">
        <div className="overflow-x-auto w-full">
          <table className="w-full min-w-[840px] text-left border-collapse">
            <thead className="bg-surface-container-low border-b border-outline-variant/40">
              <tr>
                <th className="py-3 px-space-md font-label-meta text-label-meta uppercase tracking-wider text-on-surface-variant font-semibold">
                  REPORT ID
                </th>
                <th className="py-3 px-space-md font-label-meta text-label-meta uppercase tracking-wider text-on-surface-variant font-semibold">
                  PRODUCT
                </th>
                <th className="py-3 px-space-md font-label-meta text-label-meta uppercase tracking-wider text-on-surface-variant font-semibold">
                  LOCATION
                </th>
                <th className="py-3 px-space-md font-label-meta text-label-meta uppercase tracking-wider text-on-surface-variant font-semibold">
                  OFFICER NAME
                </th>
                <th className="py-3 px-space-md font-label-meta text-label-meta uppercase tracking-wider text-on-surface-variant font-semibold">
                  STATUS
                </th>
                <th className="py-3 px-space-md font-label-meta text-label-meta uppercase tracking-wider text-on-surface-variant font-semibold text-right">
                  ACTION
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/30 font-body-sm text-body-sm">
              {filteredReports.map((report) => (
                <tr key={report.id} className="hover:bg-surface-container-low/60 transition-colors">
                  <td className="py-3.5 px-space-md whitespace-nowrap">
                    <span className="font-label-code text-label-code font-bold text-primary">
                      {report.reportCode}
                    </span>
                    <div className="font-label-meta text-label-meta text-on-surface-variant mt-0.5">
                      {report.timestamp}
                    </div>
                  </td>
                  <td className="py-3.5 px-space-md">
                    <div className="font-semibold text-on-surface">{report.productName}</div>
                    <div className="font-label-code text-label-code text-on-surface-variant">
                      {report.sku}
                    </div>
                  </td>
                  <td className="py-3.5 px-space-md whitespace-nowrap">
                    <div className="flex items-center gap-1.5 text-on-surface">
                      <span className="material-symbols-outlined text-[16px] text-on-surface-variant">
                        location_on
                      </span>
                      <span>{report.location}</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-space-md whitespace-nowrap">
                    <div className="flex items-center gap-1.5 text-on-surface">
                      <span className="material-symbols-outlined text-[16px] text-on-surface-variant">
                        badge
                      </span>
                      <span>{report.officerName}</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-space-md whitespace-nowrap">
                    <Badge status={report.status} />
                  </td>
                  <td className="py-3.5 px-space-md text-right whitespace-nowrap">
                    <button
                      onClick={() => setSelectedReport(report)}
                      className="px-3 py-1.5 bg-[#1E1E1C] text-[#FCF9F3] hover:bg-stone-800 text-xs font-medium rounded-lg inline-flex items-center gap-1.5 shadow-sm cursor-pointer transition-colors"
                      type="button"
                    >
                      <span>View Report</span>
                      <span className="material-symbols-outlined text-[14px]">visibility</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-space-md bg-surface-container-low border-t border-outline-variant/40 flex flex-col sm:flex-row items-center justify-between gap-space-sm">
          <span className="font-label-meta text-label-meta text-on-surface-variant">
            Showing {filteredReports.length} of {MOCK_REPORTS.length} entries • Ordered by Inspection Date & Report ID
          </span>
          <div className="flex items-center gap-1">
            <button className="px-2.5 py-1 rounded border border-outline-variant/50 bg-surface text-on-surface-variant font-label-code text-label-code hover:bg-surface-container cursor-pointer" disabled>
              Prev
            </button>
            <button className="px-2.5 py-1 rounded bg-primary text-on-primary font-label-code text-label-code font-semibold cursor-pointer">
              1
            </button>
            <button className="px-2.5 py-1 rounded border border-outline-variant/50 bg-surface text-on-surface font-label-code text-label-code hover:bg-surface-container cursor-pointer">
              2
            </button>
            <button className="px-2.5 py-1 rounded border border-outline-variant/50 bg-surface text-on-surface font-label-code text-label-code hover:bg-surface-container cursor-pointer">
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Drawer */}
      <ReportDetailDrawer
        report={selectedReport}
        onClose={() => setSelectedReport(null)}
      />
    </div>
  );
}
"""

with open('src/app/admin/reports/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Created src/app/admin/reports/page.tsx")
