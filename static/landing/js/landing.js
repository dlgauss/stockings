// Order form: quantity stepper, live total on the submit button, city/street dropdowns.
(function () {
  var form = document.querySelector('.order-form');
  if (!form) return;

  // Quantity stepper and total
  var qty = form.querySelector('input[name="quantity"]');
  var total = form.querySelector('[data-total]');
  var price = parseFloat(form.dataset.price);
  var money = new Intl.NumberFormat(form.dataset.locale, { maximumFractionDigits: 2 });

  function clampQty() {
    var n = parseInt(qty.value, 10);
    if (isNaN(n) || n < 1) n = 1;
    if (n > 20) n = 20;
    return n;
  }

  function updateTotal() {
    if (!total || isNaN(price)) return;
    total.textContent = money.format(price * clampQty()) + ' ' + form.dataset.currency;
  }

  form.querySelectorAll('[data-qty]').forEach(function (button) {
    button.addEventListener('click', function () {
      qty.value = Math.min(20, Math.max(1, clampQty() + parseInt(button.dataset.qty, 10)));
      updateTotal();
    });
  });
  qty.addEventListener('input', updateTotal);
  updateTotal();

  // Once a customer edits a field the server marked as wrong, drop its error message.
  form.addEventListener('input', clearError);
  form.addEventListener('change', clearError);
  form.addEventListener('click', function (event) {
    if (event.target.closest('[data-qty]')) clearError(event);
  });

  function clearError(event) {
    var field = event.target.closest('.field.has-error');
    if (!field) return;
    field.classList.remove('has-error');
    field.querySelectorAll('.error').forEach(function (error) { error.remove(); });
  }

  // City / street dropdowns: an editable WAI-ARIA combobox with a listbox popup.
  // Cities come from a built-in list (instant, matches Russian names too) plus Photon results
  // from the server; streets come from Photon for the chosen city. Free text is always accepted.
  var data = JSON.parse(document.getElementById('combo-data').textContent);
  var text = data.text;
  var cityInput = form.querySelector('[data-suggest="city"]');
  var streetInput = form.querySelector('[data-suggest="street"]');
  var cityCoords = null;
  var MAX_ITEMS = 8;
  var CYRILLIC = /[Ѐ-ӿ]/;
  var SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';
  var ICONS = {
    city: SVG + '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
    street: SVG + '<path d="M12 3v18"/><path d="M5 6h11l3 3-3 3H5z"/></svg>',
    typed: SVG + '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>'
  };

  function normalize(value) {
    return value.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }

  var cities = data.cities.map(function (city) {
    city.key = normalize(city.search);
    city.words = city.key.split(/[\s-]+/);
    return city;
  });

  function matchCities(query) {
    var q = normalize(query);
    if (!q) return cities.slice(0, data.popularCount);
    var starts = [];
    var contains = [];
    cities.forEach(function (city) {
      if (city.words.some(function (word) { return word.indexOf(q) === 0; })) starts.push(city);
      else if (city.key.indexOf(q) >= 0) contains.push(city);
    });
    return starts.concat(contains);
  }

  // Puts `label` into `el`, with the part matching `query` in <mark> (ignoring case and diacritics).
  function appendHighlighted(el, label, query) {
    var chars = Array.from(label);
    var normalized = chars.map(normalize);
    var q = normalize(query.trim());
    var start = -1;
    if (q && normalized.every(function (c) { return c.length === 1; })) {
      start = normalized.join('').indexOf(q);
    }
    if (start < 0) {
      el.textContent = label;
      return;
    }
    var end = start + q.length;
    var mark = document.createElement('mark');
    mark.textContent = chars.slice(start, end).join('');
    el.append(chars.slice(0, start).join(''), mark, chars.slice(end).join(''));
  }

  function typedItem(query) {
    return { value: query, label: text.useTyped.replace('%s', query), typed: true };
  }

  function setupCombo(input, config) {
    var root = input.closest('.combo');
    var panel = root.querySelector('.combo-panel');
    var status = root.querySelector('.combo-status');
    var list = root.querySelector('.combo-list');
    var clear = root.querySelector('.combo-clear');
    var hint = root.parentNode.querySelector('.combo-hint');
    var items = [];
    var active = -1;
    var timer = null;
    var controller = null;
    var narrow = window.matchMedia('(max-width: 600px)');

    function isOpen() {
      return !panel.hidden;
    }

    function fitToViewport() {
      // Keep the list above the on-screen keyboard: limit it to the visible space below the field.
      var viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
      var space = viewportHeight - root.getBoundingClientRect().bottom - 60;
      list.style.setProperty('--combo-max-height', Math.max(170, Math.min(320, space)) + 'px');
    }

    function open() {
      if (isOpen()) return;
      panel.hidden = false;
      root.classList.add('is-open');
      input.setAttribute('aria-expanded', 'true');
      if (narrow.matches) root.scrollIntoView({ block: 'start', behavior: 'smooth' });
      fitToViewport();
    }

    function stopLoading() {
      clearTimeout(timer);
      if (controller) controller.abort();
      controller = null;
      root.classList.remove('is-loading');
    }

    function close() {
      stopLoading();
      panel.hidden = true;
      root.classList.remove('is-open');
      input.setAttribute('aria-expanded', 'false');
      input.removeAttribute('aria-activedescendant');
      active = -1;
    }

    function setStatus(message, isMessage) {
      status.textContent = message || '';
      status.classList.toggle('is-message', Boolean(isMessage));
    }

    function highlight(index) {
      active = index;
      Array.prototype.forEach.call(list.children, function (li, i) {
        li.setAttribute('aria-selected', i === index ? 'true' : 'false');
      });
      if (index >= 0) {
        input.setAttribute('aria-activedescendant', list.children[index].id);
        list.children[index].scrollIntoView({ block: 'nearest' });
      } else {
        input.removeAttribute('aria-activedescendant');
      }
    }

    function render(newItems, statusText, isMessage) {
      items = newItems.slice(0, MAX_ITEMS);
      active = -1;
      input.removeAttribute('aria-activedescendant');
      list.textContent = '';
      items.forEach(function (item, i) {
        var li = document.createElement('li');
        li.id = list.id + '-' + i;
        li.className = 'combo-option' + (item.typed ? ' is-typed' : '');
        li.setAttribute('role', 'option');
        li.setAttribute('aria-selected', 'false');

        var icon = document.createElement('span');
        icon.className = 'combo-option-icon';
        icon.innerHTML = item.typed ? ICONS.typed : ICONS[config.kind];

        var body = document.createElement('span');
        body.className = 'combo-option-text';
        var label = document.createElement('span');
        label.className = 'combo-option-label';
        if (item.typed) label.textContent = item.label;
        else appendHighlighted(label, item.label || item.value, input.value);
        body.appendChild(label);
        if (item.hint) {
          var sub = document.createElement('span');
          sub.className = 'combo-option-hint';
          sub.textContent = item.hint;
          body.appendChild(sub);
        }

        li.append(icon, body);
        li.addEventListener('click', function () { choose(i); });
        list.appendChild(li);
      });
      setStatus(statusText, isMessage);
      if (isOpen()) fitToViewport();
    }

    function choose(index) {
      var item = items[index];
      if (!item) return;
      input.value = item.value;
      close();
      updateClear();
      config.onChoose(item, { root: root, hint: hint });
    }

    function updateClear() {
      clear.hidden = !input.value;
    }

    function fetchRemote(query, localItems) {
      controller = new AbortController();
      var params = new URLSearchParams(Object.assign({ q: query, kind: config.kind }, config.params()));
      fetch(form.dataset.suggestUrl + '?' + params, { signal: controller.signal })
        .then(function (response) { return response.json(); })
        .then(function (json) {
          root.classList.remove('is-loading');
          if (!isOpen() || input.value.trim() !== query) return;
          var seen = {};
          var merged = localItems.concat(json.results || []).filter(function (item) {
            var key = normalize(item.value);
            if (seen[key]) return false;
            seen[key] = true;
            return true;
          });
          if (merged.length) render(merged, '');
          else render([typedItem(query)], text.noResults, true);
        })
        .catch(function (error) {
          if (error.name !== 'AbortError') {
            root.classList.remove('is-loading');
            if (isOpen() && !items.length) render([typedItem(query)], '', false);
          }
        });
    }

    function update() {
      stopLoading();
      var query = input.value.trim();
      var local = config.local(query);
      var remote = query.length >= 2 && config.shouldFetch(query);
      if (!local.items.length && query && !remote && !local.status) {
        render([typedItem(query)], text.noResults, true);
        return;
      }
      render(local.items, local.status, local.isMessage);
      if (!remote) return;
      root.classList.add('is-loading');
      timer = setTimeout(function () { fetchRemote(query, local.items); }, 250);
    }

    input.addEventListener('focus', function () {
      open();
      update();
    });
    input.addEventListener('click', function () {
      if (!isOpen()) {
        open();
        update();
      }
    });
    input.addEventListener('input', function () {
      root.classList.remove('is-chosen');
      if (hint) hint.hidden = true;
      config.onEdit();
      updateClear();
      open();
      update();
    });
    input.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        if (!isOpen()) {
          open();
          update();
          return;
        }
        if (!items.length) return;
        var step = event.key === 'ArrowDown' ? 1 : -1;
        highlight((active + step + items.length) % items.length);
      } else if (event.key === 'Enter' && isOpen() && items.length) {
        event.preventDefault();
        choose(active >= 0 ? active : 0);
      } else if (event.key === 'Tab' && isOpen() && active >= 0) {
        choose(active);
      } else if (event.key === 'Escape' && isOpen()) {
        event.preventDefault();
        close();
      }
    });
    input.addEventListener('blur', close);

    // Clicking inside the panel or on the clear button must not take focus away from the input.
    panel.addEventListener('mousedown', function (event) { event.preventDefault(); });
    clear.addEventListener('mousedown', function (event) { event.preventDefault(); });
    clear.addEventListener('click', function () {
      input.value = '';
      root.classList.remove('is-chosen');
      if (hint) hint.hidden = true;
      config.onEdit();
      updateClear();
      input.focus();
      open();
      update();
    });

    function refit() {
      if (isOpen()) fitToViewport();
    }
    if (window.visualViewport) window.visualViewport.addEventListener('resize', refit);
    window.addEventListener('scroll', refit, { passive: true });

    updateClear();
    if (input.value) root.classList.add('is-chosen');
  }

  if (cityInput) {
    setupCombo(cityInput, {
      kind: 'city',
      local: function (query) {
        if (!query) return { items: matchCities(''), status: text.popular };
        var items = matchCities(query);
        if (items.length) return { items: items, status: '' };
        // Nothing local: wait for Photon, or (one letter) offer the typed text right away.
        return query.length >= 2 ? { items: [], status: text.searching, isMessage: true } : { items: [], status: '' };
      },
      shouldFetch: function () { return true; },
      params: function () { return {}; },
      onEdit: function () { cityCoords = null; },
      onChoose: function (item, combo) {
        cityCoords = item.lat != null ? { lat: item.lat, lon: item.lon } : null;
        combo.root.classList.add('is-chosen');
        if (streetInput && !streetInput.value) streetInput.focus();
      }
    });
  }

  if (streetInput) {
    setupCombo(streetInput, {
      kind: 'street',
      local: function (query) {
        if (!query) {
          return { items: [], status: cityInput.value.trim() ? text.streetStart : text.cityFirst, isMessage: true };
        }
        if (CYRILLIC.test(query)) return { items: [], status: text.latinOnly, isMessage: true };
        if (query.length < 2) return { items: [], status: text.streetStart, isMessage: true };
        return { items: [], status: text.searching, isMessage: true };
      },
      shouldFetch: function (query) { return !CYRILLIC.test(query); },
      params: function () {
        var params = { city: cityInput.value.trim() };
        if (cityCoords) {
          params.lat = cityCoords.lat;
          params.lon = cityCoords.lon;
        }
        return params;
      },
      onEdit: function () {},
      onChoose: function (item, combo) {
        if (!item.typed && !/\d/.test(item.value)) {
          // A street without a number: leave the cursor at the end for the house number.
          streetInput.value = item.value + ' ';
          combo.hint.textContent = text.houseNumber;
          combo.hint.hidden = false;
          streetInput.focus();
          streetInput.setSelectionRange(streetInput.value.length, streetInput.value.length);
        } else {
          combo.root.classList.add('is-chosen');
        }
      }
    });
  }
})();
