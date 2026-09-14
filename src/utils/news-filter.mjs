export function matchesNewsTag(serializedTags, tag) {
  return tag === null || JSON.parse(serializedTags).includes(tag);
}
