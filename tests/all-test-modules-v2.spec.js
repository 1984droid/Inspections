const { test, expect } = require('@playwright/test');

test.describe('All Test Modules PDF Generation', () => {
  async function answerAllQuestionsPass(page) {
    // Wait for page to load completely
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    let totalAnswered = 0;
    let iteration = 0;
    let maxIterations = 100; // Increased for test modules

    while (iteration < maxIterations) {
      iteration++;

      // Open collapsed details sections every 10 iterations (after multiple page reloads)
      if (iteration === 1 || iteration % 10 === 0) {
        const closedSummaries = await page.locator('details:not([open]) > summary').all();
        for (const summary of closedSummaries) {
          try {
            await summary.click();
          } catch (e) {
            // Skip if stale
          }
        }
        await page.waitForTimeout(100);
      }

      // Find first unanswered Pass label
      const allLabels = await page.locator('label.status-chip-label').all();
      let found = false;

      for (const label of allLabels) {
        try {
          const text = await label.textContent();
          const forAttr = await label.getAttribute('for');

          if (text && text.trim() === 'Pass' && forAttr && await label.isVisible()) {
            // Check if the radio is not already checked
            const radioId = forAttr;
            const radio = page.locator('#' + radioId);
            const isChecked = await radio.isChecked();

            if (!isChecked) {
              await label.click();
              totalAnswered++;
              found = true;
              // Wait for form auto-submit to complete
              await page.waitForTimeout(400);
              await page.waitForLoadState('networkidle');
              break; // Start over to find next unanswered
            }
          }
        } catch (e) {
          // Skip
        }
      }

      if (!found) {
        console.log(`  Total answered: ${totalAnswered} questions`);
        break;
      }

      if (iteration % 5 === 0) {
        console.log(`  Progress: ${totalAnswered} answered so far...`);
      }
    }
  }

  test.beforeEach(async ({ page }) => {
    await page.goto('/login/');
    await page.fill('input[name="username"]', 'josh');
    await page.fill('input[name="password"]', 'workAccount90');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('Test Module: Dielectric Category C/D/E', async ({ page }) => {
    test.setTimeout(120000);
    const custName = 'TestCust' + Date.now();
    const serial = 'SN' + Date.now();

    console.log('[Dielectric C/D/E] Creating customer and equipment');

    await page.goto('/customers/new/');
    await page.fill('input[name="name"]', custName);
    await page.click('button:has-text("Create Customer")');

    await page.selectOption('select[name="customer"]', { label: custName });
    await page.fill('input[name="serial_number"]', serial);
    await page.fill('input[name="make"]', 'Terex');
    await page.fill('input[name="model"]', 'Test');
    await page.click('button:has-text("Create Equipment")');

    await page.selectOption('select[name="template_id"]', { index: 0 });
    await page.check('input[name="test_modules"][value="3"]');
    await page.click('button:has-text("Start Inspection")');
    await page.waitForURL(/\/inspections\/\d+\//);

    console.log('[Dielectric C/D/E] Answering all questions');
    await answerAllQuestionsPass(page);

    console.log('[Dielectric C/D/E] Completing inspection');
    const inspectionId = page.url().match(/\/inspections\/(\d+)\//)[1];
    await page.goto('/inspections/' + inspectionId + '/complete/');
    await page.click('button:has-text("Confirm & Complete")');

    // Wait for completion to finish (PDFs are auto-generated)
    await page.waitForTimeout(8000);

    console.log('[Dielectric C/D/E] ✓ Inspection completed with test module - PDF should be generated');
    console.log('Inspection ID:', inspectionId);
  });

  // Test other modules
  const testModules = [
    { id: 2, name: 'Dielectric A/B' },
    { id: 4, name: 'Upper Controls' },
    { id: 5, name: 'Insulating Liner' },
    { id: 6, name: 'Aerial Ladders' },
    { id: 7, name: 'Chassis Insulating' }
  ];

  for (const tm of testModules) {
    test('Test Module: ' + tm.name, async ({ page }) => {
      test.setTimeout(120000);
      const custName = tm.name.replace(/\s+/g, '') + Date.now();
      const serial = 'SN' + Date.now();

      console.log('[' + tm.name + '] Creating customer and equipment');

      await page.goto('/customers/new/');
      await page.fill('input[name="name"]', custName);
      await page.click('button:has-text("Create Customer")');

      await page.selectOption('select[name="customer"]', { label: custName });
      await page.fill('input[name="serial_number"]', serial);
      await page.fill('input[name="make"]', 'Terex');
      await page.fill('input[name="model"]', 'Test');
      await page.click('button:has-text("Create Equipment")');

      await page.selectOption('select[name="template_id"]', { index: 0 });
      await page.check('input[name="test_modules"][value="' + tm.id + '"]');
      await page.click('button:has-text("Start Inspection")');
      await page.waitForURL(/\/inspections\/\d+\//);

      console.log('[' + tm.name + '] Answering all questions');
      await answerAllQuestionsPass(page);

      console.log('[' + tm.name + '] Completing inspection');
      const inspectionId = page.url().match(/\/inspections\/(\d+)\//)[1];
      await page.goto('/inspections/' + inspectionId + '/complete/');
      await page.click('button:has-text("Confirm & Complete")');
      await page.waitForTimeout(8000);

      console.log('[' + tm.name + '] ✓ Inspection completed with test module');
      console.log('Inspection ID:', inspectionId);
    });
  }
});
