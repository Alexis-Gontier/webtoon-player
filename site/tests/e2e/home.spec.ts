import { readFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';

const chapters = JSON.parse(readFileSync(new URL('../../src/data/chapters.json', import.meta.url), 'utf-8'));
const FIRST = chapters[0].n, SECOND = chapters[1].n;

test('badges et bouton Reprendre', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await expect(page.locator('#resume')).toBeHidden();
  await page.evaluate(([a, b]) => {
    localStorage.setItem(`read:${a}`, '1');
    localStorage.setItem(`progress:${b}`, '{"page":2,"frac":0.1}');
    localStorage.setItem('chapter', String(b));
  }, [FIRST, SECOND]);
  await page.reload();
  await expect(page.locator(`[data-chapter-card="${FIRST}"]`)).toHaveAttribute('data-status', 'read');
  await expect(page.locator(`[data-chapter-card="${SECOND}"]`)).toHaveAttribute('data-status', 'progress');
  await expect(page.locator('#resume')).toBeVisible();
  await expect(page.locator('#resume')).toHaveAttribute('href', `/chapitre/${SECOND}/`);
});

test('bascule lu / non lu et progression', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(([a, b]) => {
    localStorage.clear();
    localStorage.setItem(`read:${a}`, '1');
    localStorage.setItem(`read:${b}`, '1');
    localStorage.setItem('chapter', String(b));
  }, [FIRST, SECOND]);
  await page.reload();
  await expect(page.locator('#resume')).toBeVisible();
  await expect(page.locator('#read-count')).toHaveText('2');
  const second = page.getByRole('button', { name: `Chapitre ${SECOND} lu` });
  await expect(second).toHaveAttribute('aria-pressed', 'true');
  await second.click();
  await expect(second).toHaveAttribute('aria-pressed', 'false');
  await expect(page.locator(`[data-chapter-card="${SECOND}"]`)).toHaveAttribute('data-status', '');
  await expect(page.locator(`[data-chapter-card="${FIRST}"]`)).toHaveAttribute('data-status', 'read');
  await expect(page.locator('#read-count')).toHaveText('1');
  await expect(page.locator('#resume')).toBeHidden();
  await second.click();
  await expect(page.locator(`[data-chapter-card="${SECOND}"]`)).toHaveAttribute('data-status', 'read');
  await page.reload();
  await expect(page.locator('#read-count')).toHaveText('2');
});

test('recherche par numéro et tri mémorisé', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  const items = page.locator('#chapter-list > li:not([hidden])');
  const search = page.getByRole('searchbox', { name: 'Aller au chapitre' });
  await search.fill(String(SECOND));
  await expect(items).toHaveCount(1);
  await search.fill('9999');
  await expect(page.locator('#no-result')).toBeVisible();
  await search.fill(String(SECOND));
  await search.press('Enter');
  await expect(page).toHaveURL(new RegExp(`/chapitre/${SECOND}/$`));
  await page.goto('/');
  await expect(page.locator('#chapter-list > li').first()).toHaveAttribute('data-n', String(FIRST));
  await page.getByRole('button', { name: 'Du premier au dernier' }).click();
  await expect(page.locator('#chapter-list > li').first()).toHaveAttribute('data-n', String(chapters.at(-1).n));
  await page.reload();
  await expect(page.getByRole('button', { name: 'Du dernier au premier' })).toBeVisible();
});

test('aperçus non lus masqués par défaut, choix mémorisé', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(a => { localStorage.clear(); localStorage.setItem(`read:${a}`, '1'); }, FIRST);
  await page.reload();
  const img = (n: number) => page.locator(`[data-chapter-card="${n}"] img`);
  const toggle = page.getByRole('button', { name: 'Masquer les aperçus non lus' });
  await expect(toggle).toHaveAttribute('aria-pressed', 'true');
  await expect(img(FIRST)).toHaveCSS('filter', 'none');
  await expect(img(SECOND)).toHaveCSS('filter', /blur/);
  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-pressed', 'false');
  await expect(img(SECOND)).toHaveCSS('filter', 'none');
  await page.reload();
  await expect(img(SECOND)).toHaveCSS('filter', 'none');
});
