/* The invitation page script: progressive enhancement over finished HTML.

   File layout:
     1. The js class on <html> is the first action; the hidden initial
        states of the animations apply only under it. If the script does
        not load, everything is visible at once.
     2. The module registry: register(name, init). Every init runs after the
        document is parsed, in its own try/catch — one module's error does
        not switch the others off.
     3. The modules. They hook only onto data attributes; the is-* classes
        and the marker classes on <html> are states for the styles
        (section 7 of app.css).

   No build step and no dependencies; compatible with the CSP
   script-src 'self' (no inline code, eval or new Function). The page
   content is available without the script too. */
(function () {
  'use strict';

  document.documentElement.classList.add('js');

  var root = document.documentElement;


  /* ==========================================================================
     Module registry
     ========================================================================== */

  var modules = [];
  var started = false;

  /* Only the module name and the error type — no page data. */
  function report(name, error) {
    console.warn('app: module "' + name + '" failed (' +
      (error && error.name ? error.name : 'Error') + ')');
  }

  /* init(document) is called once, when the DOM is parsed. */
  function register(name, init) {
    modules.push({ name: name, init: init });
  }

  function start() {
    if (started) {
      return;
    }
    started = true;
    modules.forEach(function (module) {
      try {
        module.init(document);
      } catch (error) {
        report(module.name, error);
      }
    });
  }

  /* The script loads with defer: DOMContentLoaded is still ahead. The other
     branches are a safety net for another way of loading. The subscription
     comes before the module code: a failure while declaring a later module
     does not cancel the start of the earlier ones. */
  document.addEventListener('DOMContentLoaded', start);
  window.addEventListener('load', start);
  if (document.readyState === 'complete') {
    setTimeout(start, 0);
  }

  function prefersReducedMotion() {
    return typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }


  /* ==========================================================================
     The cover module — the cover animation on load
     --------------------------------------------------------------------------
     The animation itself is in CSS, under the cover-animate marker on
     <html>. The marker is set only if the page has not been painted yet:
     otherwise a cover already in view would vanish and appear again.
     ========================================================================== */

  var COVER_LATE_MS = 1000;

  function alreadyPainted() {
    var perf = window.performance;
    if (!perf || typeof perf.now !== 'function') {
      return true;
    }
    var types = window.PerformanceObserver && window.PerformanceObserver.supportedEntryTypes;
    if (types && types.indexOf('paint') !== -1 && typeof perf.getEntriesByType === 'function') {
      return perf.getEntriesByType('paint').length > 0;
    }
    /* No Paint Timing: judge by the time since the navigation started. */
    return perf.now() > COVER_LATE_MS;
  }

  register('cover', function () {
    if (prefersReducedMotion() || alreadyPainted()) {
      return;
    }
    root.classList.add('cover-animate');
  });


  /* ==========================================================================
     The coverBar module — collapsing the cover [data-cover] into the bar
     [data-cover-bar]
     --------------------------------------------------------------------------
     The bar and all the collapse rules are in CSS, under the cover-bar-on
     marker on <html>; without the marker there is no bar and the cover
     stays still. Where scroll timelines exist, CSS computes the progress
     --cover-progress (0…1) itself, and the module only sets the marker. The
     condition is the same as the @supports in app.css. Otherwise the module
     computes the progress from the cover position at most once a frame and
     writes it through CSSOM on the cover and the bar. Under reduced motion
     the progress is a step: 0 or 1. Any error removes the marker and the
     written values — the page returns to its look without the module.
     The module has no strings of its own; it leaves the cover module alone.
     ========================================================================== */

  var COVER_BAR_TIMELINES = '(animation-timeline: --a) and (timeline-scope: --a)';

  register('coverBar', function (doc) {
    var cover = doc.querySelector('[data-cover]');
    var bar = doc.querySelector('[data-cover-bar]');
    if (!cover || !bar) {
      return;
    }
    var css = window.CSS;
    if (css && typeof css.supports === 'function' && css.supports(COVER_BAR_TIMELINES)) {
      root.classList.add('cover-bar-on');
      return;
    }
    if (typeof window.requestAnimationFrame !== 'function') {
      return;
    }

    var reduced = typeof window.matchMedia === 'function' ?
      window.matchMedia('(prefers-reduced-motion: reduce)') : null;
    var nodes = [cover, bar];
    var frame = 0;
    var last = '';

    /* 0 — the cover top at the viewport top, 1 — a bar-high strip of the
       cover is left. */
    function progress() {
      var box = cover.getBoundingClientRect();
      var span = box.height - bar.offsetHeight;
      var value = span > 0 ? Math.min(1, Math.max(0, -box.top / span)) : 1;
      if (reduced && reduced.matches) {
        value = value >= 1 ? 1 : 0;
      }
      return String(Math.round(value * 1000) / 1000);
    }

    function stop() {
      window.removeEventListener('scroll', onChange, true);
      window.removeEventListener('resize', onChange);
      window.removeEventListener('load', onChange);
      if (frame) {
        window.cancelAnimationFrame(frame);
        frame = 0;
      }
      root.classList.remove('cover-bar-on');
      nodes.forEach(function (node) {
        node.style.removeProperty('--cover-progress');
        if (!node.getAttribute('style')) {
          node.removeAttribute('style');
        }
      });
    }

    function update() {
      frame = 0;
      try {
        var value = progress();
        if (value !== last) {
          last = value;
          nodes.forEach(function (node) {
            node.style.setProperty('--cover-progress', value);
          });
        }
      } catch (error) {
        stop();
        report('coverBar', error);
      }
    }

    function onChange() {
      if (!frame) {
        frame = window.requestAnimationFrame(update);
      }
    }

    /* The marker first: without it the bar is hidden and its height cannot
       be measured. The subscription comes before the first computation: on
       an error stop() removes it. On a touch screen body scrolls the
       invitation page (app.css, section 3), and an element's scroll event
       does not bubble up to window — the listener catches it in the
       capture phase, and the document scroll (desktop) as well. */
    root.classList.add('cover-bar-on');
    window.addEventListener('scroll', onChange, { passive: true, capture: true });
    window.addEventListener('resize', onChange);
    window.addEventListener('load', onChange);
    update();
  });


  /* ==========================================================================
     The events module — the event switcher [data-events]
     --------------------------------------------------------------------------
     Without the script the event cards follow one another by start time,
     and the tab list is hidden with the hidden attribute in the markup.
     With the script they become tabs following the ARIA Tabs pattern: one
     card is visible; the arrows (wrapping around), Home and End, selection
     follows focus, tabindex="0" only on the selected tab. The script sets
     the roles and the panel relations, taking the ids from the markup
     (aria-controls). The tab count goes to the styles as the --events-count
     variable through CSSOM.

     Time: a card's data-events-start and data-events-end are ISO with an
     offset; the build always fills in the end. Moments are compared as
     absolute times, so the guest's time zone does not matter. An event is
     past once its end has come, and in progress between its start and its
     end. The marks are [data-events-when="past|now"] elements in the
     markup: the script only removes and sets hidden and the is-past /
     is-now classes on the tab and the card. The module has no texts of its
     own.

     The default tab comes from defaultTab(): the primary event (the card id
     in data-events-primary) until it is past; then the nearest event that
     is not past; once all are past, the last one. Without a valid time,
     the primary one, otherwise the first.

     The recheck runs at the nearest event boundary, but at least once an
     hour, and on return to the browser tab. The recheck leaves the selected
     tab alone if the guest picked it themselves, while focus is inside the
     widget (the switch catches up when focus leaves) and while a modal
     dialog is open (the check repeats until the dialog is closed). Any
     error returns the markup to its look without the script.

     The module is declared before reveal and starts before it: hiding the
     cards shortens the page, and reveal must measure the blocks in the
     final layout — otherwise, on a reload in the middle of the page, a
     block actually on screen would fade in. parseTarget from the countdown
     module parses the times (by the time the modules start, the whole file
     has run).
     ========================================================================== */

  var EVENTS_RECHECK_MS = 3600000;    /* recheck at least once an hour */
  var EVENTS_MODAL_RETRY_MS = 1000;   /* while a dialog is open, wait for it to close */
  var EVENTS_EDGE_MS = 50;            /* recheck just after a boundary, not before it */
  var EVENTS_STEPS = { ArrowLeft: -1, ArrowUp: -1, ArrowRight: 1, ArrowDown: 1 };

  /* The viewer or another <dialog> is open: the tab under it does not
     switch. */
  function modalOpen() {
    if (root.classList.contains('is-lightbox-open')) {
      return true;
    }
    var dialogs = document.getElementsByTagName('dialog');
    for (var i = 0; i < dialogs.length; i += 1) {
      if (dialogs[i].open) {
        return true;
      }
    }
    return false;
  }

  /* The time mark on a tab or a card: 'past', 'now' or ''. */
  function markTime(node, state) {
    node.classList.toggle('is-past', state === 'past');
    node.classList.toggle('is-now', state === 'now');
    Array.prototype.forEach.call(node.querySelectorAll('[data-events-when]'), function (label) {
      label.hidden = label.getAttribute('data-events-when') !== state;
    });
  }

  function startEvents(widget) {
    var tablist = widget.querySelector('[data-events-tablist]');
    var tabs = tablist ? Array.prototype.slice.call(tablist.querySelectorAll('[data-events-tab]')) : [];
    var all = Array.prototype.slice.call(widget.querySelectorAll('[data-events-panel]'));
    var panels = tabs.map(function (tab) {
      var id = tab.getAttribute('aria-controls');
      return all.filter(function (panel) {
        return panel.id === id;
      })[0];
    });
    /* One card: nothing to switch; a card without a tab or a tab without a
       card: unexpected markup, everything stays visible. */
    if (tabs.length < 2 || panels.length !== all.length || panels.indexOf(undefined) !== -1) {
      return;
    }

    var starts = panels.map(function (panel) {
      return parseTarget(panel.getAttribute('data-events-start'));
    });
    var ends = panels.map(function (panel) {
      return parseTarget(panel.getAttribute('data-events-end'));
    });
    var timed = !starts.concat(ends).some(isNaN);
    var labelledBy = panels.map(function (panel) {
      return panel.getAttribute('aria-labelledby');
    });
    var primary = panels.map(function (panel) {
      return panel.id;
    }).indexOf(widget.getAttribute('data-events-primary'));

    var current = -1;
    var chosen = false;   /* the guest picked the tab themselves: the recheck keeps it */
    var timer = 0;

    function select(index, focus) {
      current = index;
      tabs.forEach(function (tab, i) {
        var on = i === index;
        tab.setAttribute('aria-selected', on ? 'true' : 'false');
        tab.tabIndex = on ? 0 : -1;
        panels[i].hidden = !on;
      });
      if (focus) {
        tabs[index].focus();
      }
    }

    /* Sets the marks for the moment now and returns the index of the
       nearest event that is not past (-1 when all are past). */
    function mark(now) {
      var next = -1;
      panels.forEach(function (panel, i) {
        var state = now >= ends[i] ? 'past' : now >= starts[i] ? 'now' : '';
        markTime(tabs[i], state);
        markTime(panel, state);
        if (state !== 'past' && next === -1) {
          next = i;
        }
      });
      return next;
    }

    /* The default tab is chosen here and only here; it also updates the
       marks. */
    function defaultTab(now) {
      if (!timed) {
        return Math.max(primary, 0);
      }
      var next = mark(now);
      if (primary !== -1 && now < ends[primary]) {
        return primary;
      }
      return next === -1 ? panels.length - 1 : next;
    }

    /* The next recheck is at the nearest boundary; in a background tab the
       chain does not run (visibilitychange restarts it). */
    function schedule(now, soon) {
      clearTimeout(timer);
      timer = 0;
      if (document.hidden) {
        return;
      }
      var wait = soon ? EVENTS_MODAL_RETRY_MS : EVENTS_RECHECK_MS;
      starts.concat(ends).forEach(function (moment) {
        if (moment > now && moment - now < wait) {
          wait = moment - now;
        }
      });
      timer = setTimeout(onTime, wait + EVENTS_EDGE_MS);
    }

    function refresh() {
      var now = Date.now();
      var target = defaultTab(now);
      var pending = !chosen && target !== current;
      var modal = pending && modalOpen();
      if (pending && !modal && !widget.contains(document.activeElement)) {
        select(target, false);
      }
      schedule(now, modal);
    }

    /* The look without the script: the tab list hidden, all the cards
       visible, the roles and marks removed, the original relations back. */
    function restore() {
      clearTimeout(timer);
      timer = 0;
      tablist.hidden = true;
      tablist.style.removeProperty('--events-count');
      if (!tablist.getAttribute('style')) {
        tablist.removeAttribute('style');
      }
      panels.forEach(function (panel, i) {
        panel.hidden = false;
        panel.removeAttribute('role');
        panel.removeAttribute('tabindex');
        if (labelledBy[i]) {
          panel.setAttribute('aria-labelledby', labelledBy[i]);
        } else {
          panel.removeAttribute('aria-labelledby');
        }
        markTime(tabs[i], '');
        markTime(panel, '');
      });
      tablist.removeEventListener('keydown', onKeyDown);
      tablist.removeEventListener('click', onClick);
      widget.removeEventListener('focusout', onFocusOut);
      document.removeEventListener('visibilitychange', onTime);
      window.removeEventListener('pageshow', onTime);
    }

    function guarded(handler) {
      return function (event) {
        try {
          handler(event);
        } catch (error) {
          restore();
          report('events', error);
        }
      };
    }

    var onTime = guarded(function () {
      if (timed) {
        refresh();
      }
    });

    var onClick = guarded(function (event) {
      var tab = event.target && typeof event.target.closest === 'function' ?
        event.target.closest('[data-events-tab]') : null;
      var at = tabs.indexOf(tab);
      if (at !== -1) {
        chosen = true;
        select(at, false);
      }
    });

    var onKeyDown = guarded(function (event) {
      var at = tabs.indexOf(event.target);
      if (at === -1 || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
        return;
      }
      var last = tabs.length - 1;
      var step = EVENTS_STEPS[event.key];
      var to = event.key === 'Home' ? 0 : event.key === 'End' ? last :
        typeof step === 'number' ? (at + step + tabs.length) % tabs.length : -1;
      if (to === -1) {
        return;
      }
      event.preventDefault();
      chosen = true;
      select(to, true);
    });

    /* Focus has left the widget: a deferred switch can happen. */
    var onFocusOut = guarded(function (event) {
      if (timed && !chosen && !widget.contains(event.relatedTarget)) {
        clearTimeout(timer);
        timer = setTimeout(onTime, 0);
      }
    });

    try {
      panels.forEach(function (panel, i) {
        panel.setAttribute('role', 'tabpanel');
        panel.setAttribute('tabindex', '0');
        panel.setAttribute('aria-labelledby', tabs[i].id);
      });
      tablist.style.setProperty('--events-count', String(tabs.length));
      var now = Date.now();
      select(defaultTab(now), false);
      tablist.addEventListener('keydown', onKeyDown);
      tablist.addEventListener('click', onClick);
      if (timed) {
        widget.addEventListener('focusout', onFocusOut);
        document.addEventListener('visibilitychange', onTime);
        window.addEventListener('pageshow', onTime);
        schedule(now, false);
      }
      tablist.hidden = false;
    } catch (error) {
      restore();
      throw error;
    }
  }

  register('events', function (doc) {
    Array.prototype.forEach.call(doc.querySelectorAll('[data-events]'), function (widget) {
      try {
        startEvents(widget);
      } catch (error) {
        report('events', error);
      }
    });
  });


  /* ==========================================================================
     The reveal module — revealing [data-reveal] blocks on scroll
     --------------------------------------------------------------------------
     The hidden state applies only under the reveal-on marker on <html>; the
     marker is set as the last step and removed on any error. A revealed
     block gets is-revealed and is no longer observed; when its reveal
     transition ends it gets is-settled: from then on the transition and the
     cascade delay do not apply and do not get in the way of the element's
     own transitions.
     ========================================================================== */

  /* The share of the screen height a block must enter before it appears.
     0: the reveal starts with the first visible pixel; otherwise a strip at
     the bottom edge of the screen shows a block that is on screen but
     empty. */
  var REVEAL_INSET = 0;
  var REVEAL_MARGIN = '0px 0px -' + (REVEAL_INSET * 100) + '% 0px';
  var REVEAL_STAGGER_MAX = 4;   /* cascade delay limit within one group */
  var REVEAL_SETTLE_MS = 2000;  /* safety net if transitionend never comes */

  register('reveal', function (doc) {
    var pending = Array.prototype.slice.call(doc.querySelectorAll('[data-reveal]'));
    if (!pending.length || typeof window.IntersectionObserver !== 'function' ||
        prefersReducedMotion()) {
      return; /* no marker: everything is visible */
    }

    var observer = null;
    var frame = 0;

    function viewportHeight() {
      return window.innerHeight || root.clientHeight;
    }

    /* The reveal is over: drop the transition, the cascade delay and its own
       listeners. */
    function settle(element) {
      if (element.classList.contains('is-settled')) {
        return;
      }
      element.classList.add('is-settled');
      element.style.removeProperty('--reveal-index');
      if (!element.getAttribute('style')) {
        element.removeAttribute('style');
      }
    }

    /* The end of a reveal is only the real end of the block's own opacity
       transition. During scrolling Chromium sends a stray transitionend
       with elapsedTime 0 in the first frame of the transition (a shift of
       its start time); accepting it would make is-settled drop the
       transition mid-reveal, and where that cuts the transition short the
       block would pop in with a jump. */
    function isRevealEnd(event, element) {
      if (event.target !== element) {
        return false; /* a transition of a nested element */
      }
      if (event.type === 'transitioncancel') {
        return true;
      }
      return event.propertyName === 'opacity' && event.elapsedTime > 0;
    }

    function settleLater(element) {
      var timer = 0;
      function done(event) {
        if (event && !isRevealEnd(event, element)) {
          return;
        }
        clearTimeout(timer);
        element.removeEventListener('transitionend', done);
        element.removeEventListener('transitioncancel', done);
        settle(element);
      }
      element.addEventListener('transitionend', done);
      element.addEventListener('transitioncancel', done);
      timer = setTimeout(done, REVEAL_SETTLE_MS);
    }

    /* order: the place in the group revealed at the same time; instant: no
       transition. */
    function show(element, order, instant) {
      var at = pending.indexOf(element);
      if (at === -1) {
        return;
      }
      pending.splice(at, 1);
      if (observer) {
        observer.unobserve(element);
      }
      if (instant) {
        settle(element);
      } else {
        if (order > 0) {
          element.style.setProperty('--reveal-index', String(Math.min(order, REVEAL_STAGGER_MAX)));
        }
        settleLater(element);
      }
      element.classList.add('is-revealed');
      if (!pending.length) {
        finish();
      }
    }

    function finish() {
      if (observer) {
        observer.disconnect();
        observer = null;
      }
      if (frame && typeof window.cancelAnimationFrame === 'function') {
        window.cancelAnimationFrame(frame);
      }
      frame = 0;
      doc.removeEventListener('focusin', onFocusIn);
      window.removeEventListener('scroll', onViewportChange, true);
      window.removeEventListener('resize', onViewportChange);
      window.removeEventListener('orientationchange', onViewportChange);
      doc.removeEventListener('visibilitychange', onVisibilityChange);
      window.removeEventListener('pageshow', sweep);
    }

    function fail() {
      root.classList.remove('reveal-on');
      pending = [];
      finish();
    }

    /* Wraps the event handlers: after a failure everything stays visible. */
    function guarded(handler) {
      return function (argument) {
        try {
          handler(argument);
        } catch (error) {
          fail();
          report('reveal', error);
        }
      };
    }

    /* Shows everything already on screen or above it (fast scrolling, a
       jump to the end of the page, a return from a background tab). inset
       is the share of the screen height at the bottom that a block still
       has to enter; 0 when there is none. */
    function sweepWithin(inset) {
      var limit = viewportHeight() * (1 - inset);
      var order = 0;
      pending.slice().forEach(function (element) {
        var rect = element.getBoundingClientRect();
        if (rect.bottom <= 0) {
          show(element, 0, true);
        } else if (rect.top < limit) {
          show(element, order, false);
          order += 1;
        }
      });
    }

    var sweep = guarded(function () {
      sweepWithin(0);
    });

    /* Keyboard focus inside a block that is hidden: show it at once. */
    var onFocusIn = guarded(function (event) {
      var node = event.target;
      while (node && node.nodeType === 1) {
        if (node.hasAttribute('data-reveal')) {
          show(node, 0, true);
        }
        node = node.parentElement;
      }
    });

    /* Scrolling, a resize or an orientation change: the check does not
       depend on whether the observer callback came, and runs at most once a
       frame. The boundary is the observer's; at the very end of the page a
       block may never reach it, so there it is dropped. */
    /* The end of the page is body's if body scrolls (the invitation page on
       a touch screen, app.css section 3), otherwise the document's. The
       document is then as large as the viewport and always "at the end" —
       do not ask it. */
    function atEnd() {
      var body = doc.body;
      if (window.getComputedStyle(body).overflowY !== 'visible') {
        return body.scrollTop + body.clientHeight >= body.scrollHeight - 2;
      }
      return viewportHeight() + window.pageYOffset >= root.scrollHeight - 2;
    }

    var onFrame = guarded(function () {
      frame = 0;
      sweepWithin(atEnd() ? 0 : REVEAL_INSET);
    });

    function onViewportChange() {
      if (frame) {
        return;
      }
      if (typeof window.requestAnimationFrame === 'function') {
        frame = window.requestAnimationFrame(onFrame);
      } else {
        onFrame();
      }
    }

    var onVisibilityChange = guarded(function () {
      if (!doc.hidden) {
        sweep();
      }
    });

    var onIntersect = guarded(function (entries) {
      var order = 0;
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          show(entry.target, order, false);
          order += 1;
        }
      });
      /* Blocks that the scroll jumped over give no intersection. */
      var passed = pending.filter(function (element) {
        return element.getBoundingClientRect().bottom <= 0;
      });
      passed.forEach(function (element) {
        show(element, 0, true);
      });
    });

    try {
      /* Blocks visible on load are marked before the hidden state switches
         on: they are never hidden, so they do not flicker. */
      var limit = viewportHeight();
      pending.slice().forEach(function (element) {
        if (element.getBoundingClientRect().top < limit) {
          show(element, 0, true);
        }
      });
      if (!pending.length) {
        return;
      }

      observer = new window.IntersectionObserver(onIntersect, {
        rootMargin: REVEAL_MARGIN,
        threshold: 0
      });
      pending.forEach(function (element) {
        observer.observe(element);
      });
      doc.addEventListener('focusin', onFocusIn);
      /* Capture: the body scroll (the invitation page on a touch screen)
         does not bubble up to window. */
      window.addEventListener('scroll', onViewportChange, { passive: true, capture: true });
      window.addEventListener('resize', onViewportChange);
      window.addEventListener('orientationchange', onViewportChange);
      doc.addEventListener('visibilitychange', onVisibilityChange);
      window.addEventListener('pageshow', sweep);

      root.classList.add('reveal-on');
    } catch (error) {
      fail();
      throw error;
    }
  });


  /* ==========================================================================
     The countdown module — the countdown timer [data-countdown="<dateISO>"]
     --------------------------------------------------------------------------
     The container is hidden in the markup (hidden); the date as text always
     stays next to it. With an invalid date or an event that has begun, the
     container stays hidden.
     ========================================================================== */

  var ISO_WITH_OFFSET = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?(Z|[+-]\d{2}:\d{2})$/;

  var COUNTDOWN_UNITS = [
    { name: 'days', seconds: 86400, pad: false, forms: ['день', 'дня', 'дней'] },
    { name: 'hours', seconds: 3600, pad: true, forms: ['час', 'часа', 'часов'] },
    { name: 'minutes', seconds: 60, pad: true, forms: ['минута', 'минуты', 'минут'] },
    { name: 'seconds', seconds: 1, pad: true, forms: ['секунда', 'секунды', 'секунд'] }
  ];

  /* The Russian word form for a number: forms = [one, two to four, many]. */
  function pluralRu(count, forms) {
    var n = Math.abs(count) % 100;
    var last = n % 10;
    if (n >= 11 && n <= 14) {
      return forms[2];
    }
    if (last === 1) {
      return forms[0];
    }
    if (last >= 2 && last <= 4) {
      return forms[1];
    }
    return forms[2];
  }

  function parseTarget(value) {
    var text = (value || '').trim();
    if (!ISO_WITH_OFFSET.test(text)) {
      return NaN;
    }
    return Date.parse(text);
  }

  function setText(node, text) {
    if (node && node.textContent !== text) {
      node.textContent = text;
    }
  }

  function startCountdown(container) {
    var target = parseTarget(container.getAttribute('data-countdown'));
    if (isNaN(target)) {
      return;
    }

    var cells = COUNTDOWN_UNITS.map(function (unit) {
      var cell = container.querySelector('[data-countdown-unit="' + unit.name + '"]');
      return {
        unit: unit,
        value: cell && cell.querySelector('[data-countdown-value]'),
        label: cell && cell.querySelector('[data-countdown-label]')
      };
    });
    if (cells.some(function (cell) { return !cell.value; })) {
      return;
    }

    var timer = 0;
    var over = false;

    function stop() {
      if (timer) {
        clearTimeout(timer);
        timer = 0;
      }
    }

    /* The countdown is not needed: the date as text remains. */
    function finish() {
      stop();
      over = true;
      container.hidden = true;
      document.removeEventListener('visibilitychange', onVisibilityChange);
      window.removeEventListener('pageshow', tick);
    }

    function update() {
      stop();
      var left = target - Date.now();
      if (left <= 0) {
        /* The event has begun: no zeros are shown. */
        finish();
        return;
      }

      /* Rounding up: the last second shows "1", then the countdown hides. */
      var rest = Math.ceil(left / 1000);
      cells.forEach(function (cell) {
        var amount = Math.floor(rest / cell.unit.seconds);
        rest -= amount * cell.unit.seconds;
        var text = String(amount);
        setText(cell.value, cell.unit.pad && amount < 10 ? '0' + text : text);
        setText(cell.label, pluralRu(amount, cell.unit.forms));
      });
      container.hidden = false;

      /* The next update is at the second boundary, always counted from
         Date.now(): the error does not add up. In a background tab the
         chain does not run. */
      if (!document.hidden) {
        timer = setTimeout(tick, (left % 1000) || 1000);
      }
    }

    /* Called both from the timer and from events — outside the registry's
       try/catch: on any error the countdown stops and the container hides. */
    function tick() {
      try {
        update();
      } catch (error) {
        finish();
        report('countdown', error);
      }
    }

    function onVisibilityChange() {
      if (over) {
        return;
      }
      if (document.hidden) {
        stop();
      } else {
        tick();
      }
    }

    document.addEventListener('visibilitychange', onVisibilityChange);
    window.addEventListener('pageshow', tick);
    tick();
  }

  /* A page may have several countdowns (a date widget in several sections):
     a failure of one does not affect the others. */
  register('countdown', function (doc) {
    Array.prototype.forEach.call(doc.querySelectorAll('[data-countdown]'), function (container) {
      try {
        startCountdown(container);
      } catch (error) {
        container.hidden = true;
        report('countdown', error);
      }
    });
  });


  /* ==========================================================================
     The gallery module — the photo and video viewer for a[data-lightbox]
     links
     --------------------------------------------------------------------------
     A tile link leads to a file and without the script opens it as usual:
     the browser shows a picture and plays a video in its own player. The
     links inside one [data-gallery] are swiped through as a group; a link
     outside [data-gallery] is a single item without arrows or a counter.

     A video is marked on its tile: data-media="video" (href is the video
     file), data-media-poster is the poster, data-media-ratio is the frame
     ratio "w / h" before the metadata loads.

     The dialog is a native <dialog> opened with showModal(): the browser
     provides the top layer, focus inside the dialog and closing with Esc
     (and the Back button on Android); the history does not change. Without
     showModal the module does not switch on. The dialog is created on the
     first opening; on any error the module switches off, and the link
     navigation is not cancelled.

     Videos play in a single <video controls> for the whole dialog, with
     the browser's native panel: at most one video plays at a time. Playback
     starts with play() called synchronously in the tile's press handler
     (a user gesture: without one iOS and in-app browsers give no sound). A
     video reached by swiping does not request its file and does not start
     by itself; leaving it or closing the dialog pauses it and aborts the
     download.
     ========================================================================== */

  var SVG_NS = 'http://www.w3.org/2000/svg';
  var LIGHTBOX_ICONS = {
    close: 'M6 6 18 18M18 6 6 18',
    prev: 'M15 5 8 12 15 19',
    next: 'M9 5 16 12 9 19'
  };
  var LIGHTBOX_TEXT = {
    photos: 'Просмотр фотографий',
    mixed: 'Просмотр фото и видео',
    image: 'Просмотр изображения',
    video: 'Просмотр видео',
    close: 'Закрыть',
    prev: 'Предыдущая фотография',
    next: 'Следующая фотография',
    prevItem: 'Назад',
    nextItem: 'Вперёд',
    itemImage: 'Фотография',
    itemVideo: 'Видео',
    loading: 'Загрузка…',
    error: 'Не удалось загрузить изображение.',
    videoError: 'Не удалось загрузить видео.'
  };
  var SWIPE_MIN = 48;         /* horizontal px for a gesture to count as a swipe */
  var SWIPE_RATIO = 1.5;      /* the horizontal must dominate the vertical */
  var SWIPE_CLICK_MS = 400;   /* a click right after a gesture does not close the dialog */
  var LOADING_NOTE_MS = 300;  /* the loading note only when the file is not cached */
  var ZOOMED_SCALE = 1.01;    /* the page is pinch-zoomed */
  var HAVE_NOTHING = 0;       /* readyState of a video with nothing loaded yet */
  /* The frame ratio from the markup: "w / h", whole numbers above zero. */
  var RATIO_RE = /^\s*[1-9]\d*\s*\/\s*[1-9]\d*\s*$/;

  function createElement(tag, className) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    return node;
  }

  function createIconButton(kind) {
    var button = createElement('button', 'lightbox__button lightbox__button--' + kind);
    button.type = 'button';
    button.setAttribute('aria-label', LIGHTBOX_TEXT[kind]);
    var icon = document.createElementNS(SVG_NS, 'svg');
    icon.setAttribute('class', 'lightbox__icon');
    icon.setAttribute('viewBox', '0 0 24 24');
    icon.setAttribute('aria-hidden', 'true');
    icon.setAttribute('focusable', 'false');
    var path = document.createElementNS(SVG_NS, 'path');
    path.setAttribute('d', LIGHTBOX_ICONS[kind]);
    icon.appendChild(path);
    button.appendChild(icon);
    return button;
  }

  /* The gallery ribbon: a link that gets focus is shown whole. The browser
     does not bring a partly visible item into view by itself; only the
     ribbon moves. */
  function revealInRibbon(event) {
    var link = event.target;
    var ribbon = link && typeof link.closest === 'function' &&
      link.hasAttribute('data-lightbox') ? link.closest('[data-gallery]') : null;
    if (!ribbon) {
      return;
    }
    var frame = ribbon.getBoundingClientRect();
    var box = (link.parentElement || link).getBoundingClientRect();
    if (box.left < frame.left) {
      ribbon.scrollLeft -= frame.left - box.left;
    } else if (box.right > frame.right) {
      ribbon.scrollLeft += box.right - frame.right;
    }
  }

  /* The viewer item for a tile link. label is the item's caption in the
     dialog: the alt of the tile picture, or for a video the accessible name
     of the tile itself. */
  function readItem(link) {
    var thumb = link.getElementsByTagName('img')[0];
    var alt = thumb ? thumb.alt : '';
    if (link.getAttribute('data-media') !== 'video') {
      return { href: link.getAttribute('href'), video: false, label: alt };
    }
    var ratio = link.getAttribute('data-media-ratio') || '';
    return {
      href: link.getAttribute('href'),
      video: true,
      poster: link.getAttribute('data-media-poster') || '',
      ratio: RATIO_RE.test(ratio) ? ratio.trim() : '',
      label: link.getAttribute('aria-label') || alt || LIGHTBOX_TEXT.itemVideo
    };
  }

  register('gallery', function (doc) {
    var links = doc.querySelectorAll('a[data-lightbox]');
    if (!links.length) {
      return;
    }
    doc.addEventListener('focusin', revealInRibbon);

    var Dialog = window.HTMLDialogElement;
    if (typeof Dialog !== 'function' || typeof Dialog.prototype.showModal !== 'function') {
      return; /* the links stay plain links to the files */
    }
    /* From here on a link opens the dialog, and screen readers are told so.
       Without the script there is no dialog and no attribute. */
    Array.prototype.forEach.call(links, function (link) {
      link.setAttribute('aria-haspopup', 'dialog');
    });

    var ui = null;      /* the dialog elements; created on the first opening */
    var items = [];     /* readItem() of every link of the open group */
    var index = 0;
    var opener = null;  /* the link that gets focus back */
    var loadingTimer = 0;
    var preloaded = [];
    var touches = 0;
    var swipe = null;   /* { id, x, y }: the start of a one-finger gesture */
    var swipedAt = 0;

    function lockScroll(on) {
      if (on) {
        /* Padding takes the place of the vanished scrollbar: the page under
           the dialog does not shift. The scrollbar belongs to the window, or
           to body if body scrolls (the invitation page on a touch screen,
           app.css section 3); body has no border. */
        var body = doc.body;
        var gap = window.innerWidth - root.clientWidth +
          (body ? body.offsetWidth - body.clientWidth : 0);
        if (gap > 0) {
          root.style.setProperty('--lightbox-scroll-gap', gap + 'px');
        }
        root.classList.add('is-lightbox-open');
      } else {
        root.classList.remove('is-lightbox-open');
        root.style.removeProperty('--lightbox-scroll-gap');
        if (!root.getAttribute('style')) {
          root.removeAttribute('style');
        }
      }
    }

    /* The video in the dialog is not needed: stop it and abort the
       download. Without a source load() resets the element, and the browser
       closes the connection. */
    function releaseVideo() {
      var video = ui && ui.video;
      if (!video || !video.getAttribute('src')) {
        return;
      }
      try {
        video.pause();
      } catch (ignored) { /* stopped already */ }
      video.removeAttribute('src');
      video.removeAttribute('poster');
      try {
        video.load();
      } catch (ignored) { /* no source: nothing to reset */ }
    }

    function fail(error) {
      doc.removeEventListener('click', onLinkClick);
      if (ui) {
        doc.removeEventListener('keydown', ui.onKey);
      }
      try {
        releaseVideo();
        if (ui && ui.dialog.open) {
          ui.dialog.close();
        }
      } catch (ignored) { /* the dialog is unavailable */ }
      lockScroll(false);
      report('gallery', error);
    }

    function guarded(handler) {
      return function (event) {
        try {
          handler(event);
        } catch (error) {
          fail(error);
        }
      };
    }

    function setDisabled(button, disabled) {
      if (disabled) {
        button.setAttribute('aria-disabled', 'true');
      } else {
        button.removeAttribute('aria-disabled');
      }
    }

    /* An image preloads a neighbour: the whole photo, or only the poster of
       a video. A video file is never requested ahead. */
    function preload(at) {
      var item = items[at];
      var src = item && (item.video ? item.poster : item.href);
      if (!src || preloaded.indexOf(src) !== -1) {
        return;
      }
      preloaded.push(src);
      var image = new window.Image();
      image.decoding = 'async';
      image.src = src;
    }

    /* A refusal by the browser (no gesture, an in-app browser policy) is not
       an error: the video stays on its poster and can be started from the
       panel. */
    function startVideo() {
      var promise = ui.video.play();
      if (promise && typeof promise.then === 'function') {
        promise.then(null, function () { /* did not start: waits for a press */ });
      }
    }

    function showVideo(item, autoplay) {
      var video = ui.video;
      ui.image.removeAttribute('src');
      ui.image.alt = '';
      if (item.ratio) {
        video.style.setProperty('--lightbox-ratio', item.ratio);
      } else {
        video.style.removeProperty('--lightbox-ratio');
      }
      video.setAttribute('aria-label', item.label);
      if (item.poster) {
        video.setAttribute('poster', item.poster);
      }
      video.setAttribute('src', item.href);
      if (autoplay) {
        startVideo();
      }
      preload(index + 1);
      preload(index - 1);
    }

    function showImage(item) {
      ui.dialog.classList.add('is-loading');
      ui.image.alt = item.label;
      ui.image.setAttribute('src', item.href);
      if (ui.image.complete && ui.image.naturalWidth > 0) {
        onImageLoad();
      } else {
        loadingTimer = setTimeout(function () {
          if (ui.dialog.classList.contains('is-loading')) {
            setText(ui.status, LIGHTBOX_TEXT.loading);
          }
        }, LOADING_NOTE_MS);
      }
    }

    /* autoplay only when show() is called from the tile's press handler. */
    function show(at, autoplay) {
      index = Math.max(0, Math.min(at, items.length - 1));
      var item = items[index];
      clearTimeout(loadingTimer);
      releaseVideo();
      ui.dialog.classList.remove('is-error', 'is-loading');
      ui.dialog.classList.toggle('is-video', item.video);
      setText(ui.status, '');
      setText(ui.count, (index + 1) + ' / ' + items.length);
      setText(ui.live, (item.video ? LIGHTBOX_TEXT.itemVideo : LIGHTBOX_TEXT.itemImage) +
        ' ' + (index + 1) + ' из ' + items.length);
      setDisabled(ui.prev, index === 0);
      setDisabled(ui.next, index === items.length - 1);
      if (item.video) {
        showVideo(item, autoplay);
      } else {
        showImage(item);
      }
    }

    function step(delta) {
      var at = index + delta;
      if (items.length > 1 && at >= 0 && at < items.length) {
        show(at, false);
      }
    }

    function onImageLoad() {
      if (!ui.image.getAttribute('src')) {
        return; /* a video is shown */
      }
      clearTimeout(loadingTimer);
      ui.dialog.classList.remove('is-loading');
      setText(ui.status, '');
      preload(index + 1);
      preload(index - 1);
    }

    function onImageError() {
      if (!ui.image.getAttribute('src')) {
        return;
      }
      clearTimeout(loadingTimer);
      ui.dialog.classList.remove('is-loading');
      ui.dialog.classList.add('is-error');
      setText(ui.status, LIGHTBOX_TEXT.error);
    }

    function onVideoError() {
      if (!ui.video.getAttribute('src')) {
        return; /* the source was removed on purpose (releaseVideo) */
      }
      ui.dialog.classList.add('is-error');
      setText(ui.status, LIGHTBOX_TEXT.videoError);
    }

    /* In Chrome the big ▶ button in the centre of the frame and a click on
       the frame do nothing while nothing of the video has loaded
       (preload="none"); the panel's ▶ button and Space work. Starting on a
       press on the frame happens only in this state: after it the browser
       handles a click on the frame itself (pause and resume), so there is
       no double toggle. This is a user gesture too, so sound is allowed. */
    function onVideoClick() {
      var video = ui.video;
      if (video.paused && video.readyState === HAVE_NOTHING && video.getAttribute('src')) {
        startVideo();
      }
    }

    function isZoomed() {
      return !!window.visualViewport && window.visualViewport.scale > ZOOMED_SCALE;
    }

    /* While the page is pinch-zoomed, gestures belong to the browser:
       otherwise a zoomed image could not be panned. */
    var onZoom = guarded(function () {
      ui.dialog.classList.toggle('is-zoomed', isZoomed());
    });

    /* The document, not the dialog, listens to keys while the dialog is
       open: after leaving full screen, Chrome moves focus to <body> within a
       second or two, and the dialog would stop getting keys. Keys pressed on
       the video itself (focus on it or in its panel) belong to the player:
       Space pauses, the arrows and Home/End seek, Tab moves through the
       panel buttons. */
    function onKeyDown(event) {
      if (!ui.dialog.open || event.target === ui.video ||
          event.altKey || event.ctrlKey || event.metaKey) {
        return;
      }
      var key = event.key;
      if (key === 'Tab') {
        /* Cycle through the dialog elements, also where the browser lets
           focus out into its own bar. The video is one stop: from there the
           browser leads Tab. */
        var stops = [ui.close, ui.video, ui.prev, ui.next].filter(function (node) {
          return node === ui.video ? ui.dialog.classList.contains('is-video') &&
            !ui.dialog.classList.contains('is-error') : !node.hidden;
        });
        var at = stops.indexOf(doc.activeElement);
        var last = stops.length - 1;
        if (at === -1 || (event.shiftKey ? at === 0 : at === last)) {
          event.preventDefault();
          stops[event.shiftKey ? last : 0].focus();
        }
        return;
      }
      if (event.shiftKey || items.length < 2) {
        return;
      }
      if (key === 'ArrowLeft' || key === 'ArrowRight') {
        step(key === 'ArrowLeft' ? -1 : 1);
      } else if (key === 'Home' || key === 'End') {
        show(key === 'Home' ? 0 : items.length - 1, false);
      } else {
        return;
      }
      event.preventDefault();
    }

    function onPointerDown(event) {
      if (event.pointerType === 'mouse') {
        return;
      }
      touches += 1;
      /* A gesture on the video frame is seeking on the native panel's track
         (its events come from the <video> itself), not a swipe. */
      swipe = touches === 1 && event.target !== ui.video ?
        { id: event.pointerId, x: event.clientX, y: event.clientY } : null;
    }

    function onPointerEnd(event) {
      if (event.pointerType === 'mouse') {
        return;
      }
      touches = Math.max(0, touches - 1);
      /* The finger lifted after the dialog closed (Esc during a gesture):
         nothing to swipe. */
      if (!ui.dialog.open) {
        swipe = null;
        return;
      }
      var from = swipe;
      if (!from || from.id !== event.pointerId) {
        return;
      }
      swipe = null;
      var dx = event.clientX - from.x;
      var dy = event.clientY - from.y;
      /* A vertical gesture or a gesture on a zoomed page is not a swipe. */
      if (event.type !== 'pointerup' || isZoomed() ||
          Math.abs(dx) < SWIPE_MIN || Math.abs(dx) < Math.abs(dy) * SWIPE_RATIO) {
        return;
      }
      swipedAt = Date.now();
      step(dx < 0 ? 1 : -1);
    }

    /* A click that misses the image and the buttons lands on the backdrop. */
    function onDialogClick(event) {
      var target = event.target;
      if (Date.now() - swipedAt > SWIPE_CLICK_MS &&
          (target === ui.dialog || target === ui.bar || target === ui.stage)) {
        ui.dialog.close();
      }
    }

    function onClose() {
      doc.removeEventListener('keydown', ui.onKey);
      clearTimeout(loadingTimer);
      releaseVideo();
      lockScroll(false);
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', onZoom);
      }
      ui.dialog.classList.remove('is-zoomed');
      var link = opener;
      opener = null;
      /* The tile may have been hidden while the dialog was open (another
         module switched its panel, for instance). Then focus does not go
         back to a hidden element, but does not stay in the closed dialog
         either. */
      if (link && typeof link.focus === 'function' && link.getClientRects().length) {
        link.focus({ preventScroll: true });
      } else if (ui.dialog.contains(doc.activeElement)) {
        doc.activeElement.blur();
      }
    }

    function build() {
      var dialog = createElement('dialog', 'lightbox on-overlay');
      var bar = createElement('div', 'lightbox__bar');
      var counter = createElement('p', 'lightbox__counter');
      var count = createElement('span');
      var live = createElement('span', 'visually-hidden');
      var close = createIconButton('close');
      var stage = createElement('div', 'lightbox__stage');
      var image = createElement('img', 'lightbox__image');
      var video = createElement('video', 'lightbox__video');
      var status = createElement('p', 'lightbox__status');
      var prev = createIconButton('prev');
      var next = createIconButton('next');

      count.setAttribute('aria-hidden', 'true');
      live.setAttribute('aria-live', 'polite');
      status.setAttribute('role', 'status');
      image.alt = '';
      image.decoding = 'async';
      image.draggable = false;
      /* The native panel; on an iPhone without playsinline the video would
         go straight into the system full-screen player. preload="none": a
         video reached by swiping loads not a single byte until it is
         pressed. */
      video.setAttribute('controls', '');
      video.setAttribute('playsinline', '');
      video.setAttribute('preload', 'none');
      video.setAttribute('disablepictureinpicture', '');

      counter.appendChild(count);
      counter.appendChild(live);
      bar.appendChild(counter);
      bar.appendChild(close);
      stage.appendChild(image);
      stage.appendChild(video);
      stage.appendChild(status);
      stage.appendChild(prev);
      stage.appendChild(next);
      dialog.appendChild(bar);
      dialog.appendChild(stage);

      image.addEventListener('load', guarded(onImageLoad));
      image.addEventListener('error', guarded(onImageError));
      video.addEventListener('error', guarded(onVideoError));
      video.addEventListener('click', guarded(onVideoClick));
      close.addEventListener('click', guarded(function () {
        dialog.close();
      }));
      prev.addEventListener('click', guarded(function () {
        step(-1);
      }));
      next.addEventListener('click', guarded(function () {
        step(1);
      }));
      dialog.addEventListener('click', guarded(onDialogClick));
      dialog.addEventListener('pointerdown', guarded(onPointerDown));
      dialog.addEventListener('pointerup', guarded(onPointerEnd));
      dialog.addEventListener('pointercancel', guarded(onPointerEnd));
      dialog.addEventListener('close', guarded(onClose));

      doc.body.appendChild(dialog);
      return {
        dialog: dialog, bar: bar, counter: counter, count: count, live: live,
        close: close, stage: stage, image: image, video: video, status: status,
        prev: prev, next: next, onKey: guarded(onKeyDown)
      };
    }

    /* The dialog label by the make-up of the group. */
    function dialogLabel() {
      var videos = items.filter(function (item) {
        return item.video;
      }).length;
      if (videos === items.length) {
        return LIGHTBOX_TEXT.video;
      }
      if (items.length < 2) {
        return LIGHTBOX_TEXT.image;
      }
      return LIGHTBOX_TEXT[videos ? 'mixed' : 'photos'];
    }

    function open(link) {
      var scope = link.closest('[data-gallery]');
      var group = scope ?
        Array.prototype.slice.call(scope.querySelectorAll('a[data-lightbox]')) : [link];
      if (!ui) {
        ui = build();
      }
      items = group.map(readItem);
      preloaded = [];
      touches = 0;
      swipe = null;
      opener = link;

      var single = items.length < 2;
      var photos = !items.some(function (item) {
        return item.video;
      });
      ui.counter.hidden = single;
      ui.prev.hidden = single;
      ui.next.hidden = single;
      ui.prev.setAttribute('aria-label', LIGHTBOX_TEXT[photos ? 'prev' : 'prevItem']);
      ui.next.setAttribute('aria-label', LIGHTBOX_TEXT[photos ? 'next' : 'nextItem']);
      ui.dialog.setAttribute('aria-label', dialogLabel());

      lockScroll(true);
      ui.dialog.showModal();
      doc.addEventListener('keydown', ui.onKey);
      /* Still inside the tile's press handler: play() in show() gets the
         user gesture. The counter changes inside the open dialog, so a
         screen reader announces it. */
      show(group.indexOf(link), true);
      /* For a video, focus goes to the video itself: Space pauses it rather
         than pressing the close button. */
      (items[index].video ? ui.video : ui.close).focus();
      if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', onZoom);
      }
      /* The page may have been pinch-zoomed before the dialog opened: no
         resize event will come, so the state is read at once. */
      onZoom();
    }

    function onLinkClick(event) {
      if (event.defaultPrevented || event.button !== 0 || event.altKey ||
          event.ctrlKey || event.metaKey || event.shiftKey ||
          !event.target || typeof event.target.closest !== 'function') {
        return; /* opening in a new tab and so on: as with a plain link */
      }
      var link = event.target.closest('a[data-lightbox]');
      if (!link || !link.getAttribute('href') || (ui && ui.dialog.open)) {
        return;
      }
      try {
        open(link);
        event.preventDefault();
      } catch (error) {
        fail(error); /* the navigation is not cancelled: the file opens as usual */
      }
    }

    doc.addEventListener('click', onLinkClick);
  });


  /* ==========================================================================
     Adding a module
     --------------------------------------------------------------------------
     Every module is a block of its own below this line, inside this same
     function:

       register('name', function (doc) {
         // find its elements by data attributes; no elements: return
       });

     A module does not rely on other modules or on their start order; it
     hands state to the styles through is-* classes and CSS variables set
     with style.setProperty.
     ========================================================================== */

}());
