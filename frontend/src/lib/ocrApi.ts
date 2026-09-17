/**
 * lib/ocrApi.ts — Legal Metrology OCR & Compliance Verification Service Client.
 *
 * Connects frontend directly to the OCR microservice (FastAPI, PaddleOCR, Rules Engine v4.0).
 * Matches schemas defined in ocr-service/app/schemas/report.py, compliance.py, and response.py.
 */

export const OCR_BASE_URL =
  process.env.NEXT_PUBLIC_OCR_URL || 'http://localhost:8000';

// ---------------------------------------------------------------------------
// OCR & Extraction Schemas
// ---------------------------------------------------------------------------

export interface BoundingBox {
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

export interface RawOCRLine {
  text: string;
  bbox: BoundingBox;
  confidence: number;
  sourceImage?: string | null;
}

export interface Commodity {
  name?: string | null;
  category?: string | null;
  found: boolean;
  confidence: number;
  sourceImage?: string | null;
}

export interface PartyInfo {
  name?: string | null;
  address?: string | null;
  role?: string | null;
  found: boolean;
  confidence: number;
  sourceImage?: string | null;
}

export interface MRP {
  value?: number | null;
  currency: string;
  taxIncluded?: boolean | null;
  raw?: string | null;
  bbox?: BoundingBox | null;
  found: boolean;
  confidence: number;
  sourceImage?: string | null;
}

export interface NetQuantity {
  rawValue?: string | null;
  value?: number | null;
  unit?: string | null;
  quantityType?: string | null;
  normalizedValue?: number | null;
  normalizedUnit?: string | null;
  bbox?: BoundingBox | null;
  found: boolean;
  confidence: number;
  sourceImage?: string | null;
}

export interface DateField {
  raw?: string | null;
  dateType?: string | null;
  day?: number | null;
  month?: number | null;
  year?: number | null;
  bbox?: BoundingBox | null;
  found: boolean;
  confidence: number;
  sourceImage?: string | null;
}

export interface ConsumerCare {
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  website?: string | null;
  raw?: string | null;
  bbox?: BoundingBox | null;
  found: boolean;
  confidence: number;
  sourceImage?: string | null;
}

export interface VisualEvidence {
  contrast?: Record<string, { bucket: string; contrastRatio: number }>;
  readability?: Record<string, { readable: boolean; reason: string }>;
  principalDisplayPanel?: {
    likelySourceImage?: string | null;
    confidence?: number;
    pdpConfidence?: number;
    ruleCoverage?: number;
  } | null;
  netQuantityMedianRatio?: number | null;
  quantityClearance?: {
    clearanceAbovePx?: number;
    clearanceBelowPx?: number;
    hasAdequateClearance?: boolean;
  } | null;
}

export interface ExtractionResponse {
  schemaVersion: string;
  commodity: Commodity;
  manufacturer: PartyInfo;
  packer: PartyInfo;
  importer: PartyInfo;
  mrp: MRP;
  netQuantity: NetQuantity;
  dates: {
    manufacturing?: DateField;
    packing?: DateField;
    expiry?: DateField;
  };
  consumerCare: ConsumerCare;
  rawOcr?: RawOCRLine[];
  visual?: VisualEvidence;
  uncertainFields?: string[];
}

// ---------------------------------------------------------------------------
// Rules Engine & Compliance Schemas
// ---------------------------------------------------------------------------

export type ComplianceSeverity = 'blocking' | 'warning' | 'info' | 'needs_review';
export type OverallComplianceStatus = 'compliant' | 'non_compliant' | 'needs_review';

export interface RuleResult {
  ruleId: string;
  ruleReference: string;
  description: string;
  passed: boolean;
  severity: ComplianceSeverity;
  evidenceField?: string | null;
  evidenceValue?: string | null;
  evidenceConfidence?: number | null;
  sourceImage?: string | null;
  message: string;
}

export interface ComplianceSummary {
  totalChecks: number;
  passed: number;
  failed: number;
  needsReview: number;
  blocking: number;
  warnings: number;
  infos: number;
}

export interface ComplianceResult {
  schemaVersion: string;
  overallStatus: OverallComplianceStatus;
  ruleResults: RuleResult[];
  summary: ComplianceSummary;
}

// ---------------------------------------------------------------------------
// Product Summary & Authoritative ComplianceReport
// ---------------------------------------------------------------------------

export interface ProductSummary {
  commodityName?: string | null;
  commodityCategory?: string | null;
  manufacturerName?: string | null;
  packerName?: string | null;
  importerName?: string | null;
  netQuantity?: string | null;
  mrp?: string | null;
  manufacturingDate?: string | null;
  packingDate?: string | null;
  expiryDate?: string | null;
  batchNumber?: string | null;
  consumerCareContact?: string | null;
}

export interface ComplianceReport {
  schemaVersion: string;
  reportId: string;
  generatedAt: string;
  extraction: ExtractionResponse;
  compliance: ComplianceResult;
  productSummary: ProductSummary;
}

// ---------------------------------------------------------------------------
// API Methods
// ---------------------------------------------------------------------------

export interface CheckComplianceOptions {
  preprocess?: boolean;
  apiKey?: string;
  signal?: AbortSignal;
}

/**
 * Executes the full Legal Metrology compliance pipeline against 1 or more photos.
 * Submits photos to POST /v1/check (or fallback POST /check).
 */
export async function checkCompliance(
  images: File[] | Blob[],
  options?: CheckComplianceOptions
): Promise<ComplianceReport> {
  if (!images || images.length === 0) {
    throw new Error('At least one packaging image is required for compliance verification.');
  }

  const formData = new FormData();
  images.forEach((img, idx) => {
    const filename = img instanceof File ? img.name : `scan_photo_${idx + 1}.jpg`;
    formData.append('images', img, filename);
  });

  const queryParams = new URLSearchParams();
  if (options?.preprocess !== undefined) {
    queryParams.set('preprocess_enabled', String(options.preprocess));
  }
  queryParams.set('format', 'json');

  const headers: Record<string, string> = {
    Accept: 'application/json',
  };
  if (options?.apiKey) {
    headers['X-API-Key'] = options.apiKey;
  }

  const url = `${OCR_BASE_URL}/v1/check?${queryParams.toString()}`;

  let res: Response;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
      signal: options?.signal,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    throw new Error(
      `Failed to reach OCR microservice at ${OCR_BASE_URL}. Ensure the service is running (e.g. uvicorn app.main:app on port 8000). Error: ${message}`
    );
  }

  if (!res.ok) {
    let errorDetail = `OCR Service returned HTTP ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string'
          ? errJson.detail
          : JSON.stringify(errJson.detail);
      }
    } catch {
      // fallback to status text
      errorDetail = `${errorDetail}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }

  const report: ComplianceReport = await res.json();
  return report;
}

/**
 * Checks service health and connectivity.
 */
export async function checkOcrHealth(): Promise<{ status: string; version: string }> {
  try {
    const res = await fetch(`${OCR_BASE_URL}/v1/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });
    if (!res.ok) {
      throw new Error(`Health check failed with HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    throw new Error(`Cannot connect to OCR Service at ${OCR_BASE_URL}: ${message}`);
  }
}
