//light and dark toggle, the choice is kept in this browser and otherwise follows the system
(function () {
  var button = document.querySelector('.theme-toggle');
  if (!button) return;
  var system = window.matchMedia('(prefers-color-scheme: dark)');
  function mode() {
    return document.documentElement.dataset.theme || (system.matches ? 'dark' : 'light');
  }
  function show() {
    button.dataset.mode = mode();
    button.setAttribute('aria-label', mode() === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
  }
  button.addEventListener('click', function () {
    var next = mode() === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('gf-theme', next); } catch (e) { }
    show();
  });
  if (system.addEventListener) system.addEventListener('change', show);
  show();
})();
