import React from 'react';
import { cn } from '@/lib/utils';

interface ToastProps {
  show: boolean;
  title: string;
  description?: string;
  icon?: string;
}

export const Toast: React.FC<ToastProps> = ({
  show,
  title,
  description,
  icon = 'check_circle',
}) => {
  return (
    <div
      className={cn(
        'fixed bottom-6 right-6 z-50 transform transition-all duration-300 pointer-events-none flex items-center gap-3 px-space-lg py-3 rounded-xl bg-primary text-on-primary shadow-xl border border-outline-variant/20',
        show ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'
      )}
    >
      <span className="material-symbols-outlined text-secondary text-[22px]">{icon}</span>
      <div className="flex flex-col">
        <span className="font-body-sm text-body-sm font-semibold text-on-primary leading-tight">{title}</span>
        {description && (
          <span className="font-label-meta text-label-meta text-on-primary/70 mt-0.5">{description}</span>
        )}
      </div>
    </div>
  );
};
