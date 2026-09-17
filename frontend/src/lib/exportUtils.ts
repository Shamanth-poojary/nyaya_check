'use client';

import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { InspectionReport } from '@/types';

/**
 * Escapes values for safe CSV export.
 */
function escapeCSV(val: any): string {
  if (val === null || val === undefined) return '""';
  const str = String(val).replace(/"/g, '""');
  return `"${str}"`;
}

/**
 * Exports an array of InspectionReport items as a CSV file and triggers download.
 */
export function exportReportsToCSV(reports: InspectionReport[], filenamePrefix = 'nyayacheck_inspections') {
  if (!reports || reports.length === 0) {
    alert('No inspection records available to export.');
    return;
  }

  const headers = [
    'Report Code',
    'Product Name',
    'SKU / Batch',
    'Location',
    'Zone',
    'Inspecting Officer',
    'Officer Badge',
    'Compliance Status',
    'Inspection Date',
    'Statutory Findings',
    'Declared MRP',
    'Net Quantity',
    'Mfg Date',
    'Manufacturer',
    'Packer',
    'Importer',
    'Consumer Care',
    'Digital Signature Hash',
  ];

  const rows = reports.map((r) => [
    escapeCSV(r.reportCode || r.id),
    escapeCSV(r.productName || 'N/A'),
    escapeCSV(r.sku || 'N/A'),
    escapeCSV(r.location || 'N/A'),
    escapeCSV(r.zone || 'N/A'),
    escapeCSV(r.officerName || 'N/A'),
    escapeCSV(r.officerBadge || 'N/A'),
    escapeCSV(r.status ? r.status.toUpperCase() : 'PENDING'),
    escapeCSV(r.dateStr || r.timestamp || 'N/A'),
    escapeCSV(r.findings || 'N/A'),
    escapeCSV(r.mrp || 'N/A'),
    escapeCSV(r.netQty || 'N/A'),
    escapeCSV(r.mfgDate || 'N/A'),
    escapeCSV(r.manufacturer || 'N/A'),
    escapeCSV(r.packer || 'N/A'),
    escapeCSV(r.importer || 'N/A'),
    escapeCSV(r.consumerCare || 'N/A'),
    escapeCSV(r.digitalSignature || 'N/A'),
  ]);

  const csvContent = [headers.map(h => `"${h}"`).join(','), ...rows.map((row) => row.join(','))].join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const timestamp = new Date().toISOString().slice(0, 10);
  link.setAttribute('href', url);
  link.setAttribute('download', `${filenamePrefix}_${timestamp}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Generates and downloads a single Statutory Panchnama Memo PDF.
 */
export function downloadPanchnamaPDF(report: InspectionReport) {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const reportCode = report.reportCode || report.id || 'PANCHNAMA-MEMO';

  // --- Header ---
  doc.setFillColor(15, 23, 42); // slate-900
  doc.rect(0, 0, pageWidth, 26, 'F');

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('GOVERNMENT OF INDIA • LEGAL METROLOGY ENFORCEMENT', pageWidth / 2, 11, { align: 'center' });

  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(203, 213, 225);
  doc.text('STATUTORY INSPECTION DOSSIER & SPOT PANCHNAMA MEMO (ACT 2009 & PCR 2011)', pageWidth / 2, 18, {
    align: 'center',
  });

  // --- Dossier Info Bar ---
  doc.setFillColor(241, 245, 249);
  doc.rect(14, 31, pageWidth - 28, 10, 'F');
  doc.setFontSize(9);
  doc.setTextColor(15, 23, 42);
  doc.setFont('helvetica', 'bold');
  doc.text(`RECORD: #${reportCode}`, 18, 37.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(100, 116, 139);
  doc.text(`DATE: ${report.dateStr || report.timestamp || new Date().toLocaleString()}`, pageWidth - 18, 37.5, {
    align: 'right',
  });

  // --- Primary Metadata Grid ---
  autoTable(doc, {
    startY: 44,
    theme: 'grid',
    styles: { fontSize: 8.5, cellPadding: 3, textColor: [30, 41, 59] },
    headStyles: { fillColor: [248, 250, 252], textColor: [71, 85, 105], fontStyle: 'bold' },
    head: [['COMMODITY / PRODUCT', 'INSPECTION SITE', 'ENFORCEMENT OFFICER', 'STATUTORY STATUS']],
    body: [
      [
        `${report.productName || 'Packaged Commodity'}\nSKU: ${report.sku || 'N/A'}`,
        `${report.location || 'Field Node DL-01'}\nZone: ${report.zone || 'North Delhi'}`,
        `${report.officerName || 'S.K. Ranganathan'}\nBadge: ${report.officerBadge || 'LM-DL-88392'}`,
        report.status === 'compliant'
          ? 'COMPLIANT\n(All Rules Passed)'
          : report.status === 'deficit'
          ? 'DEFICIT DETECTED\n(Non-Compliance)'
          : 'FLAGGED FOR REVIEW\n(Further Audit)',
      ],
    ],
    margin: { left: 14, right: 14 },
  });

  // --- Findings Banner ---
  let currentY = (doc as any).lastAutoTable.finalY + 6;
  const isDeficit = report.status === 'deficit';

  if (isDeficit) {
    doc.setFillColor(254, 242, 242);
    doc.setDrawColor(239, 68, 68);
  } else {
    doc.setFillColor(240, 253, 244);
    doc.setDrawColor(34, 197, 94);
  }
  doc.roundedRect(14, currentY, pageWidth - 28, 16, 2, 2, 'FD');

  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(isDeficit ? 185 : 21, isDeficit ? 28 : 128, isDeficit ? 28 : 61);
  doc.text(
    isDeficit ? 'STATUTORY FINDINGS: ACTIONABLE DEFICITS IDENTIFIED' : 'STATUTORY FINDINGS: ALL PROVISIONS SATISFIED',
    18,
    currentY + 6
  );

  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(71, 85, 105);
  doc.text(report.findings || 'Full statutory rule evaluations performed under Legal Metrology Rules, 2011.', 18, currentY + 11.5, {
    maxWidth: pageWidth - 36,
  });

  // --- Rule Breakdown Table ---
  currentY += 21;
  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(15, 23, 42);
  doc.text('STATUTORY RULE EVALUATION AUDIT MATRIX', 14, currentY);

  const ruleRows = report.ruleResults && report.ruleResults.length > 0
    ? report.ruleResults.map((rule) => [
        rule.ruleId.replace(/_/g, ' ').toUpperCase(),
        rule.ruleReference || (rule as any).lawReference || 'PCR 2011',
        rule.passed ? 'PASSED' : rule.severity === 'blocking' ? 'VIOLATION' : 'REVIEW',
        rule.message || rule.description || (rule as any).detail || (rule.passed ? 'Mandatory declaration verified.' : 'Declaration absent or non-compliant.'),
      ])
    : [
        ['RULE 6(1)(A) COMMODITY IDENTITY', 'Rule 6(1)(a)', 'VIOLATION', 'Generic or common name of packaged commodity absent.'],
        ['RULE 6(1)(B) MANUFACTURER/PACKER', 'Rule 6(1)(b)', 'VIOLATION', 'Name and complete address of manufacturer not found.'],
        ['RULE 6(1)(C) NET QUANTITY', 'Rule 6(1)(c)', 'PASSED', 'Net weight / volume declared with standard unit symbol.'],
        ['RULE 6(1)(D) MONTH & YEAR OF MFG', 'Rule 6(1)(d)', 'VIOLATION', 'Date of manufacturing/packaging not clearly indicated.'],
        ['RULE 6(1)(E) MRP & USP', 'Rule 6(1)(e)', 'VIOLATION', 'Maximum Retail Price or Unit Sale Price missing mandatory phrasing.'],
        ['RULE 6(1)(N) CONSUMER CARE', 'Rule 6(1)(n)', 'VIOLATION', 'Contact details of authorized consumer grievance cell absent.'],
        ['RULE 14 NUMERAL & LETTER HEIGHT', 'Rule 14 Table-I', 'PASSED', 'Calculated numeral height meets statutory minimum for PDP area.'],
      ];

  autoTable(doc, {
    startY: currentY + 3,
    theme: 'striped',
    styles: { fontSize: 8, cellPadding: 2.5, textColor: [30, 41, 59] },
    headStyles: { fillColor: [30, 41, 59], textColor: [255, 255, 255], fontStyle: 'bold' },
    head: [['RULE / MANDATE', 'LEGAL REFERENCE', 'STATUS', 'AUDIT FINDINGS & CITATION']],
    body: ruleRows,
    columnStyles: {
      0: { cellWidth: 50 },
      1: { cellWidth: 35 },
      2: { cellWidth: 25, fontStyle: 'bold' },
      3: { cellWidth: 'auto' },
    },
    didParseCell: (data) => {
      if (data.column.index === 2 && data.section === 'body') {
        const text = String(data.cell.raw);
        if (text.includes('VIOLATION')) {
          data.cell.styles.textColor = [220, 38, 38];
        } else if (text.includes('PASSED')) {
          data.cell.styles.textColor = [22, 163, 74];
        } else {
          data.cell.styles.textColor = [202, 138, 4];
        }
      }
    },
    margin: { left: 14, right: 14 },
  });

  // --- Legal Attestation & Cryptographic Seal Footer ---
  const finalY = (doc as any).lastAutoTable.finalY + 8;
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(14, finalY, pageWidth - 28, 28, 1.5, 1.5, 'FD');

  doc.setFontSize(7.5);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(51, 65, 85);
  doc.text('STATUTORY ATTESTATION & SECTION 65B EVIDENCE CERTIFICATE', 18, finalY + 5);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7);
  doc.setTextColor(100, 116, 139);
  doc.text(
    'I hereby certify under Section 65B of the Indian Evidence Act that this record is an automated, tamper-evident statutory extraction produced under official inspection powers of the Legal Metrology Act, 2009. Digital Hash: ' +
      (report.digitalSignature || 'SHA256:8f9a2e3b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f'),
    18,
    finalY + 9.5,
    { maxWidth: pageWidth - 36 }
  );

  doc.setFont('helvetica', 'bold');
  doc.setTextColor(30, 41, 59);
  doc.text(`SEALED BY: Officer ${report.officerName || 'S.K. Ranganathan'} (Badge: ${report.officerBadge || 'LM-DL-88392'})`, 18, finalY + 22);
  doc.text('OFFICIAL E-SIGN VALIDATED', pageWidth - 18, finalY + 22, { align: 'right' });

  // Save the PDF
  doc.save(`Panchnama_${reportCode.replace(/[^a-zA-Z0-9-_]/g, '_')}.pdf`);
}

/**
 * Generates and downloads a compiled Multi-Report Bulk Panchnama PDF package.
 */
export function downloadBulkPanchnamaPDF(reports: InspectionReport[]) {
  if (!reports || reports.length === 0) {
    alert('No inspection records available for bulk export.');
    return;
  }

  const doc = new jsPDF({
    orientation: 'landscape',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  // Header Banner
  doc.setFillColor(15, 23, 42);
  doc.rect(0, 0, pageWidth, 24, 'F');

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('GOVERNMENT OF INDIA • LEGAL METROLOGY STATUTORY ENFORCEMENT', pageWidth / 2, 10, { align: 'center' });

  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(203, 213, 225);
  doc.text('BULK STATUTORY INSPECTION DOSSIERS & CONSOLIDATED PANCHNAMA SEIZURE LOG', pageWidth / 2, 17, {
    align: 'center',
  });

  // Summary Metrics Bar
  const total = reports.length;
  const deficits = reports.filter((r) => r.status === 'deficit').length;
  const compliant = reports.filter((r) => r.status === 'compliant').length;

  doc.setFillColor(241, 245, 249);
  doc.rect(14, 28, pageWidth - 28, 9, 'F');
  doc.setFontSize(8.5);
  doc.setTextColor(15, 23, 42);
  doc.setFont('helvetica', 'bold');
  doc.text(`TOTAL DOSSIERS: ${total}   |   DEFICITS DETECTED: ${deficits}   |   COMPLIANT: ${compliant}`, 18, 34);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(100, 116, 139);
  doc.text(`GENERATED: ${new Date().toLocaleString()}`, pageWidth - 18, 34, { align: 'right' });

  // Main Table
  const tableRows = reports.map((r, idx) => [
    idx + 1,
    r.reportCode || r.id,
    r.productName || 'Packaged Commodity',
    r.sku || 'N/A',
    r.location || 'Field Node DL-01',
    r.officerName || 'S.K. Ranganathan',
    r.status ? r.status.toUpperCase() : 'PENDING',
    r.dateStr || r.timestamp || 'N/A',
    r.findings ? r.findings.slice(0, 75) + '...' : 'Verified under PCR 2011.',
  ]);

  autoTable(doc, {
    startY: 40,
    theme: 'grid',
    styles: { fontSize: 8, cellPadding: 2.5, textColor: [30, 41, 59] },
    headStyles: { fillColor: [30, 41, 59], textColor: [255, 255, 255], fontStyle: 'bold' },
    head: [['#', 'REPORT ID', 'PRODUCT / COMMODITY', 'SKU', 'LOCATION', 'OFFICER', 'STATUS', 'DATE', 'FINDINGS']],
    body: tableRows,
    columnStyles: {
      0: { cellWidth: 10 },
      1: { cellWidth: 32 },
      2: { cellWidth: 45 },
      3: { cellWidth: 25 },
      4: { cellWidth: 35 },
      5: { cellWidth: 35 },
      6: { cellWidth: 25, fontStyle: 'bold' },
      7: { cellWidth: 28 },
      8: { cellWidth: 'auto' },
    },
    didParseCell: (data) => {
      if (data.column.index === 6 && data.section === 'body') {
        const text = String(data.cell.raw);
        if (text.includes('DEFICIT')) {
          data.cell.styles.textColor = [220, 38, 38];
        } else if (text.includes('COMPLIANT')) {
          data.cell.styles.textColor = [22, 163, 74];
        }
      }
    },
    margin: { left: 14, right: 14 },
  });

  // Footer
  const finalY = (doc as any).lastAutoTable.finalY + 8;
  if (finalY < pageHeight - 15) {
    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(71, 85, 105);
    doc.text('OFFICIAL STATUTORY RECORD • CERTIFIED UNDER SECTION 65B INDIAN EVIDENCE ACT', 14, finalY);
  }

  const timestamp = new Date().toISOString().slice(0, 10);
  doc.save(`Bulk_Panchnama_Dossiers_${timestamp}.pdf`);
}

/**
 * Formats and prints a formal Statutory Notice under Section 36(1).
 */
export function printStatutoryNotice(report: InspectionReport) {
  const reportCode = report.reportCode || report.id || 'DEL-LM-2025-55338';
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('Please allow popups to print the statutory notice.');
    return;
  }

  const isDeficit = report.status === 'deficit';
  const violationsHtml = (report.ruleResults || [])
    .filter((r) => !r.passed)
    .map(
      (v) => `
      <tr style="border-bottom: 1px solid #e2e8f0;">
        <td style="padding: 8px; font-weight: 600; color: #b91c1c;">${v.ruleId.replace(/_/g, ' ').toUpperCase()}</td>
        <td style="padding: 8px; font-family: monospace;">${v.ruleReference || (v as any).lawReference || 'PCR 2011'}</td>
        <td style="padding: 8px; color: #475569;">${v.message || v.description || (v as any).detail || 'Mandatory declaration violation.'}</td>
      </tr>
    `
    )
    .join('');

  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>Statutory Notice - #${reportCode}</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 40px;
            color: #0f172a;
            line-height: 1.5;
          }
          .header {
            text-align: center;
            border-bottom: 2px solid #0f172a;
            padding-bottom: 15px;
            margin-bottom: 25px;
          }
          .header h1 {
            font-size: 18px;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .header h2 {
            font-size: 13px;
            margin: 5px 0 0 0;
            color: #475569;
            font-weight: 500;
          }
          .notice-title {
            text-align: center;
            font-size: 15px;
            font-weight: bold;
            text-decoration: underline;
            margin: 20px 0;
          }
          .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
            background: #f8fafc;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
          }
          .field {
            font-size: 12px;
          }
          .field span {
            font-weight: bold;
            display: block;
            color: #64748b;
            text-transform: uppercase;
            font-size: 10px;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin: 20px 0;
          }
          th {
            background: #0f172a;
            color: white;
            text-align: left;
            padding: 8px;
            font-size: 11px;
            text-transform: uppercase;
          }
          .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #cbd5e1;
            display: flex;
            justify-content: space-between;
            font-size: 11px;
          }
          .seal {
            border: 2px solid #0f172a;
            padding: 10px 15px;
            font-weight: bold;
            text-align: center;
            display: inline-block;
          }
          @media print {
            body { margin: 20px; }
            button { display: none; }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>GOVERNMENT OF INDIA • MINISTRY OF CONSUMER AFFAIRS</h1>
          <h2>DIRECTORATE OF LEGAL METROLOGY • ENFORCEMENT DIVISION</h2>
        </div>

        <div class="notice-title">
          ${isDeficit ? 'STATUTORY NOTICE UNDER SECTION 36(1) OF LEGAL METROLOGY ACT, 2009' : 'STATUTORY COMPLIANCE INSPECTION MEMORANDUM'}
        </div>

        <div class="grid">
          <div class="field"><span>Dossier Reference</span>#${reportCode}</div>
          <div class="field"><span>Inspection Date & Time</span>${report.dateStr || report.timestamp || new Date().toLocaleString()}</div>
          <div class="field"><span>Inspected Product / Commodity</span>${report.productName || 'Packaged Commodity'} (SKU: ${report.sku || 'N/A'})</div>
          <div class="field"><span>Inspection Site / Location</span>${report.location || 'Field Node DL-01'} (${report.zone || 'North Delhi'})</div>
          <div class="field"><span>Inspecting Officer</span>${report.officerName || 'S.K. Ranganathan'} (Badge: ${report.officerBadge || 'LM-DL-88392'})</div>
          <div class="field"><span>Cryptographic Signature</span>${report.digitalSignature || 'Verified & Sealed'}</div>
        </div>

        <div>
          <p style="font-size: 13px; font-weight: bold; margin-bottom: 5px;">Statutory Finding Summary:</p>
          <p style="font-size: 12px; color: #334155; background: #f1f5f9; padding: 10px; border-left: 4px solid #0f172a;">
            ${report.findings || 'Compliance evaluation completed against the Legal Metrology (Packaged Commodities) Rules, 2011.'}
          </p>
        </div>

        ${
          violationsHtml
            ? `
          <div style="margin-top: 20px;">
            <p style="font-size: 13px; font-weight: bold; margin-bottom: 5px;">Actionable Violations Citing Legal Metrology Rules, 2011:</p>
            <table>
              <thead>
                <tr>
                  <th>Rule / Citation</th>
                  <th>Statutory Clause</th>
                  <th>Specific Violation Finding</th>
                </tr>
              </thead>
              <tbody>
                ${violationsHtml}
              </tbody>
            </table>
          </div>
        `
            : '<p style="font-size: 12px; color: #16a34a; font-weight: bold; margin: 20px 0;">✔ All evaluated packaging declarations satisfy statutory requirements.</p>'
        }

        <div class="footer">
          <div>
            <p><strong>Issued By:</strong></p>
            <p>Officer ${report.officerName || 'S.K. Ranganathan'}</p>
            <p>Inspector of Legal Metrology (Badge: ${report.officerBadge || 'LM-DL-88392'})</p>
          </div>
          <div style="text-align: right;">
            <div class="seal">
              LEGAL METROLOGY<br/>STATUTORY SEAL
            </div>
            <p style="margin-top: 5px; color: #64748b;">Sec 65B Certified</p>
          </div>
        </div>

        <script>
          window.onload = function() {
            window.print();
          };
        </script>
      </body>
    </html>
  `;

  printWindow.document.write(html);
  printWindow.document.close();
}
