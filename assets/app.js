const page = document.body.dataset.page || "home";

/* 站点设置（含外观）：读取「已发布」副本，后台改完发布后前台即生效 */
const SITE = window.SiteStore ? SiteStore.frontend() : { settings: {} };
const S = SITE.settings || {};
const AP = S.appearance || {};
function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

const nav = [
  ["home", "首页", "index.html"],
  ["team", "团队介绍", "team.html"],
  ["research", "科研成果", "research.html"],
  ["news", "新闻动态", "news.html"],
  ["contact", "联系我们", "contact.html"],
];

const researchPages = new Set(["research", "publications", "patents", "projects"]);
const navHtml = nav.map(([key, label, href]) => {
  const active = key === "research" ? researchPages.has(page) : key === page || (key === "team" && page === "member");
  if (key !== "research") {
    return `<div class="nav-item ${active ? "active" : ""}"><a class="nav-link" href="${href}" ${active ? 'aria-current="page"' : ""}>${label}</a></div>`;
  }
  return `<div class="nav-item research-nav ${active ? "active" : ""}">
    <a class="nav-link" href="research.html" ${page === "research" ? 'aria-current="page"' : ""}>科研成果</a>
    <button class="nav-button submenu-toggle" type="button" aria-expanded="false" aria-label="展开科研成果子菜单"><span class="nav-caret">▼</span></button>
    <div class="submenu">
      <a href="publications.html">论文</a>
      <a href="patents.html">专利</a>
      <a href="projects.html">项目</a>
    </div>
  </div>`;
}).join("");

document.querySelector("#site-header").innerHTML = `
  <div class="scroll-progress" aria-hidden="true"><i></i></div>
  <header>
    <div class="brand-bar"><div class="brand-inner">
      <a class="brand" href="index.html" aria-label="${esc(S.name || "课题组")}首页">
        <span class="brand-mark" id="brand-mark-lab">课题组<br>LOGO</span>
        <span><span class="brand-name">${esc(S.name || "某某课题组")}</span><span class="brand-en">${esc(S.nameEn || "EMBODIED INTELLIGENCE LAB")}</span></span>
      </a>
      <div class="brand university">
        ${AP.logoUni
          ? `<span class="brand-mark uni-lockup" id="brand-mark-uni">校名标识</span>`
          : `<span class="brand-mark" id="brand-mark-uni">安农大<br>LOGO</span><span><span class="brand-name">${esc(S.university || "安徽农业大学")}</span><span class="brand-en">${esc(S.universityEn || "ANHUI AGRICULTURAL UNIVERSITY")}</span></span>`}
      </div>
    </div></div>
    <nav class="site-nav" aria-label="主导航">
      <button class="mobile-toggle" type="button" aria-expanded="false">菜单</button>
      <div class="nav-inner">${navHtml}</div>
    </nav>
  </header>`;

document.querySelector("#site-footer").innerHTML = `
  <footer class="site-footer"><div class="footer-inner">
    <span>${esc(S.name || "某某课题组")} · ${esc(S.university || "安徽农业大学")}</span>
    <span>${esc(AP.footerNote != null ? AP.footerNote : "此页面为结构框架，正式名称与素材待替换")}</span>
  </div></footer>`;

/* ════════ 应用外观：主题色 / 字体 / Logo（后台「网站外观」发布后生效） ════════ */
(function applyAppearance() {
  const root = document.documentElement;
  const stacks = {
    serif: '"Noto Serif SC", "Songti SC", SimSun, serif',
    sans: '"Noto Sans SC", "Microsoft YaHei", system-ui, sans-serif'
  };
  try {
    if (AP.colorPrimary) {
      root.style.setProperty("--navy", AP.colorPrimary);
      root.style.setProperty("--navy-deep", `color-mix(in srgb, ${AP.colorPrimary}, #000 22%)`);
    }
    if (AP.colorAccent) root.style.setProperty("--wine", AP.colorAccent);
    if (AP.fontHeading === "sans") root.style.setProperty("--serif", stacks.sans);
    else root.style.removeProperty("--serif");
    if (AP.fontBody === "serif") root.style.setProperty("--sans", stacks.serif);
    else root.style.removeProperty("--sans");
  } catch (e) { /* 外观字段异常时不阻塞页面 */ }
  function setMark(id, dataUrl) {
    const el = document.getElementById(id);
    if (!el || !dataUrl) return;
    el.classList.add("has-img");
    el.style.backgroundImage = `url("${dataUrl}")`;
    el.style.backgroundSize = "contain";
    el.style.backgroundPosition = "center";
    el.style.backgroundRepeat = "no-repeat";
  }
  setMark("brand-mark-lab", AP.logoLab);
  setMark("brand-mark-uni", AP.logoUni);
  if (S.name) document.title = document.title.replace("某某课题组", S.name);
})();

const siteNav = document.querySelector(".site-nav");
const mobileToggle = document.querySelector(".mobile-toggle");
const researchNav = document.querySelector(".research-nav");
const submenuToggle = document.querySelector(".submenu-toggle");

mobileToggle.addEventListener("click", () => {
  const open = siteNav.classList.toggle("menu-open");
  mobileToggle.setAttribute("aria-expanded", String(open));
  mobileToggle.textContent = open ? "收起菜单" : "菜单";
});

submenuToggle.addEventListener("click", () => {
  const open = researchNav.classList.toggle("open");
  submenuToggle.setAttribute("aria-expanded", String(open));
});

document.addEventListener("click", (event) => {
  if (!researchNav.contains(event.target)) {
    researchNav.classList.remove("open");
    submenuToggle.setAttribute("aria-expanded", "false");
  }
});

/* ════════ 滚动进度条 + 导航吸顶阴影 ════════ */
const progressBar = document.querySelector(".scroll-progress i");
function onScrollChrome() {
  const max = document.documentElement.scrollHeight - window.innerHeight;
  const ratio = max > 0 ? Math.min(1, window.scrollY / max) : 0;
  if (progressBar) progressBar.style.width = (ratio * 100).toFixed(2) + "%";
  siteNav.classList.toggle("scrolled", window.scrollY > 8);
}
window.addEventListener("scroll", onScrollChrome, { passive: true });
onScrollChrome();

/* ════════ 滚动渐入（尊重 prefers-reduced-motion） ════════ */
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const revealEls = [...document.querySelectorAll("[data-reveal]")];
if (reduceMotion || !("IntersectionObserver" in window)) {
  revealEls.forEach((el) => el.classList.add("revealed"));
} else {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("revealed");
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -60px 0px" });
  revealEls.forEach((el) => io.observe(el));
}

/* 统计节与全屏分节滚动已按需求移除：首页为自然滚动，无滚轮翻页、无下一屏箭头、无数字滚动 */
