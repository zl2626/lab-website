# Homepage, Admin, and Dual Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a HIROL-inspired, backend-managed homepage with a dependable mobile experience, verifiable content publishing, and working GitHub Pages and Vercel deployments.

**Architecture:** Keep Django as the content source and Astro as the static renderer. Reduce the homepage to one selected hero, a lab introduction, latest news, and recruitment contact; keep the content contract in the existing `/api/content/` bundle and make deployment state explicit in Django Admin.

**Tech Stack:** Astro 7, TypeScript, plain CSS, Node test runner, Django, PostgreSQL/SQLite tests, Vercel, GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-09-16-homepage-admin-deployment-design.md`

## Global Constraints

- Desktop navigation order is 首页、团队成员、科研平台、科研成果、加入我们.
- Mobile navigation must not wrap or cause horizontal page overflow and must expose 44px minimum touch targets.
- Homepage content must come from Django Admin fields already represented by `/api/content/`; GitHub Pages remains a Markdown-backed static mirror.
- No new web-font dependency; use the existing system font stack.
- Preserve existing public URLs for member, platform, publication, news, and recruitment pages.
- A configured `API_BASE` failure must stop a production build instead of silently publishing fallback content.
- The Vercel build and the `BASE_PATH=/lab-website` Pages build must both pass the distribution verifier.

## File Map

- `api/core/serializers.py`: canonical default navigation contract returned by Django.
- `src/lib/content.ts`: matching fallback navigation contract for Markdown builds.
- `src/data/site.json`: repository fallback content used by GitHub Pages.
- `src/utils/home.mjs`: small, testable homepage-selection helpers.
- `src/pages/index.astro`: homepage structure and page-specific responsive styling.
- `src/components/Header.astro`: desktop single-row navigation and accessible mobile menu.
- `src/styles/global.css`: shared blue visual tokens and header primitives.
- `api/core/admin.py`: homepage field guidance and post-commit rebuild UX.
- `api/core/tests.py`: backend content, upload, navigation, and rebuild regression coverage.
- `tests/home.test.mjs`: homepage-selection unit tests.
- `tests/check-dist.mjs`: rendered homepage, SEO, and image-loading assertions.
- `README.md`: editor workflow and deployment behavior.

---

### Task 1: Lock the navigation and homepage data contract

**Files:**
- Modify: `api/core/tests.py`
- Modify: `api/core/serializers.py`
- Modify: `src/lib/content.ts`
- Modify: `src/data/site.json`

**Interfaces:**
- Produces: `DEFAULT_NAV` with exactly five ordered items in both backend and frontend fallback loaders.
- Produces: `serialize_site(SiteSetting) -> dict` that still preserves a genuinely customized navigation list.
- Consumes: existing `SiteSetting.nav` JSON list and legacy-default rescue behavior.

- [ ] **Step 1: Write failing backend navigation tests**

Add assertions that an empty navigation serializes to:

```python
[
    {"label": "首页", "href": "/"},
    {"label": "团队成员", "href": "/team"},
    {"label": "科研平台", "href": "/platform"},
    {"label": "科研成果", "href": "/publications"},
    {"label": "加入我们", "href": "/join"},
]
```

Keep the existing custom-navigation test and assert its exact list is not expanded or reordered.

- [ ] **Step 2: Run the targeted backend tests and confirm the old nine-item default fails**

Run:

```powershell
.venv/Scripts/python.exe api/manage.py test core.tests.ContentApiTests --settings=labbackend.test_settings
```

Expected: the new default-navigation assertion fails because the current default has nine items.

- [ ] **Step 3: Implement the canonical five-item default**

Replace the backend and frontend `DEFAULT_NAV` constants with the five-item list above. Extend `LEGACY_DEFAULT_NAV_HREFS` to recognize the current nine-item default so an untouched existing database upgrades once, while custom lists remain unchanged. Update `src/data/site.json` only if it contains the old explicit default.

- [ ] **Step 4: Run the targeted backend tests**

Run the command from Step 2.

Expected: all `ContentApiTests` pass.

- [ ] **Step 5: Commit the navigation contract**

```powershell
git add api/core/tests.py api/core/serializers.py src/lib/content.ts src/data/site.json
git commit -m "feat: simplify the primary site navigation"
```

---

### Task 2: Select one backend-managed hero and latest news deterministically

**Files:**
- Create: `src/utils/home.mjs`
- Create: `tests/home.test.mjs`
- Modify: `src/pages/index.astro`

**Interfaces:**
- Produces: `selectHomeHero(homeSlides, fallback): object`, returning the first published/serialized slide or the supplied fallback.
- Produces: `clampHomeCount(value, fallback): number`, constrained to 1–12.
- Consumes: `HomeSlideItem[]`, `site.groupPhoto`, `site.name`, `site.nameEn`, `site.tagline`, and `NewsItem[]` already ordered by the content loader.

- [ ] **Step 1: Write failing unit tests**

Create `tests/home.test.mjs` with coverage equivalent to:

```js
import assert from 'node:assert/strict';
import test from 'node:test';
import { clampHomeCount, selectHomeHero } from '../src/utils/home.mjs';

test('selectHomeHero uses the first configured slide', () => {
  const fallback = { title: 'Fallback' };
  assert.equal(selectHomeHero([{ title: 'First' }, { title: 'Second' }], fallback).title, 'First');
});

test('selectHomeHero falls back when no slide is configured', () => {
  const fallback = { title: 'Fallback' };
  assert.equal(selectHomeHero([], fallback), fallback);
});

test('clampHomeCount accepts valid values and clamps extremes', () => {
  assert.equal(clampHomeCount('6', 4), 6);
  assert.equal(clampHomeCount('0', 4), 1);
  assert.equal(clampHomeCount('100', 4), 12);
  assert.equal(clampHomeCount('bad', 4), 4);
});
```

- [ ] **Step 2: Run the unit test and confirm the missing module fails**

Run: `node --test tests/home.test.mjs`

Expected: failure because `src/utils/home.mjs` does not exist.

- [ ] **Step 3: Implement the helper module**

Implement only the two exported pure functions. Keep content sorting in the existing loader/serializer and do not duplicate it in the homepage.

- [ ] **Step 4: Replace homepage carousel selection**

In `src/pages/index.astro`, create one fallback hero from site settings, call `selectHomeHero(homeSlides, fallbackHero)`, and delete the carousel state, controls, interval, and multi-slide markup. Keep the first hero image eager/high-priority and use the news count helper for the latest-news list.

- [ ] **Step 5: Run all Node unit tests**

Run: `npm test`

Expected: all Node tests pass, including the new homepage tests.

- [ ] **Step 6: Commit the homepage data selection**

```powershell
git add src/utils/home.mjs tests/home.test.mjs src/pages/index.astro
git commit -m "refactor: use one deterministic homepage hero"
```

---

### Task 3: Build the HIROL-inspired homepage and responsive header

**Files:**
- Modify: `src/pages/index.astro`
- Modify: `src/components/Header.astro`
- Modify: `src/styles/global.css`
- Modify: `tests/check-dist.mjs`

**Interfaces:**
- Consumes: the hero selected in Task 2, `site.description`, `site.groupPhoto`, `news`, and `site.openings`.
- Produces: one `h1`, one eager hero image, lazy below-fold images, `.mobile-nav-toggle`, and a menu panel whose expanded state is represented by `aria-expanded`.

- [ ] **Step 1: Add failing rendered-output checks**

Extend `tests/check-dist.mjs` for `dist/index.html` to assert:

```js
const home = fs.readFileSync(path.join(DIST, 'index.html'), 'utf8');
if (!home.includes('class="home-hero"')) issues.push('index.html: 缺少单图首页首屏');
if (!home.includes('class="home-latest"')) issues.push('index.html: 缺少实验室最新动态');
if (home.includes('home-carousel') || home.includes('banner-dots')) issues.push('index.html: 仍包含旧轮播');
if (!/class="hero-image"[^>]+fetchpriority="high"/.test(home)) issues.push('index.html: 首屏图片未设置高优先级');
```

Build and run `npm run verify:dist`.

Expected: verifier fails because the new structural classes are absent and the old carousel is present.

- [ ] **Step 2: Implement the new homepage structure**

Replace the page body with:

1. `.home-hero` using the selected backend hero.
2. `.home-intro` with lab description, group photo, and three live content counts.
3. `.home-latest` using the newest published news cards.
4. `.home-contact` using recruitment and contact fields.

Use semantic headings, meaningful image alt text for content images, empty alt only for purely decorative images, and links through `u()`/`asset()` for Pages compatibility.

- [ ] **Step 3: Implement the desktop and mobile header**

Keep the five desktop links in one row at wide breakpoints. Add a real button for mobile, a panel containing the same links, Escape-to-close behavior, outside-click closing, current-page indication, focus-visible styles, and body-scroll safety. Ensure search and theme controls remain reachable.

- [ ] **Step 4: Apply the revised token system and page styling**

Update shared colors to the approved blue/white palette while preserving dark-mode variables. In homepage CSS, use one visual emphasis—the hero photograph—then quiet section dividers, restrained shadows, consistent image ratios, and no decorative numbering. Add breakpoints for 1024px, 768px, 390px, and 320px.

- [ ] **Step 5: Build and run the rendered verifier**

Run:

```powershell
npm run build
npm run verify:dist
```

Expected: build exits 0; verifier reports zero broken links and zero basic-standard issues.

- [ ] **Step 6: Commit the visual implementation**

```powershell
git add src/pages/index.astro src/components/Header.astro src/styles/global.css tests/check-dist.mjs
git commit -m "feat: redesign the lab homepage and mobile navigation"
```

---

### Task 4: Make homepage editing and rebuild behavior explicit in Django Admin

**Files:**
- Modify: `api/core/admin.py`
- Modify: `api/core/tests.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: existing `ImageOrUrlField`, `schedule_rebuild(request, modeladmin)`, `transaction.on_commit`, and `trigger_deploy()`.
- Produces: admin guidance stating that the first published HomeSlide is the homepage hero and that saved published content appears after a successful rebuild.

- [ ] **Step 1: Add failing admin tests**

Add tests that verify:

```python
self.assertIn("首页只展示排序最前", HomeSlideAdmin.fieldsets[0][1]["description"])
```

Also preserve and run existing tests that prove uploaded images are stored and served, one request schedules only one rebuild, disabled auto-rebuild performs no deploy request, and the callback runs after transaction commit.

- [ ] **Step 2: Run the targeted admin tests and confirm the guidance assertion fails**

Run:

```powershell
.venv/Scripts/python.exe api/manage.py test core.tests.AdminCoverageTests core.tests.AdminWorkflowTests --settings=labbackend.test_settings
```

Expected: the new hero-guidance assertion fails against the current text.

- [ ] **Step 3: Improve admin guidance without changing the storage model**

Update the HomeSlide list/field descriptions to explain that only the first published item is used on the redesigned homepage, recommend a 16:9 image around 1920×1080, and explain safe center cropping. Keep direct upload and URL paste behavior unchanged. Update the dashboard/editor documentation to distinguish “saved in database”, “rebuild accepted”, and “deployment ready”.

- [ ] **Step 4: Run the complete Django test suite**

Run:

```powershell
.venv/Scripts/python.exe api/manage.py test core --settings=labbackend.test_settings
```

Expected: all backend tests pass with no external deploy or database calls.

- [ ] **Step 5: Commit the admin reliability work**

```powershell
git add api/core/admin.py api/core/tests.py README.md
git commit -m "docs: clarify homepage publishing in the admin"
```

---

### Task 5: Verify performance, SEO, GitHub Pages, and Vercel release

**Files:**
- Modify: `tests/check-dist.mjs`
- Modify: `README.md`
- Inspect: `astro.config.mjs`
- Inspect: `vercel.json`
- Inspect: `scripts/publish-pages.mjs`

**Interfaces:**
- Consumes: production build output in `dist/`, the `publish:pages` script, the `origin/main` repository, and the linked Vercel project.
- Produces: a pushed `main`, a published `gh-pages` branch, and a verified Vercel production deployment URL/status.

- [ ] **Step 1: Strengthen performance and SEO assertions**

Add distribution checks that the homepage has one `h1`, non-empty description/canonical/Open Graph image metadata, no legacy autoplay interval, one high-priority hero image at most, and lazy loading on below-fold news/team imagery. Keep the existing all-page link, alt-text, and trailing-content checks.

- [ ] **Step 2: Run the full local verification matrix**

Run:

```powershell
npm test
npm run build
npm run verify:dist
.venv/Scripts/python.exe api/manage.py test core --settings=labbackend.test_settings
$env:BASE_PATH='/lab-website'; $env:SITE_URL='https://zl2626.github.io'; npm run build; npm run verify:dist; Remove-Item Env:BASE_PATH; Remove-Item Env:SITE_URL
git diff --check
git status --short
```

Expected: every command exits 0; the verifier reports zero broken links and zero basic-standard issues in both root and subpath builds.

- [ ] **Step 3: Perform visual checks at desktop and mobile widths**

Serve `dist/` locally and capture/inspect the homepage at 1440px and 390px. Verify the hero crop, single-row desktop navigation, mobile menu, no horizontal overflow, readable overlays, keyboard focus, and reduced-motion behavior. Correct any observed regression and rerun Step 2.

- [ ] **Step 4: Push the verified main branch**

```powershell
git push origin main
```

Expected: GitHub accepts the new commits and `origin/main` matches `main`.

- [ ] **Step 5: Publish GitHub Pages**

Run: `npm run publish:pages`

Expected: the script builds with `/lab-website`, passes its verifier, pushes `gh-pages`, and prints `https://zl2626.github.io/lab-website/`.

- [ ] **Step 6: Deploy and watch Vercel**

Use the connected Vercel deployment tools to locate the project linked to `zl2626/lab-website`. The push to the default branch should trigger the production build; watch it until it reaches `ready`, `failed`, or `canceled`. If no linked project exists, create/link it only after confirming the Vercel team scope. Never expose environment values or tokens.

- [ ] **Step 7: Verify live endpoints**

Check the final production homepage, `/api/health/`, `/api/content/`, and `/api/admin/` on Vercel, plus the GitHub Pages homepage. Record the exact URLs and terminal deployment status in the handoff; if a protected Vercel URL returns 401/403, report protection rather than a broken deployment.

- [ ] **Step 8: Commit final verification/documentation adjustments if any**

```powershell
git add tests/check-dist.mjs README.md
git commit -m "test: verify homepage deployment output"
git push origin main
```

Skip this commit when Step 1 was already included in Task 3 and no final file changed.
