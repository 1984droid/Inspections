const { test } = require('@playwright/test');

test('Complete inspection with test module', async ({ page }) => {
  await page.goto('/login/');
  await page.fill('input[name="username"]', 'josh');
  await page.fill('input[name="password"]', 'workAccount');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');

  const custName = `TC${Date.now()}`;
  
  // Create customer
  await page.goto('/customers/new/');
  await page.fill('input[name="name"]', custName);
  await page.click('button:has-text("Create Customer")');
  
  // Create equipment
  await page.selectOption('select[name="customer"]', { label: custName });
  await page.fill('input[name="serial_number"]', `SN${Date.now()}`);
  await page.fill('input[name="make"]', 'Terex');
  await page.fill('input[name="model"]', 'Test');
  await page.click('button:has-text("Create Equipment")');
  
  // Start inspection with test module
  await page.selectOption('select[name="template_id"]', { index: 0 });
  await page.check('input[name="test_modules"][value="3"]');
  await page.click('button:has-text("Start Inspection")');
  await page.waitForURL(/\/inspections\/\d+\//);
  
  const inspectionId = page.url().match(/\/inspections\/(\d+)\//)[1];
  console.log('Created inspection:', inspectionId);
  
  // Go directly to complete
  await page.goto(`/inspections/${inspectionId}/complete/`);
  await page.click('button:has-text("Confirm & Complete")');
  await page.waitForTimeout(5000);
  
  // Generate PDF
  await page.click('a:has-text("Generate PDF Package")');
  await page.waitForTimeout(3000);
  
  console.log('✓ PDF generation triggered!');
  console.log('Final URL:', page.url());
});
