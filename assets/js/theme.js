//light and dark toggle, the choice is kept in this browser and otherwise follows the system
//the theme itself is set before the page paints, by the script in _includes/head-custom.html
(function () {
  var button = document.querySelector('.theme-toggle');
  var system = window.matchMedia('(prefers-color-scheme: dark)');
  function set(mode) {
    document.documentElement.dataset.theme = mode;
    if (button) button.setAttribute('aria-label', mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
  }
  function saved() {
    try { return localStorage.getItem('gf-theme'); } catch (e) { return null; }
  }
  if (button) button.addEventListener('click', function () {
    var next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('gf-theme', next); } catch (e) { }
    set(next);
  });
  //follow the system until a choice is made
  if (system.addEventListener) system.addEventListener('change', function () {
    if (!saved()) set(system.matches ? 'dark' : 'light');
  });
  set(document.documentElement.dataset.theme);
})();
