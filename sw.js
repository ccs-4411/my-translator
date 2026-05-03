self.addEventListener("fetch", e=>{
    if(e.request.url.includes("/languages") || 
       e.request.url.includes("/tts") || 
       e.request.method === "POST"){
        return; // ❗ API 不攔
    }

    e.respondWith(
        fetch(e.request).catch(()=>caches.match(e.request))
    );
});
