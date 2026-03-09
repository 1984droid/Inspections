const { test } = require('@playwright/test');

test('Debug inspection page', async ({ page }) => {
  await page.goto('/login/');
  await page.fill('input[name="username"]', 'josh');
  await page.fill('input[name="password"]', 'workAccount');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');

  // Visit inspection 21
  await page.goto('/inspections/21/');
  await page.waitForLoadState('networkidle');

  const title = await page.title();
  const content = await page.content();
  
  console.log('Title:', title);
  console.log('Has Complete button:', content.includes('Complete Inspection'));
  console.log('Has questions:', content.includes('data-question-id'));
  console.log('Page size:', content.length);
});
