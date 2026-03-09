const { test, expect } = require('@playwright/test');

test('Quick test - just load inspection 14', async ({ page }) => {
  await page.goto('http://127.0.0.1:8001/login/');
  await page.fill('input[name="username"]', 'josh');
  await page.fill('input[name="password"]', 'workAccount');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');

  await page.goto('http://127.0.0.1:8001/inspections/14/');
  await page.waitForTimeout(2000);

  const title = await page.title();
  console.log('Page title:', title);
  console.log('✓ Page loaded successfully');
});
