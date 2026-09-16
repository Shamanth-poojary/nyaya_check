import React from 'react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  label: string;
  value: string;
  subtitle: string;
  trend?: string;
  isError?: boolean;
  badge?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  subtitle,
  trend,
  isError = false,
  badge,
}) => {
  return (
    <div className="bg-surface-container-low p-space-md rounded-xl border border-outline-variant/30 flex flex-col justify-between shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
      <div className="flex items-center justify-between">
        <span className="font-body-sm text-body-sm text-on-surface-variant">{label}</span>
        {badge && (
          <span className="px-2 py-0.5 rounded bg-error-container text-on-error-container font-label-code text-label-code font-medium">
            {badge}
          </span>
        )}
      </div>
      <div className="mt-2">
        <span
          className={cn(
            'font-headline-lg text-headline-lg font-semibold tracking-tight',
            isError ? 'text-error' : 'text-primary'
          )}
        >
          {value}
        </span>
      </div>
      <div className="mt-3 flex items-center gap-1.5 font-body-sm text-body-sm">
        {trend && (
          <div className="flex items-center gap-1 text-secondary font-medium">
            <span className="material-symbols-outlined text-[16px]">trending_up</span>
            <span>{trend}</span>
          </div>
        )}
        {!trend && (
          <span className={cn('font-body-sm text-body-sm', isError ? 'text-error font-medium' : 'text-on-surface-variant')}>
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
};
