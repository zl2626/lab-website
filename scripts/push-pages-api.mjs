/**
 * 用 GitHub Git Data API 把 dist/ 发布到 gh-pages 分支（git push 的兜底方案）。
 * 适用场景：本机到 github.com:443 的连接不稳定，git push 反复超时，
 *           但 api.github.com 可达。效果与 git push -f origin gh-pages 等价。
 */

import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

const API = 'https://api.github.com';

function blobSha(buf) {
  const h = crypto.createHash('sha1');
  h.update('blob ' + buf.length + '\0');
  h.update(buf);
  return h.digest('hex');
}

export async function pushViaApi({ repo, branch, dir, token, message }) {
  const H = {
    Authorization: 'token ' + token,
    Accept: 'application/vnd.github+json',
    'User-Agent': 'lab-website-publish',
    'Content-Type': 'application/json',
  };

  const api = async (p, opts = {}) => {
    const r = await fetch(API + p, { headers: H, ...opts });
    const txt = await r.text();
    let body;
    try { body = JSON.parse(txt); } catch { body = txt; }
    if (!r.ok) throw new Error(p + ' -> ' + r.status + ' ' + JSON.stringify(body).slice(0, 300));
    return body;
  };

  // 收集待发布文件（.git 是本地临时仓库，不能进 tree）
  const files = [];
  (function walk(d, prefix) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      if (e.name === '.git') continue;
      const rel = prefix ? prefix + '/' + e.name : e.name;
      if (e.isDirectory()) walk(path.join(d, e.name), rel);
      else files.push(rel);
    }
  })(dir, '');
  files.sort();

  // 读远端现有 tree，只上传内容有变化的文件（省时间也省 API 配额）
  let parent = null;
  const remote = {};
  try {
    const ref = await api('/repos/' + repo + '/git/ref/heads/' + branch);
    parent = ref.object.sha;
    const c = await api('/repos/' + repo + '/git/commits/' + parent);
    const t = await api('/repos/' + repo + '/git/trees/' + c.tree.sha + '?recursive=1');
    for (const it of t.tree) if (it.type === 'blob') remote[it.path] = it.sha;
  } catch {
    // 首次发布时分支还不存在，属于正常情况
  }

  const tree = [];
  let uploaded = 0;
  for (const rel of files) {
    const buf = fs.readFileSync(path.join(dir, rel));
    const sha = blobSha(buf);
    if (remote[rel] === sha) {
      tree.push({ path: rel, mode: '100644', type: 'blob', sha });
      continue;
    }
    const blob = await api('/repos/' + repo + '/git/blobs', {
      method: 'POST',
      body: JSON.stringify({ content: buf.toString('base64'), encoding: 'base64' }),
    });
    tree.push({ path: rel, mode: '100644', type: 'blob', sha: blob.sha });
    uploaded++;
  }

  const treeRes = await api('/repos/' + repo + '/git/trees', {
    method: 'POST',
    body: JSON.stringify({ tree }),
  });
  const commit = await api('/repos/' + repo + '/git/commits', {
    method: 'POST',
    body: JSON.stringify({
      message,
      tree: treeRes.sha,
      parents: parent ? [parent] : [],
      author: { name: 'lab-website', email: 'noreply@github.com' },
      committer: { name: 'lab-website', email: 'noreply@github.com' },
    }),
  });

  try {
    await api('/repos/' + repo + '/git/refs/heads/' + branch, {
      method: 'PATCH',
      body: JSON.stringify({ sha: commit.sha, force: true }),
    });
  } catch {
    await api('/repos/' + repo + '/git/refs', {
      method: 'POST',
      body: JSON.stringify({ ref: 'refs/heads/' + branch, sha: commit.sha }),
    });
  }

  return { commit: commit.sha, files: files.length, uploaded, unchanged: parent !== null };
}
