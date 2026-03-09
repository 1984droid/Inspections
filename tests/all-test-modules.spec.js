const { test, expect } = require('@playwright/test');

test.describe('All Test Modules PDF Generation', () => {
  let customerName;
  let equipmentSerial;

  async function createCustomerWithDetails(page, name) {
    await page.goto('/customers/new/');
    await page.fill('input[name="name"]', name);
    await page.click('button:has-text("Create Customer")');
    await expect(page).toHaveURL('/equipment/new/');
  }

  async function createEquipmentWithVehicle(page, customerName, serial) {
    await page.selectOption('select[name="customer"]', { label: customerName });
    await page.fill('input[name="serial_number"]', serial);
    await page.fill('input[name="make"]', 'Terex');
    await page.fill('input[name="model"]', 'Test');
    await page.click('button:has-text("Create Equipment")');
    await expect(page.url()).toContain('/inspections/new/?equipment_id=');
  }

  async function answerAllQuestionsPass(page) {
    // Wait for Pass buttons to appear
    await page.waitForSelector('button:has-text("Pass")', { timeout: 10000 });
    await page.waitForTimeout(500);

    let iteration = 0;
    while (iteration < 150) {
      iteration++;
      
      // Find unanswered Pass buttons (not in a .selected parent or without .selected class)
      const passButtons = page.locator('button:has-text("Pass")').filter({ hasNot: page.locator('.selected') });
      const count = await passButtons.count();
      
      console.log(`  Iteration ${iteration}: Found ${count} unanswered questions`);

      if (count === 0) {
        console.log(`  All questions answered!`);
        break;
      }

      // Click first unanswered Pass button
      await passButtons.first().click();
      await page.waitForTimeout(200);
    }
  }

  test.beforeEach(async ({ page }) => {
    await page.goto('/login/');
    await page.fill('input[name="username"]', 'josh');
    await page.fill('input[name="password"]', 'workAccount');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('Test Module: Dielectric Category C/D/E', async ({ page }) => {
    test.setTimeout(120000);
    customerName = `DielCDE${Date.now()}`;
    equipmentSerial = `SN${Date.now()}`;

    console.log('[Dielectric C/D/E] Creating customer and equipment');
    await createCustomerWithDetails(page, customerName);
    await createEquipmentWithVehicle(page, customerName, equipmentSerial);

    await page.selectOption('select[name="template_id"]', { index: 0 });
    await page.check('input[name="test_modules"][value="3"]');
    await page.click('button:has-text("Start Inspection")');
    await page.waitForURL(/\/inspections\/\d+\//);

    console.log('[Dielectric C/D/E] Answering all questions');
    await answerAllQuestionsPass(page);

    console.log('[Dielectric C/D/E] Completing inspection');
    const inspectionId = page.url().match(/\/inspections\/(\d+)\//)[1];
    await page.goto(`/inspections/${inspectionId}/complete/`);
    await page.click('button:has-text("Confirm & Complete")');
    await page.waitForTimeout(3000);

    console.log('[Dielectric C/D/E] Generating PDF');
    await page.click('a:has-text("Generate PDF Package")');
    await page.waitForTimeout(5000);

    const pdfLink = page.locator('a[href*="inspection_package"]');
    await expect(pdfLink.first()).toBeVisible({ timeout: 10000 });
    console.log('[Dielectric C/D/E] ✓ PDF generated successfully');
  });

  // Repeat for other test modules
  for (const testModule of [
    { id: 2, name: 'Dielectric A/B' },
    { id: 4, name: 'Upper Controls' },
    { id: 5, name: 'Insulating Liner' },
    { id: 6, name: 'Aerial Ladders' },
    { id: 7, name: 'Chassis Insulating' }
  ]) {
    test(`Test Module: ${testModule.name}`, async ({ page }) => {
      test.setTimeout(120000);
      customerName = `${testModule.name.replace(/\s+/g, '')}${Date.now()}`;
      equipmentSerial = `SN${Date.now()}`;

      console.log(`[${testModule.name}] Creating customer and equipment`);
      await createCustomerWithDetails(page, customerName);
      await createEquipmentWithVehicle(page, customerName, equipmentSerial);

      await page.selectOption('select[name="template_id"]', { index: 0 });
      await page.check(`input[name="test_modules"][value="${testModule.id}"]`);
      await page.click('button:has-text("Start Inspection")');
      await page.waitForURL(/\/inspections\/\d+\//);

      console.log(`[${testModule.name}] Answering all questions`);
      await answerAllQuestionsPass(page);

      console.log(`[${testModule.name}] Completing inspection`);
      const inspectionId = page.url().match(/\/inspections\/(\d+)\//)[1];
      await page.goto(`/inspections/${inspectionId}/complete/`);
      await page.click('button:has-text("Confirm & Complete")');
      await page.waitForTimeout(3000);

      console.log(`[${testModule.name}] Generating PDF`);
      await page.click('a:has-text("Generate PDF Package")');
      await page.waitForTimeout(5000);

      const pdfLink = page.locator('a[href*="inspection_package"]');
      await expect(pdfLink.first()).toBeVisible({ timeout: 10000 });
      console.log(`[${testModule.name}] ✓ PDF generated successfully`);
    });
  }
});
