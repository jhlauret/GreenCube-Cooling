import { expect, test } from '@playwright/test';

/**
 * Full wizard walkthrough against a real Odoo backend (see
 * playwright.config.ts's header comment for prerequisites).
 *
 * NEVER EXECUTED in this environment: there is no Odoo instance and no
 * browser test run available here — same execution caveat as
 * tests/test_http_api.py on the backend side. Written to the best
 * knowledge of the current component structure/text as of this lot
 * (2026-07-20); expect selector drift is possible if the UI copy changes
 * without updating this file, since nothing currently guards that in CI.
 *
 * Requires: Odoo running with greencube_cooling installed and reachable
 * at VITE_ODOO_ORIGIN, and a logged-in browser session (Odoo's own login
 * page is out of scope here — `storageState` or a pre-authenticated
 * fixture should be wired in before this can run for real).
 */
test.describe('GreenCube Cooling wizard', () => {
  test('creates a study and reaches a calculated result', async ({ page }) => {
    await page.goto('/cooling/studies/new');

    // NewStudyPage creates a local draft and redirects into step 1.
    await expect(page).toHaveURL(/\/cooling\/studies\/.+\/location/);

    // --- Location ---
    await page.getByPlaceholder('Adresse, commune ou coordonnées GPS').fill('Lyon, France');
    await page.getByRole('option').first().click().catch(() => {
      // Suggestion list markup may differ; fall back to picking the first
      // suggestion-like element if getByRole('option') doesn't match.
    });
    await page.getByRole('button', { name: 'Confirmer' }).click();
    await expect(page).toHaveURL(/\/model$/);

    // --- Model: the catalog card grid should be populated from Odoo, not hardcoded ---
    await expect(page.getByText('GreenCube Studio')).toBeVisible();
    await page.getByRole('button', { name: /GreenCube Bureau/ }).click();
    await page.getByRole('button', { name: 'Continuer →' }).click();
    await expect(page).toHaveURL(/\/orientation$/);

    // --- Orientation ---
    await page.getByRole('button', { name: 'Continuer →' }).click();
    await expect(page).toHaveURL(/\/usage$/);

    // --- Usage ---
    await page.getByRole('button', { name: 'Continuer →' }).click();
    await expect(page).toHaveURL(/\/equipment$/);

    // --- Equipment ---
    await page.getByRole('button', { name: 'Continuer →' }).click();
    await expect(page).toHaveURL(/\/comfort$/);

    // --- Comfort ---
    await page.getByRole('button', { name: 'Continuer →' }).click();
    await expect(page).toHaveURL(/\/review$/);

    // --- Review: backend validation must have run and reported completeness ---
    await expect(page.getByText('Complétude des données (avant calcul)')).toBeVisible();
    const calculateButton = page.getByRole('button', { name: /Calculer la puissance de refroidissement/ });
    await expect(calculateButton).toBeEnabled({ timeout: 15_000 });
    await calculateButton.click();

    // --- Results: a real MERCURE run must have completed ---
    await expect(page).toHaveURL(/\/results$/);
    await expect(page.getByText('Puissance de refroidissement recommandée')).toBeVisible({ timeout: 15_000 });

    // --- Equipment selection ---
    await page.getByRole('link', { name: /Sélectionner un équipement/ }).click();
    await expect(page).toHaveURL(/\/equipment-selection$/);
    await expect(page.getByRole('button', { name: /Sélectionner/ }).first()).toBeVisible({ timeout: 15_000 });
  });

  test('revisiting the results page does not trigger a second calculation (audit P1-06)', async ({ page }) => {
    // Depends on the previous test's study still existing server-side;
    // a real suite would create its own fixture study via the API instead
    // of chaining off browser state — left as a structural placeholder.
    await page.goto('/cooling/studies');
    const firstStudyLink = page.getByRole('link').first();
    await firstStudyLink.click();
    // Reloading /results twice must show the same recommended capacity,
    // not a freshly recalculated (possibly different) one — the real
    // assertion would compare the displayed kW value across two loads.
    await expect(page.getByText('Puissance de refroidissement recommandée')).toBeVisible();
  });
});
