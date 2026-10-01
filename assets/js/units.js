//recipe pages: show metric amounts as freedom units, converted in the browser from the metric text
//the same rules as scripts/units.py, which does it for the freedom edition of the book
(function () {
var FRACTION_VALUES = { '½': 0.5, '¼': 0.25, '¾': 0.75, '⅓': 1 / 3, '⅔': 2 / 3, '⅛': 0.125 };
var EIGHTHS = ['', '⅛', '¼', '⅜', '½', '⅝', '¾', '⅞'];
var NUMBER = '(?:\\d+(?:\\.\\d+)?(?:\\s?[½¼¾⅓⅔⅛])?|[½¼¾⅓⅔⅛])';
var AMOUNT = new RegExp('(^|[^\\w.])(' + NUMBER + ')(?:(\\s?(?:-|–|to)\\s?)(' + NUMBER + '))?(\\s?)(°C|kg|g|ml|litres?|liters?|cm|mm|l)(?![A-Za-z])', 'g');

function amountValue(text) {
  var match = /^(\d+(?:\.\d+)?)?\s?([½¼¾⅓⅔⅛])?$/.exec(text);
  return parseFloat(match[1] || 0) + (FRACTION_VALUES[match[2]] || 0);
}
function nearest(x, step) { return Math.floor(x / step + 0.5) * step; }
function showEighths(x) {
  var n = Math.round(x * 8), whole = Math.floor(n / 8);
  return (whole ? String(whole) : '') + EIGHTHS[n % 8];
}
function asWeight(grams) {
  var oz = grams / 28.3495;
  if (oz < 16) return showEighths(Math.max(nearest(oz, oz >= 4 ? 0.5 : 0.25), 0.25)) + ' oz';
  var whole = Math.round(oz), pounds = Math.floor(whole / 16), ounces = whole % 16;
  return pounds + ' lb' + (ounces ? ' ' + ounces + ' oz' : '');
}
function asVolume(ml) {
  if (ml >= 1000) return showEighths(nearest(ml / 946.353, 0.25)) + ' qt';
  var fl = ml / 29.5735;
  return showEighths(Math.max(nearest(fl, fl >= 1 ? 0.5 : 0.25), 0.25)) + ' fl oz';
}
function asLength(mm) {
  var inches = mm / 25.4, step = inches < 1 ? 0.125 : inches < 4 ? 0.25 : 0.5;
  return showEighths(Math.max(nearest(inches, step), 0.125)) + ' in';
}
function asTemperature(celsius) {
  var f = celsius * 9 / 5 + 32;
  return nearest(f, f >= 250 ? 25 : 5) + '°F';
}
//unit: [multiplier to the base value (g, ml, mm or °C), formatter]
var CONVERSIONS = {
  '°C': [1, asTemperature], g: [1, asWeight], kg: [1000, asWeight],
  ml: [1, asVolume], l: [1000, asVolume], litre: [1000, asVolume], litres: [1000, asVolume],
  liter: [1000, asVolume], liters: [1000, asVolume], cm: [10, asLength], mm: [1, asLength]
};

function toFreedom(text) {
  return text.replace(AMOUNT, function (all, before, first, between, second, space, unit) {
    if (unit === 'l' && space) return all;
    var rule = CONVERSIONS[unit], out = rule[1](amountValue(first) * rule[0]);
    if (second !== undefined) out += between + rule[1](amountValue(second) * rule[0]);
    return before + out;
  });
}

function setUpUnits(page) {
  var button = page.querySelector('.units-toggle');
  var body = page.querySelector('.recipe-body');
  if (!button || !body) return;
  var originals = new Map();
  var walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
  for (var node = walker.nextNode(); node; node = walker.nextNode()) {
    if (toFreedom(node.nodeValue) !== node.nodeValue) originals.set(node, node.nodeValue);
  }
  //nothing to convert on this recipe, so no toggle
  if (!originals.size) return;
  button.hidden = false;

  function set(freedom) {
    originals.forEach(function (text, node) { node.nodeValue = freedom ? toFreedom(text) : text; });
    button.setAttribute('aria-pressed', freedom);
    button.classList.toggle('on', freedom);
    try { localStorage.setItem('gitfood-units', freedom ? 'freedom' : 'metric'); } catch (e) { /*private mode*/ }
  }
  button.addEventListener('click', function () { set(!button.classList.contains('on')); });
  var saved = null;
  try { saved = localStorage.getItem('gitfood-units'); } catch (e) { saved = null; }
  if (saved === 'freedom') set(true);
}

if (typeof document !== 'undefined') document.addEventListener('DOMContentLoaded', function () {
  var recipe = document.querySelector('.recipe-page');
  if (recipe) setUpUnits(recipe);
});

if (typeof module !== 'undefined') module.exports = { toFreedom: toFreedom };
})();
