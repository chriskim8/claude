const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const htmlPath = 'file://' + path.resolve(__dirname, 'index.html');
  const outDir = path.resolve(__dirname, 'screenshots');
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto(htmlPath);
  await page.waitForLoadState('networkidle');

  // Tab 1 — Existing Pattern (reference)
  await page.screenshot({ path: path.join(outDir, '01-existing.png'), fullPage: true });
  console.log('01 existing');

  // Tab 2 — Revised weekly
  await page.locator('.proto-tab').nth(1).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(outDir, '02-revised-weekly.png'), fullPage: true });
  console.log('02 revised-weekly');

  // Tab 3 — Revised 4-week cadence
  await page.locator('.proto-tab').nth(2).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(outDir, '03-revised-4week.png'), fullPage: true });
  console.log('03 revised-4week');

  // Tab 4 — Cancel states
  await page.locator('.proto-tab').nth(3).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(outDir, '04-cancel-states.png'), fullPage: true });
  console.log('04 cancel-states');

  await browser.close();
  console.log('Done:', outDir);
})();
