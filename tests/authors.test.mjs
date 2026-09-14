import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildAuthorIndex,
  membersWithPublications,
  normalizeName,
  publicationIncludesMember,
  publicationsByMember,
} from '../src/utils/authors.mjs';

const members = [
  { slug: 'zhang-wei', name: '张伟', nameEn: 'Wei Zhang', role: '导师' },
  { slug: 'li-na', name: '李娜', nameEn: 'Na Li', role: '博士后' },
  { slug: 'sun-hao', name: '孙浩', nameEn: 'Hao Sun', role: '本科生' },
];

const publications = [
  { slug: 'p1', title: 'Cross-Modal Retrieval', authors: ['Na Li', 'Wei Zhang'], year: 2026 },
  { slug: 'p2', title: 'Open-Vocabulary 3D', authors: ['Qiang Wang', 'Wei Zhang'], year: 2026 },
  { slug: 'p3', title: '早期工作', authors: ['李娜'], year: 2023 },
];

test('归一化姓名：大小写与多余空格不影响匹配', () => {
  assert.equal(normalizeName('  Na   Li '), 'na li');
  assert.equal(normalizeName(null), '');
});

test('按英文名匹配到成员', () => {
  assert.equal(publicationIncludesMember(publications[0], members[1]), true); // Na Li -> 李娜
  assert.equal(publicationIncludesMember(publications[1], members[1]), false); // 没有李娜
});

test('中文署名同样能匹配', () => {
  assert.equal(publicationIncludesMember(publications[2], members[1]), true);
});

test('不做模糊匹配：部分姓名不会被算作命中', () => {
  const short = { slug: 'li', name: '李', nameEn: 'Li' };
  assert.equal(publicationIncludesMember(publications[0], short), false);
});

test('没有姓名的成员永远不会命中', () => {
  assert.equal(publicationIncludesMember(publications[0], { name: '', nameEn: '' }), false);
  assert.equal(publicationIncludesMember(publications[0], {}), false);
});

test('publicationsByMember 按年份倒序', () => {
  const result = publicationsByMember(publications, members[1]);
  assert.deepEqual(result.map((p) => p.slug), ['p1', 'p3']);
});

test('buildAuthorIndex 同时收中英文名，且保留先出现的成员', () => {
  const index = buildAuthorIndex(members);
  assert.equal(index['wei zhang'].slug, 'zhang-wei');
  assert.equal(index['张伟'].slug, 'zhang-wei');
  assert.equal(index['na li'].slug, 'li-na');
  assert.equal(index['unknown'], undefined);
});

test('membersWithPublications 只返回确实有论文的成员', () => {
  const result = membersWithPublications(members, publications);
  assert.deepEqual(result.map((m) => m.slug), ['zhang-wei', 'li-na']);
});
