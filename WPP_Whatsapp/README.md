I am try use playwright as threadsafe
and try all function sync but in event function
like `page.on("event", func)` must use async function,
may be playwright exec only one sync function in same time, 
so if you need more use them as async

now all function has two type 

- one relate to event (play in background) like `page.on` need use async and await
- other not relate to event, use without async and await