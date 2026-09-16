export function selectHomeHero(homeSlides, fallback) {
  return homeSlides[0] ?? fallback;
}

export function clampHomeCount(value, fallback) {
  const parsed = Number.parseInt(String(value ?? '').trim(), 10);

  if (!Number.isFinite(parsed)) return fallback;

  return Math.min(Math.max(parsed, 1), 12);
}
