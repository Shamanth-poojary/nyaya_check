'use client';

import React from 'react';
import Link from 'next/link';
import { StatCard } from '@/components/ui/StatCard';
import { ComplianceChart } from '@/components/nyayacheck/ComplianceChart';
import { DeficitCategoryCard } from '@/components/nyayacheck/DeficitCategoryCard';
import { RegionalTable } from '@/components/nyayacheck/RegionalTable';
import { ADMIN_STATS, DEFICIT_CATEGORIES } from '@/data/mockData';

export default function AdminDashboardPage() {
  return (
    <div className="flex flex-col w-full pb-space-xl">
      {/* Top Statutory Ribbon & Title Area */}
      <div className="px-space-lg pt-space-xl pb-space-lg bg-surface">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-md max-w-[1520px] mx-auto w-full border-b border-outline-variant/30 pb-space-lg">
          <div className="flex flex-col space-y-1">
            <h2 className="font-headline-lg text-headline-lg text-primary tracking-tight font-semibold">
              Overview
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Summary of statutory metrology compliance across active regions.
            </p>
          </div>
          <div className="flex items-center gap-space-sm">
            <div className="bg-surface-container-low px-3 py-1.5 rounded-lg flex items-center gap-2 border border-outline-variant/30">
              <span className="w-2 h-2 rounded-full bg-secondary"></span>
              <span className="font-body-sm text-body-sm text-on-surface-variant">
                Synced 14m ago
              </span>
            </div>
            <button
              onClick={() => alert('Special statutory audit notice issued across 6 monitored zones.')}
              className="bg-primary hover:bg-primary-container text-on-primary px-4 py-1.5 rounded-lg font-body-sm text-body-sm flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">add_task</span>
              <span>Initiate Special Audit</span>
            </button>
          </div>
        </div>
      </div>

      {/* Primary Dashboard Canvas */}
      <div className="px-space-lg pb-space-xl max-w-[1520px] mx-auto w-full space-y-space-lg">
        {/* 4 Clean Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-space-md">
          <StatCard
            label="Total Inspections"
            value={ADMIN_STATS.totalInspections}
            subtitle={ADMIN_STATS.inspectionsTrend}
            trend={ADMIN_STATS.inspectionsTrend}
          />
          <StatCard
            label="Active Officers"
            value={ADMIN_STATS.activeOfficers}
            subtitle={ADMIN_STATS.officersSub}
          />
          <StatCard
            label="Overall Compliance"
            value={ADMIN_STATS.overallCompliance}
            subtitle={ADMIN_STATS.complianceSub}
          />
          <StatCard
            label="Deficit Rate"
            value={ADMIN_STATS.deficitRate}
            subtitle={ADMIN_STATS.deficitCount}
            isError={true}
            badge="Action Required"
          />
        </div>

        {/* Enforcement Trends and Top Deficit Categories */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-space-lg items-stretch">
          {/* Chart column (8 cols) */}
          <div className="xl:col-span-8 bg-surface-container-low p-space-lg rounded-xl border border-outline-variant/30 flex flex-col justify-between gap-space-md">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <h3 className="font-headline-sm text-headline-sm text-primary font-semibold">
                    Enforcement Trajectory
                  </h3>
                  <span className="px-2 py-0.5 rounded-full bg-secondary-container/60 text-secondary font-label-meta text-label-meta font-medium inline-flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">trending_down</span>
                    Deficit Ratio -4.2%
                  </span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Monthly inspection volume & compliance distribution over past 6 months
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="inline-flex items-center p-0.5 rounded-lg bg-surface-container-highest border border-outline-variant/40 text-on-surface-variant font-label-meta text-label-meta">
                  <span className="px-2 py-1 rounded bg-surface text-primary font-semibold shadow-sm">
                    Last 6 Months
                  </span>
                  <span className="px-2 py-1 hover:text-primary cursor-pointer transition-colors">
                    FY 2024
                  </span>
                </div>
                <div className="hidden md:flex items-center gap-3 pl-2 border-l border-outline-variant/40">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-secondary"></span>
                    <span className="font-body-sm text-body-sm text-on-surface-variant">Compliant</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-error"></span>
                    <span className="font-body-sm text-body-sm text-on-surface-variant">Deficit</span>
                  </div>
                </div>
              </div>
            </div>

            <ComplianceChart />

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-xs text-on-surface-variant font-body-sm text-body-sm">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px] text-secondary">
                  check_circle
                </span>
                <span>
                  Deficit curve decreased by 4.2% following recent gazette inspection updates.
                </span>
              </div>
              <div className="flex items-center gap-3 font-label-code text-[12px] text-on-surface-variant/80">
                <span className="inline-flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>Pass target: &gt;85%
                </span>
                <span className="inline-flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-error"></span>Deficit cap: &lt;15%
                </span>
              </div>
            </div>
          </div>

          {/* Top Deficit Categories (4 cols) */}
          <div className="xl:col-span-4 bg-surface-container-low p-space-lg rounded-xl border border-outline-variant/30 flex flex-col justify-between gap-space-md">
            <div className="space-y-1">
              <h3 className="font-headline-sm text-headline-sm text-primary font-semibold">
                Top Deficit Categories
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Frequent breach types across monitored regional godowns
              </p>
            </div>

            <DeficitCategoryCard categories={DEFICIT_CATEGORIES} />

            <Link
              href="/admin/reports"
              className="w-full py-2 rounded-lg bg-surface-container-highest text-primary hover:bg-primary hover:text-on-primary font-body-sm text-body-sm font-medium transition-all text-center flex items-center justify-center gap-1 cursor-pointer"
            >
              <span>View Detailed Register</span>
              <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            </Link>
          </div>
        </div>

        {/* Regional Overview Table */}
        <RegionalTable />

        {/* Statutory Note */}
        <div className="p-space-md rounded-xl bg-surface-container-low border border-outline-variant/30 flex items-center justify-between text-on-surface-variant font-body-sm text-body-sm">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px] text-secondary">
              verified
            </span>
            <span>
              Statutory enforcement monitored in accordance with Legal Metrology Act, 2009 and Packaged Commodities Rules (PCR).
            </span>
          </div>
          <span className="font-label-code text-label-code text-on-surface-variant">
            Standard Protocol Active
          </span>
        </div>
      </div>
    </div>
  );
}
