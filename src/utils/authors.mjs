/**
 * 成员与成果之间的作者匹配。
 *
 * 成果的 authors 是一串姓名字符串（通常是英文原文，如 "Na Li"），
 * 成员的 nameEn 也是同一套写法，因此用「归一化后精确相等」来匹配：
 * 不做模糊匹配 —— 中文姓名只有两三个字，模糊匹配很容易把不相干的人算进来。
 */

/** 归一化：去首尾空白、压缩内部空白、转小写 */
export function normalizeName(value) {
  return String(value ?? '').replace(/\s+/g, ' ').trim().toLowerCase();
}

/** 某个成果是否包含这位成员（按中英文名精确匹配） */
export function publicationIncludesMember(item, member) {
  const targets = [normalizeName(member?.nameEn), normalizeName(member?.name)].filter(Boolean);
  if (!targets.length) return false;
  return (item?.authors ?? []).some((author) => targets.includes(normalizeName(author)));
}

/** 这位成员参与过的成果，按年份从新到旧 */
export function publicationsByMember(publications, member) {
  return (publications ?? [])
    .filter((item) => publicationIncludesMember(item, member))
    .sort((a, b) => b.year - a.year || String(a.title).localeCompare(String(b.title)));
}

/**
 * 建立「归一化作者名 -> 成员」的索引，用于把成果里的作者名变成链接。
 * 同名冲突时保留第一个（成员列表本身是按组内排序的）。
 */
export function buildAuthorIndex(members) {
  const index = {};
  for (const member of members ?? []) {
    for (const candidate of [member.nameEn, member.name]) {
      const key = normalizeName(candidate);
      if (key && !index[key]) {
        index[key] = { slug: member.slug, name: member.name, role: member.role };
      }
    }
  }
  return index;
}

/** 成果里出现过的成员（用于成果页的「作者」筛选下拉），保持成员原本的顺序 */
export function membersWithPublications(members, publications) {
  return (members ?? []).filter((member) =>
    (publications ?? []).some((item) => publicationIncludesMember(item, member))
  );
}
