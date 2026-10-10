import { readFileSync } from 'node:fs';
import { expect, test, type Page } from '@playwright/test';

const chapters = JSON.parse(readFileSync(new URL('../../src/data/chapters.json', import.meta.url), 'utf-8'));
const FIRST = chapters[0].n, SECOND = chapters[1].n, LAST = chapters.at(-1).n;

const counter = (page: Page) => page.locator('.page-hud b');
async function scrollToPage(page: Page, p: number, frac = 0.5) {
  await page.evaluate(([p, frac]) => {
    const img = document.querySelector<HTMLImageElement>(`#strip img.fr[data-page="${p}"]`)!;
    const box = img.getBoundingClientRect();
    window.scrollTo(0, box.top + window.scrollY + frac * box.height);
  }, [p, frac]);
  await page.waitForTimeout(400); // sauvegarde différée de 250 ms
}

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.clear());
});

test('mode par défaut EN|FR, changement au clavier', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await expect(page.locator('html')).toHaveAttribute('data-view', 'both');
  await expect(page.locator('.seg')).toBeVisible();
  await page.keyboard.press('3');
  await expect(page.locator('html')).toHaveAttribute('data-view', 'fr');
  await expect(page.locator('#strip img.en').first()).toBeHidden();
  await expect(page.getByRole('button', { name: 'FR', exact: true })).toHaveAttribute('aria-pressed', 'true');
});

test('les boutons de mode et le compteur sont au premier plan', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  for (const selector of ['.seg button', '.page-hud']) {
    const target = page.locator(selector).first();
    await expect(target).toBeVisible();
    const box = (await target.boundingBox())!;
    const onTop = await page.evaluate(([x, y, sel]) => {
      const hit = document.elementFromPoint(x, y);
      return !!hit?.closest(sel);
    }, [box.x + box.width / 2, box.y + box.height / 2, selector] as const);
    expect(onTop, `${selector} recouvert`).toBe(true);
  }
  await page.locator('.seg button').last().click();
  await expect(page.locator('html')).toHaveAttribute('data-view', 'fr');
});

test('changer de mode garde la page en cours', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await expect(page.locator('.seg')).toBeVisible();
  await scrollToPage(page, 3);
  await expect(counter(page)).toContainText('03');
  await page.keyboard.press('1');
  await page.waitForTimeout(200);
  await expect(counter(page)).toContainText('03');
});

test('la position est reprise après rechargement, le mode aussi', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await expect(page.locator('.seg')).toBeVisible();
  await page.keyboard.press('3');
  await scrollToPage(page, 4);
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-view', 'fr');
  await expect(counter(page)).toContainText('04');
});

test('flèches : chapitre suivant, rien après le dernier', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await expect(page.locator('.seg')).toBeVisible();
  await page.keyboard.press('ArrowRight');
  await expect(page).toHaveURL(new RegExp(`/chapitre/${SECOND}/$`));
  await page.goto(`/chapitre/${LAST}/`);
  await expect(page.locator('.seg')).toBeVisible();
  await page.keyboard.press('ArrowRight');
  await page.waitForTimeout(300);
  await expect(page).toHaveURL(new RegExp(`/chapitre/${LAST}/$`));
});

test('fin de chapitre : marqué lu', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await expect(page.locator('.seg')).toBeVisible();
  await page.evaluate(() => document.getElementById('end')!.scrollIntoView());
  await page.waitForTimeout(400);
  expect(await page.evaluate(n => localStorage.getItem(`read:${n}`), FIRST)).toBe('1');
});

test('aide des raccourcis', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await expect(page.locator('.seg')).toBeVisible();
  await page.keyboard.press('?');
  await expect(page.getByRole('dialog', { name: 'Raccourcis' })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('sans JavaScript : lecture EN|FR', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(`/chapitre/${FIRST}/`);
  await expect(page.locator('#strip img.en').first()).toBeVisible();
  await expect(page.locator('#strip img.fr').first()).toBeVisible();
  await context.close();
});

test('mobile 390 px : pas de défilement horizontal', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const path of ['/', `/chapitre/${FIRST}/`]) {
    await page.goto(path);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  }
});
