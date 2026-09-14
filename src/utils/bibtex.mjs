/** Escape metadata as literal BibTeX text; never invent missing fields. */
export function escapeBibtex(value) {
  const escapes = {
    '\\': '\\textbackslash{}', '{': '\\{', '}': '\\}',
    '%': '\\%', '&': '\\&', '#': '\\#', '_': '\\_',
    '$': '\\$', '~': '\\textasciitilde{}', '^': '\\textasciicircum{}',
  };
  return String(value).replace(/[\\{}%&#_$~^]/g, (char) => escapes[char]).replace(/[\r\n]+/g, ' ');
}

export function publicationBibtex(item) {
  const type = item.type === '期刊论文' ? 'article' : item.type === '会议论文' ? 'inproceedings' : 'misc';
  const fields = [['title', item.title], ['year', item.year]];
  if (item.authors.length) fields.push(['author', item.authors.join(' and ')]);
  if (item.venue) fields.push([type === 'article' ? 'journal' : type === 'inproceedings' ? 'booktitle' : 'howpublished', item.venue]);
  if (item.link) fields.push(['url', item.link]);
  const key = String(item.slug).replace(/[^a-zA-Z0-9_-]/g, '-') || `publication-${item.year}`;
  return `@${type}{${key},\n${fields.map(([name, value]) => `  ${name} = {${escapeBibtex(value)}}`).join(',\n')}\n}\n`;
}
