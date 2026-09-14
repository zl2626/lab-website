import test from 'node:test';
import assert from 'node:assert/strict';
import { matchesNewsTag } from '../src/utils/news-filter.mjs';

test('news filters preserve commas inside a tag', () => {
  assert.equal(matchesNewsTag('["视觉,机器人","CVPR"]', '视觉,机器人'), true);
  assert.equal(matchesNewsTag('["视觉,机器人"]', '视觉'), false);
});

test('a tag named all is distinct from the unfiltered option', () => {
  assert.equal(matchesNewsTag('["CVPR"]', 'all'), false);
  assert.equal(matchesNewsTag('["all"]', 'all'), true);
  assert.equal(matchesNewsTag('[]', null), true);
});
