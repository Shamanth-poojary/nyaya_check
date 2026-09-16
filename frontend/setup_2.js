const fs = require('fs');

// src/app/globals.css
fs.writeFileSync('src/app/globals.css', `@import "tailwindcss";

:root {
  --primary: #040404;
  --primary-container: #1e1e1c;
  --on-primary: #ffffff;
  --on-primary-container: #878683;
  
  --secondary: #35684d;
  --secondary-container: #b5ecc9;
  --on-secondary-container: #3a6d51;
  --secondary-fixed: #b8efcc;
  
  --surface: #fcf9f3;
  --background: #fcf9f3;
  --surface-container-lowest: #ffffff;
  --surface-container-low: #f6f3ed;
  --surface-container: #f0eee7;
  --surface-container-high: #ebe8e2;
  --surface-container-highest: #e5e2dc;
  
  --on-surface: #1c1c18;
  --on-surface-variant: #464741;
  --outline: #777771;
  --outline-variant: #c7c7bf;
  
  --error: #ba1a1a;
  --error-container: #ffdad6;
  --on-error-container: #93000a;
  
  --tertiary: #140000;
  --tertiary-container: #460002;
  --on-tertiary-container: #d36559;
}

@theme {
  --color-primary: #040404;
  --color-primary-container: #1e1e1c;
  --color-on-primary: #ffffff;
  --color-on-primary-container: #878683;

  --color-secondary: #35684d;
  --color-secondary-container: #b5ecc9;
  --color-on-secondary-container: #3a6d51;
  --color-secondary-fixed: #b8efcc;

  --color-surface: #fcf9f3;
  --color-background: #fcf9f3;
  --color-surface-container-lowest: #ffffff;
  --color-surface-container-low: #f6f3ed;
  --color-surface-container: #f0eee7;
  --color-surface-container-high: #ebe8e2;
  --color-surface-container-highest: #e5e2dc;

  --color-on-surface: #1c1c18;
  --color-on-surface-variant: #464741;
  --color-outline: #777771;
  --color-outline-variant: #c7c7bf;

  --color-error: #ba1a1a;
  --color-error-container: #ffdad6;
  --color-on-error-container: #93000a;

  --spacing-space-xs: 0.25rem;
  --spacing-space-sm: 0.5rem;
  --spacing-space-md: 1rem;
  --spacing-space-lg: 1.5rem;
  --spacing-space-xl: 2.25rem;
  --spacing-margin: 2.5rem;
  --spacing-margin-mobile: 1rem;
  --spacing-gutter: 1.5rem;
  --spacing-gutter-mobile: 0.75rem;

  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

body {
  background-color: var(--surface);
  color: var(--on-surface);
  font-family: var(--font-sans);
  margin: 0;
  padding: 0;
  -webkit-font-smoothing: antialiased;
}

/* Custom typography utilities matching Stitch */
.font-headline-display {
  font-family: var(--font-sans);
  font-size: 3rem;
  line-height: 1.15;
  letter-spacing: -0.03em;
  font-weight: 600;
}

.font-headline-lg {
  font-family: var(--font-sans);
  font-size: 2rem;
  line-height: 1.25;
  letter-spacing: -0.02em;
  font-weight: 600;
}

.font-headline-md {
  font-family: var(--font-sans);
  font-size: 1.375rem;
  line-height: 1.35;
  letter-spacing: -0.015em;
  font-weight: 600;
}

.font-headline-sm {
  font-family: var(--font-sans);
  font-size: 1.125rem;
  line-height: 1.4;
  letter-spacing: -0.01em;
  font-weight: 600;
}

.font-body-lg {
  font-family: var(--font-sans);
  font-size: 1.125rem;
  line-height: 1.6;
  letter-spacing: -0.005em;
  font-weight: 400;
}

.font-body-md {
  font-family: var(--font-sans);
  font-size: 0.9375rem;
  line-height: 1.55;
  letter-spacing: 0em;
  font-weight: 400;
}

.font-body-sm {
  font-family: var(--font-sans);
  font-size: 0.8125rem;
  line-height: 1.5;
  letter-spacing: 0.005em;
  font-weight: 400;
}

.font-label-code {
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  line-height: 1.4;
  letter-spacing: -0.01em;
  font-weight: 500;
}

.font-label-meta {
  font-family: var(--font-mono);
  font-size: 0.6875rem;
  line-height: 1.3;
  letter-spacing: 0.04em;
  font-weight: 500;
}

/* Material Symbols font setup */
.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}
`);

// src/app/layout.tsx
fs.writeFileSync('src/app/layout.tsx', `import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "NyayaCheck — Minimal Legal Metrology & Compliance Intelligence",
  description: "Official Legal Metrology statutory enforcement, packaged commodity compliance verification, and evidentiary audit platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={\`\${inter.variable} \${jetbrainsMono.variable}\`}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-surface font-body-md text-on-surface antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
`);

// src/components/ui/Badge.tsx
fs.writeFileSync('src/components/ui/Badge.tsx', `import React from 'react';
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
`);

// src/components/ui/Button.tsx
fs.writeFileSync('src/components/ui/Button.tsx', `import React from 'react';
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
`);

// src/components/ui/Card.tsx
fs.writeFileSync('src/components/ui/Card.tsx', `import React from 'react';
import { cn } from '@/lib/utils';

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div
    className={cn(
      'bg-surface-container-low rounded-xl border border-outline-variant/30 p-space-lg shadow-sm',
      className
    )}
    {...props}
  >
    {children}
  </div>
);

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={cn('flex flex-col space-y-1 pb-space-sm', className)} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className, children, ...props }) => (
  <h3 className={cn('font-headline-sm text-headline-sm text-primary font-semibold', className)} {...props}>
    {children}
  </h3>
);
`);

// src/components/ui/StatCard.tsx
fs.writeFileSync('src/components/ui/StatCard.tsx', `import React from 'react';
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
`);

// src/components/ui/Toast.tsx
fs.writeFileSync('src/components/ui/Toast.tsx', `import React from 'react';
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
`);

console.log('Setup 2 complete');
