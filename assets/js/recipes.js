// Sortable, filterable recipe tables on the homepage and tag pages.
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('table.recipes').forEach(function (table) {
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
      var words = box.value.toLowerCase().split(/\s+/).filter(Boolean);
      var shown = 0;
      rows.forEach(function (row) {
        var text = row.textContent.toLowerCase();
        var match = words.every(function (w) { return text.indexOf(w) !== -1; });
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
      function sort() {
        var ascending = th.getAttribute('aria-sort') !== 'ascending';
        headers.forEach(function (h) { h.removeAttribute('aria-sort'); });
        th.setAttribute('aria-sort', ascending ? 'ascending' : 'descending');
        rows.sort(function (a, b) {
          var x = a.cells[col].textContent.trim(), y = b.cells[col].textContent.trim();
          if (!x || !y) return (!x) - (!y);  // blank dates last either way
          return ascending ? x.localeCompare(y) : y.localeCompare(x);
        });
        rows.forEach(function (row) { tbody.appendChild(row); });
      }
      th.addEventListener('click', sort);
      th.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); sort(); }
      });
    });
    headers[0].setAttribute('aria-sort', 'ascending');  // generated sorted by name
  });
});
