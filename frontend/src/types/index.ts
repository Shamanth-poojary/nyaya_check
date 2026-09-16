export type ReportStatus = 'compliant' | 'deficit' | 'review';

export interface InspectionReport {
  id: string;
  reportCode: string;
  productName: string;
  sku: string;
  location: string;
  zone: string;
  officerName: string;
  officerBadge: string;
  status: ReportStatus;
  timestamp: string;
  dateStr: string;
  findings: string;
  digitalSignature: string;
  mrp?: string;
  netQty?: string;
  mfgDate?: string;
  manufacturer?: string;
  consumerCare?: string;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  isoDate: string;
  officerName: string;
  officerInitials: string;
  badgeId: string;
  eventType: 'signin' | 'signout-manual' | 'signout-auto' | 'renew';
  eventLabel: string;
  deviceModel: string;
  deviceMeta: string;
  locationNode: string;
  coordinates: string;
  hashSeal: string;
}

export interface DeficitCategory {
  id: string;
  title: string;
  rule: string;
  percentage: string;
  packCount: string;
  severity: 'high' | 'medium' | 'low';
}

export interface RegionalRecord {
  id: string;
  zone: string;
  totalPackages: string;
  violations: string;
  deficitRate: string;
  isHighDeficit: boolean;
}

export interface MonthTrend {
  month: string;
  passRate: number;
  deficitRate: number;
  total: number;
}
