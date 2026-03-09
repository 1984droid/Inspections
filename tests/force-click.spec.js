const { test } = require('@playwright/test');

test('Force click Complete button', async ({ page }) => {
  await page.goto('/login/');
  await page.fill('input[name="username"]', 'josh');
  await page.fill('input[name="password"]', 'workAccount');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');

  await page.goto('/inspections/26/');
  await page.waitForLoadState('networkidle');
  
  // Force click the button even if not visible
  await page.locator('a:has-text("Complete Inspection")').click({ force: true });
  console.log('✓ Force clicked Complete button');
  
  await page.waitForTimeout(1000);
  console.log('Current URL:', page.url());
});
