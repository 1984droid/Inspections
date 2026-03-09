const { test, expect } = require('@playwright/test');

test('Complete inspection with all PASS answers', async ({ page }) => {
  const inspectionId = process.env.INSPECTION_ID || '7';

  // Login
  await page.goto('http://localhost:3000/login/');
  await page.fill('input[name="username"]', 'josh');
  await page.fill('input[name="password"]', 'workAccount');
  await page.click('button[type="submit"]');
  await page.waitForURL('http://localhost:3000/');

  // Navigate to inspection
  console.log(`Navigating to inspection ${inspectionId}...`);
  await page.goto(`http://localhost:3000/inspections/${inspectionId}/`);

  // Wait for page to load completely
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);

  // Find all PASS radio buttons
  const allPassRadios = await page.locator('input[type="radio"][value="P"], input[type="radio"][value="pass"]').all();
  console.log(`Found ${allPassRadios.length} PASS radio buttons`);

  // Click each PASS radio button and wait for save
  for (let i = 0; i < allPassRadios.length; i++) {
    const radio = allPassRadios[i];

    if (await radio.isVisible() && await radio.isEnabled()) {
      const name = await radio.getAttribute('name');
      console.log(`[${i+1}/${allPassRadios.length}] Clicking PASS for: ${name}`);

      await radio.click();

      // Wait for potential AJAX save request
      await page.waitForTimeout(500);
    }
  }

  console.log('All PASS buttons clicked, waiting for final save...');
  await page.waitForTimeout(2000);

  // Navigate to complete page
  console.log('Navigating to complete page...');
  await page.goto(`http://localhost:3000/inspections/${inspectionId}/complete/`);
  await page.waitForTimeout(1000);

  // Click confirm and complete button
  const confirmButton = page.locator('button:has-text("Confirm & Complete"), button:has-text("Confirm")').first();
  if (await confirmButton.count() > 0) {
    console.log('Clicking Confirm & Complete...');
    await confirmButton.click();
    await page.waitForTimeout(3000);
  } else {
    console.log('No confirm button found!');
  }

  // Take a screenshot for verification
  await page.screenshot({ path: `inspection-${inspectionId}-completed.png`, fullPage: true });

  console.log('Inspection completion script finished');
  console.log(`View inspection at: http://localhost:3000/inspections/${inspectionId}/`);
});
