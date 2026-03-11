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

  await page.screenshot({ path: path.join(outDir, '01-pattern-index.png'), fullPage: true });
  console.log('01 pattern-index');

  await page.locator('.proto-tab').nth(1).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(outDir, '02-define-pattern.png'), fullPage: true });
  console.log('02 define-pattern');

  await page.locator('.proto-tab').nth(2).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(outDir, '03-apply-pattern.png'), fullPage: true });
  console.log('03 apply-pattern');

  await page.locator('.proto-tab').nth(3).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(outDir, '04-calendar-result.png'), fullPage: true });
  console.log('04 calendar-result');

  await browser.close();
  console.log('Done:', outDir);
})();
