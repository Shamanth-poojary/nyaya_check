import base64
import os

files = {}

# 1. admin layout
files['src/app/admin/layout.tsx'] = """'use client';

import React from 'react';
import { AdminSidebar } from '@/components/layout/AdminSidebar';
import { AdminHeader } from '@/components/layout/AdminHeader';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-surface min-h-screen text-on-surface">
      <AdminSidebar />
      <div className="pl-72">
        <AdminHeader />
        <main className="w-full pt-16 bg-surface min-h-screen">
          {children}
        </main>
      </div>
    </div>
  );
}
"""

# 2. inspector layout
files['src/app/inspector/layout.tsx'] = """'use client';

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
"""

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created {path}")
