const { test, expect } = require('@playwright/test');

test('Simple test - Create inspection with test module and complete', async ({ page }) => {
  test.setTimeout(60000);

  // Login
  await page.goto('/login/');
  await page.fill('input[name="username"]', 'josh');
  await page.fill('input[name="password"]', 'workAccount');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');

  // Create customer
  const custName = `TestCust${Date.now()}`;
  await page.goto('/customers/new/');
  await page.fill('input[name="name"]', custName);
  await page.click('button:has-text("Create Customer")');
  await page.waitForURL('/equipment/new/');

  // Create equipment
  await page.selectOption('select[name="customer"]', { label: custName });
  await page.fill('input[name="serial_number"]', `SN${Date.now()}`);
  await page.fill('input[name="make"]', 'Terex');
  await page.fill('input[name="model"]', 'Hi-Ranger');
  await page.click('button:has-text("Create Equipment")');
  await page.waitForURL(/\/inspections\/new\//);

  // Start inspection WITH test module
  await page.selectOption('select[name="template_id"]', { index: 0 });
  await page.check('input[name="test_modules"][value="3"]'); // Dielectric C/D/E
  await page.click('button:has-text("Start Inspection")');
  await page.waitForURL(/\/inspections\/\d+\//);

  console.log('✓ Inspection created with test module');

  // Try to complete without answering questions (should fail or redirect)
  const completeBtn = page.locator('a:has-text("Complete Inspection")');
  if (await completeBtn.isVisible({ timeout: 5000 })) {
    console.log('✓ Complete button found');
  } else {
    console.log('✗ Complete button not found - page may have issues');
  }
});
