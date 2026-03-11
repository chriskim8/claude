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

  // Tab 1 — Rules Index
  await page.screenshot({ path: path.join(outDir, '01-rules-index.png'), fullPage: true });
  console.log('01 rules-index');

  // Tab 2 — Simple cancel rule
  await page.locator('.proto-tab').nth(1).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(outDir, '02-simple-cancel.png'), fullPage: true });
  console.log('02 simple-cancel');

  // Tab 3 — Advanced cancel rule
  await page.locator('.proto-tab').nth(2).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(outDir, '03-advanced-cancel.png'), fullPage: true });
  console.log('03 advanced-cancel');

  // Tab 4 — Calendar result
  await page.locator('.proto-tab').nth(3).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(outDir, '04-calendar-result.png'), fullPage: true });
  console.log('04 calendar-result');

  await browser.close();
  console.log('Done:', outDir);
})();
