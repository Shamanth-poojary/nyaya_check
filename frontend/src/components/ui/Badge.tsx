import React from 'react';
import { cn } from '@/lib/utils';
import { ReportStatus } from '@/types';

interface BadgeProps {
  status?: ReportStatus | 'active' | 'locked' | 'action-required';
  children?: React.ReactNode;
  className?: string;
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({ status = 'compliant', children, className, dot = true }) => {
  const getStyles = () => {
    switch (status) {
      case 'compliant':
        return 'bg-secondary-container text-on-secondary-container border-secondary/20';
      case 'deficit':
        return 'bg-error-container text-on-error-container border-error/20';
      case 'review':
        return 'bg-surface-container-highest text-on-surface border-outline-variant/40';
      case 'action-required':
        return 'bg-error-container text-on-error-container';
      case 'locked':
        return 'bg-surface-container-high text-error border-error/20';
      case 'active':
        return 'bg-secondary-container/60 text-on-secondary-container border-secondary/20';
      default:
        return 'bg-surface-container-high text-on-surface';
    }
  };

  const getDotColor = () => {
    switch (status) {
      case 'compliant':
      case 'active':
        return 'bg-secondary';
      case 'deficit':
      case 'action-required':
        return 'bg-error';
      case 'review':
        return 'bg-outline';
      default:
        return 'bg-secondary';
    }
  };

  const defaultText = () => {
    switch (status) {
      case 'compliant': return 'Compliant';
      case 'deficit': return 'Deficit Detected';
      case 'review': return 'Review Required';
      case 'action-required': return 'Action Required';
      case 'locked': return 'LOCKED';
      case 'active': return 'ACTIVE';
      default: return '';
    }
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-label-code text-label-code font-semibold border',
        getStyles(),
        className
      )}
    >
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full', getDotColor())} />}
      {children || defaultText()}
    </span>
  );
};
