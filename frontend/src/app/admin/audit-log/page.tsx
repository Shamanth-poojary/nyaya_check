'use client';

import React, { useState } from 'react';
import { MOCK_AUDIT_LOGS } from '@/data/mockData';
import { Toast } from '@/components/ui/Toast';

export default function AdminAuditLogPage() {
  const [search, setSearch] = useState('');
  const [eventFilter, setEventFilter] = useState('all');
  const [toastMsg, setToastMsg] = useState('');
  const [showToast, setShowToast] = useState(false);

  const triggerToast = (msg: string) => {
    setToastMsg(msg);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const filteredLogs = MOCK_AUDIT_LOGS.filter((entry) => {
    const matchesSearch =
      entry.officerName.toLowerCase().includes(search.toLowerCase()) ||
      entry.badgeId.toLowerCase().includes(search.toLowerCase()) ||
      entry.locationNode.toLowerCase().includes(search.toLowerCase());

    const matchesEvent = eventFilter === 'all' || entry.eventType === eventFilter;

    return matchesSearch && matchesEvent;
  });

  return (
    <div className="flex flex-col w-full">
      {/* Top Authority Banner */}
      <div className="px-margin pt-space-lg pb-space-md">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-space-md pb-space-lg">
          <div className="flex flex-col max-w-3xl">
            <div className="flex items-center gap-space-sm mb-space-xs">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-meta text-label-meta uppercase tracking-wider">
                <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                Statutory Archive Digest
              </span>
              <span className="font-label-meta text-label-meta text-on-surface-variant/60">
                GAZETTE ID: NYA-LM-SEC65B-2025/Q1
              </span>
            </div>
            <h2 className="font-headline-lg text-headline-lg text-on-surface tracking-tight font-semibold">
              Officer Session & Security Audit Log
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant mt-1">
              Chronological tamper-evident record of officer sign-ins, terminal handshakes, and field authentication events under Legal Metrology Enforcement Directives.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-space-sm self-start lg:self-end">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-container-high text-on-surface">
              <span className="material-symbols-outlined text-[17px] text-secondary">gavel</span>
              <span className="font-label-code text-label-code text-on-surface font-medium">
                Read-Only Security Ledger • Section 65B Admissible
              </span>
            </div>
            <button
              onClick={() => triggerToast('Exporting Section 65B CSV: IN-LM-SEC65B-2025.csv')}
              className="inline-flex items-center gap-2 px-space-md py-1.5 rounded-lg bg-primary-container text-on-primary font-body-sm text-body-sm font-medium hover:bg-primary transition-all duration-150 active:scale-[0.98] cursor-pointer"
            >
              <span className="material-symbols-outlined text-[17px]">download</span>
              <span>Export Immutable CSV</span>
            </button>
          </div>
        </div>

        {/* Cryptographic Chain Status Callout */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-space-sm p-space-md rounded-xl bg-surface-container-low mb-space-lg">
          <div className="flex flex-col p-space-sm rounded-lg bg-surface">
            <span className="font-label-meta text-label-meta text-on-surface-variant uppercase tracking-wider">
              Ledger Head Signature
            </span>
            <span className="font-label-code text-label-code text-on-surface font-semibold mt-1">
              sha256:7a9e9140...4b1c83df
            </span>
            <span className="font-label-meta text-label-meta text-secondary flex items-center gap-1 mt-1 font-medium">
              <span className="material-symbols-outlined text-[13px]">lock</span> Consensus Verified
            </span>
          </div>
          <div className="flex flex-col p-space-sm rounded-lg bg-surface">
            <span className="font-label-meta text-label-meta text-on-surface-variant uppercase tracking-wider">
              Active Handshakes (IST)
            </span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="font-headline-sm text-headline-sm font-semibold text-on-surface">24 Terminals</span>
              <span className="font-label-meta text-label-meta text-secondary font-medium">100% Attested</span>
            </div>
            <span className="font-label-meta text-label-meta text-on-surface-variant mt-1">Zero unmapped hardware</span>
          </div>
          <div className="flex flex-col p-space-sm rounded-lg bg-surface">
            <span className="font-label-meta text-label-meta text-on-surface-variant uppercase tracking-wider">
              Tamper Detection Engine
            </span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="font-headline-sm text-headline-sm font-semibold text-secondary">Zero Deviations</span>
            </div>
            <span className="font-label-meta text-label-meta text-on-surface-variant mt-1">Merkle tree leaf sequence unbroken</span>
          </div>
          <div className="flex flex-col p-space-sm rounded-lg bg-surface">
            <span className="font-label-meta text-label-meta text-on-surface-variant uppercase tracking-wider">
              Certifying Notary Daemon
            </span>
            <span className="font-label-code text-label-code text-on-surface font-semibold mt-1">
              IN-NIC-STAMP-V4
            </span>
            <span className="font-label-meta text-label-meta text-on-surface-variant mt-1">Sub-second clock drift: ±1.4ms</span>
          </div>
        </div>

        {/* Filter Ribbon */}
        <div className="p-space-md rounded-xl bg-surface-container mb-space-md">
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-space-sm">
            <div className="flex flex-1 flex-wrap items-center gap-space-sm">
              <div className="relative min-w-[200px] flex-1 md:flex-initial">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-on-surface-variant/70 pointer-events-none">
                  search
                </span>
                <input
                  className="w-full pl-9 pr-3 py-2 bg-surface rounded-lg font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:bg-surface-container-lowest"
                  placeholder="Search Officer or Badge ID..."
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>

              <div className="relative min-w-[180px] flex-1 md:flex-initial">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-on-surface-variant/70 pointer-events-none">
                  verified_user
                </span>
                <select
                  value={eventFilter}
                  onChange={(e) => setEventFilter(e.target.value)}
                  className="w-full appearance-none pl-9 pr-8 py-2 bg-surface rounded-lg font-body-sm text-body-sm text-on-surface focus:outline-none cursor-pointer"
                >
                  <option value="all">All Auth Events ({MOCK_AUDIT_LOGS.length})</option>
                  <option value="signin">Sign-in Successful</option>
                  <option value="renew">Token Renewal</option>
                  <option value="signout-manual">Sign-out (Manual)</option>
                  <option value="signout-auto">Sign-out (Automatic)</option>
                </select>
                <span className="absolute right-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-on-surface-variant/60 pointer-events-none">
                  expand_more
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between lg:justify-end gap-space-sm pt-space-xs lg:pt-0">
              <span className="font-label-meta text-label-meta uppercase tracking-wider text-on-surface-variant">
                Displaying {filteredLogs.length} of {MOCK_AUDIT_LOGS.length} Logged Events
              </span>
              <button
                onClick={() => { setSearch(''); setEventFilter('all'); }}
                className="px-2 py-1 text-on-surface-variant hover:text-on-surface font-label-meta text-label-meta uppercase tracking-wider underline cursor-pointer"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Audit Table Surface */}
        <div className="rounded-xl bg-surface-container-low overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-high text-on-surface-variant font-label-meta text-label-meta uppercase tracking-wider">
                  <th className="py-3 px-space-md font-medium">Timestamp (IST)</th>
                  <th className="py-3 px-space-md font-medium">Officer Identity & Badge</th>
                  <th className="py-3 px-space-md font-medium">Authentication Event</th>
                  <th className="py-3 px-space-md font-medium">Terminal / Hardware Profile</th>
                  <th className="py-3 px-space-md font-medium">Geolocation Node</th>
                  <th className="py-3 px-space-md font-medium text-right">Integrity Hash Seal</th>
                </tr>
              </thead>
              <tbody className="font-body-sm text-body-sm text-on-surface divide-y divide-outline-variant/20">
                {filteredLogs.map((item) => (
                  <tr key={item.id} className="hover:bg-surface-container-high/60 transition-colors">
                    <td className="py-3.5 px-space-md whitespace-nowrap">
                      <div className="flex flex-col">
                        <span className="font-label-code text-label-code text-on-surface font-semibold">
                          {item.timestamp}
                        </span>
                        <span className="font-label-meta text-label-meta text-on-surface-variant">
                          {item.isoDate}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-space-md">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded bg-surface-container-highest flex items-center justify-center font-label-code text-label-code text-on-surface font-bold">
                          {item.officerInitials}
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="font-semibold text-on-surface leading-snug">
                            {item.officerName}
                          </span>
                          <span className="font-label-code text-label-code text-on-surface-variant">
                            {item.badgeId}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-space-md whitespace-nowrap">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-label-code text-label-code font-medium ${
                          item.eventType === 'signin'
                            ? 'bg-secondary-container/70 text-on-secondary-container'
                            : item.eventType === 'renew'
                            ? 'bg-surface-container-highest text-on-surface-variant'
                            : 'bg-surface-container text-on-surface-variant'
                        }`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${item.eventType === 'signin' ? 'bg-secondary' : 'bg-outline'}`}></span>
                        {item.eventLabel}
                      </span>
                    </td>
                    <td className="py-3.5 px-space-md">
                      <div className="flex flex-col">
                        <span className="font-medium text-on-surface">{item.deviceModel}</span>
                        <span className="font-label-meta text-label-meta text-on-surface-variant">{item.deviceMeta}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-space-md">
                      <div className="flex flex-col">
                        <span className="text-on-surface font-medium">{item.locationNode}</span>
                        <span className="font-label-code text-label-code text-on-surface-variant">{item.coordinates}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-space-md text-right whitespace-nowrap">
                      <span className="font-label-code text-label-code px-2 py-1 rounded bg-surface text-on-surface-variant font-medium">
                        {item.hashSeal}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Table Footer */}
          <div className="p-space-md bg-surface-container flex flex-col md:flex-row items-center justify-between gap-space-md border-t border-outline-variant/30">
            <div className="flex items-center gap-space-sm">
              <div className="w-2 h-2 rounded-full bg-secondary"></div>
              <span className="font-label-meta text-label-meta text-on-surface-variant">
                SHA-256 Merkle Ledger ID: <span className="font-label-code font-medium text-on-surface">MLK-IN-DELHI-20250314-88A</span>
              </span>
            </div>
            <span className="font-label-meta text-label-meta text-on-surface-variant">
              Section 65B Electronic Ledger Active
            </span>
          </div>
        </div>

        {/* Certificate Callout */}
        <div className="mt-space-lg mb-space-xl p-space-md rounded-xl bg-surface-container-low flex flex-col sm:flex-row items-start sm:items-center justify-between gap-space-md border border-outline-variant/30">
          <div className="flex items-start gap-space-sm">
            <span className="material-symbols-outlined text-secondary text-[22px] mt-0.5">policy</span>
            <div className="flex flex-col">
              <span className="font-body-sm text-body-sm font-semibold text-on-surface">
                Statutory Evidence Compliance Certificate
              </span>
              <p className="font-label-meta text-label-meta text-on-surface-variant mt-0.5">
                This log constitutes electronic record admissible under Section 65B(4) of the Indian Evidence Act, 1872 / Bharatiya Sakshya Adhiniyam, 2023.
              </p>
            </div>
          </div>
          <button
            onClick={() => triggerToast('Digital Certificate SHA-256: d83a79...f021bc Verified')}
            className="px-space-md py-1.5 rounded-lg bg-surface hover:bg-surface-container-high text-on-surface font-label-code text-label-code font-medium transition-colors cursor-pointer shrink-0 border border-outline-variant/40"
          >
            View Cert Hash
          </button>
        </div>
      </div>

      <Toast
        show={showToast}
        title={toastMsg}
        description="Tamper-evident verification validated by gateway."
      />
    </div>
  );
}
