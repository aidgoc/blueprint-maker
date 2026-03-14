// static/editor/blocks/kpi-grid.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  BlockEditor.registerBlockType('kpi-grid', {
    render: function(data, style) {
      var grid = _ce('div', 'be-kpi-grid');
      (data || []).forEach(function(kpi) {
        var card = _ce('div', 'be-kpi-card');
        card.appendChild(_ce('div', 'be-kpi-name', kpi.name || ''));
        card.appendChild(_ce('div', 'be-kpi-value', (kpi.unit || '') + (kpi.value || '')));
        card.appendChild(_ce('div', 'be-kpi-target', 'Target: ' + (kpi.unit || '') + (kpi.target || '')));
        grid.appendChild(card);
      });
      return grid;
    },
    editor: function(data, style, onChange) {
      var items = JSON.parse(JSON.stringify(data || []));
      var container = _ce('div', 'be-editor-kpi');

      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        items.forEach(function(kpi, idx) {
          var row = _ce('div', 'be-kpi-row');
          ['name','value','target','unit'].forEach(function(field) {
            var inp = document.createElement('input');
            inp.className = 'be-input be-input-sm'; inp.placeholder = field; inp.value = kpi[field] || '';
            inp.oninput = function() { items[idx][field] = inp.value; onChange(items); };
            row.appendChild(inp);
          });
          var trendSel = document.createElement('select');
          trendSel.className = 'be-select-sm';
          ['stable','up','down'].forEach(function(t) {
            var o = document.createElement('option'); o.value = t; o.textContent = t;
            if (t === (kpi.trend || 'stable')) o.selected = true; trendSel.appendChild(o);
          });
          trendSel.onchange = function() { items[idx].trend = trendSel.value; onChange(items); };
          row.appendChild(trendSel);
          var del = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          del.onclick = function() { items.splice(idx, 1); onChange(items); rebuild(); };
          row.appendChild(del);
          container.appendChild(row);
        });
        var addBtn = _ce('button', 'be-btn-add', '+ Add KPI');
        addBtn.onclick = function() { items.push({name:'',value:'',target:'',unit:'',trend:'stable'}); onChange(items); rebuild(); };
        container.appendChild(addBtn);
      }
      rebuild();
      return container;
    }
  });
})();
