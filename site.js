/* Shared header, footer, galleries and lightbox. You shouldn't need to edit this. */
(function(){
  const page = document.body.dataset.page;          // home | places | people | streets | about | journal | contact
  const SETS = ["Places","People","Streets"];
  const isWork = page==="home" || SETS.map(s=>s.toLowerCase()).includes(page);

  /* ---------- header + footer ---------- */
  const nav = [["index.html","Work",isWork],["about.html","About",page==="about"],["journal.html","Journal",page==="journal"],["contact.html","Contact",page==="contact"]];
  document.body.insertAdjacentHTML("afterbegin", `
    <header><div class="wrap bar">
      <a href="index.html" class="logo">Nduwimana Claude<span>photography</span></a>
      <nav class="main">${nav.map(([h,t,on])=>`<a href="${h}" class="${on?"on":""}">${t}</a>`).join("")}</nav>
      <button class="burger" aria-label="Menu"><i></i><i></i><i></i></button>
    </div></header>`);
  document.body.insertAdjacentHTML("beforeend", `
    <footer><div class="wrap">
      <span>© ${new Date().getFullYear()} Nduwimana Claude. All photographs are my own.</span>
      <span>nduwimanaclaude.com</span>
    </div></footer>
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

  /* ---------- placeholders ---------- */
  function placeholder(p, w){
    const h = Math.round(w / (p.ratio||1.5)), [a,b] = p.tone || ["#ccc","#444"];
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><defs><linearGradient id="g" x1="0" y1="0" x2="0.3" y2="1"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient><radialGradient id="r" cx="0.7" cy="0.3" r="0.6"><stop offset="0" stop-color="#fff" stop-opacity=".28"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs><rect width="100%" height="100%" fill="url(#g)"/><rect width="100%" height="100%" fill="url(#r)"/><text x="50%" y="50%" fill="#fff" fill-opacity=".55" font-family="Georgia,serif" font-style="italic" font-size="${Math.round(w/22)}" text-anchor="middle" dominant-baseline="middle">your photo here</text></svg>`;
    return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  }
  const srcOf = (p, w=1200, ratio) => p.src || placeholder(ratio ? {...p, ratio} : p, w);
  const $ = id => document.getElementById(id);

  /* ---------- lightbox ---------- */
  let list = [], cur = 0;
  function show(i){
    cur = i; const p = list[i];
    $("lbImg").src = srcOf(p, 2000); $("lbImg").alt = p.title;
    $("lbCap").innerHTML = `<b>${p.title}</b>${p.place}`;
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
    $("hero").innerHTML = `<img src="${srcOf(hero, 2100, innerWidth<760 ? 0.8 : 21/9)}" alt="${hero.title}">`;
    $("heroTitle").textContent = hero.title; $("heroPlace").textContent = hero.place;
    $("hero").onclick = () => openLb([hero], 0);
    $("sets").innerHTML = SETS.map(s => {
      const items = PHOTOS.filter(p=>p.set===s);
      const cover = PHOTOS.find(p=>p.title===COVERS[s]) || items[0];
      return `<a class="set-card" href="${s.toLowerCase()}.html">
        <div class="frame"><img loading="lazy" src="${srcOf(cover, 900, 0.8)}" alt="${s}"></div>
        <h3>${s}</h3><div class="label">${items.length} photographs</div></a>`;
    }).join("");
  }

  /* ---------- collection pages ---------- */
  const set = SETS.find(s => s.toLowerCase()===page);
  if(set){
    $("tabs").innerHTML = SETS.map(s=>`<a href="${s.toLowerCase()}.html" class="${s===set?"on":""}">${s}</a>`).join("");
    const items = PHOTOS.filter(p=>p.set===set);
    $("gallery").innerHTML = items.map((p,i)=>`
      <figure class="tile" data-i="${i}">
        <div class="frame" style="aspect-ratio:${p.ratio}"><img loading="lazy" src="${srcOf(p, 900)}" alt="${p.title}, ${p.place}"></div>
        <figcaption class="meta"><span>${p.title}</span><span>${p.place}</span></figcaption>
      </figure>`).join("");
    $("gallery").querySelectorAll(".tile").forEach(t => t.onclick = () => openLb(items, +t.dataset.i));
  }

  /* ---------- about ---------- */
  if(page==="about") $("portrait").innerHTML = `<img src="${PORTRAIT.src || placeholder({...PORTRAIT, ratio:0.8}, 800)}" alt="Portrait of Nduwimana Claude">`;

  /* ---------- journal ---------- */
  if(page==="journal"){
    $("posts").innerHTML = POSTS.map(p=>`<a class="post" href="${p.url}">
      <span class="label">${p.date}</span><div><h3>${p.title}</h3><p>${p.blurb}</p></div><span class="label">Read →</span></a>`).join("");
    $("subForm").addEventListener("submit", e => {
      e.preventDefault();
      // Once the Substack is live, swap this form for Substack's embed code.
      $("subNote").textContent = "Thanks! The newsletter is launching soon. Use the link below to find it on Substack.";
    });
  }
})();
