'use client';

import React, { useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Toast } from '@/components/ui/Toast';

const MOCK_USERS = [
  {
    id: 'u1',
    name: 'S.K. Ranganathan',
    badge: 'LM-DL-88392',
    role: 'Field Inspector',
    zone: 'North Delhi Zonal Node',
    status: 'active',
    lastActive: 'Today, 14:02 IST',
    device: 'Zebra TC57 Handheld',
  },
  {
    id: 'u2',
    name: 'Ananya Patnaik',
    badge: 'LM-DL-90411',
    role: 'Field Inspector',
    zone: 'Narela Wholesale Hub',
    status: 'active',
    lastActive: 'Today, 13:40 IST',
    device: 'Samsung Tab Active4',
  },
  {
    id: 'u3',
    name: 'Tenzing Jamatia',
    badge: 'LM-DL-74129',
    role: 'Senior Metrology Officer',
    zone: 'Kirti Nagar Storage Yard',
    status: 'active',
    lastActive: 'Today, 12:15 IST',
    device: 'Zebra TC57 Handheld',
  },
  {
    id: 'u4',
    name: 'Vikramaditya Katoch',
    badge: 'LM-HR-22081',
    role: 'Field Inspector',
    zone: 'Gurugram Logistics Node',
    status: 'active',
    lastActive: 'Today, 10:55 IST',
    device: 'Toughpad FZ-G1',
  },
  {
    id: 'u5',
    name: 'Priya Sundaram',
    badge: 'LM-KA-40192',
    role: 'Field Inspector',
    zone: 'South Logistics Hub',
    status: 'active',
    lastActive: 'Today, 09:30 IST',
    device: 'Samsung Tab Active4',
  },
];

export default function ManageUsersPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [showToast, setShowToast] = useState(false);
  const [toastMsg, setToastMsg] = useState('');

  const triggerToast = (msg: string) => {
    setToastMsg(msg);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const filteredUsers = MOCK_USERS.filter((u) =>
    u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.badge.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.zone.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex flex-col w-full px-space-lg py-space-lg max-w-7xl mx-auto gap-space-lg">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-md border-b border-outline-variant/40 pb-space-md">
        <div className="flex flex-col">
          <div className="flex items-center gap-space-xs text-on-surface-variant mb-1">
            <span className="font-label-meta text-label-meta uppercase tracking-wider">
              Jurisdiction Administration
            </span>
            <span className="text-outline-variant font-label-meta text-label-meta">•</span>
            <span className="font-label-meta text-label-meta uppercase tracking-wider text-secondary font-semibold">
              Officer Rosters
            </span>
          </div>
          <h2 className="font-headline-lg text-headline-lg text-on-surface tracking-tight font-semibold">
            Manage Officers & Terminals
          </h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
            Gazetted inspector accounts, device certificate handshakes, and zonal field assignments.
          </p>
        </div>
        <button
          onClick={() => triggerToast('Officer enrollment modal dispatched')}
          className="inline-flex items-center gap-1.5 px-space-md py-2.5 rounded-lg bg-primary text-on-primary font-body-sm text-body-sm font-semibold hover:bg-primary-container transition-colors shadow-sm cursor-pointer"
        >
          <span className="material-symbols-outlined text-[18px]">person_add</span>
          <span>Enroll New Officer</span>
        </button>
      </div>

      <div className="flex items-center justify-between gap-4">
        <div className="relative w-full max-w-md">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">
            search
          </span>
          <input
            className="w-full bg-surface-container-low pl-10 pr-space-md py-2.5 rounded-lg border border-outline-variant/50 font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary shadow-xs"
            placeholder="Search by Officer Name, Badge ID, or Zone..."
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <span className="font-label-meta text-label-meta uppercase tracking-wider text-on-surface-variant">
          Active: <strong className="text-primary">{filteredUsers.length} Officers</strong>
        </span>
      </div>

      <div className="bg-surface rounded-xl border border-outline-variant/40 shadow-sm overflow-hidden">
        <div className="overflow-x-auto w-full">
          <table className="w-full min-w-[800px] text-left border-collapse">
            <thead className="bg-surface-container-low border-b border-outline-variant/40 font-label-meta text-label-meta uppercase tracking-wider text-on-surface-variant">
              <tr>
                <th className="py-3 px-space-md">Officer / Badge</th>
                <th className="py-3 px-space-md">Department Role</th>
                <th className="py-3 px-space-md">Assigned Jurisdiction Node</th>
                <th className="py-3 px-space-md">Attested Hardware</th>
                <th className="py-3 px-space-md">Status</th>
                <th className="py-3 px-space-md text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/30 font-body-sm text-body-sm text-on-surface">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-surface-container-low/60 transition-colors">
                  <td className="py-3.5 px-space-md">
                    <div className="font-semibold text-on-surface">{user.name}</div>
                    <span className="font-label-code text-label-code text-on-surface-variant">
                      {user.badge}
                    </span>
                  </td>
                  <td className="py-3.5 px-space-md">{user.role}</td>
                  <td className="py-3.5 px-space-md">
                    <div className="flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[16px] text-on-surface-variant">
                        location_on
                      </span>
                      <span>{user.zone}</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-space-md font-label-meta text-label-meta">
                    {user.device}
                  </td>
                  <td className="py-3.5 px-space-md">
                    <Badge status="active">Active Duty</Badge>
                  </td>
                  <td className="py-3.5 px-space-md text-right">
                    <button
                      onClick={() => triggerToast(`Managing keys for ${user.name}`)}
                      className="px-3 py-1 rounded border border-outline-variant/50 bg-surface hover:bg-surface-container text-primary font-body-sm text-xs transition-colors cursor-pointer"
                    >
                      Configure Keys
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Toast show={showToast} title={toastMsg} />
    </div>
  );
}
