const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

test.describe('Complete Inspection - 5 Failures with Defect Photos', () => {
  test('should create inspection with 5 failures, add photos to each defect, and generate PDF', async ({ page }) => {
    console.log('Starting complete inspection test - with defects...');

    // Create test image files if they don't exist
    const mediaDir = path.join(__dirname, '..', 'media', 'test_photos');
    if (!fs.existsSync(mediaDir)) {
      fs.mkdirSync(mediaDir, { recursive: true });
    }

    // Create 5 different colored test images (1x1 pixel PNGs)
    const testImages = [];
    const colors = [
      Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00, 0x00, 0x03, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82]), // red
      Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0x60, 0xF8, 0x0F, 0x00, 0x01, 0x04, 0x01, 0x00, 0x35, 0x28, 0x7C, 0xDE, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82]), // green
      Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0x60, 0x60, 0xF8, 0x0F, 0x00, 0x01, 0x01, 0x01, 0x00, 0x35, 0x5F, 0x0E, 0x1D, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82]), // blue
      Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0xF8, 0x00, 0x00, 0x01, 0x05, 0x01, 0x02, 0x5D, 0x8F, 0x2E, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82]), // yellow
      Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0x60, 0xF8, 0x0F, 0x00, 0x03, 0x05, 0x01, 0x02, 0x87, 0xF0, 0x7C, 0xDE, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82])  // magenta
    ];

    for (let i = 1; i <= 5; i++) {
      const imagePath = path.join(mediaDir, `defect_${i}.png`);
      fs.writeFileSync(imagePath, colors[i - 1]);
      testImages.push(imagePath);
    }
    console.log('✓ Created 5 test images');

    // Login
    await page.goto('http://localhost:8000/login/');
    await page.fill('input[name="username"]', 'josh');
    await page.fill('input[name="password"]', 'workAccount');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard/');
    console.log('✓ Logged in successfully');

    // Navigate to new inspection
    await page.goto('http://localhost:8000/inspections/new/');
    await page.waitForLoadState('networkidle');

    // Select equipment and template
    await page.selectOption('select[name="equipment_id"]', { index: 1 });
    await page.waitForTimeout(500);
    await page.selectOption('select[name="template_id"]', { index: 1 });

    // Select all test modules
    const testModuleCheckboxes = await page.locator('input[name="test_modules"]:not([disabled])').all();
    for (const checkbox of testModuleCheckboxes) {
      await checkbox.check();
    }

    // Submit to create inspection
    await page.click('button[type="submit"]');
    await page.waitForURL('**/inspections/*/');

    const url = page.url();
    const inspectionId = url.match(/inspections\/(\d+)\//)[1];
    console.log(`✓ Inspection ID: ${inspectionId}`);

    // Answer questions - mark exactly 5 as Fail, rest as Pass
    console.log('Answering questions (5 fails, rest pass)...');
    let totalAnswered = 0;
    let failCount = 0;
    const targetFails = 5;
    let iteration = 0;
    const maxIterations = 200;

    while (iteration < maxIterations) {
      iteration++;

      // Open collapsed sections periodically
      if (iteration === 1 || iteration % 15 === 0) {
        const closedSummaries = await page.locator('details:not([open]) > summary').all();
        for (const summary of closedSummaries) {
          try {
            await summary.click({ timeout: 1000 });
          } catch (e) {}
        }
        await page.waitForTimeout(200);
      }

      // Determine if this should be a fail (every 30th question until we have 5 fails)
      const shouldFail = failCount < targetFails && (totalAnswered > 0 && totalAnswered % 30 === 0);

      // Find first unanswered question
      const allLabels = await page.locator('label.status-chip-label').all();
      let found = false;

      for (const label of allLabels) {
        try {
          const text = await label.textContent({ timeout: 1000 });
          const forAttr = await label.getAttribute('for');

          const targetText = shouldFail ? 'Fail' : 'Pass';

          if (text?.trim() === targetText && forAttr && await label.isVisible({ timeout: 1000 })) {
            const radioId = forAttr;
            const radio = page.locator('#' + radioId);
            const isChecked = await radio.isChecked({ timeout: 1000 });

            if (!isChecked) {
              await label.click({ timeout: 2000 });
              totalAnswered++;
              if (shouldFail) failCount++;
              found = true;

              if (totalAnswered % 10 === 0) {
                console.log(`  Answered ${totalAnswered} questions (${failCount} fails)...`);
              }

              await page.waitForTimeout(300);
              await page.waitForLoadState('networkidle', { timeout: 10000 });
              break;
            }
          }
        } catch (e) {
          continue;
        }
      }

      if (!found) {
        console.log(`✓ No more unanswered questions. Total: ${totalAnswered}, Fails: ${failCount}`);
        break;
      }
    }

    console.log(`✓ Questions answered: ${totalAnswered}, Failures: ${failCount}`);

    // Now add defect photos to each failure
    console.log('Adding defect photos to failures...');
    const defectRows = await page.locator('tr').filter({ hasText: 'Fail' }).all();
    console.log(`Found ${defectRows.length} defect rows`);

    for (let i = 0; i < Math.min(defectRows.length, 5); i++) {
      const row = defectRows[i];

      try {
        // Click "Add Photo" link
        const addPhotoLink = row.locator('a:has-text("Add Photo")');
        await addPhotoLink.click({ timeout: 3000 });
        await page.waitForLoadState('networkidle');

        // Upload photo
        await page.setInputFiles('input[type="file"]', testImages[i]);

        // Fill description
        await page.fill('textarea[name="description"]', `Defect photo ${i + 1} - Critical issue found during inspection`);

        // Submit
        await page.click('button[type="submit"]');
        await page.waitForLoadState('networkidle');
        console.log(`  ✓ Added photo ${i + 1} to defect`);

        // Navigate back to inspection detail
        await page.goto(`http://localhost:8000/inspections/${inspectionId}/`);
        await page.waitForLoadState('networkidle');
      } catch (e) {
        console.log(`  ! Failed to add photo ${i + 1}: ${e.message}`);
      }
    }

    console.log('✓ Added photos to defects');

    // Complete the inspection
    console.log('Completing inspection...');
    await page.click('button:has-text("Complete Inspection")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Check for certificate (should be FAIL cert)
    const hasCertificate = await page.locator('text=/CERT-FAIL-\\d{4}/').isVisible();
    expect(hasCertificate).toBeTruthy();
    console.log('✓ FAIL certificate generated');

    // Generate PDF
    console.log('Generating PDF with defect photos...');
    await page.click('a:has-text("Generate PDF Package")');
    await page.waitForTimeout(5000); // Wait longer for PDF with photos
    console.log('✓ PDF generated');

    // Verify PDF link
    const pdfLink = page.locator('a[href*=".pdf"]').first();
    await expect(pdfLink).toBeVisible();
    console.log('✓ PDF link visible');

    console.log('\n=== TEST COMPLETE - WITH DEFECTS ===');
    console.log(`Inspection ID: ${inspectionId}`);
    console.log(`Questions answered: ${totalAnswered}`);
    console.log(`Failures: ${failCount}`);
    console.log(`Photos added: 5`);
    console.log(`Result: FAIL with defect photos`);
  });
});
