"""
capture_proposal_screenshots.py

Takes fresh screenshots from Amion Next for proposal visual collateral.
Uses test account credentials from smoke-residency.js.
"""

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL  = 'https://www.amion.com'
EMAIL     = 'testamion@gmail.com'
PASSWORD  = 'kac1QWB@frg2ctr9cwj'
ORG_ID    = '1084dff1-96c7-4f49-8f5f-e589fcf30101'
SCHED_ID  = 'ddb4c70a-d3ba-4e05-b996-227a78830024'

MANAGER   = f'{BASE_URL}/manager/schedules/{SCHED_ID}'
SCHED     = f'{BASE_URL}/organizations/{ORG_ID}/schedules/{SCHED_ID}'
ORG       = f'{BASE_URL}/organizations/{ORG_ID}'

SIGN_IN   = (
    f'{BASE_URL}/dox-auth-omniauth-session/signin'
    '?return_to=https%3A%2F%2Fwww.amion.com%2Forganizations'
    '&theme=5fca039e-29e7-40e5-80d9-315bb485c772'
)

OUT = Path('/Users/chriskim/notes/residency/user-journeys/screenshots')


async def login(page):
    await page.goto(SIGN_IN, wait_until='networkidle')
    await page.fill('input[name="login"]', EMAIL)
    await page.keyboard.press('Enter')
    await page.wait_for_load_state('networkidle')
    await page.fill('input[name="password"]', PASSWORD)
    await page.keyboard.press('Enter')
    await page.wait_for_load_state('networkidle')
    print('  ✓ Logged in')


async def nav(page, url, wait_ms=1500):
    await page.goto(url, wait_until='networkidle')
    await page.wait_for_timeout(wait_ms)


async def shot(page, name):
    path = OUT / name
    await page.screenshot(path=str(path), full_page=False)
    print(f'  ✓ {name}')


async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({'width': 1440, 'height': 900})

        print('Logging in...')
        await login(page)

        # ── Rules & Templates ────────────────────────────────────────────────
        # Navigate to manager settings, click Rules & Templates in sidebar
        print('Rules & Templates...')
        await nav(page, f'{MANAGER}/settings')
        try:
            link = page.locator('a:has-text("Rules & Templates"), a:has-text("Rules")')
            if await link.first.is_visible(timeout=4000):
                await link.first.click()
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(800)
        except Exception:
            pass
        await shot(page, 'manager-rules-templates.png')

        # ── Call Services ────────────────────────────────────────────────────
        print('Call Services...')
        await nav(page, f'{MANAGER}/settings')
        try:
            link = page.locator('a:has-text("Call"):not(:has-text("Cross"))')
            if await link.first.is_visible(timeout=4000):
                await link.first.click()
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(800)
        except Exception:
            await nav(page, f'{MANAGER}/services/call')
        await shot(page, 'manager-services-call.png')

        # ── Manager call calendar ────────────────────────────────────────────
        print('Manager call calendar...')
        await nav(page, f'{SCHED}/call', wait_ms=2000)
        await shot(page, 'manager-call-calendar.png')

        # ── Clinic templates panel ────────────────────────────────────────────
        print('Clinic templates panel...')
        await nav(page, f'{SCHED}/clinic', wait_ms=2000)
        try:
            btn = page.locator('button:has-text("Clinic Templates"), [data-testid="clinic-templates"]')
            if await btn.first.is_visible(timeout=4000):
                await btn.first.click()
                await page.wait_for_timeout(1000)
        except Exception:
            pass
        await shot(page, 'manager-clinic-templates-panel.png')

        # ── Clinic Services ──────────────────────────────────────────────────
        print('Clinic Services...')
        await nav(page, f'{MANAGER}/settings')
        try:
            link = page.locator('a:has-text("Clinic")')
            if await link.first.is_visible(timeout=4000):
                await link.first.click()
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(800)
        except Exception:
            pass
        await shot(page, 'manager-services-clinics.png')

        # ── Viewer call calendar ─────────────────────────────────────────────
        print('Viewer call calendar...')
        await nav(page, f'{SCHED}/calendar?assignment_kind=call', wait_ms=2000)
        await shot(page, 'viewer-call-calendar.png')

        await browser.close()
        print(f'\nAll screenshots saved to {OUT}')


if __name__ == '__main__':
    asyncio.run(capture())
