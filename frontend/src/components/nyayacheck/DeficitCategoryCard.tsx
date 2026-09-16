import React from 'react';
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
