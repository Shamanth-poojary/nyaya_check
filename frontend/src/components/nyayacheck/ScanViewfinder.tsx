'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  checkCompliance,
  type ComplianceReport,
  type RuleResult,
} from '@/lib/ocrApi';
import { addInspectionReport } from '@/data/mockData';
import type { InspectionReport, ReportStatus } from '@/types';

export const ScanViewfinder: React.FC = () => {
  const router = useRouter();

  // Mode & files state
  const [mode, setMode] = useState<'upload' | 'camera'>('upload');
  const [files, setFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [selectedPreviewIndex, setSelectedPreviewIndex] = useState<number>(0);
  const [isDragging, setIsDragging] = useState(false);

  // File input ref for reliable programmatic click
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Camera stream state
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  // Pipeline execution state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState<string>('');
  const [preprocessEnabled, setPreprocessEnabled] = useState(false);
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccessCode, setSavedSuccessCode] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'rules'>('summary');

  // Initialize preview URLs when files change
  useEffect(() => {
    const urls = files.map((f) => URL.createObjectURL(f));
    setPreviewUrls(urls);
    if (urls.length > 0 && selectedPreviewIndex >= urls.length) {
      setSelectedPreviewIndex(0);
    }
    return () => {
      urls.forEach((u) => URL.revokeObjectURL(u));
    };
  }, [files]);

  // Clean up camera stream on unmount or mode switch
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  }, []);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  const startCamera = async () => {
    setCameraError(null);
    stopCamera();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setCameraError(`Camera access denied or unavailable (${msg}). Please use photo upload.`);
      setCameraActive(false);
    }
  };

  const handleModeSwitch = (newMode: 'upload' | 'camera') => {
    setMode(newMode);
    setError(null);
    if (newMode === 'camera') {
      startCamera();
    } else {
      stopCamera();
    }
  };

  // Capture frame from video to canvas
  const handleSnapPhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const capturedFile = new File([blob], `pdp_snap_${Date.now()}.jpg`, {
          type: 'image/jpeg',
        });
        setFiles((prev) => [...prev, capturedFile]);
        setSelectedPreviewIndex(files.length);
      },
      'image/jpeg',
      0.92
    );
  };

  // Helper to append validated files
  const addValidatedFiles = (incomingFiles: File[]) => {
    const valid: File[] = [];
    for (const f of incomingFiles) {
      if (f.size > 15 * 1024 * 1024) {
        alert(`File ${f.name} exceeds maximum allowed size of 15MB.`);
        continue;
      }
      valid.push(f);
    }
    if (valid.length > 0) {
      setFiles((prev) => [...prev, ...valid]);
      setError(null);
      if (mode === 'camera') {
        setMode('upload');
        stopCamera();
      }
    }
  };

  // Handle file uploads through input dialog
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const chosen = e.target.files ? Array.from(e.target.files) : [];
    if (chosen.length === 0) return;
    addValidatedFiles(chosen);
    // Reset input value so re-selecting same file triggers onChange
    e.target.value = '';
  };

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files).filter((f) =>
        f.type.startsWith('image/')
      );
      if (droppedFiles.length === 0) {
        setError('Please drop valid image files (JPEG, PNG, WebP).');
        return;
      }
      addValidatedFiles(droppedFiles);
    }
  };

  // 1-Click Demo Product Loader
  const handleLoadDemoPhoto = async () => {
    try {
      const res = await fetch('/sample_package.png');
      if (!res.ok) throw new Error('Sample image not found on server');
      const blob = await res.blob();
      const sampleFile = new File([blob], 'demo_packaged_commodity.png', {
        type: 'image/png',
      });
      setFiles([sampleFile]);
      setSelectedPreviewIndex(0);
      setMode('upload');
      stopCamera();
      setError(null);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`Failed to load demo photo: ${msg}`);
    }
  };

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    if (selectedPreviewIndex >= index && selectedPreviewIndex > 0) {
      setSelectedPreviewIndex((prev) => prev - 1);
    }
  };

  // Trigger OCR + Rules pipeline
  const handleRunScan = async () => {
    if (files.length === 0) {
      fileInputRef.current?.click();
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setSavedSuccessCode(null);

    // Multi-stage progress indicators
    setAnalysisStep('Uploading packaging photos to OCR service...');
    const timer1 = setTimeout(() => {
      setAnalysisStep('Detecting text boxes & Principal Display Panel (PaddleOCR)...');
    }, 1200);
    const timer2 = setTimeout(() => {
      setAnalysisStep('Classifying statutory declarations & visual contrast...');
    }, 2800);
    const timer3 = setTimeout(() => {
      setAnalysisStep('Evaluating Legal Metrology (Packaged Commodities) Rules, 2011...');
    }, 4500);

    try {
      const result = await checkCompliance(files, {
        preprocess: preprocessEnabled,
      });
      setReport(result);
      if (mode === 'camera') {
        stopCamera();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      setIsAnalyzing(false);
      setAnalysisStep('');
    }
  };

  // Confirm and persist report into register
  const handleConfirmReport = () => {
    if (!report) return;
    setIsSaving(true);

    const isDeficit = report.compliance.overallStatus === 'non_compliant';
    const isNeedsReview = report.compliance.overallStatus === 'needs_review';
    const status: ReportStatus = isDeficit ? 'deficit' : isNeedsReview ? 'review' : 'compliant';

    const pSummary = report.productSummary;
    const reportCode = `#REP-${Math.floor(10000 + Math.random() * 90000)}`;

    const newReport: InspectionReport = {
      id: report.reportId || String(Date.now()),
      reportCode,
      productName: pSummary.commodityName || 'Packaged Commodity Inspection',
      sku: pSummary.batchNumber || `PKG-${Date.now().toString().slice(-6)}`,
      location: 'Field Verification Node DL-01',
      zone: 'Zone Z-01',
      officerName: 'S.K. Ranganathan',
      officerBadge: 'LM-DL-88392',
      status,
      timestamp: new Date().toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        dateStyle: 'medium',
        timeStyle: 'short',
      }),
      dateStr: new Date().toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      }).toUpperCase(),
      findings: isDeficit
        ? `Statutory non-compliance detected. Evaluated ${report.compliance.summary.totalChecks} legal metrology checks (${report.compliance.summary.failed} violations, ${report.compliance.summary.passed} passed).`
        : `Statutory compliance verified across all ${report.compliance.summary.totalChecks} mandatory packaging rules.`,
      digitalSignature: `SHA-256: ${report.reportId.slice(0, 16)}... (Verified & Attested)`,
      mrp: pSummary.mrp || undefined,
      netQty: pSummary.netQuantity || undefined,
      mfgDate: pSummary.manufacturingDate || pSummary.packingDate || undefined,
      manufacturer: pSummary.manufacturerName || undefined,
      packer: pSummary.packerName || undefined,
      consumerCare: pSummary.consumerCareContact || undefined,
      category: pSummary.commodityCategory || undefined,
      sourceImages: previewUrls,
      rawReport: report,
      ruleResults: report.compliance.ruleResults,
      complianceSummary: report.compliance.summary,
    };

    addInspectionReport(newReport);
    setSavedSuccessCode(reportCode);
    setIsSaving(false);

    // Navigate to reports register with new report highlighted
    setTimeout(() => {
      router.push(`/inspector/reports?reportId=${encodeURIComponent(newReport.id)}`);
    }, 900);
  };

  const handleResetScan = () => {
    setReport(null);
    setFiles([]);
    setPreviewUrls([]);
    setError(null);
    setSavedSuccessCode(null);
    if (mode === 'camera') {
      startCamera();
    }
  };

  // Helper values for display
  const pSummary = report?.productSummary;
  const overallStatus = report?.compliance.overallStatus;
  const isViolation = overallStatus === 'non_compliant';
  const isReview = overallStatus === 'needs_review';

  // Extract rules requiring manual check, warning, or blocking violations
  const attentionRules = report?.compliance.ruleResults.filter(
    (r) => !r.passed || r.severity === 'needs_review' || r.severity === 'warning'
  ) || [];

  // Metadata mapping rule IDs to plain-English citizen explanations & actionable guidance
  const RULE_INFO: Record<string, { title: string; hint: string; action: string }> = {
    rule_6_commodity_identity: {
      title: 'Product / Brand Name',
      hint: 'Under Rule 6(1)(a), every package must clearly state what commodity it is (e.g. "Lemon Soda", "Atta", "Hair Oil") on the front panel so buyers know what they are purchasing.',
      action: 'Check the front of the package. If the product name is printed there, confirm it matches. You can also snap a clearer, well-lit photo of the front label.',
    },
    rule_6_mrp_declaration: {
      title: 'Maximum Retail Price (MRP)',
      hint: 'Under Rule 6(1)(e), the price must be clearly printed in Indian Rupees (₹) and must state "Inclusive of all taxes".',
      action: 'Check that the price on the neck, cap, or body of the pack is legible and includes tax indication.',
    },
    rule_6_net_quantity: {
      title: 'Net Weight / Volume',
      hint: 'Under Rule 6(1)(f) & Rule 12, the net quantity must be printed in standard metric units (ml, l, g, kg).',
      action: 'Verify that the net quantity is clearly declared and easy to read.',
    },
    rule_14_numeral_height: {
      title: 'Letter & Number Print Height',
      hint: 'Under Rule 14, printed numbers (like volume or weight) must meet a minimum height (e.g. at least 4 mm for 500g–1kg packs) so they cannot be printed in tiny, deceptive text.',
      action: 'Verify physically on the bottle/pack that the net quantity numbers are at least 4 mm tall and not printed in tiny font.',
    },
    rule_6_date_of_packing: {
      title: 'Date of Packing / Manufacture',
      hint: 'Under Rule 6(1)(d), the month and year of packaging or manufacture must be printed so consumers know when the product was packed.',
      action: 'Check the neck, cap, or base of the bottle for printed manufacturing or expiry dates.',
    },
    rule_6_manufacturer_packer: {
      title: 'Manufacturer / Packer Name & Address',
      hint: 'Under Rule 6(1)(b), the full legal company name and postal address with city and PIN code must be visible.',
      action: 'Ensure the panel containing the complete manufacturer or packer address is captured clearly.',
    },
    rule_6_consumer_care: {
      title: 'Consumer Grievance Care Contact',
      hint: 'Under Rule 6(1)(n), a customer helpline telephone number, email, or postal address must be provided for consumer complaints.',
      action: 'Ensure the customer care phone number or email address on the label is clearly legible.',
    },
    rule_13_unit_validity: {
      title: 'Standard Metric Units',
      hint: 'Under Rule 13, packages must use standard metric units (g, kg, ml, l) without misleading non-standard symbols.',
      action: 'Verify standard symbols are used without typographical errors.',
    },
    rule_7_10_readability: {
      title: 'Visual Readability & Clarity',
      hint: 'Statutory declarations must have clear contrast and must not be hidden or obscured by glossy glare.',
      action: 'Avoid strong glare or reflections when taking photos of glossy or transparent bottles.',
    },
    rule_7_10_contrast: {
      title: 'Text-to-Background Contrast',
      hint: 'Printed text must stand out distinctly from the background color so it can be read without straining.',
      action: 'Check that text printed on transparent plastic or dark backgrounds is legible.',
    },
    rule_7_10_font_ratio: {
      title: 'Declaration Prominence',
      hint: 'Mandatory information must not be printed in miniscule font compared to surrounding advertising slogans.',
      action: 'Ensure declarations are prominently positioned on the principal display panel.',
    },
    rule_schedules_dimensions: {
      title: 'Physical Dimensions',
      hint: 'Commodities like garments or cables must state physical length and width dimensions.',
      action: 'Verify dimensions if applicable to this commodity category.',
    },
    rule_schedules_standard_quantities: {
      title: 'Prescribed Standard Size',
      hint: 'Certain staple commodities like tea, oil, and biscuits must be sold in prescribed standard pack sizes under Schedule-II.',
      action: 'Verify that this pack complies with schedule standard quantities.',
    },
  };

  const getFriendlyRuleDetails = (ruleId: string) => {
    return (
      RULE_INFO[ruleId] || {
        title: ruleId.replace(/_/g, ' ').replace(/^rule \d+ /i, '').replace(/\b\w/g, (c) => c.toUpperCase()),
        hint: 'This statutory packaging declaration is required under the Legal Metrology (Packaged Commodities) Rules, 2011.',
        action: 'Verify this declaration physically on the product packaging.',
      }
    );
  };

  // Maps core statutory fields to their actual rules engine evaluation result
  const getFieldAudit = (field: 'commodity' | 'mrp' | 'net_quantity' | 'date' | 'manufacturer' | 'consumer_care') => {
    if (!report) return null;
    const results = report.compliance.ruleResults;
    switch (field) {
      case 'commodity':
        return results.find((r) => r.ruleId === 'rule_6_commodity_identity');
      case 'mrp':
        return results.find((r) => r.ruleId === 'rule_6_mrp_declaration');
      case 'net_quantity': {
        const numHeight = results.find((r) => r.ruleId === 'rule_14_numeral_height');
        if (numHeight && (!numHeight.passed || numHeight.severity === 'needs_review' || numHeight.severity === 'warning')) {
          return numHeight;
        }
        return results.find((r) => r.ruleId === 'rule_6_net_quantity') || numHeight;
      }
      case 'date':
        return results.find((r) => r.ruleId === 'rule_6_date_of_packing');
      case 'manufacturer':
        return results.find((r) => r.ruleId === 'rule_6_manufacturer_packer');
      case 'consumer_care':
        return results.find((r) => r.ruleId === 'rule_6_consumer_care');
    }
  };

  const commodityAudit = getFieldAudit('commodity');
  const mrpAudit = getFieldAudit('mrp');
  const netQtyAudit = getFieldAudit('net_quantity');
  const dateAudit = getFieldAudit('date');
  const mfgAudit = getFieldAudit('manufacturer');
  const careAudit = getFieldAudit('consumer_care');

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-space-lg items-start">
      {/* Hidden Global File Input for Reliable Browser Compatibility */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple
        className="hidden"
        onChange={handleFileInput}
      />

      {/* LEFT: Industrial Viewfinder & Photo Stream */}
      <div className="xl:col-span-7 flex flex-col gap-space-md">
        {/* Main Viewfinder Frame & Dropzone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative w-full aspect-[4/3] sm:aspect-[16/11] bg-surface-container-highest rounded-2xl overflow-hidden shadow-sm border transition-all select-none ${
            isDragging
              ? 'border-secondary border-2 bg-secondary/10'
              : 'border-outline-variant group'
          }`}
        >
          {mode === 'camera' ? (
            <div className="relative w-full h-full bg-black flex items-center justify-center">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className={`w-full h-full object-cover ${cameraActive ? 'block' : 'hidden'}`}
              />
              {!cameraActive && (
                <div className="p-6 text-center text-on-surface-variant flex flex-col items-center gap-2">
                  <span className="material-symbols-outlined text-[36px] text-primary">videocam_off</span>
                  <p className="font-body-sm text-body-sm text-surface max-w-sm">
                    {cameraError || 'Camera is inactive. Click "Start Camera" or switch to Photo Upload.'}
                  </p>
                  <button
                    type="button"
                    onClick={startCamera}
                    className="mt-2 px-4 py-2 rounded-xl bg-primary text-on-primary text-xs font-semibold cursor-pointer"
                  >
                    Start Camera
                  </button>
                </div>
              )}
            </div>
          ) : previewUrls.length > 0 ? (
            <img
              src={previewUrls[selectedPreviewIndex]}
              alt={`Packaging inspection photo ${selectedPreviewIndex + 1}`}
              className="w-full h-full object-contain bg-black/90 transition-all duration-200"
            />
          ) : (
            <div
              onClick={() => fileInputRef.current?.click()}
              className="w-full h-full flex flex-col items-center justify-center p-6 text-center text-on-surface-variant bg-surface-container-high/40 cursor-pointer hover:bg-surface-container-high/70 transition-colors"
            >
              <div className="w-16 h-16 rounded-full bg-surface shadow-xs flex items-center justify-center text-primary mb-3">
                <span className="material-symbols-outlined text-[36px]">cloud_upload</span>
              </div>
              <p className="font-headline-sm text-headline-sm text-primary font-bold">
                Click to Upload or Drag Photos Here
              </p>
              <p className="font-body-sm text-body-sm text-on-surface-variant max-w-sm mt-1">
                Attach packaging photos (Front PDP, Back, Side Panels, MRP area) to execute statutory verification.
              </p>
              <div className="mt-4 flex items-center gap-2">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    fileInputRef.current?.click();
                  }}
                  className="px-4 py-2 rounded-xl bg-primary text-on-primary font-body-sm text-body-sm font-semibold shadow-xs hover:bg-primary-container transition-colors cursor-pointer"
                >
                  Browse Files
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleLoadDemoPhoto();
                  }}
                  className="px-3.5 py-2 rounded-xl border border-outline-variant bg-surface hover:bg-surface-container font-body-sm text-body-sm text-primary font-medium transition-colors cursor-pointer"
                >
                  Load Sample Photo
                </button>
              </div>
            </div>
          )}

          {/* Statutory PDP Target Alignment Overlay */}
          <div className="absolute inset-8 sm:inset-12 pointer-events-none flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div className="w-7 h-7 border-t-2 border-l-2 border-surface shadow-sm"></div>
              <div className="w-7 h-7 border-t-2 border-r-2 border-surface shadow-sm"></div>
            </div>
            <div className="self-center px-3.5 py-1.5 rounded-full bg-primary/80 backdrop-blur-md text-surface font-body-sm text-body-sm shadow-sm flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px] text-secondary">
                center_focus_strong
              </span>
              <span>Place Principal Display Panel (PDP) inside frame</span>
            </div>
            <div className="flex items-end justify-between">
              <div className="w-7 h-7 border-b-2 border-l-2 border-surface shadow-sm"></div>
              <div className="w-7 h-7 border-b-2 border-r-2 border-surface shadow-sm"></div>
            </div>
          </div>

          {/* Hidden Canvas for Camera Snapshot */}
          <canvas ref={canvasRef} className="hidden" />

          {/* Analyzing HUD Overlay */}
          {isAnalyzing && (
            <div className="absolute inset-0 bg-primary/75 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center text-white z-20">
              <div className="w-12 h-12 border-3 border-secondary border-t-transparent rounded-full animate-spin mb-4"></div>
              <p className="font-headline-sm text-headline-sm font-semibold tracking-wide">
                Processing Legal Metrology Scan
              </p>
              <p className="font-body-sm text-body-sm text-surface/90 max-w-md mt-2 font-mono">
                {analysisStep}
              </p>
            </div>
          )}
        </div>

        {/* Thumbnail Gallery (Multi-Image Support) */}
        {previewUrls.length > 0 && (
          <div className="flex items-center gap-2.5 overflow-x-auto pb-1">
            {previewUrls.map((url, idx) => (
              <div
                key={idx}
                className={`relative w-20 h-16 rounded-xl overflow-hidden border-2 shrink-0 cursor-pointer transition-all ${
                  selectedPreviewIndex === idx
                    ? 'border-primary shadow-sm scale-105'
                    : 'border-outline-variant/60 opacity-80 hover:opacity-100'
                }`}
                onClick={() => {
                  setSelectedPreviewIndex(idx);
                  if (mode === 'camera') setMode('upload');
                }}
              >
                <img
                  src={url}
                  alt={`Thumb ${idx + 1}`}
                  className="w-full h-full object-cover bg-black"
                />
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveFile(idx);
                  }}
                  className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/70 hover:bg-error text-white flex items-center justify-center text-xs cursor-pointer"
                  title="Remove image"
                >
                  ✕
                </button>
                <span className="absolute bottom-0.5 left-1 text-[10px] font-mono text-white/90 bg-black/60 px-1 rounded">
                  #{idx + 1}
                </span>
              </div>
            ))}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-20 h-16 rounded-xl border-2 border-dashed border-outline-variant/70 hover:border-primary flex flex-col items-center justify-center text-on-surface-variant hover:text-primary cursor-pointer shrink-0 transition-colors bg-surface-container-low"
            >
              <span className="material-symbols-outlined text-[20px]">add_photo_alternate</span>
              <span className="text-[10px] font-medium mt-0.5">+ Add Photo</span>
            </button>
          </div>
        )}

        {/* Controls Bar */}
        <div className="bg-surface-container-lowest p-space-md rounded-2xl flex flex-wrap items-center justify-between gap-space-md border border-outline-variant shadow-sm">
          {/* Mode Switcher & Input Controls */}
          <div className="flex items-center gap-2">
            <div className="inline-flex rounded-xl p-1 bg-surface-container border border-outline-variant/40">
              <button
                type="button"
                onClick={() => handleModeSwitch('upload')}
                className={`px-3 py-1.5 rounded-lg font-body-sm text-body-sm font-medium transition-colors cursor-pointer flex items-center gap-1.5 ${
                  mode === 'upload'
                    ? 'bg-surface text-primary shadow-xs font-semibold'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">upload_file</span>
                <span>Upload</span>
              </button>
              <button
                type="button"
                onClick={() => handleModeSwitch('camera')}
                className={`px-3 py-1.5 rounded-lg font-body-sm text-body-sm font-medium transition-colors cursor-pointer flex items-center gap-1.5 ${
                  mode === 'camera'
                    ? 'bg-surface text-primary shadow-xs font-semibold'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">photo_camera</span>
                <span>Live Camera</span>
              </button>
            </div>

            {mode === 'upload' ? (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center gap-2 h-10 px-3.5 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-body-sm text-body-sm font-medium transition-colors cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">add_circle</span>
                  <span>Select Photos</span>
                </button>
                {files.length === 0 && (
                  <button
                    type="button"
                    onClick={handleLoadDemoPhoto}
                    className="inline-flex items-center gap-1.5 h-10 px-3 rounded-xl border border-outline-variant/60 hover:bg-surface-container text-on-surface-variant font-body-sm text-body-sm font-medium transition-colors cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[16px]">science</span>
                    <span>Load Demo</span>
                  </button>
                )}
              </div>
            ) : (
              <button
                type="button"
                onClick={handleSnapPhoto}
                disabled={!cameraActive || isAnalyzing}
                className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-secondary text-on-primary hover:bg-secondary/90 disabled:opacity-50 font-body-sm text-body-sm font-semibold cursor-pointer shadow-xs transition-colors"
              >
                <span className="material-symbols-outlined text-[18px]">camera</span>
                <span>Snap Photo ({files.length} ready)</span>
              </button>
            )}
          </div>

          {/* Preprocess Toggle & Action Button */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setPreprocessEnabled(!preprocessEnabled)}
              className={`px-3 py-1.5 rounded-xl border text-xs font-label-code transition-colors cursor-pointer flex items-center gap-1.5 ${
                preprocessEnabled
                  ? 'bg-secondary-container text-on-secondary-container border-secondary/40 font-semibold'
                  : 'border-outline-variant/60 text-on-surface-variant hover:bg-surface-container'
              }`}
              title="Enhance contrast for faint or glossy packages via OpenCV CLAHE"
            >
              <span className="material-symbols-outlined text-[14px]">
                {preprocessEnabled ? 'tune' : 'auto_fix_normal'}
              </span>
              <span>CLAHE Preprocess: {preprocessEnabled ? 'ON' : 'OFF'}</span>
            </button>

            <button
              type="button"
              onClick={handleRunScan}
              disabled={isAnalyzing}
              className="flex items-center gap-2 bg-primary text-on-primary px-5 h-10 rounded-xl shadow-sm hover:bg-primary-container disabled:opacity-50 active:scale-[0.98] transition-all font-body-md text-body-md font-semibold cursor-pointer"
            >
              <span className="material-symbols-outlined text-[20px]">
                {isAnalyzing ? 'sync' : 'document_scanner'}
              </span>
              <span>
                {isAnalyzing
                  ? 'Scanning...'
                  : files.length === 0
                  ? 'Choose Images'
                  : `Scan Package (${files.length})`}
              </span>
            </button>
          </div>
        </div>

        {/* Status / Error Toast */}
        {error && (
          <div className="p-space-md rounded-xl bg-error-container/40 border border-error/30 text-on-error-container font-body-sm text-body-sm flex items-start gap-3">
            <span className="material-symbols-outlined text-error text-[20px] shrink-0 mt-0.5">
              error
            </span>
            <div className="flex-1">
              <p className="font-semibold text-error">Scan Error</p>
              <p className="mt-0.5 leading-relaxed">{error}</p>
            </div>
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-on-error-container/70 hover:text-on-error-container text-xs font-bold cursor-pointer"
            >
              ✕
            </button>
          </div>
        )}

        {savedSuccessCode && (
          <div className="p-space-md rounded-xl bg-secondary-container/50 border border-secondary/30 text-on-secondary-container font-body-sm text-body-sm flex items-center gap-3">
            <span className="material-symbols-outlined text-secondary text-[20px] shrink-0">
              check_circle
            </span>
            <p className="font-medium">
              Report registered as <strong className="font-mono">{savedSuccessCode}</strong>. Redirecting to statutory log...
            </p>
          </div>
        )}
      </div>

      {/* RIGHT: Extracted Statutory Findings & Compliance HUD */}
      <div className="xl:col-span-5 flex flex-col gap-space-md">
        <div className="bg-surface-container-lowest rounded-2xl p-space-lg flex flex-col gap-space-md border border-outline-variant shadow-sm">
          {/* Header */}
          <div className="flex items-start justify-between gap-space-sm pb-space-sm border-b border-outline-variant">
            <div className="flex flex-col">
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`w-2 h-2 rounded-full ${
                    !report
                      ? 'bg-outline'
                      : isViolation
                      ? 'bg-error'
                      : isReview
                      ? 'bg-amber-500'
                      : 'bg-secondary'
                  }`}
                ></span>
                <span
                  className={`font-label-meta text-label-meta uppercase font-semibold tracking-wider ${
                    !report
                      ? 'text-on-surface-variant'
                      : isViolation
                      ? 'text-error'
                      : isReview
                      ? 'text-amber-700'
                      : 'text-secondary'
                  }`}
                >
                  {report ? 'Statutory Audit Findings' : 'Awaiting Inspection'}
                </span>
              </div>
              <h2 className="font-headline-sm text-headline-sm text-primary font-bold">
                {pSummary?.commodityName ||
                  (report
                    ? pSummary?.commodityCategory
                      ? `${pSummary.commodityCategory.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())} Pack (Brand Unverified)`
                      : 'Consumer Pack (Brand Unverified)'
                    : 'Package Inspection')}
              </h2>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
                {pSummary?.commodityCategory ? (
                  <span className="capitalize font-medium text-primary">
                    Category: {pSummary.commodityCategory.replace(/_/g, ' ')}
                  </span>
                ) : (
                  <span>Ready for image capture & metrology audit</span>
                )}
              </p>
            </div>

            {/* Top Status Pill */}
            {report && (
              <div className="flex flex-col items-end shrink-0">
                {isViolation ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-error-container text-on-error-container font-label-code text-label-code font-semibold">
                    <span className="material-symbols-outlined text-[15px]">error</span>
                    <span>Deficit Detected</span>
                  </span>
                ) : isReview ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-100 text-amber-900 font-label-code text-label-code font-semibold">
                    <span className="material-symbols-outlined text-[15px]">warning</span>
                    <span>Review Required ({attentionRules.length})</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-container text-on-secondary-container font-label-code text-label-code font-semibold">
                    <span className="material-symbols-outlined text-[15px]">check</span>
                    <span>100% Compliant</span>
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Compliance Verdict Banner */}
          {report ? (
            <div
              className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl font-body-sm text-body-sm font-medium ${
                isViolation
                  ? 'bg-error-container/40 text-on-error-container border border-error/20'
                  : isReview
                  ? 'bg-amber-100/80 text-amber-950 border border-amber-300/60'
                  : 'bg-secondary-container/40 text-on-secondary-container border border-secondary/20'
              }`}
            >
              <span
                className={`material-symbols-outlined text-[20px] shrink-0 ${
                  isViolation ? 'text-error' : isReview ? 'text-amber-700' : 'text-secondary'
                }`}
              >
                {isViolation ? 'error' : isReview ? 'help' : 'verified'}
              </span>
              <span className="leading-snug">
                {isViolation
                  ? `${report.compliance.summary.failed} Packaging Deficit(s) Found (${report.compliance.summary.passed} Passed)`
                  : isReview
                  ? `${attentionRules.length} Packaging Detail${attentionRules.length > 1 ? 's' : ''} Need Quick Verification (${report.compliance.summary.passed} Passed Automatically)`
                  : `All ${report.compliance.summary.totalChecks} Mandatory Declarations Verified`}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-container font-body-sm text-body-sm text-on-surface-variant">
              <span className="material-symbols-outlined text-[18px]">info</span>
              <span>Upload or capture product photos and click "Scan Package" to execute audit.</span>
            </div>
          )}

          {/* Plain-English Attention Callout for Citizens & Inspectors */}
          {report && attentionRules.length > 0 && (
            <div className="rounded-xl p-3 bg-amber-50 border border-amber-200/90 flex flex-col gap-2.5 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-amber-950 font-bold text-xs uppercase tracking-wider">
                  <span className="material-symbols-outlined text-[17px] text-amber-700">announcement</span>
                  {attentionRules.length} Item{attentionRules.length > 1 ? 's' : ''} Requiring Attention
                </span>
                <span className="text-[11px] text-amber-850 font-medium">Citizen & Inspector Checklist</span>
              </div>
              <div className="flex flex-col gap-2">
                {attentionRules.map((rule) => {
                  const info = getFriendlyRuleDetails(rule.ruleId);
                  const isBlocking = rule.severity === 'blocking' || !rule.passed;
                  return (
                    <div
                      key={rule.ruleId}
                      className={`rounded-lg p-2.5 bg-white border flex flex-col gap-1.5 shadow-2xs ${
                        isBlocking ? 'border-red-200 bg-red-50/20' : 'border-amber-200 bg-amber-50/30'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-primary text-xs flex items-center gap-1.5">
                          <span
                            className={`w-2 h-2 rounded-full shrink-0 ${
                              isBlocking ? 'bg-error' : 'bg-amber-500'
                            }`}
                          ></span>
                          {info.title}
                        </span>
                        <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-medium">
                          {rule.ruleReference || 'Legal Metrology'}
                        </span>
                      </div>

                      {/* What is the specific issue? */}
                      <p className="text-on-surface text-[11.5px] leading-relaxed">
                        <strong className={isBlocking ? 'text-error font-semibold' : 'text-amber-950 font-semibold'}>
                          Issue:{' '}
                        </strong>
                        {rule.message || rule.description}
                      </p>

                      {/* Actionable guidance for normal citizen / inspector */}
                      <div className="flex items-start gap-1.5 text-[11px] text-on-surface-variant bg-surface-container-low px-2 py-1.5 rounded-md">
                        <span className="material-symbols-outlined text-[15px] text-primary shrink-0 mt-0.5">
                          lightbulb
                        </span>
                        <span>
                          <strong className="text-primary font-medium">How to verify: </strong>
                          {info.action}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Tab Navigation: Declarations vs Rule Details */}
          {report && (
            <div className="flex items-center gap-1 border-b border-outline-variant/40 pb-1">
              <button
                type="button"
                onClick={() => setActiveTab('summary')}
                className={`px-3 py-1 rounded-lg text-xs font-medium cursor-pointer transition-colors ${
                  activeTab === 'summary'
                    ? 'bg-surface-container-high text-primary font-bold'
                    : 'text-on-surface-variant hover:text-primary'
                }`}
              >
                Statutory Declarations
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('rules')}
                className={`px-3 py-1 rounded-lg text-xs font-medium cursor-pointer transition-colors ${
                  activeTab === 'rules'
                    ? 'bg-surface-container-high text-primary font-bold'
                    : 'text-on-surface-variant hover:text-primary'
                }`}
              >
                Rule Audits ({report.compliance.ruleResults.length})
              </button>
            </div>
          )}

          {/* TAB 1: Key Mandatory Declarations */}
          {(!report || activeTab === 'summary') && (
            <div className="flex flex-col divide-y divide-outline-variant">
              {/* 1. Product / Commodity Name */}
              <div className="flex items-start justify-between py-2.5 gap-2">
                <div className="flex flex-col flex-1">
                  <span className="font-body-sm text-body-sm text-on-surface-variant">Product / Commodity Name</span>
                  <span className="font-body-md text-body-md text-primary font-semibold">
                    {pSummary?.commodityName || (report ? 'Not Identified on Scanned Panels' : '—')}
                  </span>
                  {report && commodityAudit && (!commodityAudit.passed || commodityAudit.severity === 'needs_review') && (
                    <span className="text-[11px] text-amber-800 font-medium mt-0.5">
                      Brand name unconfirmed on label. Check front of pack.
                    </span>
                  )}
                </div>
                {report && (
                  <span
                    className={`inline-flex items-center gap-1 font-label-code text-label-code font-semibold shrink-0 ${
                      !commodityAudit || commodityAudit.passed
                        ? 'text-secondary'
                        : commodityAudit.severity === 'blocking'
                        ? 'text-error'
                        : 'text-amber-700'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {!commodityAudit || commodityAudit.passed
                        ? 'check_circle'
                        : commodityAudit.severity === 'blocking'
                        ? 'error'
                        : 'warning'}
                    </span>
                    {!commodityAudit || commodityAudit.passed
                      ? 'Rule 6(1)(a) Pass'
                      : commodityAudit.severity === 'blocking'
                      ? 'Missing'
                      : 'Verify Brand'}
                  </span>
                )}
              </div>

              {/* 2. Net Quantity */}
              <div className="flex items-start justify-between py-2.5 gap-2">
                <div className="flex flex-col flex-1">
                  <span className="font-body-sm text-body-sm text-on-surface-variant">Net Quantity</span>
                  <span className="font-headline-sm text-headline-sm text-primary font-semibold">
                    {pSummary?.netQuantity || (report ? 'Not Found' : '—')}
                  </span>
                  {report && netQtyAudit && (!netQtyAudit.passed || netQtyAudit.severity === 'needs_review') && (
                    <span className="text-[11px] text-amber-800 font-medium mt-0.5">
                      {netQtyAudit.message || 'Check physically: numeral font must be ≥ 4mm tall.'}
                    </span>
                  )}
                </div>
                {report && (
                  <span
                    className={`inline-flex items-center gap-1 font-label-code text-label-code font-semibold shrink-0 ${
                      netQtyAudit && netQtyAudit.severity === 'needs_review'
                        ? 'text-amber-700'
                        : netQtyAudit && (!netQtyAudit.passed || netQtyAudit.severity === 'blocking')
                        ? 'text-error'
                        : pSummary?.netQuantity
                        ? 'text-secondary'
                        : 'text-error'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {netQtyAudit && netQtyAudit.severity === 'needs_review'
                        ? 'warning'
                        : netQtyAudit && (!netQtyAudit.passed || netQtyAudit.severity === 'blocking')
                        ? 'error'
                        : pSummary?.netQuantity
                        ? 'check_circle'
                        : 'error'}
                    </span>
                    {netQtyAudit && netQtyAudit.severity === 'needs_review'
                      ? 'Check Print Height'
                      : netQtyAudit && (!netQtyAudit.passed || netQtyAudit.severity === 'blocking')
                      ? 'Deficit Detected'
                      : pSummary?.netQuantity
                      ? 'Rule 12 Compliant'
                      : 'Missing'}
                  </span>
                )}
              </div>

              {/* 3. Retail Sale Price (MRP) */}
              <div className="flex items-start justify-between py-2.5 gap-2">
                <div className="flex flex-col flex-1">
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    Retail Sale Price (MRP)
                  </span>
                  <span className="font-headline-sm text-headline-sm text-primary font-semibold">
                    {pSummary?.mrp || (report ? 'Not Declared' : '—')}
                  </span>
                  {report && mrpAudit && (!mrpAudit.passed || mrpAudit.severity === 'needs_review') && (
                    <span className="text-[11px] text-amber-800 font-medium mt-0.5">
                      {mrpAudit.message}
                    </span>
                  )}
                </div>
                {report && (
                  <span
                    className={`inline-flex items-center gap-1 font-label-code text-label-code font-semibold shrink-0 ${
                      mrpAudit && mrpAudit.severity === 'needs_review'
                        ? 'text-amber-700'
                        : mrpAudit && (!mrpAudit.passed || mrpAudit.severity === 'blocking')
                        ? 'text-error'
                        : pSummary?.mrp
                        ? 'text-secondary'
                        : 'text-error'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {mrpAudit && mrpAudit.severity === 'needs_review'
                        ? 'warning'
                        : mrpAudit && (!mrpAudit.passed || mrpAudit.severity === 'blocking')
                        ? 'error'
                        : pSummary?.mrp
                        ? 'check_circle'
                        : 'error'}
                    </span>
                    {mrpAudit && mrpAudit.severity === 'needs_review'
                      ? 'Verify MRP'
                      : mrpAudit && (!mrpAudit.passed || mrpAudit.severity === 'blocking')
                      ? 'Deficit Detected'
                      : pSummary?.mrp
                      ? 'Rule 6(1)(e) Pass'
                      : 'Missing'}
                  </span>
                )}
              </div>

              {/* 4. Date of Packing / Mfg */}
              <div className="flex items-start justify-between py-2.5 gap-2">
                <div className="flex flex-col flex-1">
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    Date of Packing / Mfg
                  </span>
                  <span className="font-headline-sm text-headline-sm text-primary font-semibold">
                    {pSummary?.packingDate || pSummary?.manufacturingDate || (report ? 'Not Declared' : '—')}
                  </span>
                  {report && dateAudit && (!dateAudit.passed || dateAudit.severity === 'needs_review') && (
                    <span className="text-[11px] text-amber-800 font-medium mt-0.5">
                      {dateAudit.message}
                    </span>
                  )}
                </div>
                {report && (
                  <span
                    className={`inline-flex items-center gap-1 font-label-code text-label-code font-semibold shrink-0 ${
                      dateAudit && dateAudit.severity === 'needs_review'
                        ? 'text-amber-700'
                        : dateAudit && (!dateAudit.passed || dateAudit.severity === 'blocking')
                        ? 'text-error'
                        : pSummary?.packingDate || pSummary?.manufacturingDate
                        ? 'text-secondary'
                        : 'text-amber-700'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {dateAudit && dateAudit.severity === 'needs_review'
                        ? 'warning'
                        : dateAudit && (!dateAudit.passed || dateAudit.severity === 'blocking')
                        ? 'error'
                        : pSummary?.packingDate || pSummary?.manufacturingDate
                        ? 'check_circle'
                        : 'warning'}
                    </span>
                    {dateAudit && dateAudit.severity === 'needs_review'
                      ? 'Verify Date Format'
                      : dateAudit && (!dateAudit.passed || dateAudit.severity === 'blocking')
                      ? 'Missing Date'
                      : pSummary?.packingDate || pSummary?.manufacturingDate
                      ? 'Rule 6(1)(d) Pass'
                      : 'Uncertain'}
                  </span>
                )}
              </div>

              {/* 5. Manufacturer / Packer */}
              <div className="flex items-start justify-between py-2.5 gap-2">
                <div className="flex flex-col flex-1">
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    Manufacturer / Packer
                  </span>
                  <span className="font-body-md text-body-md text-primary font-semibold truncate max-w-[220px]">
                    {pSummary?.manufacturerName || pSummary?.packerName || (report ? 'Not Declared' : '—')}
                  </span>
                  {report && mfgAudit && (!mfgAudit.passed || mfgAudit.severity === 'needs_review') && (
                    <span className="text-[11px] text-amber-800 font-medium mt-0.5">
                      {mfgAudit.message}
                    </span>
                  )}
                </div>
                {report && (
                  <span
                    className={`inline-flex items-center gap-1 font-label-code text-label-code font-semibold shrink-0 ${
                      mfgAudit && mfgAudit.severity === 'needs_review'
                        ? 'text-amber-700'
                        : mfgAudit && (!mfgAudit.passed || mfgAudit.severity === 'blocking')
                        ? 'text-error'
                        : pSummary?.manufacturerName || pSummary?.packerName
                        ? 'text-secondary'
                        : 'text-error'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {mfgAudit && mfgAudit.severity === 'needs_review'
                        ? 'warning'
                        : mfgAudit && (!mfgAudit.passed || mfgAudit.severity === 'blocking')
                        ? 'error'
                        : pSummary?.manufacturerName || pSummary?.packerName
                        ? 'check_circle'
                        : 'error'}
                    </span>
                    {mfgAudit && mfgAudit.severity === 'needs_review'
                      ? 'Verify Address'
                      : mfgAudit && (!mfgAudit.passed || mfgAudit.severity === 'blocking')
                      ? 'Missing Address'
                      : pSummary?.manufacturerName || pSummary?.packerName
                      ? 'Rule 6(1)(b) Pass'
                      : 'Missing'}
                  </span>
                )}
              </div>

              {/* 6. Consumer Care */}
              <div className="flex items-start justify-between py-2.5 gap-2">
                <div className="flex flex-col flex-1">
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    Consumer Grievance Care
                  </span>
                  <span className="font-body-md text-body-md text-primary font-semibold truncate max-w-[220px]">
                    {pSummary?.consumerCareContact || (report ? 'Not Declared' : '—')}
                  </span>
                  {report && careAudit && (!careAudit.passed || careAudit.severity === 'needs_review') && (
                    <span className="text-[11px] text-amber-800 font-medium mt-0.5">
                      {careAudit.message}
                    </span>
                  )}
                </div>
                {report && (
                  <span
                    className={`inline-flex items-center gap-1 font-label-code text-label-code font-semibold shrink-0 ${
                      careAudit && careAudit.severity === 'needs_review'
                        ? 'text-amber-700'
                        : careAudit && (!careAudit.passed || careAudit.severity === 'blocking')
                        ? 'text-error'
                        : pSummary?.consumerCareContact
                        ? 'text-secondary'
                        : 'text-amber-700'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {careAudit && careAudit.severity === 'needs_review'
                        ? 'warning'
                        : careAudit && (!careAudit.passed || careAudit.severity === 'blocking')
                        ? 'error'
                        : pSummary?.consumerCareContact
                        ? 'check_circle'
                        : 'warning'}
                    </span>
                    {careAudit && careAudit.severity === 'needs_review'
                      ? 'Verify Helpline'
                      : careAudit && (!careAudit.passed || careAudit.severity === 'blocking')
                      ? 'Missing Helpline'
                      : pSummary?.consumerCareContact
                      ? 'Rule 6(1)(n) Pass'
                      : 'Needs Review'}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: Rule-by-Rule Audit Breakdown */}
          {report && activeTab === 'rules' && (
            <div className="flex flex-col divide-y divide-outline-variant/30 max-h-72 overflow-y-auto">
              {report.compliance.ruleResults.map((rule: RuleResult, idx: number) => {
                const info = getFriendlyRuleDetails(rule.ruleId);
                const isIssue = !rule.passed || rule.severity === 'needs_review' || rule.severity === 'warning';
                return (
                  <div key={idx} className="py-2.5 flex flex-col gap-1 text-xs">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-semibold text-primary">{info.title}</span>
                        <span className="text-on-surface-variant/70 font-mono text-[10px]">
                          ({rule.ruleReference})
                        </span>
                        <span className="text-[10px] text-on-surface-variant/50 font-mono">
                          #{rule.ruleId}
                        </span>
                      </div>
                      <span
                        className={`shrink-0 px-2 py-0.5 rounded font-label-code text-[11px] font-semibold ${
                          rule.passed
                            ? 'bg-secondary-container text-on-secondary-container'
                            : rule.severity === 'blocking'
                            ? 'bg-error-container text-on-error-container'
                            : 'bg-amber-100 text-amber-900'
                        }`}
                      >
                        {rule.passed ? 'PASS' : rule.severity === 'blocking' ? 'VIOLATION' : 'REVIEW'}
                      </span>
                    </div>
                    <p className="text-on-surface font-body-sm text-xs">
                      {rule.message || rule.description}
                    </p>
                    {rule.evidenceValue && (
                      <span className="font-mono text-[11px] text-on-surface-variant">
                        Detected: {rule.evidenceValue}
                      </span>
                    )}
                    {isIssue && (
                      <div className="flex items-center gap-1 text-[11px] text-amber-850 bg-amber-50/80 px-2 py-1 rounded">
                        <span className="material-symbols-outlined text-[14px] text-amber-700">lightbulb</span>
                        <span>{info.action}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Bottom Actions */}
          <div className="flex flex-col gap-2.5 pt-space-xs">
            {report ? (
              <>
                <button
                  type="button"
                  onClick={handleConfirmReport}
                  disabled={isSaving}
                  className="w-full flex items-center justify-center gap-2.5 bg-primary text-on-primary py-3 px-4 rounded-xl font-body-md text-body-md font-semibold shadow-sm hover:bg-primary-container disabled:opacity-50 transition-colors text-center cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]">assignment_turned_in</span>
                  <span>{isSaving ? 'Attesting & Filing...' : 'Confirm & Register Report'}</span>
                </button>
                <button
                  type="button"
                  onClick={handleResetScan}
                  className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-body-sm text-body-sm font-medium transition-colors cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">replay</span>
                  <span>Retake / Scan Another Package</span>
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={handleRunScan}
                disabled={isAnalyzing}
                className="w-full flex items-center justify-center gap-2 bg-primary text-on-primary py-3 px-4 rounded-xl font-body-md text-body-md font-semibold shadow-sm hover:bg-primary-container disabled:opacity-40 transition-colors text-center cursor-pointer"
              >
                <span className="material-symbols-outlined text-[20px]">document_scanner</span>
                <span>{files.length === 0 ? 'Select Photos to Scan' : `Scan ${files.length} Photo(s)`}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
