import assert from 'node:assert/strict';
import test from 'node:test';
import { clampHomeCount, selectHomeHero } from '../src/utils/home.mjs';

test('selectHomeHero uses the first configured slide', () => {
  const fallback = { title: 'Fallback' };

  assert.equal(
    selectHomeHero([{ title: 'First' }, { title: 'Second' }], fallback).title,
    'First',
  );
});

test('selectHomeHero falls back when no slide is configured', () => {
  const fallback = { title: 'Fallback' };

  assert.equal(selectHomeHero([], fallback), fallback);
});

test('clampHomeCount accepts valid values and clamps extremes', () => {
  assert.equal(clampHomeCount('6', 4), 6);
  assert.equal(clampHomeCount('0', 4), 1);
  assert.equal(clampHomeCount('100', 4), 12);
  assert.equal(clampHomeCount('bad', 4), 4);
});
