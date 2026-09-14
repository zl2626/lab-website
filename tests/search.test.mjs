import test from 'node:test';
import assert from 'node:assert/strict';

import { escapeHtml, highlightMatches, scoreEntry, searchEntries, tokenize } from '../src/utils/search.mjs';

const entries = [
  { type: 'research', title: '计算机视觉', subtitle: 'Computer Vision', text: '目标检测 图像分割' },
  { type: 'member', title: '张伟', subtitle: '导师 · 教授', text: 'Wei Zhang 计算机视觉 多模态学习' },
  { type: 'news', title: '课题组 3 篇论文被 CVPR 2026 接收', subtitle: '论文被 CVPR 2026 接收', text: '2026-06-20' },
  { type: 'publication', title: 'Open-Vocabulary 3D Instance Segmentation', subtitle: '2026 · CVPR', text: 'Qiang Wang Wei Zhang' },
];

test('tokenize 支持中英文与多关键词', () => {
  assert.deepEqual(tokenize('  视觉  CVPR '), ['视觉', 'cvpr']);
  assert.deepEqual(tokenize(''), []);
  assert.deepEqual(tokenize(null), []);
});

test('标题命中排在正文命中之前', () => {
  const tokens = tokenize('视觉');
  const titleHit = scoreEntry(entries[0], tokens); // 标题
  const textHit = scoreEntry(entries[1], tokens); // 仅在附加文本里
  assert.ok(titleHit > textHit);
});

test('多关键词是 AND 语义：缺一个就整体不匹配', () => {
  assert.ok(scoreEntry(entries[2], tokenize('cvpr 接收')) > 0);
  assert.equal(scoreEntry(entries[2], tokenize('cvpr 不存在的词')), -1);
});

test('searchEntries 按相关度排序并遵守数量上限', () => {
  const results = searchEntries(entries, 'CVPR', 1);
  assert.equal(results.length, 1);
  assert.equal(results[0].title, '课题组 3 篇论文被 CVPR 2026 接收');

  const all = searchEntries(entries, '视觉');
  assert.deepEqual(
    all.map((item) => item.title),
    ['计算机视觉', '张伟']
  );
});

test('空查询返回空数组，而不是整个索引', () => {
  assert.deepEqual(searchEntries(entries, '   '), []);
});

test('高亮会转义 HTML，避免把索引内容当成标签注入', () => {
  assert.equal(escapeHtml('<img src=x onerror=1>'), '&lt;img src=x onerror=1&gt;');
  const html = highlightMatches('a<b>视觉', ['视觉']);
  assert.ok(html.includes('&lt;b&gt;'));
  assert.ok(html.includes('<mark>视觉</mark>'));
  assert.ok(!html.includes('<b>'));
});

test('高亮对正则元字符保持字面量匹配', () => {
  const html = highlightMatches('C++ 与 C# 对比', ['c++']);
  assert.ok(html.includes('<mark>C++</mark>'));
});
