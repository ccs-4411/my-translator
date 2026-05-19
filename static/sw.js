const CACHE_NAME = "ai-translator-v1";

const urlsToCache = [

    "/",
    "/manifest.json",
    "/static/icon-192.png",
    "/static/icon-512.png"

];

// install
self.addEventListener("install", e=>{

    self.skipWaiting();

    e.waitUntil(

        caches.open(CACHE_NAME)
        .then(cache=>{

            return cache.addAll(urlsToCache);

        })

    );

});

// activate
self.addEventListener("activate", e=>{

    clients.claim();

});

// fetch
self.addEventListener("fetch", e=>{

    // API 不快取
    if(

        e.request.url.includes("/languages")
        ||

        e.request.url.includes("/translate")
        ||
