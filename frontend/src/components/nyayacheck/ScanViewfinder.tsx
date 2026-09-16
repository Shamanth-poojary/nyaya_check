'use client';

import React, { useState } from 'react';
import Link from 'next/link';

export const ScanViewfinder: React.FC = () => {
  const [isCapturing, setIsCapturing] = useState(false);
  const [isDeficitSimulated, setIsDeficitSimulated] = useState(false);
  const [imagePreview, setImagePreview] = useState(
    'https://lh3.googleusercontent.com/aida-public/AB6AXuAHEPTVoU-5vPHn6GygzGmzQjA5Hlw1hKVRkWNy_Ldy6EB80spMnHstZA-HHUc-1sdTb5TQYARh8ybdzQVgUMGIcN6qggKSOB5OqtZnRGS9oDbNTgcaoTDAlI0-kCurpz3QAJQ-TLj9-h0LHxjnBvVjfyb-zs5QOTxXCY9zmCAuPaqbP7t3M0_f0CU5UAqGkM6MDF0pZe80YnRpy1tOsLHcmW_NNMSKuudHuEP7IsxSi2d4IUfIa_kP2Q'
  );

  const handleCapture = () => {
    setIsCapturing(true);
    setTimeout(() => {
      setIsCapturing(false);
    }, 300);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setImagePreview(event.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-space-lg items-start">
      {/* LEFT: Viewfinder HUD */}
      <div className="xl:col-span-7 flex flex-col gap-space-md">
        <div className="relative w-full aspect-[4/3] sm:aspect-[16/11] bg-surface-container-highest rounded-2xl overflow-hidden shadow-sm border border-outline-variant group select-none">
          <img
            src={imagePreview}
            alt="Packaged product label inspection viewfinder"
            className={`w-full h-full object-cover transition-all duration-200 ${
              isCapturing ? 'opacity-40 scale-[1.03]' : ''
            }`}
          />
          <div className="absolute inset-8 sm:inset-12 pointer-events-none flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div className="w-7 h-7 border-t-2 border-l-2 border-surface shadow-sm"></div>
              <div className="w-7 h-7 border-t-2 border-r-2 border-surface shadow-sm"></div>
            </div>
            <div className="self-center px-3.5 py-1.5 rounded-full bg-primary/75 backdrop-blur-md text-surface font-body-sm text-body-sm shadow-sm flex items-center gap-2">
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
        </div>

        <div className="bg-surface-container-lowest p-space-md rounded-2xl flex items-center justify-between gap-space-md border border-outline-variant shadow-sm">
          <div className="flex items-center gap-3">
            <label
              htmlFor="package-file-input"
              className="cursor-pointer inline-flex items-center gap-2 h-11 px-4 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-body-sm text-body-sm font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-[20px]">upload_file</span>
              <span>Upload Image</span>
              <input
                id="package-file-input"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileUpload}
              />
            </label>
            <button
              type="button"
              onClick={() => setIsDeficitSimulated(!isDeficitSimulated)}
              className="px-3 py-2 rounded-xl border border-outline-variant/50 text-xs font-label-code text-on-surface-variant hover:bg-surface-container transition-colors cursor-pointer"
            >
              Toggle Violation: {isDeficitSimulated ? 'DEFICIT' : 'PASS'}
            </button>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleCapture}
              className="flex items-center gap-2.5 bg-primary text-on-primary px-6 h-11 rounded-xl shadow-sm hover:bg-primary-container active:scale-[0.98] transition-all font-body-md text-body-md font-semibold cursor-pointer"
            >
              <span className="material-symbols-outlined text-[20px]">photo_camera</span>
              <span>Capture & Scan</span>
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT: Extracted Statutory Findings */}
      <div className="xl:col-span-5 flex flex-col gap-space-md">
        <div className="bg-surface-container-lowest rounded-2xl p-space-lg flex flex-col gap-space-md border border-outline-variant shadow-sm">
          <div className="flex items-start justify-between gap-space-sm pb-space-sm border-b border-outline-variant">
            <div className="flex flex-col">
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2 h-2 rounded-full ${isDeficitSimulated ? 'bg-error' : 'bg-secondary'}`}></span>
                <span className={`font-label-meta text-label-meta uppercase font-semibold tracking-wider ${isDeficitSimulated ? 'text-error' : 'text-secondary'}`}>
                  Extracted Findings
                </span>
              </div>
              <h2 className="font-headline-sm text-headline-sm text-primary font-bold">
                Aashirvaad Superior MP Sharbati Atta 5kg
              </h2>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
                Package ID: <span className="font-label-code text-label-code text-primary font-medium">PKG-2025-0982-DL</span>
              </p>
            </div>

            <div className="flex flex-col items-end shrink-0">
              {isDeficitSimulated ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-error-container text-on-error-container font-label-code text-label-code font-semibold">
                  <span className="material-symbols-outlined text-[15px]">error</span>
                  <span>Deficit Detected</span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-container text-on-secondary-container font-label-code text-label-code font-semibold">
                  <span className="material-symbols-outlined text-[15px]">check</span>
                  <span>98.4% Match</span>
                </span>
              )}
            </div>
          </div>

          <div
            className={`flex items-center gap-2 px-3 py-2 rounded-lg font-body-sm text-body-sm ${
              isDeficitSimulated
                ? 'bg-error-container/40 text-on-error-container'
                : 'bg-secondary-container/40 text-on-secondary-container'
            }`}
          >
            <span className={`material-symbols-outlined text-[18px] ${isDeficitSimulated ? 'text-error' : 'text-secondary'}`}>
              {isDeficitSimulated ? 'error' : 'verified'}
            </span>
            <span className="font-medium">
              {isDeficitSimulated
                ? 'Rule 14 Numeral Height Deficit Under Minimum Threshold'
                : 'All 5 Mandatory Declarations Verified'}
            </span>
          </div>

          <div className="flex flex-col divide-y divide-outline-variant">
            <div className="flex items-center justify-between py-3">
              <div className="flex flex-col">
                <span className="font-body-sm text-body-sm text-on-surface-variant">Net Quantity</span>
                <span className="font-headline-sm text-headline-sm text-primary font-semibold">5 kg (5000 g)</span>
              </div>
              <span className={`inline-flex items-center gap-1 font-label-code text-label-code font-semibold ${isDeficitSimulated ? 'text-error' : 'text-secondary'}`}>
                <span className="material-symbols-outlined text-[18px]">{isDeficitSimulated ? 'error' : 'check_circle'}</span>
                {isDeficitSimulated ? 'Height <4mm' : 'Compliant'}
              </span>
            </div>

            <div className="flex items-center justify-between py-3">
              <div className="flex flex-col">
                <span className="font-body-sm text-body-sm text-on-surface-variant">Retail Sale Price (MRP)</span>
                <span className="font-headline-sm text-headline-sm text-primary font-semibold">
                  ₹ 345.00 <span className="font-body-sm text-body-sm font-normal text-on-surface-variant">(₹ 69.00 / kg)</span>
                </span>
              </div>
              <span className="inline-flex items-center gap-1 text-secondary font-label-code text-label-code font-semibold">
                <span className="material-symbols-outlined text-[18px]">check_circle</span> Compliant
              </span>
            </div>

            <div className="flex items-center justify-between py-3">
              <div className="flex flex-col">
                <span className="font-body-sm text-body-sm text-on-surface-variant">Date of Packing</span>
                <span className="font-headline-sm text-headline-sm text-primary font-semibold">14 / 02 / 2025</span>
              </div>
              <span className="inline-flex items-center gap-1 text-secondary font-label-code text-label-code font-semibold">
                <span className="material-symbols-outlined text-[18px]">check_circle</span> Compliant
              </span>
            </div>

            <div className="flex items-center justify-between py-3">
              <div className="flex flex-col">
                <span className="font-body-sm text-body-sm text-on-surface-variant">Manufacturer / Packer</span>
                <span className="font-body-md text-body-md text-primary font-semibold truncate max-w-[200px]">ITC Limited, Sector 8</span>
              </div>
              <span className="inline-flex items-center gap-1 text-secondary font-label-code text-label-code font-semibold">
                <span className="material-symbols-outlined text-[18px]">check_circle</span> Compliant
              </span>
            </div>

            <div className="flex items-center justify-between py-3">
              <div className="flex flex-col">
                <span className="font-body-sm text-body-sm text-on-surface-variant">Consumer Care</span>
                <span className="font-body-md text-body-md text-primary font-semibold">1800-425-4444</span>
              </div>
              <span className="inline-flex items-center gap-1 text-secondary font-label-code text-label-code font-semibold">
                <span className="material-symbols-outlined text-[18px]">check_circle</span> Compliant
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-2.5 pt-space-xs">
            <Link
              href="/inspector/reports"
              className="w-full flex items-center justify-center gap-2.5 bg-primary text-on-primary py-3 px-4 rounded-xl font-body-md text-body-md font-semibold shadow-sm hover:bg-primary-container transition-colors text-center"
            >
              <span className="material-symbols-outlined text-[20px]">assignment_turned_in</span>
              <span>Confirm & Generate Report</span>
            </Link>
            <button
              type="button"
              onClick={handleCapture}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-body-sm text-body-sm font-medium transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">replay</span>
              <span>Retake</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
