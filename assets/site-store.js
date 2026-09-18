/* 站点数据存储 + 前台内容渲染（原型专用）。
   原理：后台 admin.html 把「草稿」存到 localStorage；点「发布更新」后
   草稿副本变成「已发布副本」。前台每个页面加载时读取已发布副本渲染内容，
   因此后台发布后，前台刷新即可看到修改（正式实现时由数据库 + 构建取代）。 */
(function () {
  "use strict";

  var KEY_DRAFT = "labSiteDraft.v2";
  var KEY_PUBLISHED = "labSitePublished.v2";

  function read(key) {
    try {
      var raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  }
  function clone(v) { return JSON.parse(JSON.stringify(v)); }

  window.SiteStore = {
    KEY_DRAFT: KEY_DRAFT,
    KEY_PUBLISHED: KEY_PUBLISHED,
    seed: function () { return clone(window.SITE_DATA); },
    draft: function () { return read(KEY_DRAFT); },
    published: function () { return read(KEY_PUBLISHED); },
    /* 后台工作台入口：草稿优先，其次已发布，最后种子 */
    open: function () {
      var base = this.seed();
      var pub = this.published() || {};
      var draft = this.draft() || {};
      Object.keys(pub).forEach(function (k) { base[k] = pub[k]; });
      Object.keys(draft).forEach(function (k) { base[k] = draft[k]; });
      return base;
    },
    saveDraft: function (state) {
      try { localStorage.setItem(KEY_DRAFT, JSON.stringify(state)); } catch (e) {}
    },
    publish: function (state) {
      this.saveDraft(state);
      try { localStorage.setItem(KEY_PUBLISHED, JSON.stringify(state)); } catch (e) {}
    },
    reset: function () {
      try { localStorage.removeItem(KEY_DRAFT); localStorage.removeItem(KEY_PUBLISHED); } catch (e) {}
    },
    /* 前台页面读取：云端发布副本 > 本机已发布副本 > 种子 */
    frontend: function () {
      var base = this.seed();
      var pub = this.published() || {};
      Object.keys(pub).forEach(function (k) { base[k] = pub[k]; });
      if (remoteData) Object.keys(remoteData).forEach(function (k) { base[k] = remoteData[k]; });
      return base;
    }
  };

  /* ═══════════ 前台渲染 ═══════════ */
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function q(id) { return new URLSearchParams(location.search).get(id); }
  /* 作者归一化精确匹配（继承旧项目规则：不做模糊匹配） */
  function norm(s) { return String(s || "").replace(/\s+/g, " ").trim().toLowerCase(); }
  function memberPubs(d, m) {
    var keys = [norm(m.name), norm(m.nameEn)].filter(Boolean);
    return (d.pubs || []).filter(function (p) {
      if (!p.published) return false;
      var authors = p.authors.split(/[,;，；]/).map(norm);
      return keys.some(function (k) { return authors.indexOf(k) >= 0; });
    });
  }

  function photoDiv(cls, url, fallback) {
    if (url) return '<div class="' + cls + '" style="background-image:url(\'' + url + '\');background-size:cover;background-position:center"></div>';
    return '<div class="' + cls + '">' + fallback + "</div>";
  }
  function newsRow(n) {
    var parts = (n.date || "").split("-");
    var show = parts.length === 3 ? parts[0] + " <strong>" + parts[1] + "." + parts[2] + "</strong>" : esc(n.date);
    return '<a class="news-row" href="news-detail.html?id=' + n.id + '">' +
      '<time class="news-date">' + show + "</time>" +
      '<div class="news-copy"><h3>' + esc(n.title) + (n.pinned ? ' <span class="pin-badge">置顶</span>' : "") + "</h3><p>" + esc(n.summary) + "</p></div>" +
      photoDiv("thumb", n.cover, "新闻缩略图") + "</a>";
  }

  /* 最新成果卡：featured 论文优先，不足补专利/项目 */
  function featuredItems(d, n) {
    var feats = (d.pubs || []).filter(function (p) { return p.published && p.featured; })
      .slice().sort(function (a, b) { return b.year - a.year; })
      .map(function (p) { return { title: p.title, venueShort: p.venueShort, year: p.year, type: p.type, href: "publications.html" }; });
    (d.patents || []).filter(function (p) { return p.published; }).forEach(function (pt) {
      if (feats.length < n) feats.push({ title: pt.name, venueShort: pt.kind, year: pt.year, type: pt.status, href: "patents.html" });
    });
    (d.projects || []).filter(function (p) { return p.published && p.status === "在研"; }).forEach(function (pj) {
      if (feats.length < n) feats.push({ title: pj.name, venueShort: pj.category, year: pj.startYear, type: pj.status, href: "projects.html" });
    });
    return feats.slice(0, n);
  }
  function resultCards(feats) {
    return feats.map(function (p) {
      return '<a class="result-card" href="' + p.href + '"><div class="card-copy"><h3>' + esc(p.title) + '</h3><div class="meta">' + esc(p.venueShort) + " · " + esc(p.year) + " · " + esc(p.type) + "</div></div></a>";
    }).join("");
  }

  function renderHome(d) {
    function set(id, html) { var el = document.getElementById(id); if (el) el.innerHTML = html; }
    set("hero-title", esc(d.home.welcome));
    set("hero-sub", esc(d.settings.nameEn));
    set("hero-research", "<strong>主要研究：</strong>" + esc(d.home.researchLine));
    /* 简介与方向编号列表（条目 = 标题 + 说明，后台自由编辑） */
    set("about-copy-text", "<p>" + esc(d.home.about) + "</p>");
    set("about-directions", (d.home.aboutDirections || []).map(function (item, i) {
      var t = typeof item === "string" ? item : (item && item.t) || "";
      var desc = typeof item === "string" ? "" : (item && item.d) || "";
      return '<div class="direction-line"><span class="num">' + String(i + 1).padStart(2, "0") + "</span><span><b>" + esc(t) + "</b>" + (desc ? " — " + esc(desc) : "") + "</span></div>";
    }).join(""));
    /* Hero 背景（后台「首页设置」可更换；深色遮罩保证文字可读） */
    var heroEl = document.getElementById("hero");
    if (heroEl && d.home.heroBg) heroEl.style.backgroundImage = "linear-gradient(rgba(11,19,27,.68), rgba(11,19,27,.78)), url('" + d.home.heroBg + "')";
    /* 科研平台三图 */
    set("platform-grid", (d.home.platform || []).map(function (u, i) {
      return photoDiv("visual platform-shot", u, "实验室图片 " + (i + 1) + "<br>4:3");
    }).join(""));
    /* 首页团队合照 */
    var tp = document.querySelector(".about-photo");
    if (tp && d.home.photo) { tp.style.backgroundImage = "url('" + d.home.photo + "')"; tp.style.backgroundSize = "cover"; tp.style.backgroundPosition = "center"; tp.textContent = ""; }
    /* 导师卡：后台可选导师，默认第一位上架导师 */
    var mentors = (d.members || []).filter(function (m) { return m.role === "mentor" && m.published; });
    var mentor = mentors.filter(function (m) { return d.home.mentorId && m.id === Number(d.home.mentorId); })[0] || mentors[0];
    set("about-mentor", mentor ?
      '<a class="profile-card" href="member.html?id=' + mentor.id + '">' + photoDiv("visual portrait", mentor.photo, "导师照片 4:5") + '<div class="profile-card-copy"><b>' + esc(mentor.name) + "</b><span>" + esc(mentor.title || "导师") + '</span><span class="meta">' + esc(mentor.email || "") + "</span></div></a>" : "");
    /* 最新新闻 3 条 */
    var news = (d.news || []).filter(function (n) { return n.published; })
      .slice().sort(function (a, b) { return (b.pinned - a.pinned) || (a.date < b.date ? 1 : -1); }).slice(0, 3);
    set("home-news", news.map(newsRow).join(""));
    /* 最新成果：featured 优先，不足补专利/项目 */
    set("home-results", resultCards(featuredItems(d, 3)));
  }

  function renderTeam(d) {
    var mentorBox = document.getElementById("mentor-box");
    var mentor = (d.members || []).filter(function (m) { return m.role === "mentor" && m.published; })[0];
    if (mentorBox && mentor) {
      mentorBox.innerHTML = '<a class="mentor-card" href="member.html?id=' + mentor.id + '">' + photoDiv("visual portrait", mentor.photo, "导师照片") + '<div><h2>' + esc(mentor.name) + '</h2><dl class="details"><dt>职称</dt><dd>' + esc(mentor.title || "") + '</dd><dt>电子邮箱</dt><dd>' + esc(mentor.email) + "</dd></dl></div></a>";
    }
    var grid = document.getElementById("masters-grid");
    if (grid) {
      var masters = (d.members || []).filter(function (m) { return m.role === "master" && m.published; });
      grid.innerHTML = masters.map(function (m) {
        return '<a class="member-tile" href="member.html?id=' + m.id + '" aria-label="查看 ' + esc(m.name) + ' 详情">' + photoDiv("visual portrait", m.photo, "成员照片") + '<span class="member-name">' + esc(m.name) + "</span></a>";
      }).join("");
    }
  }

  function renderMember(d) {
    var wrap = document.getElementById("member-page");
    if (!wrap) return;
    var id = Number(q("id"));
    var m = (d.members || []).filter(function (x) { return x.published && x.id === id; })[0] ||
            (d.members || []).filter(function (x) { return x.published && x.role === "mentor"; })[0];
    if (!m) { wrap.innerHTML = '<p class="meta">没有找到该成员。</p>'; return; }
    var roleLabel = m.role === "mentor" ? (m.title || "导师") : "硕士研究生";
    document.title = m.name + "｜" + d.settings.name;
    wrap.innerHTML =
      '<section class="profile-top">' + photoDiv("visual portrait", m.photo, "个人照片<br>4:5") + '<div><h1>' + esc(m.name) + '</h1><p class="meta">' + esc(m.joinYear) + " 年加入 · " + roleLabel + '</p><dl class="details"><dt>电子邮箱</dt><dd>' + esc(m.email || "—") + '</dd><dt>加入年份</dt><dd>' + esc(m.joinYear) + "</dd></dl></div></section>" +
      '<section class="section profile-section"><div class="section-head"><h2>个人简介</h2></div>' + ((m.bio || "").split(/\n+/).filter(Boolean).map(function (s) { return "<p>" + esc(s) + "</p>"; }).join("") || "<p>暂无简介。</p>") + "</section>" +
      '<section class="section profile-section"><div class="section-head accent"><h2>相关成果</h2></div><ul class="compact-list">' +
      (memberPubs(d, m).map(function (p) { return "<li>" + esc(p.title) + ' <span class="meta">' + esc(p.venueShort) + " " + esc(p.year) + "</span></li>"; }).join("") || "<li>暂无关联成果。</li>") +
      "</ul></section>";
  }

  function renderResearch(d) {
    var featsBox = document.getElementById("home-results");
    if (featsBox) featsBox.innerHTML = resultCards(featuredItems(d, 3));
    var pubs = (d.pubs || []).filter(function (p) { return p.published; })
      .slice().sort(function (a, b) { return b.year - a.year; }).slice(0, 3);
    var recentPubs = document.getElementById("recent-pubs");
    if (recentPubs) recentPubs.innerHTML = pubs.map(function (p) {
      return "<li><strong>" + esc(p.year) + "</strong>　" + esc(p.title) + ' <span class="meta">' + esc(p.venueShort) + "</span></li>";
    }).join("");
    var ongoing = (d.projects || []).filter(function (p) { return p.published && p.status === "在研"; });
    var ongoingBox = document.getElementById("ongoing-projects");
    if (ongoingBox) ongoingBox.innerHTML = ongoing.map(function (p) {
      return "<li><strong>" + esc(p.name) + '</strong><br><span class="meta">' + esc(p.sponsor) + " · " + esc(p.startYear) + "–" + esc(p.endYear) + "</span></li>";
    }).join("");
  }

  function pubItem(p) {
    return '<article class="archive-item"><span class="tag">' + esc(p.type) + '</span><h3>' + esc(p.title) + (p.featured ? ' <span class="tag wine">最新成果</span>' : "") + "</h3><p>" + esc(p.authors) + ". " + esc(p.venueShort || p.venue) + ", " + esc(p.year) + (p.link ? ". " + esc(p.link) : "") + "</p></article>";
  }
  function byYearDesc(a, b) { return b - a; }
  function yearBlocks(list, fmt) {
    var years = list.map(fmt.year).filter(function (v, i, arr) { return arr.indexOf(v) === i; }).sort(byYearDesc);
    return years.map(function (y) {
      return '<h2 class="year">' + y + "</h2>" + list.filter(function (x) { return fmt.year(x) === y; }).map(fmt.item).join("");
    }).join("");
  }
  function renderPublications(d) {
    var box = document.getElementById("pub-archive");
    if (!box) return;
    var pubs = (d.pubs || []).filter(function (p) { return p.published; });
    box.innerHTML = yearBlocks(pubs, { year: function (p) { return p.year; }, item: pubItem });
  }
  function renderPatents(d) {
    var box = document.getElementById("patent-archive");
    if (!box) return;
    var list = (d.patents || []).filter(function (p) { return p.published; });
    box.innerHTML = list.length ? yearBlocks(list, {
      year: function (p) { return p.year; },
      item: function (p) {
        return '<article class="archive-item"><span class="tag">' + esc(p.kind) + '</span><span class="tag ' + (p.status === "已授权" ? "" : "dim") + '">' + esc(p.status) + '</span><h3>' + esc(p.name) + "</h3><p>" + esc(p.inventors) + " · " + esc(p.no || "") + "</p></article>";
      }
    }) : '<div class="empty-state">还没有录入专利。</div>';
  }
  function renderProjects(d) {
    var box = document.getElementById("project-archive");
    if (!box) return;
    var list = (d.projects || []).filter(function (p) { return p.published; });
    box.innerHTML = list.length ? list.map(function (p) {
      return '<article class="archive-item"><span class="tag">' + esc(p.category) + '</span><h2>' + esc(p.name) + "</h2><p>项目来源：" + esc(p.sponsor) + " · 负责人：" + esc(p.leader) + " · " + esc(p.startYear) + "–" + esc(p.endYear) + " · " + esc(p.status) + "</p><p>" + esc(p.summary) + "</p></article>";
    }).join("") : '<div class="empty-state">还没有录入项目。</div>';
  }
  function renderNewsList(d) {
    var box = document.getElementById("news-list");
    if (!box) return;
    var list = (d.news || []).filter(function (n) { return n.published; })
      .slice().sort(function (a, b) { return (b.pinned - a.pinned) || (a.date < b.date ? 1 : -1); });
    box.innerHTML = list.length ? list.map(newsRow).join("") : '<div class="empty-state">还没有发布新闻。</div>';
  }
  function renderNewsDetail(d) {
    var box = document.getElementById("news-article");
    if (!box) return;
    var id = Number(q("id"));
    var n = (d.news || []).filter(function (x) { return x.published && x.id === id; })[0] ||
            (d.news || []).filter(function (x) { return x.published; })
              .slice().sort(function (a, b) { return a.date < b.date ? 1 : -1; })[0];
    if (!n) { box.innerHTML = "<p>暂无新闻。</p>"; return; }
    document.title = n.title + "｜" + d.settings.name;
    var crumbs = document.querySelector(".page-hero .breadcrumb");
    if (crumbs) crumbs.innerHTML = '<a href="news.html">新闻动态</a> / 正文';
    var head = document.querySelector(".page-hero");
    if (head) {
      head.querySelector("h1").textContent = n.title;
      head.querySelector("p").textContent = "发布时间：" + n.date;
    }
    box.innerHTML = '<p class="lead">' + esc(n.summary) + '</p>' + photoDiv("visual article-visual", n.cover, "新闻正文图片") + "<p>" + (esc(n.body) || "正文内容正在整理，敬请期待。") + "</p>";
  }
  function renderContact(d) {
    function set(id, v) { var el = document.getElementById(id); if (el) el.textContent = v; }
    set("contact-email", d.contact.email);
    set("contact-phone", d.contact.phone);
    set("contact-address", d.contact.address);
    set("contact-postcode", d.contact.postcode);
  }

  function renderAll() {
    var d = window.SiteStore.frontend();
    var page = document.body.dataset.page;
    if (page === "home") renderHome(d);
    else if (page === "team") renderTeam(d);
    else if (page === "member") renderMember(d);
    else if (page === "research") renderResearch(d);
    else if (page === "publications") renderPublications(d);
    else if (page === "patents") renderPatents(d);
    else if (page === "projects") renderProjects(d);
    else if (page === "news") {
      if (document.body.dataset.view === "detail") renderNewsDetail(d);
      else renderNewsList(d);
    }
    else if (page === "contact") renderContact(d);
  }

  /* 云端发布副本：后台「发布更新」会把整站数据写入仓库 site-data-published.json。
     读取顺序：GitHub API（无 CDN 缓存，发布后立即生效）→ raw 兜底 → 本机已发布副本 → 种子。
     每个浏览器会话最多拉取一次（5 分钟节流），避免超出接口频次限制。 */
  var REPO = "zl2626/lab-website";
  var PUB_FILE = "site-data-published.json";
  var API_URL = "https://api.github.com/repos/" + REPO + "/contents/" + PUB_FILE + "?ref=gh-pages";
  var RAW_URL = "https://raw.githubusercontent.com/" + REPO + "/gh-pages/" + PUB_FILE;
  var CDN_URL = "https://cdn.jsdelivr.net/gh/" + REPO + "@gh-pages/" + PUB_FILE;
  var remoteData = null;
  function b64ToUtf8(b64) {
    if (!b64) return null;
    try { return decodeURIComponent(escape(atob(String(b64).replace(/\s/g, "")))); }
    catch (e) { try { return atob(b64); } catch (e2) { return null; } }
  }
  function b64ToUtf8Json(b64) {
    var txt = b64ToUtf8(b64);
    if (!txt) return null;
    try { return JSON.parse(txt); } catch (e) { return null; }
  }
  /* 新旧数据保护：云端带时间戳（新版发布）视为权威；
     云端是旧数据（无时间戳）时，仅在本浏览器没有已发布副本时才采用，
     防止初始化种子盖住本机刚发布、尚未同步成功的内容。 */
  function acceptRemote(j) {
    if (!j || !j.settings || !j.home) return;
    var pub = read(KEY_PUBLISHED);
    var remT = j._publishTime ? Date.parse(j._publishTime) : 0;
    var pubT = pub && pub._publishTime ? Date.parse(pub._publishTime) : 0;
    if (!remT && pub) return;
    if (remT && pubT && remT < pubT) return;
    remoteData = j;
    renderAll();
  }
  function fetchRemote(mode) {
    var url = mode === "api" ? API_URL : (mode === "raw" ? RAW_URL : CDN_URL);
    var next = mode === "api" ? "raw" : (mode === "raw" ? "cdn" : null);
    var sep = mode === "api" ? "&" : "?";
    fetch(url + sep + "t=" + Date.now())
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (j) {
        if (mode === "api") {
          if (!j || !j.content) throw new Error("empty");
          acceptRemote(b64ToUtf8Json(j.content));
        } else {
          acceptRemote(j);
        }
      })
      .catch(function () { if (next) fetchRemote(next); });
  }
  if (location.protocol.indexOf("http") === 0) {
    var lastFetch = 0;
    try { lastFetch = Number(sessionStorage.getItem("labRemoteFetch.v1") || 0); } catch (e) {}
    if (!lastFetch || Date.now() - lastFetch > 5 * 60 * 1000) {
      try { sessionStorage.setItem("labRemoteFetch.v1", String(Date.now())); } catch (e) {}
      fetchRemote("api");
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", renderAll);
  else renderAll();
})();
