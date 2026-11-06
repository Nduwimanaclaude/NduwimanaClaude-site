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
  { src:"photos/blue-ridge-sunset.jpg",     title:"Last light",              place:"Blue Ridge Parkway, VA",       set:"Places",  ratio:1.5,   featured:true },
  { src:"photos/antelope-canyon.jpg",       title:"Antelope Canyon",         place:"Page, AZ",                     set:"Places",  ratio:0.75 },
  { src:"photos/thors-hammer.jpg",          title:"Thor's Hammer",           place:"Bryce Canyon, UT",             set:"Places",  ratio:1.5 },
  { src:"photos/aventine-keyhole.jpg",      title:"Through the keyhole",     place:"Aventine Hill, Rome",          set:"Places",  ratio:0.75 },
  { src:"photos/blue-ridge-road.jpg",       title:"The road down",           place:"Blue Ridge, VA",               set:"Places",  ratio:0.667 },
  { src:"photos/mabry-mill.jpg",            title:"Mabry Mill",              place:"Blue Ridge Parkway, VA",       set:"Places",  ratio:1.5 },
  { src:"photos/bryce-amphitheater.jpg",    title:"The amphitheater",        place:"Bryce Canyon, UT",             set:"Places",  ratio:1.5 },
  { src:"photos/double-arch.jpg",           title:"Double Arch",             place:"Arches, UT",                   set:"Places",  ratio:1.5 },
  { src:"photos/hill-through-branches.jpg", title:"Through the branches",    place:"Blue Ridge, VA",               set:"Places",  ratio:1.5 },
  { src:"photos/horses-utah.jpg",           title:"Evening pasture",         place:"Utah",                         set:"Places",  ratio:1.5 },

  { src:"photos/red-dress-rome.jpg",        title:"Red dress, big bus",      place:"Rome, Italy",                  set:"People",  ratio:0.667 },
  { src:"photos/st-peters.jpg",             title:"St. Peter's",             place:"Vatican City",                 set:"People",  ratio:1.5 },
  { src:"photos/bryce-trail-sign.jpg",      title:"Sunset Point trail",      place:"Bryce Canyon, UT",             set:"People",  ratio:1.5 },

  { src:"photos/place-des-vosges.jpg",      title:"Place des Vosges",        place:"Paris, France",                set:"Streets", ratio:0.667 },
  { src:"photos/aventine-street.jpg",       title:"Up the Aventine",         place:"Rome, Italy",                  set:"Streets", ratio:1.5 },
  { src:"photos/santa-maria-maggiore.jpg",  title:"Santa Maria Maggiore",    place:"Rome, Italy",                  set:"Streets", ratio:0.667 },
  { src:"photos/bryce-shared-path.jpg",     title:"Shared use path",         place:"Bryce Canyon, UT",             set:"Streets", ratio:1.5 }
];

/* Cover photo for each collection card on the home page (by title). */
const COVERS = { Places:"Antelope Canyon", People:"Red dress, big bus", Streets:"Place des Vosges" };

/* Your portrait on the About page. */
const PORTRAIT = { src:"", tone:["#c8b8a6","#3a332c"] };

/* Journal entries: paste in links to your Substack posts as you publish them. */
const POSTS = [
  { date:"Coming soon", title:"Why I started shooting again", blurb:"The first post. A little about the camera, the city, and the plan.", url:"https://nduwimanaclaude.substack.com" }
];
