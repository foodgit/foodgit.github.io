// Site behaviour: homepage recipe browser, sortable/filterable tag-page tables, and
// on recipe pages tick-off ingredients/steps and keep-screen-on. Everything here is
// optional: without it every recipe is still listed and every page still reads fine.
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.recipe-browser').forEach(setUpBrowser);
  document.querySelectorAll('table.recipes').forEach(setUpTable);
  var recipe = document.querySelector('.recipe-page');
  if (recipe) {
    setUpTicks(recipe);
    setUpKeepAwake(recipe);
  }
});

function words(text) { return text.toLowerCase().split(/\s+/).filter(Boolean); }

// Homepage: sidebar filters (any within a group, all across groups), search, sort.
function setUpBrowser(browser) {
  var list = browser.querySelector('.recipe-list');
  var items = Array.prototype.slice.call(list.children);
  var boxes = Array.prototype.slice.call(browser.querySelectorAll('.filters input[type=checkbox]'));
  var search = browser.querySelector('.recipe-search');
  var sort = browser.querySelector('.recipe-sort');
  var status = browser.querySelector('.results-status');
  var pills = browser.querySelector('.active-filters');
  var aside = browser.querySelector('.filters');
  var toggle = browser.querySelector('.filters-toggle');
  var done = browser.querySelector('.filters-done');

  function selected() {
    var groups = {};
    boxes.forEach(function (b) {
      if (b.checked) (groups[b.dataset.group] = groups[b.dataset.group] || []).push(b.value);
    });
    return groups;
  }

  function update() {
    var groups = selected(), query = words(search.value), shown = 0, active = [];
    Object.keys(groups).forEach(function (g) { active = active.concat(groups[g]); });
    items.forEach(function (li) {
      var tags = li.dataset.tags.split(' '), meal = li.dataset.meal.split(' ');
      var ok = Object.keys(groups).every(function (g) {
        var have = g === 'meal' ? meal : tags;
        return groups[g].some(function (t) { return have.indexOf(t) !== -1; });
      });
      var text = li.textContent.toLowerCase();
      ok = ok && query.every(function (w) { return text.indexOf(w) !== -1; });
      li.hidden = !ok;
      if (ok) shown++;
    });
    status.textContent = shown === items.length && !query.length
      ? items.length + ' recipes' : shown + ' of ' + items.length + ' recipes';
    if (active.length || query.length) {
      var clear = document.createElement('button');
      clear.type = 'button';
      clear.className = 'link-button';
      clear.textContent = 'clear';
      clear.addEventListener('click', function () {
        boxes.forEach(function (b) { b.checked = false; });
        search.value = '';
        update();
      });
      status.appendChild(document.createTextNode(' '));
      status.appendChild(clear);
    }
    toggle.textContent = active.length ? 'Filters (' + active.length + ')' : 'Filters';
    done.textContent = 'Show ' + shown + ' recipes';
    pills.textContent = '';
    boxes.filter(function (b) { return b.checked; }).forEach(function (b) {
      var pill = document.createElement('button');
      pill.type = 'button';
      pill.className = 'pill';
      pill.textContent = b.value.replace(/_/g, ' ') + ' ×';
      pill.setAttribute('aria-label', 'Remove filter ' + b.value);
      pill.addEventListener('click', function () { b.checked = false; update(); });
      pills.appendChild(pill);
    });
  }

  function reorder() {
    var key = sort.value;
    items.sort(function (a, b) {
      if (key === 'name') return a.textContent.localeCompare(b.textContent);
      var x = a.dataset[key] || '', y = b.dataset[key] || '';
      return y.localeCompare(x);  // newest first; recipes without a date go last
    });
    items.forEach(function (li) { list.appendChild(li); });
  }

  boxes.forEach(function (b) { b.addEventListener('change', update); });
  search.addEventListener('input', update);
  sort.addEventListener('change', reorder);
  toggle.addEventListener('click', function () { aside.classList.toggle('open'); });
  done.addEventListener('click', function () { aside.classList.remove('open'); });
  update();
}

// Tag pages: click a column header to sort, and a filter box above the table.
function setUpTable(table) {
  var tbody = table.tBodies[0];
  var rows = Array.prototype.slice.call(tbody.rows);
  var headers = Array.prototype.slice.call(table.tHead.rows[0].cells);

  var box = document.createElement('input');
  box.type = 'search';
  box.className = 'recipe-filter';
  box.placeholder = 'Filter by name, tag or date';
  box.setAttribute('aria-label', 'Filter recipes');
  var count = document.createElement('span');
  count.className = 'recipe-count';
  count.setAttribute('aria-live', 'polite');
  var bar = document.createElement('div');
  bar.className = 'recipe-toolbar';
  bar.appendChild(box);
  bar.appendChild(count);
  table.parentNode.insertBefore(bar, table);

  function filter() {
    var query = words(box.value), shown = 0;
    rows.forEach(function (row) {
      var text = row.textContent.toLowerCase();
      var match = query.every(function (w) { return text.indexOf(w) !== -1; });
      row.hidden = !match;
      if (match) shown++;
    });
    count.textContent = shown === rows.length ? rows.length + ' recipes'
                                              : shown + ' of ' + rows.length + ' recipes';
  }
  box.addEventListener('input', filter);
  filter();

  headers.forEach(function (th, col) {
    if (!th.hasAttribute('data-sort')) return;
    th.tabIndex = 0;
    function sortBy() {
      var ascending = th.getAttribute('aria-sort') !== 'ascending';
      headers.forEach(function (h) { h.removeAttribute('aria-sort'); });
      th.setAttribute('aria-sort', ascending ? 'ascending' : 'descending');
      rows.sort(function (a, b) {
        var x = a.cells[col].textContent.trim(), y = b.cells[col].textContent.trim();
        if (!x || !y) return (!x) - (!y);
        return ascending ? x.localeCompare(y) : y.localeCompare(x);
      });
      rows.forEach(function (row) { tbody.appendChild(row); });
    }
    th.addEventListener('click', sortBy);
    th.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); sortBy(); }
    });
  });
  headers[0].setAttribute('aria-sort', 'ascending');
}

// Recipe pages: tap an ingredient or step to tick it off; remembered on this device.
function setUpTicks(page) {
  var body = page.querySelector('.recipe-body');
  var items = [];
  ['ingredients', 'method'].forEach(function (id) {
    var heading = body.querySelector('h2#' + id);
    for (var el = heading && heading.nextElementSibling; el && el.tagName !== 'H2'; el = el.nextElementSibling) {
      var found = el.querySelectorAll(id === 'method' ? 'li, blockquote > p' : 'li');
      if (el.tagName === 'LI') found = [el];
      Array.prototype.forEach.call(found, function (item) {
        if (item.closest('li') !== item && item.tagName === 'P' && item.closest('li')) return;
        items.push(item);
      });
    }
  });
  if (!items.length) return;

  var key = 'gitfood-ticks:' + location.pathname;
  var ticked = [];
  try { ticked = JSON.parse(localStorage.getItem(key)) || []; } catch (e) { ticked = []; }
  var clear = page.querySelector('.clear-ticks');

  function save() {
    ticked = items.map(function (item, i) { return item.classList.contains('done') ? i : -1; })
                  .filter(function (i) { return i !== -1; });
    try { localStorage.setItem(key, JSON.stringify(ticked)); } catch (e) { /* private mode */ }
    if (clear) clear.hidden = !ticked.length;
  }

  items.forEach(function (item, i) {
    item.classList.add('tickable');
    item.setAttribute('role', 'checkbox');
    item.tabIndex = 0;
    if (ticked.indexOf(i) !== -1) item.classList.add('done');
    item.setAttribute('aria-checked', item.classList.contains('done'));
    function toggle(e) {
      if (e.target.closest('a')) return;
      item.classList.toggle('done');
      item.setAttribute('aria-checked', item.classList.contains('done'));
      save();
    }
    item.addEventListener('click', toggle);
    item.addEventListener('keydown', function (e) {
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); toggle(e); }
    });
  });
  if (clear) {
    clear.addEventListener('click', function () {
      items.forEach(function (item) { item.classList.remove('done'); item.setAttribute('aria-checked', false); });
      save();
    });
    clear.hidden = !ticked.length;
  }
}

// Recipe pages: stop the screen dimming while cooking (where the browser allows it).
function setUpKeepAwake(page) {
  var button = page.querySelector('.keep-awake');
  if (!button || !('wakeLock' in navigator)) return;
  var lock = null;
  button.hidden = false;

  function set(on) {
    button.setAttribute('aria-pressed', on);
    button.classList.toggle('on', on);
  }
  function request() {
    return navigator.wakeLock.request('screen').then(function (l) {
      lock = l;
      set(true);
      lock.addEventListener('release', function () { if (lock === l) { lock = null; } });
    }).catch(function () { set(false); });
  }
  button.addEventListener('click', function () {
    if (button.classList.contains('on')) {
      set(false);
      if (lock) lock.release();
      lock = null;
    } else {
      request();
    }
  });
  // the browser drops the lock when the tab is hidden; take it back on return
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible' && button.classList.contains('on') && !lock) request();
  });
}
