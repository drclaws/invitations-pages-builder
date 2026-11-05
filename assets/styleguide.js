/* Showcase script (styleguide.html).
 *
 * Reads the list of tokens straight from the design-system style sheet
 * (document.styleSheets -> :root rules -> --* properties) and shows their
 * computed values (getComputedStyle), recalculating them when the window
 * width changes. It configures nothing and is not part of the built site.
 *
 * Without this script the showcase still works: the components and the type
 * scale are static markup; only the token table is built by the script.
 */
(function () {
  'use strict';

  // The same first step as in the page script: progressive enhancement.
  document.documentElement.classList.add('js');

  var SOURCE = 'app.css'; // tokens come from the design system only, not from the showcase

  var GROUPS = [
    ['Reference widths and interpolation', /^--(vw-|fluid$|bp-)/],
    ['Colours', /^--color-/],
    ['Fonts', /^--(font-|line-height-|tracking-)/],
    ['Type scale', /^--text-/],
    ['Spacing', /^--(space-|flow-)/],
    ['Container', /^--container-/],
    ['Grid', /^--(grid-|gallery-columns|countdown-columns|countdown-gap|countdown-inline-|countdown-stack-)/],
    ['Radii, shadows, lines', /^--(radius-|shadow-|line-width|focus-ring|opacity-)/],
    ['Image aspect ratios and framing', /^--(ratio-|image-focus)/],
    ['Viewport height, cover, media height limit', /^--(viewport-|cover-height-|cover-min-|media-max-)/],
    ['Motion', /^--(duration-|ease-|reveal-|cover-distance|hover-scale)/],
    ['Accessibility and layers', /^--(tap-|z-|safe-inset-)/],
    ['Component tokens', /^--(media-play-|icon-|countdown-cell|schedule-|divider-|card-|btn-)/]
  ];
  var OTHER = 'Other';

  var COLOR_RE = /^(#[0-9a-f]{3,8}|rgba?\(|hsla?\()/i;

  /* For a custom property getComputedStyle returns the value as written
     (the whole clamp/calc), not a length. To show the computed value, the
     length is measured with a hidden probe: its width is set to var(--token)
     and the resolved width is read back. Units that depend on the font of a
     particular element (ch, em) are not resolved: the probe has its own font,
     and the number would differ from the one in the component, so the value
     as written is shown. The exception is the media query thresholds (--bp-*)
     in em: there em is the browser's default font size, and the probe
     measures them at font-size: medium. */
  var LENGTH_RE = /^(calc|clamp|min|max|env)\(|^-?[0-9.]+(px|rem|vw|vh|svh|dvh|lvh|vmin|vmax)$/;
  var MEDIA_EM_RE = /^--bp-/;
  var EM_RE = /^-?[0-9.]+em$/;
  /* A short value in rem/em is shown together with the pixels: "48em = 768px". */
  var RELATIVE_RE = /^-?[0-9.]+(rem|em)$/;
  var probe = null;

  function probeElement() {
    if (probe) return probe;
    probe = document.createElement('div');
    probe.setAttribute('aria-hidden', 'true');
    probe.style.position = 'absolute';
    probe.style.insetInlineStart = '0';
    probe.style.insetBlockStart = '0';
    probe.style.blockSize = '0';
    probe.style.visibility = 'hidden';
    probe.style.pointerEvents = 'none';
    document.body.appendChild(probe);
    return probe;
  }

  function resolveLength(name) {
    var node = probeElement();
    node.style.removeProperty('width');
    node.style.setProperty('font-size', MEDIA_EM_RE.test(name) ? 'medium' : 'inherit');
    node.style.setProperty('width', 'var(' + name + ')');
    var resolved = getComputedStyle(node).width;
    node.style.removeProperty('width');
    return /^-?[0-9.]+px$/.test(resolved) ? resolved : null;
  }

  /* Returns what to show in the table and the full value for the tooltip. */
  function readValue(css, name) {
    var raw = css.getPropertyValue(name).trim().replace(/\s+/g, ' ');
    var shown = raw;
    var title = '';
    if (LENGTH_RE.test(raw) || (MEDIA_EM_RE.test(name) && EM_RE.test(raw))) {
      var resolved = resolveLength(name);
      if (resolved && resolved !== raw) {
        shown = RELATIVE_RE.test(raw) ? raw + ' = ' + resolved : resolved;
        title = raw;
      }
    }
    return { raw: raw, shown: shown, title: title };
  }

  function groupOf(name) {
    for (var i = 0; i < GROUPS.length; i++) {
      if (GROUPS[i][1].test(name)) return GROUPS[i][0];
    }
    return OTHER;
  }

  /* Collects the custom property names from every :root rule of the source sheet. */
  function collectNames() {
    var names = [];
    var seen = Object.create(null);

    function walk(rules) {
      for (var i = 0; i < rules.length; i++) {
        var rule = rules[i];
        if (rule.style && rule.selectorText &&
            /(^|,)\s*:root\s*$/.test(rule.selectorText)) {
          for (var j = 0; j < rule.style.length; j++) {
            var prop = rule.style[j];
            if (prop.indexOf('--') === 0 && !seen[prop]) {
              seen[prop] = true;
              names.push(prop);
            }
          }
        }
        // @media, @supports and nested rules. The check has to come after
        // rule.style: an ordinary rule has cssRules too (nested CSS), just
        // empty.
        if (rule.cssRules && rule.cssRules.length) walk(rule.cssRules);
      }
    }

    var sheets = document.styleSheets;
    for (var s = 0; s < sheets.length; s++) {
      var sheet = sheets[s];
      if (!sheet.href || sheet.href.indexOf(SOURCE) === -1) continue;
      var rules;
      try {
        rules = sheet.cssRules;
      } catch (err) {
        continue; // just in case: a cross-origin sheet
      }
      if (rules) walk(rules);
    }
    return names;
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function build(container, names) {
    var css = getComputedStyle(document.documentElement);
    var known = Object.create(null);
    names.forEach(function (n) { known[n] = true; });

    var order = [];
    var buckets = Object.create(null);
    names.forEach(function (name) {
      var group = groupOf(name);
      if (!buckets[group]) {
        buckets[group] = [];
        order.push(group);
      }
      buckets[group].push(name);
    });

    var rows = [];
    order.forEach(function (group) {
      container.appendChild(el('h3', 'sg-tokens__group', group));
      var list = el('div', 'sg-tokens');
      buckets[group].forEach(function (name) {
        var row = el('div', 'sg-token');
        var value = readValue(css, name);

        var swatch = null;
        if (COLOR_RE.test(value.raw)) {
          swatch = el('span', 'sg-token__swatch');
          swatch.setAttribute('aria-hidden', 'true');
          swatch.style.backgroundColor = value.raw;
          row.appendChild(swatch);
        }

        row.appendChild(el('code', 'sg-token__name', name));
        var valueNode = el('code', 'sg-token__value', value.shown);
        if (value.title) valueNode.title = value.title;
        row.appendChild(valueNode);

        var badge = null;
        if (/-(mobile|desktop)$/.test(name)) {
          badge = 'reference value';
        } else if (known[name + '-mobile'] && known[name + '-desktop']) {
          badge = 'mobile/desktop';
        }
        if (badge) row.appendChild(el('span', 'sg-token__badge', badge));

        list.appendChild(row);
        rows.push({ name: name, valueNode: valueNode, swatch: swatch });
      });
      container.appendChild(list);
    });
    return rows;
  }

  function refresh(rows, meta) {
    var css = getComputedStyle(document.documentElement);
    rows.forEach(function (row) {
      var value = readValue(css, row.name);
      if (row.valueNode.textContent !== value.shown) {
        row.valueNode.textContent = value.shown;
      }
      if (value.title) row.valueNode.title = value.title;
      if (row.swatch) row.swatch.style.backgroundColor = value.raw;
    });
    if (meta) {
      var width = document.documentElement.clientWidth;
      meta.textContent = '';
      meta.appendChild(el('span', null, 'viewport width: ' + width + ' px'));
      // The layout breakpoint is read from the --bp-layout token, not hard-coded.
      var bp = css.getPropertyValue('--bp-layout').trim();
      var desktop = bp ? window.matchMedia('(min-width: ' + bp + ')').matches : false;
      meta.appendChild(el('span', null, 'layout: ' + (desktop ? 'desktop' : 'mobile') +
        (bp ? ' (breakpoint ' + bp + ')' : '')));
      meta.appendChild(el('span', null, 'tokens: ' + rows.length));
    }
  }

  /* The "Font size check" switch: sets an attribute on <html> by which the
     showcase style sheet changes the font size of the root element. */
  function initFontScale(onChange) {
    var group = document.querySelector('[data-font-scale]');
    if (!group) return;
    var buttons = group.querySelectorAll('[data-font-scale-value]');
    group.addEventListener('click', function (event) {
      var button = event.target.closest('[data-font-scale-value]');
      if (!button) return;
      var scale = button.getAttribute('data-font-scale-value');
      if (scale === '100') {
        document.documentElement.removeAttribute('data-sg-font-scale');
      } else {
        document.documentElement.setAttribute('data-sg-font-scale', scale);
      }
      for (var i = 0; i < buttons.length; i++) {
        var pressed = buttons[i] === button;
        buttons[i].setAttribute('aria-pressed', pressed ? 'true' : 'false');
        buttons[i].classList.toggle('btn--primary', pressed);
        buttons[i].classList.toggle('btn--secondary', !pressed);
      }
      onChange();
    });
  }

  function init() {
    var container = document.querySelector('[data-token-table]');
    if (!container) return;
    var meta = document.querySelector('[data-token-meta]');
    var names = collectNames();
    if (!names.length) {
      container.appendChild(el('p', 'sg-note',
        'The tokens could not be read from the style sheet. Open the page ' +
        'through a local HTTP server, not as file://.'));
      return;
    }
    var rows = build(container, names);
    refresh(rows, meta);

    initFontScale(function () { refresh(rows, meta); });

    var pending = false;
    window.addEventListener('resize', function () {
      if (pending) return;
      pending = true;
      window.requestAnimationFrame(function () {
        pending = false;
        refresh(rows, meta);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}());
