'use client';

import { useState, useEffect, useCallback } from 'react';
import { getCurrentUser } from './api';

export interface OfficerProfile {
  id?: number;
  name: string;
  email: string;
  role: 'admin' | 'inspector';
  badge: string;
  avatar: string;
  phone: string;
  zonalUnit: string;
  jurisdiction: string;
}

export const DEFAULT_AVATAR =
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=256&h=256';

export const DEFAULT_OFFICER_PROFILE: OfficerProfile = {
  name: 'S.K. Ranganathan',
  email: 'sk.ranganathan@delhi.gov.in',
  role: 'inspector',
  badge: 'LM-DL-88392',
  avatar: DEFAULT_AVATAR,
  phone: '+91 98402 11983',
  zonalUnit: 'North Delhi',
  jurisdiction: 'North Delhi Zone II',
};

const STORAGE_KEY = 'nyayacheck_officer_profile';
const AUTH_USER_KEY = 'auth_user';
const EVENT_KEY = 'officer_profile_updated';

export function getSavedOfficerProfile(): OfficerProfile {
  if (typeof window === 'undefined') {
    return DEFAULT_OFFICER_PROFILE;
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    const authUserStr = localStorage.getItem(AUTH_USER_KEY);
    const authUser = authUserStr ? JSON.parse(authUserStr) : null;

    if (stored) {
      const parsed = JSON.parse(stored);
      if (authUser?.name && !parsed.hasCustomName) {
        parsed.name = authUser.name;
      }
      if (authUser?.email && !parsed.hasCustomEmail) {
        parsed.email = authUser.email;
      }
      return { ...DEFAULT_OFFICER_PROFILE, ...parsed };
    }

    if (authUser) {
      return {
        ...DEFAULT_OFFICER_PROFILE,
        name: authUser.name || DEFAULT_OFFICER_PROFILE.name,
        email: authUser.email || DEFAULT_OFFICER_PROFILE.email,
        role: authUser.role || 'inspector',
      };
    }
  } catch (err) {
    console.warn('Failed to load officer profile:', err);
  }

  return DEFAULT_OFFICER_PROFILE;
}

export function saveOfficerProfile(profile: Partial<OfficerProfile>): OfficerProfile {
  if (typeof window === 'undefined') return DEFAULT_OFFICER_PROFILE;

  try {
    const current = getSavedOfficerProfile();
    const updated: OfficerProfile = {
      ...current,
      ...profile,
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

    // Also update auth_user cache name & email if changed
    const authUserStr = localStorage.getItem(AUTH_USER_KEY);
    if (authUserStr) {
      const authUser = JSON.parse(authUserStr);
      if (profile.name) authUser.name = profile.name;
      if (profile.email) authUser.email = profile.email;
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(authUser));
    }

    window.dispatchEvent(new CustomEvent(EVENT_KEY, { detail: updated }));
    return updated;
  } catch (err) {
    console.error('Failed to save officer profile:', err);
    return DEFAULT_OFFICER_PROFILE;
  }
}

export function useOfficerProfile() {
  const [profile, setProfile] = useState<OfficerProfile>(() => getSavedOfficerProfile());

  const refreshProfile = useCallback(() => {
    setProfile(getSavedOfficerProfile());
  }, []);

  useEffect(() => {
    refreshProfile();

    // Check backend session if available
    getCurrentUser()
      .then((res) => {
        if (res.user) {
          localStorage.setItem(AUTH_USER_KEY, JSON.stringify(res.user));
          setProfile((prev) => {
            const updated = {
              ...prev,
              name: res.user!.name || prev.name,
              email: res.user!.email || prev.email,
              role: res.user!.role || prev.role,
            };
            return updated;
          });
        }
      })
      .catch(() => {
        // user not authenticated with backend session or offline
      });

    const handleUpdate = (e: Event) => {
      const customEvent = e as CustomEvent<OfficerProfile>;
      if (customEvent.detail) {
        setProfile(customEvent.detail);
      } else {
        refreshProfile();
      }
    };

    window.addEventListener(EVENT_KEY, handleUpdate);
    window.addEventListener('storage', handleUpdate);

    return () => {
      window.removeEventListener(EVENT_KEY, handleUpdate);
      window.removeEventListener('storage', handleUpdate);
    };
  }, [refreshProfile]);

  return {
    profile,
    updateProfile: saveOfficerProfile,
    refreshProfile,
  };
}
