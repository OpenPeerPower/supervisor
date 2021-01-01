
try {
  new Function("import('/api/oppio/app/frontend_latest/entrypoint.df099659.js')")();
} catch (err) {
  var el = document.createElement('script');
  el.src = '/api/oppio/app/frontend_es5/entrypoint.d303236e.js';
  document.body.appendChild(el);
}
  