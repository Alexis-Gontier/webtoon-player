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
