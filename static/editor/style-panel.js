// static/editor/style-panel.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  window.StylePanel = {
    show: function(block, anchor) {
      this.hide();
      var panel = _ce('div', 'be-style-panel');
      panel.id = 'stylePanel';

      panel.appendChild(_ce('div', 'be-style-title', 'Block Style'));

      // Color scheme
      panel.appendChild(_ce('label', 'be-style-label', 'Color'));
      var colors = ['default','blue','green','orange','red','purple','teal'];
      var colorRow = _ce('div', 'be-style-colors');
      colors.forEach(function(c) {
        var swatch = _ce('button', 'be-swatch be-swatch-' + c);
        if (c === (block.style.color_scheme || 'default')) swatch.classList.add('active');
        swatch.onclick = function() {
          block.style.color_scheme = c;
          block.html_cache = '';
          BlockEditor.renderAll();
          BlockEditor._scheduleSave();
          StylePanel.hide();
        };
        colorRow.appendChild(swatch);
      });
      panel.appendChild(colorRow);

      // Layout
      panel.appendChild(_ce('label', 'be-style-label', 'Layout'));
      var layouts = ['default','compact','wide'];
      var layoutSel = document.createElement('select');
      layoutSel.className = 'be-select';
      layouts.forEach(function(l) {
        var o = document.createElement('option'); o.value = l; o.textContent = l;
        if (l === (block.style.layout || 'default')) o.selected = true;
        layoutSel.appendChild(o);
      });
      layoutSel.onchange = function() {
        block.style.layout = layoutSel.value;
        block.html_cache = '';
        BlockEditor.renderAll();
        BlockEditor._scheduleSave();
      };
      panel.appendChild(layoutSel);

      // Position near anchor
      document.body.appendChild(panel);
      var rect = anchor.getBoundingClientRect();
      panel.style.top = (rect.bottom + 5) + 'px';
      panel.style.left = rect.left + 'px';

      // Close on outside click
      setTimeout(function() {
        document.addEventListener('click', function handler(e) {
          if (!panel.contains(e.target) && e.target !== anchor) {
            StylePanel.hide();
            document.removeEventListener('click', handler);
          }
        });
      }, 10);
    },

    hide: function() {
      var existing = document.getElementById('stylePanel');
      if (existing) existing.parentNode.removeChild(existing);
    }
  };
})();
