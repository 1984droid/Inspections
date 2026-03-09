const { test, expect } = require('@playwright/test');

test.describe('Complete Inspection - All Pass with All Test Modules', () => {
  test('should create inspection, select all test modules, answer all pass, and generate PDF', async ({ page }) => {
    console.log('Starting complete inspection test - all pass...');

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
    console.log('✓ On new inspection page');

    // Select equipment
    await page.selectOption('select[name="equipment_id"]', { index: 1 });
    await page.waitForTimeout(500); // Wait for JS to update test module visibility
    console.log('✓ Selected equipment');

    // Select periodic template
    await page.selectOption('select[name="template_id"]', { index: 1 });
    console.log('✓ Selected periodic template');

    // Select all visible test modules (should only show C/D/E for Category C equipment)
    const testModuleCheckboxes = await page.locator('input[name="test_modules"]:not([disabled])').all();
    console.log(`Found ${testModuleCheckboxes.length} test modules to select`);

    for (const checkbox of testModuleCheckboxes) {
      await checkbox.check();
    }
    console.log('✓ Selected all test modules');

    // Submit to create inspection
    await page.click('button[type="submit"]');
    await page.waitForURL('**/inspections/*/');
    console.log('✓ Inspection created');

    // Get inspection ID from URL
    const url = page.url();
    const inspectionId = url.match(/inspections\/(\d+)\//)[1];
    console.log(`✓ Inspection ID: ${inspectionId}`);

    // Answer all questions as Pass
    console.log('Starting to answer questions...');
    let totalAnswered = 0;
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
          } catch (e) {
            // Skip if stale or not clickable
          }
        }
        await page.waitForTimeout(200);
      }

      // Find first unanswered Pass button
      const allLabels = await page.locator('label.status-chip-label').all();
      let found = false;

      for (const label of allLabels) {
        try {
          const text = await label.textContent({ timeout: 1000 });
          const forAttr = await label.getAttribute('for');

          if (text?.trim() === 'Pass' && forAttr && await label.isVisible({ timeout: 1000 })) {
            const radioId = forAttr;
            const radio = page.locator('#' + radioId);
            const isChecked = await radio.isChecked({ timeout: 1000 });

            if (!isChecked) {
              await label.click({ timeout: 2000 });
              totalAnswered++;
              found = true;

              if (totalAnswered % 10 === 0) {
                console.log(`  Answered ${totalAnswered} questions...`);
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
        console.log(`✓ No more unanswered questions found after ${totalAnswered} answers`);
        break;
      }
    }

    console.log(`✓ Total questions answered: ${totalAnswered}`);

    // Complete the inspection
    console.log('Completing inspection...');
    await page.click('button:has-text("Complete Inspection")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    console.log('✓ Inspection completed');

    // Check for certificate number
    const hasCertificate = await page.locator('text=/CERT-PASS-\\d{4}/').isVisible();
    expect(hasCertificate).toBeTruthy();
    console.log('✓ Certificate number generated');

    // Generate PDF
    console.log('Generating PDF...');
    await page.click('a:has-text("Generate PDF Package")');
    await page.waitForTimeout(3000); // Wait for PDF generation
    console.log('✓ PDF generated');

    // Verify PDF link is present
    const pdfLink = page.locator('a[href*=".pdf"]').first();
    await expect(pdfLink).toBeVisible();
    console.log('✓ PDF link visible');

    console.log('\n=== TEST COMPLETE - ALL PASS ===');
    console.log(`Inspection ID: ${inspectionId}`);
    console.log(`Questions answered: ${totalAnswered}`);
    console.log(`Result: PASS with all test modules`);
  });
});
