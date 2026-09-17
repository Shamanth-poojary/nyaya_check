/**
 * test-ocr-integration.mjs — End-to-end Integration Test for Frontend OCR Client.
 *
 * Simulates the browser client payload sent by ScanViewfinder.tsx to http://127.0.0.1:8000/v1/check
 * and verifies complete compliance report assembly, schema compatibility, and error paths.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const OCR_BASE_URL = process.env.NEXT_PUBLIC_OCR_URL || 'http://127.0.0.1:8000';

async function runTests() {
  console.log('====================================================');
  console.log('Phase 07 — End-to-End Integration Verification Suite');
  console.log(`Target OCR Service URL: ${OCR_BASE_URL}`);
  console.log('====================================================\n');

  let passed = 0;
  let failed = 0;

  // TEST 1: Health Endpoint Check
  try {
    process.stdout.write('Test 1: Health & Readiness Endpoint Check... ');
    const res = await fetch(`${OCR_BASE_URL}/v1/health`, { headers: { Accept: 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    const data = await res.json();
    if (data.status !== 'healthy' && data.status !== 'ok') {
      throw new Error(`Unexpected health status: ${JSON.stringify(data)}`);
    }
    console.log(`[PASS] (version: ${data.version || 'v1'})`);
    passed++;
  } catch (err) {
    console.log(`[FAIL] -> ${err.message}`);
    failed++;
  }

  // TEST 2: Real Product Photo Upload & Compliance Check
  try {
    process.stdout.write('Test 2: Full-Pipeline POST /v1/check with Real Product Photo... ');
    const samplePath = path.resolve(__dirname, '../ocr-service/test_images/clean/sample.png');
    if (!fs.existsSync(samplePath)) {
      throw new Error(`Sample image not found at ${samplePath}`);
    }

    const fileBuffer = fs.readFileSync(samplePath);
    const blob = new Blob([fileBuffer], { type: 'image/png' });
    const formData = new FormData();
    formData.append('images', blob, 'sample_product.png');

    const tStart = Date.now();
    const res = await fetch(`${OCR_BASE_URL}/v1/check?format=json`, {
      method: 'POST',
      body: formData,
    });

    const elapsed = ((Date.now() - tStart) / 1000).toFixed(2);
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`HTTP ${res.status}: ${errText}`);
    }

    const report = await res.json();

    // Assert Schema v4.0 contract
    if (report.schemaVersion !== '4.0') {
      throw new Error(`Expected schemaVersion '4.0', got '${report.schemaVersion}'`);
    }
    if (!report.reportId) {
      throw new Error('reportId missing from ComplianceReport');
    }
    if (!report.compliance || !report.compliance.overallStatus) {
      throw new Error('compliance object or overallStatus missing');
    }
    if (!report.productSummary) {
      throw new Error('productSummary missing from ComplianceReport');
    }
    if (!Array.isArray(report.compliance.ruleResults)) {
      throw new Error('ruleResults missing or not an array');
    }

    console.log(`[PASS] (${elapsed}s, status: ${report.compliance.overallStatus}, checks: ${report.compliance.summary.totalChecks})`);
    console.log(`   - Detected Commodity: ${report.productSummary.commodityName || 'None'}`);
    console.log(`   - Declared Net Quantity: ${report.productSummary.netQuantity || 'None'}`);
    console.log(`   - Declared MRP: ${report.productSummary.mrp || 'None'}`);
    console.log(`   - Rules Evaluated: ${report.compliance.ruleResults.length} (${report.compliance.summary.passed} passed, ${report.compliance.summary.failed} failed)`);
    passed++;
  } catch (err) {
    console.log(`[FAIL] -> ${err.message}`);
    failed++;
  }

  // TEST 3: Error Handling - Missing Images Rejected
  try {
    process.stdout.write('Test 3: Empty Payload Boundary Validation... ');
    const emptyForm = new FormData();
    const res = await fetch(`${OCR_BASE_URL}/v1/check`, {
      method: 'POST',
      body: emptyForm,
    });
    if (res.status === 400 || res.status === 422) {
      console.log(`[PASS] (Safely rejected with HTTP ${res.status})`);
      passed++;
    } else {
      throw new Error(`Expected HTTP 400/422, received HTTP ${res.status}`);
    }
  } catch (err) {
    console.log(`[FAIL] -> ${err.message}`);
    failed++;
  }

  // TEST 4: Error Handling - Unsupported Format Requested (e.g. PDF deferral)
  try {
    process.stdout.write('Test 4: PDF Deferral Contract Validation (format=pdf)... ');
    const samplePath = path.resolve(__dirname, '../ocr-service/test_images/clean/sample.png');
    const fileBuffer = fs.readFileSync(samplePath);
    const blob = new Blob([fileBuffer], { type: 'image/png' });
    const formData = new FormData();
    formData.append('images', blob, 'sample_product.png');

    const res = await fetch(`${OCR_BASE_URL}/v1/check?format=pdf`, {
      method: 'POST',
      body: formData,
    });
    if (res.status === 400) {
      const err = await res.json();
      if (err.detail && err.detail.includes('deferred')) {
        console.log('[PASS] (Correctly returned HTTP 400 PDF deferral message)');
        passed++;
      } else {
        throw new Error(`Unexpected error detail: ${JSON.stringify(err)}`);
      }
    } else {
      throw new Error(`Expected HTTP 400 for format=pdf, got ${res.status}`);
    }
  } catch (err) {
    console.log(`[FAIL] -> ${err.message}`);
    failed++;
  }

  console.log('\n----------------------------------------------------');
  console.log(`Integration Test Results: ${passed} passed, ${failed} failed`);
  console.log('----------------------------------------------------');

  if (failed > 0) {
    process.exit(1);
  }
}

runTests();
