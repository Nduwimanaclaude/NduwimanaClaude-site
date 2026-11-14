/* GENERATED from Website/_site.json on the NAS. Edit that file, not this one. */
window.SITE_TEXT = {"logo": "Nduwimana Claude", "logo_small": "photography", "home_intro": "Pictures of places, people, and the in-between moments. *Made between St. Louis, Dallas, and wherever the weekend goes.*", "about_title": "Hi, I'm Nduwimana.", "about": ["I'm a photographer who shoots mostly on a Canon, mostly on weekends, and mostly whatever stops me on the way somewhere else. This site is where the keepers end up.", "I studied business at WashU in St. Louis and work in finance during the week. Photography is the part of the week that slows things down. I like quiet light, city edges, and anything that looks better at 6am than it has any right to."], "now_title": "What I'm up to.", "now_intro": "Updated November 2026. A snapshot of what has my attention these days.", "now": ["**Shooting.** Mostly street and landscape around Richmond and the Blue Ridge, on the Canon R6 II and the Mavic 4 Pro. Working on getting more people into my street photos.", "**Training.** Building up to my first half marathon in December. Easy miles, lots of zone 2, and a lot more patience than I expected.", "**Trying new things.** Social dance, pottery, and climbing. Bad at all three, having fun anyway.", "**Building.** This site, plus a little home server setup that turns photos I drop in a folder into pages here."], "contact_title": "Say hello.", "contact_intro": "For collaborations, questions, or just to talk about a photo, email me. I usually reply within a couple of days.", "email": "nclaude@nduwimanaclaude.com", "based_in": "Richmond, VA", "journal_title": "Stories behind the pictures.", "journal_intro": "I write a newsletter on Substack with the longer version: where a set of photos came from, what I was shooting with, and whatever I'm thinking about that week.", "footer_subscribe": "New photo sets and the stories behind them, sent from Substack."};

(function(){
  var T = window.SITE_TEXT || {}, page = document.body.dataset.page;
  function e(s){ return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function md(s){ return e(s).replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>").replace(/\*(.+?)\*/g,"<em>$1</em>"); }
  function has(k){ return T[k] != null && T[k] !== "" && !(Array.isArray(T[k]) && !T[k].length); }
  function set(sel, k){ if(!has(k)) return; var el = document.querySelector(sel); if(el) el.innerHTML = md(T[k]); }
  function paras(sel, k){ if(!has(k)) return; var box = document.querySelector(sel); if(!box) return;
    var ps = Array.prototype.filter.call(box.children, function(c){ return c.tagName === "P" && !c.classList.contains("note"); });
    var at = ps.length ? ps[0] : box.firstChild; var list = Array.isArray(T[k]) ? T[k] : [T[k]];
    list.forEach(function(t){ var p = document.createElement("p"); p.innerHTML = md(t); box.insertBefore(p, at); });
    ps.forEach(function(p){ p.remove(); });
    Array.prototype.forEach.call(box.querySelectorAll("p.note"), function(n){ n.remove(); }); }
  if(has("logo")){ var l = document.querySelector(".logo"); if(l && l.firstChild && l.firstChild.nodeType === 3) l.firstChild.nodeValue = T.logo; }
  set(".logo span", "logo_small"); set(".foot-sub p", "footer_subscribe");
  if(page === "home") set(".intro p", "home_intro");
  if(page === "about"){ set(".page-head h1", "about_title"); paras(".split .body", "about"); }
  if(page === "now"){ set(".page-head h1", "now_title"); set(".page-head p", "now_intro"); paras(".split .body", "now"); }
  if(page === "journal"){ set(".page-head h1", "journal_title"); set(".page-head p", "journal_intro"); }
  if(page === "contact"){ set(".page-head h1", "contact_title"); set(".page-head p", "contact_intro");
    if(has("email")){ var c = document.querySelector(".contact-line"); if(c){ c.textContent = T.email; c.href = "mailto:" + T.email; } }
    if(has("based_in")) Array.prototype.forEach.call(document.querySelectorAll(".contact-list div"), function(d){
      if(d.firstElementChild && /based in/i.test(d.firstElementChild.textContent) && d.lastElementChild) d.lastElementChild.textContent = T.based_in; }); }
})();
