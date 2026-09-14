import test from 'node:test';
import assert from 'node:assert/strict';
import { escapeBibtex, publicationBibtex } from '../src/utils/bibtex.mjs';

const paper = { slug: 'example-2026', title: 'Vision & Learning', year: 2026, authors: ['Na Li', 'Wei Zhang'], venue: 'CVPR', type: '会议论文', link: 'https://example.org/paper' };

test('conference citations preserve metadata without inventing volume or DOI', () => {
  const bib = publicationBibtex(paper);
  assert.match(bib, /^@inproceedings\{example-2026,/);
  assert.ok(bib.includes('author = {Na Li and Wei Zhang}'));
  assert.ok(bib.includes('booktitle = {CVPR}'));
  assert.ok(bib.includes('title = {Vision \\& Learning}'));
  assert.doesNotMatch(bib, /doi =|volume =/);
});
test('journal and other publication types use suitable fields', () => {
  assert.match(publicationBibtex({ ...paper, type: '期刊论文' }), /journal = \{CVPR\}/);
  assert.match(publicationBibtex({ ...paper, type: '专利' }), /^@misc/);
});
test('literal braces, backslashes and newlines cannot break field boundaries', () => {
  assert.equal(escapeBibtex('A{B}\\C\n50%'), 'A\\{B\\}\\textbackslash{}C 50\\%');
  const bib = publicationBibtex({ ...paper, authors: [], link: '', slug: 'bad,key}' });
  assert.match(bib, /^@inproceedings\{bad-key-,/);
  assert.doesNotMatch(bib, /author =|url =/);
});
