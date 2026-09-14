import test from 'node:test';
import assert from 'node:assert/strict';

import { shouldShowToc, slugifyHeading, withHeadingAnchors } from '../src/utils/toc.mjs';

test('中文标题生成可读的锚点，标点被去掉', () => {
  assert.equal(slugifyHeading('主要研究内容'), '主要研究内容');
  assert.equal(slugifyHeading('研究问题：开放环境'), '研究问题开放环境');
  assert.equal(slugifyHeading('Stage 1: Data'), 'stage-1-data');
  assert.equal(slugifyHeading('   '), 'section');
});

test('给 h2 / h3 补 id 并收集目录', () => {
  const html = '<p>引言</p><h2>主要研究内容</h2><p>x</p><h3>跨域泛化</h3><h2>代表性工作</h2>';
  const { html: out, headings } = withHeadingAnchors(html);

  assert.equal(headings.length, 3);
  assert.deepEqual(headings.map((h) => h.text), ['主要研究内容', '跨域泛化', '代表性工作']);
  assert.deepEqual(headings.map((h) => h.level), [2, 3, 2]);
  assert.ok(out.includes('id="主要研究内容"'));
  assert.ok(out.includes('id="跨域泛化"'));
  assert.ok(out.includes('id="代表性工作"'));
});

test('同名标题自动加序号，不产生重复 id', () => {
  const { headings, html } = withHeadingAnchors('<h2>方法</h2><h2>方法</h2><h2>方法</h2>');
  assert.deepEqual(headings.map((h) => h.id), ['方法', '方法-2', '方法-3']);
  assert.equal((html.match(/id="方法/g) || []).length, 3);
});

test('已经带 id 的标题不重复添加，但仍进目录', () => {
  const { html, headings } = withHeadingAnchors('<h2 id="custom">已有锚点</h2>');
  assert.equal(headings[0].id, 'custom');
  assert.equal((html.match(/\bid=/g) || []).length, 1);
});

test('h4 及以下不进目录，但同样获得锚点', () => {
  const { html, headings } = withHeadingAnchors('<h4>细节</h4>');
  assert.equal(headings.length, 0);
  assert.ok(html.includes('id="细节"'));
});

test('标题里的行内标签不会进目录文字', () => {
  const { headings } = withHeadingAnchors('<h2>关于 <code>Transformer</code> 的改进</h2>');
  assert.equal(headings[0].text, '关于 Transformer 的改进');
});

test('目录显示阈值：小节太少就不显示', () => {
  assert.equal(shouldShowToc([]), false);
  assert.equal(shouldShowToc([{ level: 2, id: 'a', text: 'a' }]), false);
  assert.equal(
    shouldShowToc([
      { level: 2, id: 'a', text: 'a' },
      { level: 2, id: 'b', text: 'b' },
      { level: 2, id: 'c', text: 'c' },
    ]),
    true
  );
});

test('空输入不报错', () => {
  assert.deepEqual(withHeadingAnchors(''), { html: '', headings: [] });
  assert.deepEqual(withHeadingAnchors(null), { html: '', headings: [] });
});
