const { test } = require('@playwright/test');

test('Direct complete', async ({ page }) => {
  await page.goto('/login/');
  await page.fill('input[name="username"]', 'josh');
  await page.fill('input[name="password"]', 'workAccount');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');

  // Go directly to complete page
  await page.goto('/inspections/26/complete/');
  await page.waitForLoadState('networkidle');
  
  console.log('On complete page');
  
  // Submit the form
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(3000);
  
  console.log('Final URL:', page.url());
  console.log('✓ Test complete');
});
