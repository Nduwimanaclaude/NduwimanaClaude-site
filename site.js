/* Shared header, footer, galleries and lightbox. You shouldn't need to edit this. */
(function(){
  const page = document.body.dataset.page;          // home | <collection> | about | journal | now | contact | sitemap
  // Collections come from photos.js (generated from the NAS folders).
  const CATS = (typeof SETS !== "undefined" && SETS.length) ? SETS : [...new Set(PHOTOS.map(p=>p.set))];
  const RESERVED = ["index","about","journal","contact","now","links","404","tools","photos","content","site","style","sitemap","robots","favicon","apple-touch-icon"];
  const slugify = s => { let x = s.toLowerCase().replace(/['’]/g,"").replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"") || "photo"; return RESERVED.includes(x) ? x+"-photos" : x; };
  const isWork = page==="home" || CATS.some(s=>slugify(s)===page);
  const SUB = (typeof SUBSTACK !== "undefined") ? SUBSTACK : { url:"https://nduwimanaclaude.substack.com", live:false };
  const esc = s => String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  const $ = id => document.getElementById(id);

  const IG_ICON = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="0.9" fill="currentColor" stroke="none"/></svg>`;
  const SS_ICON = `<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M4 3h16v2.6H4zM4 7.8h16v2.6H4zM4 12.6h16V22l-8-4.5L4 22z"/></svg>`;

  /* ---------- header ---------- */
  const nav = [["index.html","Work",isWork],["about.html","About",page==="about"],["journal.html","Journal",page==="journal"],["contact.html","Contact",page==="contact"]];
  document.body.insertAdjacentHTML("afterbegin", `
    <header><div class="wrap bar">
      <a href="index.html" class="logo">Nduwimana Claude<span>photography</span></a>
      <nav class="main">${nav.map(([h,t,on])=>`<a href="${h}" class="${on?"on":""}">${t}</a>`).join("")}</nav>
      <button class="burger" aria-label="Menu"><i></i><i></i><i></i></button>
    </div></header>`);

  /* ---------- subscribe box (Substack) ---------- */
  const subBox = () => SUB.live
    ? `<iframe class="ss-embed" src="${SUB.url}/embed" title="Subscribe on Substack" frameborder="0" scrolling="no"></iframe>`
    : `<a class="sub-btn" href="${SUB.url}" target="_blank" rel="noopener">Subscribe on Substack</a><p class="sub-note">The newsletter is launching soon.</p>`;

  /* ---------- footer ---------- */
  const mapLinks = [["index.html","Work"], ...CATS.map(s=>[`${slugify(s)}.html`, s]), ["about.html","About"], ["journal.html","Journal"], ["now.html","Now"], ["contact.html","Contact"]];
  document.body.insertAdjacentHTML("beforeend", `
    <footer class="foot">
      <div class="wrap foot-grid">
        <div class="foot-col foot-sub">
          <h4>Subscribe</h4>
          <p>New photo sets and the stories behind them, sent from Substack.</p>
          ${subBox()}
        </div>
        <div class="foot-col">
          <h4>Sitemap</h4>
          <ul>${mapLinks.map(([h,t])=>`<li><a href="${h}">${esc(t)}</a></li>`).join("")}</ul>
        </div>
        <div class="foot-col">
          <h4>Follow</h4>
          <div class="foot-social">
            <a href="https://www.instagram.com/_claude_photography/" target="_blank" rel="noopener" aria-label="Instagram">${IG_ICON}<span>Instagram</span></a>
            ${SUB.live ? `<a href="${SUB.url}" target="_blank" rel="noopener" aria-label="Substack">${SS_ICON}<span>Substack</span></a>` : ""}
          </div>
        </div>
      </div>
      <div class="wrap foot-mark" aria-hidden="true"><svg viewBox="0 0 1000 96" preserveAspectRatio="xMidYMid meet"><text x="0" y="84" textLength="1000" lengthAdjust="spacingAndGlyphs">NDUWIMANA CLAUDE</text></svg></div>
      <div class="wrap foot-legal">
        <span>© ${new Date().getFullYear()} Nduwimana Claude. All rights reserved.</span>
        <a href="sitemap.html">Sitemap</a>
      </div>
    </footer>
    <div class="lb" id="lb" role="dialog" aria-modal="true">
      <span class="count" id="lbCount"></span>
      <button class="x" id="lbX" aria-label="Close">×</button>
      <button class="prev" id="lbPrev" aria-label="Previous">‹</button>
      <div class="stage"><img id="lbImg" alt=""></div>
      <div class="cap" id="lbCap"></div>
      <button class="next" id="lbNext" aria-label="Next">›</button>
    </div>`);
  document.querySelector(".burger").onclick = () => document.body.classList.toggle("menu");
  const header = document.querySelector("header");
  addEventListener("scroll", () => header.classList.toggle("scrolled", scrollY > 10), {passive:true});

  /* ---------- images: placeholders + blur-up ---------- */
  function placeholder(p, w){
    const h = Math.round(w / (p.ratio||1.5)), [a,b] = p.tone || ["#ccc","#444"];
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><defs><linearGradient id="g" x1="0" y1="0" x2="0.3" y2="1"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient></defs><rect width="100%" height="100%" fill="url(#g)"/></svg>`;
    return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  }
  const srcOf = (p, w=1200, ratio) => p.src || placeholder(ratio ? {...p, ratio} : p, w);
  const smallOf = (p, w=900, ratio) => p.srcSmall || srcOf(p, w, ratio);   // 1200px copy for grids/covers
  const blur = p => p.lqip ? `background-image:url('${p.lqip}');` : "";
  const pic = (p, src, extra="") => `<img class="fade" ${extra} src="${src}" alt="${esc(p.title)}${p.place?", "+esc(p.place):""}" style="object-position:${p.focus||"center"}">`;
  function reveal(root){
    root.querySelectorAll("img.fade:not(.in)").forEach(im => {
      if(im.complete && im.naturalWidth) im.classList.add("in");
      else { im.addEventListener("load", () => im.classList.add("in"), {once:true}); im.addEventListener("error", () => im.classList.add("in"), {once:true}); }
    });
  }

  /* ---------- lightbox ---------- */
  let list = [], cur = 0;
  const SPEC_ORDER = ["camera","lens","focal","aperture","shutter","iso"];
  function show(i){
    cur = i; const p = list[i];
    $("lbImg").src = srcOf(p, 2000); $("lbImg").alt = p.title;
    const specs = p.specs ? SPEC_ORDER.filter(k=>p.specs[k]).map(k=>esc(p.specs[k])).join(" · ") : "";
    $("lbCap").innerHTML = `<b>${esc(p.title)}</b>${esc(p.place)}${specs ? `<span class="specs">${specs}</span>` : ""}`;
    $("lbCount").textContent = list.length > 1 ? `${i+1} / ${list.length}` : "";
  }
  function openLb(items, i){ list = items; show(i); $("lb").classList.add("open"); document.body.style.overflow="hidden"; }
  function closeLb(){ $("lb").classList.remove("open"); document.body.style.overflow=""; }
  const step = d => show((cur + d + list.length) % list.length);
  $("lbX").onclick = closeLb;
  $("lbPrev").onclick = e => { e.stopPropagation(); step(-1); };
  $("lbNext").onclick = e => { e.stopPropagation(); step(1); };
  $("lb").onclick = e => { if(e.target.id==="lb" || e.target.classList.contains("stage")) closeLb(); };
  document.addEventListener("keydown", e => {
    if(e.key==="Escape"){ closeLb(); document.body.classList.remove("menu"); }
    if(!$("lb").classList.contains("open")) return;
    if(e.key==="ArrowLeft") step(-1);
    if(e.key==="ArrowRight") step(1);
  });
  let tx = null;
  $("lb").addEventListener("touchstart", e => tx = e.touches[0].clientX, {passive:true});
  $("lb").addEventListener("touchend", e => { if(tx===null) return; const dx = e.changedTouches[0].clientX - tx; if(Math.abs(dx)>40) step(dx<0?1:-1); tx=null; });

  /* ---------- home ---------- */
  if(page==="home"){
    const hero = PHOTOS.find(p=>p.featured) || PHOTOS[0];
    $("hero").setAttribute("style", blur(hero));
    $("hero").innerHTML = pic(hero, srcOf(hero, 2100, innerWidth<760 ? 0.8 : 21/9), hero.srcSmall ? `srcset="${hero.srcSmall} 1200w, ${hero.src} 2400w" sizes="(max-width: 760px) 100vw, 1400px"` : "");
    $("heroTitle").textContent = hero.title; $("heroPlace").textContent = hero.place;
    $("hero").onclick = () => openLb([hero], 0);
    reveal($("hero"));

    /* photo strip: mixed across collections, arrows only, loops forever */
    if($("stripTrack")) initStrip();

    $("sets").innerHTML = CATS.map(s => {
      const items = PHOTOS.filter(p=>p.set===s);
      const cover = items.find(p=>typeof COVERS!=="undefined" && p.title===COVERS[s]) || items[0];
      return `<a class="set-card ink-${cover.ink==="dark"?"dark":"light"}" href="${slugify(s)}.html">
        <div class="frame" style="${blur(cover)}">${pic(cover, smallOf(cover, 900, 0.8), 'loading="lazy"')}</div>
        <div class="set-over"><h3>${esc(s)}</h3><span>View Gallery</span></div></a>`;
    }).join("");
    reveal($("sets"));
  }

  function initStrip(){
    const per = CATS.map(s => PHOTOS.filter(p=>p.set===s));
    const mix = [];
    for(let i=0; mix.length < Math.min(PHOTOS.length, 24) && i < PHOTOS.length; i++) per.forEach(l => { if(l[i] && mix.length < 24) mix.push(l[i]); });
    const N = mix.length, track = $("stripTrack");
    if(!N){ $("strip").parentElement.style.display="none"; return; }
    const copies = N > 1 ? 3 : 1;
    const all = Array.from({length:copies}, () => mix).flat();
    track.innerHTML = all.map((p,k)=>`<figure class="strip-item" data-k="${k}" style="aspect-ratio:${p.ratio||1.5};${blur(p)}">${pic(p, smallOf(p, 900), k<N*2?"":'loading="lazy"')}</figure>`).join("");
    reveal(track);
    track.querySelectorAll(".strip-item").forEach(el => el.onclick = () => openLb(mix, +el.dataset.k % N));
    if(N < 2){ $("stripPrev").hidden = $("stripNext").hidden = true; return; }
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    let idx = N, busy = false;
    const items = () => track.children;
    const place = anim => {
      track.style.transition = anim && !reduce ? "transform .55s cubic-bezier(.2,.7,.2,1)" : "none";
      track.style.transform = `translateX(${-items()[idx].offsetLeft}px)`;
    };
    const normalize = () => {
      busy = false;
      if(idx >= 2*N){ idx -= N; place(false); }
      else if(idx < N){ idx += N; place(false); }
    };
    track.addEventListener("transitionend", normalize);
    const go = d => {
      if(busy) return;
      idx += d; busy = !reduce; place(true);
      if(reduce) normalize();
      else setTimeout(() => { if(busy) normalize(); }, 800);   // safety if transitionend is missed
    };
    $("stripPrev").onclick = () => go(-1);
    $("stripNext").onclick = () => go(1);
    let sx = null;
    track.addEventListener("touchstart", e => sx = e.touches[0].clientX, {passive:true});
    track.addEventListener("touchend", e => { if(sx===null) return; const dx = e.changedTouches[0].clientX - sx; if(Math.abs(dx)>40) go(dx<0?1:-1); sx=null; });
    let rw = innerWidth;
    addEventListener("resize", () => { if(innerWidth!==rw){ rw = innerWidth; place(false); } });
    requestAnimationFrame(() => place(false));
  }

  /* ---------- collection pages: justified rows ---------- */
  const set = CATS.find(s => slugify(s)===page);
  if(set){
    $("tabs").innerHTML = CATS.map(s=>`<a href="${slugify(s)}.html" class="${s===set?"on":""}">${esc(s)}</a>`).join("");
    const items = PHOTOS.filter(p=>p.set===set);
    const el = $("gallery"); el.className = "jgrid";
    let lastW = 0;
    const layout = () => {
      const W = el.clientWidth; if(!W || W===lastW) return; lastW = W;
      const gap = W < 760 ? 6 : 10, H = W < 560 ? 230 : W < 1100 ? 280 : 340;
      let html = "", row = [], sum = 0;
      const flush = (h, last) => {
        html += `<div class="jrow${last?" last":""}" style="height:${h}px">` + row.map(({p,i}) =>
          `<figure class="jt" data-i="${i}" style="width:${(p.ratio||1.5)*h}px;${blur(p)}">${pic(p, smallOf(p, 900), 'loading="lazy"')}<figcaption><b>${esc(p.title)}</b><span>${esc(p.place)}</span></figcaption></figure>`
        ).join("") + `</div>`;
        row = []; sum = 0;
      };
      const rowH = (n, total) => (W - gap*(n-1)) / total;
      items.forEach((p,i) => {
        const r = p.ratio||1.5;
        const before = row.length ? rowH(row.length, sum) : Infinity;
        const after = rowH(row.length+1, sum + r);
        if(after <= H){
          // close the row at whichever height lands closer to the target
          if(row.length && Math.abs(before - H) < Math.abs(after - H)){ flush(Math.floor(before*100)/100, false); row.push({p,i}); sum = r; }
          else { row.push({p,i}); sum += r; flush(Math.floor(after*100)/100, false); }
        } else { row.push({p,i}); sum += r; }
      });
      if(row.length){ const h = rowH(row.length, sum); flush(h <= H*1.3 ? Math.floor(h*100)/100 : H, true); }
      el.style.setProperty("--gap", gap+"px");
      el.innerHTML = html;
      el.querySelectorAll(".jt").forEach(t => t.onclick = () => openLb(items, +t.dataset.i));
      reveal(el);
    };
    layout();
    let t; addEventListener("resize", () => { clearTimeout(t); t = setTimeout(layout, 120); });
    if(document.fonts) document.fonts.ready.then(() => { lastW = 0; layout(); });
  }

  /* ---------- sitemap page ---------- */
  if(page==="sitemap" && $("sitemapList")){
    const groups = [
      ["Work", [["index.html","Home"], ...CATS.map(s=>[`${slugify(s)}.html`, `${s} (${PHOTOS.filter(p=>p.set===s).length} photos)`])]],
      ["About", [["about.html","About"],["now.html","Now"],["journal.html","Journal"],["contact.html","Contact"],["links.html","Links"]]],
    ];
    $("sitemapList").innerHTML = groups.map(([g,ls]) => `<div class="sm-group"><div class="label">${g}</div><ul>${ls.map(([h,t])=>`<li><a href="${h}">${esc(t)}</a></li>`).join("")}</ul></div>`).join("");
  }

  /* ---------- about ---------- */
  if(page==="about" && typeof PORTRAIT!=="undefined" && $("portrait")) $("portrait").innerHTML = `<img src="${PORTRAIT.src || placeholder({...PORTRAIT, ratio:0.8}, 800)}" alt="Portrait of Nduwimana Claude">`;

  /* ---------- journal ---------- */
  if(page==="journal"){
    if($("subBox")) $("subBox").innerHTML = subBox();
    if(typeof POSTS!=="undefined" && $("posts")) $("posts").innerHTML = POSTS.map(p=>`<a class="post" href="${p.url}">
      <span class="label">${esc(p.date)}</span><div><h3>${esc(p.title)}</h3><p>${esc(p.blurb)}</p></div><span class="label">Read →</span></a>`).join("");
  }
})();
