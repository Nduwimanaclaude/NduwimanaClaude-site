/* ============================================================
   YOUR PHOTOS GO HERE. This is the only file you need to edit
   to add, remove, or reorder photos.

   - Put image files in the /photos folder and set src to
     "photos/your-file.jpg". Export long edge ~2400px, JPG ~80%.
   - set decides which page it shows on: "Places", "People" or "Streets".
   - ratio is width / height (3:2 landscape = 1.5, 4:5 portrait = 0.8).
   - featured: true puts it on the home page hero (use one).
   - Leave src empty ("") to show a placeholder.
   ============================================================ */
const PHOTOS = [
  { src:"", title:"Morning on the James", place:"Richmond, VA",  set:"Places",  ratio:1.5,  featured:true, tone:["#c9b79a","#5d6a72"] },
  { src:"", title:"Forest Park, late",    place:"St. Louis, MO", set:"Places",  ratio:0.8,  tone:["#93a07f","#2f3a2c"] },
  { src:"", title:"Belle Isle rocks",     place:"Richmond, VA",  set:"Places",  ratio:1.25, tone:["#a7b3b8","#3c4a52"] },
  { src:"", title:"Hill country fence",   place:"Texas",         set:"Places",  ratio:1.5,  tone:["#d9c18f","#7a8b6d"] },
  { src:"", title:"Blue hour",            place:"Richmond, VA",  set:"Places",  ratio:0.8,  tone:["#6f86a8","#1d2433"] },

  { src:"", title:"Carnival lights",      place:"St. Louis, MO", set:"People",  ratio:1.5,  tone:["#e0a96d","#3b2333"] },
  { src:"", title:"Before the race",      place:"Richmond, VA",  set:"People",  ratio:0.8,  tone:["#b8a38c","#2b2b2b"] },
  { src:"", title:"Graduation",           place:"St. Louis, MO", set:"People",  ratio:1.5,  tone:["#cdb9a3","#4b3a30"] },
  { src:"", title:"Front porch",          place:"Dallas, TX",    set:"People",  ratio:0.8,  tone:["#c79c7a","#3d2c25"] },

  { src:"", title:"Deep Ellum wall",      place:"Dallas, TX",    set:"Streets", ratio:0.8,  tone:["#d36b4a","#2e2a3a"] },
  { src:"", title:"Carytown, 6pm",        place:"Richmond, VA",  set:"Streets", ratio:1.5,  tone:["#e8c28a","#6b4f3c"] },
  { src:"", title:"Corner store",         place:"St. Louis, MO", set:"Streets", ratio:1,    tone:["#9fb7c4","#3d3a4f"] },
  { src:"", title:"Rain on Broad St",     place:"Richmond, VA",  set:"Streets", ratio:0.8,  tone:["#8d9599","#262a2e"] }
];

/* Cover photo for each collection card on the home page (by title). */
const COVERS = { Places:"Forest Park, late", People:"Before the race", Streets:"Deep Ellum wall" };

/* Your portrait on the About page. */
const PORTRAIT = { src:"", tone:["#c8b8a6","#3a332c"] };

/* Journal entries: paste in links to your Substack posts as you publish them. */
const POSTS = [
  { date:"Coming soon", title:"Why I started shooting again", blurb:"The first post. A little about the camera, the city, and the plan.", url:"https://nduwimanaclaude.substack.com" }
];
