'use client';

import React from 'react';
import { MONTHLY_TRENDS } from '@/data/mockData';

export const ComplianceChart: React.FC = () => {
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

        {/* Chart Canvas */}
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
                      style={{ height: deficitHeight + 'px' }}
                    />
                    <div
                      className="w-full bg-secondary transition-all group-hover:brightness-105"
                      style={{ height: compliantHeight + 'px' }}
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
