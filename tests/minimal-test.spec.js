const { test } = require('@playwright/test');

test('Minimal - complete inspection with test module', async ({ page }) => {
  await page.goto('/login/');
  await page.fill('input[name="username"]', 'josh');
  await page.fill('input[name="password"]', 'workAccount');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');

  // Visit latest inspection  
  await page.goto('/inspections/26/');
  await page.waitForLoadState('networkidle');
  
  console.log('Page loaded');
  
  // Try to click Complete
  try {
    await page.locator('a:has-text("Complete Inspection")').scrollIntoViewIfNeeded({ timeout: 2000 });
    console.log('Button scrolled into view');
    await page.locator('a:has-text("Complete Inspection")').click({ timeout: 3000 });
    console.log('✓ Clicked Complete button');
  } catch (e) {
    console.log('✗ Failed:', e.message);
  }
});
