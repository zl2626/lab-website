#!/usr/bin/env node
/**
 * 把 Astro 前端发布到 GitHub Pages。
 *
 * 为什么单独写这个脚本，而不是用 GitHub Actions：
 *   push 含 .github/workflows/ 的文件要求 token 具备 workflow 权限，
 *   而本仓库部署用的 token 只有 repo 权限，会被 GitHub 直接拒收。
 *   所以走「本地构建 + 推送 gh-pages 分支」这条路，仓库的
 *   Settings → Pages 也配成了 Deploy from a branch → gh-pages / (root)。
 *
 * 用法：npm run publish:pages
 */

import { execFileSync } from 'node:child_process';
import { cpSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { pushViaApi } from './push-pages-api.mjs';

// ── 换仓库名 / 用户名时改这两处 ────────────────────────────────────────────
const REPO_SLUG = 'zl2626/lab-website';
const BRANCH = 'gh-pages';
// ──────────────────────────────────────────────────────────────────────────

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const [OWNER, NAME] = REPO_SLUG.split('/');
const BASE_PATH = '/' + NAME;
const SITE_URL = 'https://' + OWNER + '.github.io';

function run(cmd, args, opts = {}) {
  return execFileSync(cmd, args, { cwd: ROOT, stdio: 'inherit', ...opts });
}

console.log('\n▶ 1/3 构建静态站（BASE_PATH=' + BASE_PATH + '）');
run('npm', ['run', 'build'], {
  shell: process.platform === 'win32',
  env: { ...process.env, BASE_PATH, SITE_URL },
});

console.log('\n▶ 2/3 自检构建产物');
run('npm', ['run', 'verify:dist'], {
  shell: process.platform === 'win32',
  // SITE_URL 让自检脚本把 abs() 生成的同源绝对地址也当成站内链接检查，
  // 否则 /api/admin/... 这类死链会绕过检测（GitHub Pages 上没有后端）。
  env: { ...process.env, BASE_PATH, SITE_URL },
});

console.log('\n▶ 3/3 推送到 ' + BRANCH + ' 分支');
const stage = mkdtempSync(join(tmpdir(), 'lab-pages-'));
try {
  cpSync(join(ROOT, 'dist'), stage, { recursive: true });
  // GitHub Pages 默认跑 Jekyll，会吃掉下划线开头的文件；这个空文件用来关掉它
  writeFileSync(join(stage, '.nojekyll'), '');

  const remote = 'https://github.com/' + REPO_SLUG + '.git';
  run('git', ['init', '-q', '-b', BRANCH], { cwd: stage });
  run('git', ['add', '-A'], { cwd: stage });
  run(
    'git',
    [
      '-c',
      'user.name=lab-website',
      '-c',
      'user.email=noreply@github.com',
      'commit',
      '-q',
      '-m',
      '发布 GitHub Pages 静态站（由 npm run publish:pages 生成）',
    ],
    { cwd: stage },
  );
  run('git', ['remote', 'add', 'origin', remote], { cwd: stage });

  // 优先走普通 git push；本机到 github.com:443 偶尔连不上，这时改用 GitHub API。
  // 两条路效果一样：都是把这一版静态站写成 gh-pages 分支的新提交。
  let pushed = false;
  try {
    run('git', ['push', '-f', 'origin', BRANCH], { cwd: stage });
    pushed = true;
  } catch {
    console.log('   ⚠ git push 失败（多为网络原因），改用 GitHub API 发布…');
  }

  if (!pushed) {
    const token = readGithubToken();
    if (!token) {
      throw new Error(
        'git push 失败，且没有读到 GitHub 凭据（git credential fill 为空），无法用 API 兜底。',
      );
    }
    const r = await pushViaApi({
      repo: REPO_SLUG,
      branch: BRANCH,
      dir: stage,
      token,
      message: '发布 GitHub Pages 静态站（由 npm run publish:pages 生成）',
    });
    console.log(
      '   已通过 API 发布 ' + r.files + ' 个文件（新上传 ' + r.uploaded + ' 个），提交 ' +
        r.commit.slice(0, 7),
    );
  }

  console.log('\n✅ 已发布：' + SITE_URL + BASE_PATH + '/');
  console.log('   GitHub 通常需要 1~2 分钟完成上线。');
} finally {
  rmSync(stage, { recursive: true, force: true });
}

/** 从 git credential helper 里取 GitHub 凭据（不打印、不落盘）。 */
function readGithubToken() {
  try {
    const out = execFileSync('git', ['credential', 'fill'], {
      input: 'protocol=https\nhost=github.com\n\n',
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    });
    const m = out.match(/^password=(.+)$/m);
    return m ? m[1].trim() : '';
  } catch {
    return '';
  }
}
