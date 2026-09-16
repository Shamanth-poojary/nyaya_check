import os

# 1. Inspector New Scan
new_scan_content = """'use client';

import React from 'react';
import { ScanViewfinder } from '@/components/nyayacheck/ScanViewfinder';

export default function InspectorNewScanPage() {
  return (
    <div className="flex flex-col w-full pb-space-xl">
      {/* Top Statutory Protocol Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-md mb-space-lg">
        <div className="flex flex-col">
          <div className="flex items-center gap-2 text-secondary font-label-meta text-label-meta uppercase tracking-wider mb-1">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
            <span>Legal Metrology Inspection</span>
          </div>
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
"""

with open('src/app/inspector/new-scan/page.tsx', 'w', encoding='utf-8') as f:
    f.write(new_scan_content)
print("Created src/app/inspector/new-scan/page.tsx")

# 2. Inspector Reports
reports_content = """'use client';

import React, { useState } from 'react';
import { MOCK_REPORTS } from '@/data/mockData';
import { InspectionReport, ReportStatus } from '@/types';
import { Badge } from '@/components/ui/Badge';
import { ReportDetailDrawer } from '@/components/nyayacheck/ReportDetailDrawer';

export default function InspectorReportsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | ReportStatus>('all');
  const [selectedReport, setSelectedReport] = useState<InspectionReport | null>(null);

  // Filter reports submitted by Officer S.K. Ranganathan or all
  const filteredReports = MOCK_REPORTS.filter((report) => {
    const matchesSearch =
      report.productName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.reportCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.location.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || report.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="flex flex-col w-full pb-margin">
      <div className="flex flex-col w-full py-space-lg max-w-7xl mx-auto gap-space-lg">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-md border-b border-outline-variant/40 pb-space-md">
          <div className="flex flex-col">
            <div className="flex items-center gap-space-xs text-on-surface-variant mb-1">
              <span className="font-label-meta text-label-meta uppercase tracking-wider">
                Enforcement Register
              </span>
              <span className="text-outline-variant font-label-meta text-label-meta">•</span>
              <span className="font-label-meta text-label-meta uppercase tracking-wider text-secondary font-semibold">
                Statutory Filings
              </span>
            </div>
            <h2 className="font-headline-lg text-headline-lg text-on-surface tracking-tight font-semibold">
              My Inspection Reports
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
              Chronological log of verified statutory inspection dossiers and compliance filings submitted under Inspector Badge LM-DL-88392.
            </p>
          </div>
          <div className="flex items-center gap-space-sm">
            <button
              onClick={() => alert('Exporting my inspection CSV log...')}
              className="inline-flex items-center gap-space-xs px-space-md py-2 rounded-lg bg-surface border border-outline-variant/60 text-on-surface font-body-sm text-body-sm hover:bg-surface-container-high transition-colors shadow-sm cursor-pointer"
              type="button"
            >
              <span className="material-symbols-outlined text-[18px]">table_chart</span>
              <span>Export CSV</span>
            </button>
            <button
              onClick={() => alert('Generating panchnama PDF filings...')}
              className="inline-flex items-center gap-space-xs px-space-md py-2 rounded-lg bg-primary text-on-primary font-body-sm text-body-sm hover:bg-primary-container transition-colors shadow-sm cursor-pointer"
              type="button"
            >
              <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
              <span>Bulk PDF Panchnama</span>
            </button>
          </div>
        </div>

        {/* Filter Ribbon */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-space-sm items-center">
          <div className="md:col-span-6 relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">
              search
            </span>
            <input
              className="w-full bg-surface-container-low pl-10 pr-space-md py-2.5 rounded-lg border border-outline-variant/50 font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary shadow-xs"
              placeholder="Search by Product, Report ID, or Location..."
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
              <option value="deficit">Non-Compliant / Deficit</option>
              <option value="compliant">Compliant / Correct</option>
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

        {/* Reports Table */}
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
                        className="px-3 py-1.5 bg-[#1E1E1C] text-[#FCF9F3] hover:bg-stone-800 text-xs font-medium rounded-lg inline-flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
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

        {/* Dossier Drawer */}
        <ReportDetailDrawer
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      </div>
    </div>
  );
}
"""

with open('src/app/inspector/reports/page.tsx', 'w', encoding='utf-8') as f:
    f.write(reports_content)
print("Created src/app/inspector/reports/page.tsx")

# 3. Inspector Settings
settings_content = """'use client';

import React, { useState } from 'react';
import { Toast } from '@/components/ui/Toast';

export default function InspectorSettingsPage() {
  const [showToast, setShowToast] = useState(false);
  const [offlineSync, setOfflineSync] = useState(true);
  const [avatar, setAvatar] = useState(
    'https://lh3.googleusercontent.com/aida-public/AB6AXuCl76By1vtUiTeEHRzV5GW2Xa13xQiWRLhXs5XP6pvqxaaJofBodxznf0MUIRhZu3Ozw6FCKJNbV9-0CTcWfyfjnadwGG8PO7W5QCQU7B7P356qyfSCjD1BaZ9OjnLtrw2C8yJi0TwWa_e0kakumnqnV8RFNqdgIzbGQnLJ6RljUBncYzgVk3FTfT41VrEY2PH98XEBaN0cJK7BWNRmGaX6KMcfzrgdGc3JIEOk6IllLFn4akOrr5_czQ'
  );

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setAvatar(event.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3500);
  };

  return (
    <div className="flex flex-col w-full pb-16">
      {/* Header */}
      <div className="py-8 flex flex-col gap-1 border-b border-surface-container-highest">
        <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight font-semibold">
          Settings
        </h1>
        <p className="font-body-md text-body-md text-on-surface-variant">
          Manage your officer profile, contact details, and account security.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-10 mt-8">
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
          {/* Section 1: Officer Identification (7 cols) */}
          <section className="xl:col-span-7 flex flex-col gap-6 bg-surface-container-low p-6 lg:p-8 rounded-2xl shadow-sm">
            <div className="flex items-center justify-between pb-4 border-b border-surface-container-high">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-primary text-[24px]">badge</span>
                <div>
                  <h2 className="font-headline-sm text-headline-sm text-primary font-semibold">
                    Officer Official Identification
                  </h2>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">
                    Gazetted field inspector credentials under Legal Metrology Act, 2009.
                  </p>
                </div>
              </div>
              <span className="font-label-code text-label-code bg-surface-container-high px-2.5 py-1 rounded text-on-surface font-semibold">
                ENFORCER ROLE
              </span>
            </div>

            {/* Photo Identification */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 bg-surface p-4 rounded-xl border border-outline-variant/30">
              <div className="relative group">
                <div className="w-24 h-24 rounded-xl overflow-hidden bg-surface-container-highest flex-shrink-0">
                  <img
                    src={avatar}
                    alt="Officer portrait"
                    className="w-full h-full object-cover object-top"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-2 min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-body-md text-body-md font-semibold text-primary">
                    Departmental Portrait File
                  </span>
                  <span className="font-label-meta text-label-meta text-outline uppercase bg-surface-container px-1.5 py-0.5 rounded">
                    ICAO Compliant
                  </span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Front-facing portrait embedded in digital inspection memos & spot summons.
                </p>
                <div className="flex flex-wrap items-center gap-3 mt-1">
                  <label className="cursor-pointer inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container-highest transition-colors font-body-sm text-body-sm font-medium text-on-surface shadow-xs">
                    <span className="material-symbols-outlined text-[18px]">upload_file</span>
                    <span>Upload New Headshot</span>
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleImageChange}
                    />
                  </label>
                </div>
              </div>
            </div>

            {/* Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="flex flex-col gap-1.5">
                <label className="font-label-meta text-label-meta uppercase tracking-wider text-outline">
                  Gazetted Full Name
                </label>
                <div className="relative">
                  <input
                    className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                    type="text"
                    defaultValue="S.K. Ranganathan"
                  />
                  <span className="material-symbols-outlined absolute right-3 top-2.5 text-[20px] text-secondary">
                    verified
                  </span>
                </div>
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  Matches Central Gazette Reg No. #CG-2018/88392
                </span>
              </div>

              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-label-meta text-label-meta uppercase tracking-wider text-outline">
                    Zonal Badge Serial
                  </label>
                  <span className="font-label-meta text-label-meta text-error font-semibold flex items-center gap-0.5">
                    <span className="material-symbols-outlined text-[13px]">lock</span> LOCKED
                  </span>
                </div>
                <input
                  className="w-full bg-surface-container-highest/80 text-on-surface font-label-code text-label-code px-3.5 py-2.5 rounded-lg cursor-not-allowed select-none border border-outline-variant/40"
                  readOnly
                  type="text"
                  defaultValue="LM-DL-88392"
                />
                <span className="font-body-sm text-body-sm text-outline">
                  Statutory ID bound to DL Northern Zonal Registry.
                </span>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-meta text-label-meta uppercase tracking-wider text-outline">
                  Encrypted Terminal Mobile
                </label>
                <input
                  className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                  type="tel"
                  defaultValue="+91 98402 11983"
                />
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  Receives OTP challenges for seized custody receipts.
                </span>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-meta text-label-meta uppercase tracking-wider text-outline">
                  Government Directory Email
                </label>
                <input
                  className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                  type="email"
                  defaultValue="sk.ranganathan@delhi.gov.in"
                />
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  Official reports & court dockets dispatch here.
                </span>
              </div>
            </div>

            {/* Jurisdiction banner */}
            <div className="mt-2 p-4 rounded-xl bg-surface flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-outline-variant/30">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center text-primary">
                  <span className="material-symbols-outlined text-[22px]">apartment</span>
                </div>
                <div className="flex flex-col">
                  <span className="font-body-sm text-body-sm font-semibold text-primary">
                    Assigned Jurisdiction: North Delhi Zone II
                  </span>
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    Sub-divisional Magistracy: Civil Lines, Tis Hazari Complex
                  </span>
                </div>
              </div>
              <span className="font-label-code text-label-code bg-secondary-container text-on-secondary-container px-2.5 py-1 rounded font-medium">
                ACTIVE COMMISSION
              </span>
            </div>
          </section>

          {/* Section 2: Password & Offline Sync (5 cols) */}
          <section className="xl:col-span-5 flex flex-col gap-6 bg-surface-container-low p-6 lg:p-8 rounded-2xl shadow-sm self-start">
            <div className="flex items-center gap-3 pb-2 border-b border-surface-container-high">
              <span className="material-symbols-outlined text-primary text-[22px]">lock</span>
              <div>
                <h2 className="font-headline-sm text-headline-sm text-primary font-semibold">
                  Change Password
                </h2>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Update your portal access credentials.
                </p>
              </div>
            </div>

            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="font-body-sm text-body-sm font-medium text-on-surface">
                  Current Password
                </label>
                <input
                  className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                  placeholder="••••••••••••"
                  type="password"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-body-sm text-body-sm font-medium text-on-surface">
                  New Password
                </label>
                <input
                  className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                  placeholder="Enter new password"
                  type="password"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="font-body-sm text-body-sm font-medium text-on-surface">
                  Confirm New Password
                </label>
                <input
                  className="w-full bg-surface text-on-surface px-3.5 py-2.5 rounded-lg font-body-md text-body-md outline-none border border-outline-variant/50 focus:border-primary"
                  placeholder="Re-type new password"
                  type="password"
                />
              </div>
            </div>

            <div className="pt-2 border-t border-surface-container-high">
              <div className="flex items-center justify-between py-1">
                <div className="flex flex-col">
                  <span className="font-body-sm text-body-sm font-medium text-primary">
                    Auto-sync offline records
                  </span>
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    Sync inspection drafts when connection resumes
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={offlineSync}
                  onChange={(e) => setOfflineSync(e.target.checked)}
                  className="w-5 h-5 accent-primary cursor-pointer"
                />
              </div>
            </div>
          </section>
        </div>

        {/* Master Action Bar */}
        <div className="flex items-center justify-end gap-3 pt-6 border-t border-surface-container-high">
          <button
            type="button"
            className="px-5 py-2.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface font-body-md text-body-md font-medium transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-6 py-2.5 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-body-md text-body-md font-semibold transition-all shadow-sm cursor-pointer"
          >
            Save Changes
          </button>
        </div>
      </form>

      <Toast
        show={showToast}
        title="Parameters Synchronised"
        description="Officer profile & device parameters written to cryptographic ledger."
      />
    </div>
  );
}
"""

with open('src/app/inspector/settings/page.tsx', 'w', encoding='utf-8') as f:
    f.write(settings_content)
print("Created src/app/inspector/settings/page.tsx")
