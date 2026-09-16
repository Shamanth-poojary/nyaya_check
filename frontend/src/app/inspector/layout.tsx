'use client';

import React from 'react';
import { InspectorSidebar } from '@/components/layout/InspectorSidebar';
import { InspectorHeader } from '@/components/layout/InspectorHeader';

export default function InspectorLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-surface min-h-screen text-on-surface">
      <InspectorSidebar />
      <div className="pl-72">
        <InspectorHeader />
        <main className="w-full pt-16 bg-surface px-space-lg min-h-screen">
          {children}
        </main>
      </div>
    </div>
  );
}
