<script lang="ts">
  import { onMount } from 'svelte';
  import { navigate } from 'astro:transitions/client';
  import { createStore, parseView, progressKey, readKey, VIEWS, type View } from '../lib/storage';
  import { anchorFrom, parseAnchor, scrollTargetFor, type Anchor } from '../lib/position';
  import { chapterPath } from '../lib/urls';

  interface Props {
    chapter: number;
    total: number;
    prev: number | null;
    next: number | null;
    prefetch: { en: string; fr: string }[];
  }
  let { chapter, total, prev, next, prefetch }: Props = $props();

  const LABELS: Record<View, { short: string; title: string }> = {
    en: { short: 'EN', title: 'Anglais seul (1)' },
    both: { short: 'EN | FR', title: 'Les deux (2)' },
    fr: { short: 'FR', title: 'Français seul (3)' },
  };
  const store = createStore();
  const root = document.documentElement;

  let view = $state<View>(parseView(store.get('view')));
  let page = $state(1);
  let progress = $state(0);
  let helpOpen = $state(false);
  let showCounter = $state(store.get('counter') !== 'hide');

  function toggleCounter() {
    showCounter = !showCounter;
    store.set('counter', showCounter ? '' : 'hide');
  }

  const pad = (n: number) => String(n).padStart(2, '0');
  const column = () => (view === 'en' ? 'en' : 'fr');
  const visibleImgs = () => [...document.querySelectorAll<HTMLImageElement>(`#strip img.${column()}`)];
  const boxes = () => visibleImgs().map(img => img.getBoundingClientRect());
  const goTo = (a: Anchor | null) => window.scrollTo(0, scrollTargetFor(a, boxes(), window.scrollY));

  function setView(nextView: View) {
    if (nextView === view) return;
    const a = anchorFrom(boxes());
    view = nextView;
    root.dataset.view = nextView; // tout de suite : la largeur change avant de recalculer la position
    goTo(a);
    store.set('view', nextView);
  }

  function save() {
    const end = document.getElementById('end');
    if (end && end.getBoundingClientRect().top < innerHeight) {
      store.set(progressKey(chapter), '');
      store.set(readKey(chapter), '1');
      return;
    }
    const a = anchorFrom(boxes());
    if (a) store.set(progressKey(chapter), a.page === 0 && a.frac === 0 ? '' : JSON.stringify(a));
  }

  function go(n: number | null) {
    if (n !== null) navigate(chapterPath(n));
  }

  // Compteur : page de la colonne visible au milieu de l'écran ; à refaire quand le mode change.
  $effect(() => {
    const observer = new IntersectionObserver(entries => {
      for (const e of entries) if (e.isIntersecting) page = Number((e.target as HTMLElement).dataset.page);
    }, { rootMargin: '-50% 0px -50% 0px' });
    document.querySelectorAll(`#strip img.${column()}`).forEach(img => observer.observe(img));
    return () => observer.disconnect();
  });

  $effect(() => {
    const bar = document.getElementById('progress');
    if (bar) bar.style.width = `${progress}%`;
  });

  onMount(() => {
    store.set('chapter', String(chapter));
    goTo(parseAnchor(store.get(progressKey(chapter))));

    let lastY = window.scrollY;
    let saveTimer: number | undefined;
    const onScroll = () => {
      const y = window.scrollY, max = root.scrollHeight - innerHeight;
      // Barre cachée en descendant, visible en remontant.
      if (y > lastY && y > 240) root.dataset.chrome = 'hidden';
      else delete root.dataset.chrome;
      progress = max > 0 ? Math.min(100, (y / max) * 100) : 0;
      lastY = y;
      clearTimeout(saveTimer);
      saveTimer = window.setTimeout(save, 250);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if ((e.target as HTMLElement).closest('input, select, textarea, [contenteditable]')) return;
      if (e.key === 'ArrowLeft') go(prev);
      else if (e.key === 'ArrowRight') go(next);
      else if (e.key === '1' || e.key === '2' || e.key === '3') setView(VIEWS[Number(e.key) - 1]);
      else if (e.key === '?') helpOpen = !helpOpen;
      else if (e.key === 'p' || e.key === 'P') toggleCounter();
      else if (e.key === 'Escape') helpOpen = false;
    };
    // Sauvegarde avant que la navigation ne remplace la page (après, la bande est détachée).
    document.addEventListener('astro:before-preparation', save);
    window.addEventListener('pagehide', save);
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('keydown', onKey);
    // Premières pages du chapitre suivant en tâche de fond.
    const prefetchTimer = window.setTimeout(() => {
      const langs = view === 'both' ? (['en', 'fr'] as const) : [view];
      for (const p of prefetch) for (const lang of langs) new Image().src = p[lang];
    }, 2000);

    return () => {
      document.removeEventListener('astro:before-preparation', save);
      window.removeEventListener('pagehide', save);
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('keydown', onKey);
      clearTimeout(saveTimer);
      clearTimeout(prefetchTimer);
      delete root.dataset.chrome;
    };
  });
</script>

<div class="seg" role="group" aria-label="Affichage">
  {#each VIEWS as v (v)}
    <button type="button" aria-pressed={view === v} title={LABELS[v].title} onclick={() => setView(v)}>{LABELS[v].short}</button>
  {/each}
</div>

<!-- Replié en pastille quand on le masque, pour pouvoir le rouvrir au doigt (pas de clavier sur mobile). -->
<button
  type="button"
  class="page-hud"
  class:collapsed={!showCounter}
  aria-label={showCounter ? 'Masquer le compteur de pages' : 'Afficher le compteur de pages'}
  title={showCounter ? 'Masquer le compteur (P)' : 'Afficher le compteur (P)'}
  onclick={toggleCounter}
>
  {#if showCounter}
    <span class="hud-text" aria-live="polite">PAGE<b>{pad(page)}<span> / {pad(total)}</span></b></span>
  {:else}
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M7 3h10v18H7z M4 6v12" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" /></svg>
  {/if}
</button>

{#if helpOpen}
  <div class="help" role="dialog" aria-labelledby="help-title">
    <h2 id="help-title">Raccourcis</h2>
    <dl>
      <dt><kbd>←</kbd> <kbd>→</kbd></dt><dd>Chapitre précédent / suivant</dd>
      <dt><kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd></dt><dd>Anglais / les deux / français</dd>
      <dt><kbd>P</kbd></dt><dd>Afficher ou masquer le compteur de pages</dd>
      <dt><kbd>?</kbd></dt><dd>Afficher ou masquer cette aide</dd>
      <dt><kbd>Échap</kbd></dt><dd>Fermer</dd>
    </dl>
    <button type="button" class="end-btn" onclick={() => (helpOpen = false)}>Fermer</button>
  </div>
{/if}
