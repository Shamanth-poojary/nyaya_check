import React from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'dark';
  size?: 'sm' | 'md' | 'lg';
  icon?: string;
  iconRight?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  icon,
  iconRight = false,
  ...props
}) => {
  const getVariant = () => {
    switch (variant) {
      case 'primary':
        return 'bg-primary text-on-primary hover:bg-primary-container shadow-sm';
      case 'dark':
        return 'bg-[#1E1E1C] text-[#FCF9F3] hover:bg-stone-800 shadow-sm';
      case 'secondary':
        return 'bg-secondary-container text-on-secondary-container hover:bg-secondary-fixed';
      case 'outline':
        return 'bg-surface border border-outline-variant/60 text-on-surface hover:bg-surface-container-high shadow-sm';
      case 'ghost':
        return 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface';
    }
  };

  const getSize = () => {
    switch (size) {
      case 'sm':
        return 'px-3 py-1.5 text-xs font-medium rounded-lg gap-1.5';
      case 'md':
        return 'px-4 py-2 font-body-sm text-body-sm rounded-lg gap-2';
      case 'lg':
        return 'px-6 py-2.5 font-body-md text-body-md font-semibold rounded-xl gap-2.5';
    }
  };

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center transition-all duration-150 active:scale-[0.98] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
        getVariant(),
        getSize(),
        className
      )}
      {...props}
    >
      {icon && !iconRight && <span className="material-symbols-outlined text-[18px]">{icon}</span>}
      {children}
      {icon && iconRight && <span className="material-symbols-outlined text-[18px]">{icon}</span>}
    </button>
  );
};
