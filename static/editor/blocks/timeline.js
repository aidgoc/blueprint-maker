// static/editor/blocks/timeline.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  BlockEditor.registerBlockType('timeline', {
    render: function(data, style) {
      var div = _ce('div', 'be-timeline');
      (data || []).forEach(function(item) {
        var row = _ce('div', 'be-tl-item');
        row.appendChild(_ce('div', 'be-tl-phase', item.phase || ''));
        if (item.duration) row.appendChild(_ce('div', 'be-tl-dur', item.duration));
        (item.activities || []).forEach(function(a) { row.appendChild(_ce('div', 'be-tl-act', a)); });
        div.appendChild(row);
      });
      return div;
    },
    editor: function(data, style, onChange) {
      var items = JSON.parse(JSON.stringify(data || []));
      var container = _ce('div', 'be-editor-timeline');

      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        items.forEach(function(item, idx) {
          var row = _ce('div', 'be-tl-edit-row');
          var phaseIn = document.createElement('input');
          phaseIn.className = 'be-input'; phaseIn.placeholder = 'Phase'; phaseIn.value = item.phase || '';
          phaseIn.oninput = function() { items[idx].phase = phaseIn.value; onChange(items); };
          row.appendChild(phaseIn);

          var durIn = document.createElement('input');
          durIn.className = 'be-input be-input-sm'; durIn.placeholder = 'Duration'; durIn.value = item.duration || '';
          durIn.oninput = function() { items[idx].duration = durIn.value; onChange(items); };
          row.appendChild(durIn);

          // Activities as comma-separated
          var actIn = document.createElement('input');
          actIn.className = 'be-input'; actIn.placeholder = 'Activities (comma-separated)';
          actIn.value = (item.activities || []).join(', ');
          actIn.oninput = function() { items[idx].activities = actIn.value.split(',').map(function(a) { return a.trim(); }).filter(Boolean); onChange(items); };
          row.appendChild(actIn);

          var del = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          del.onclick = function() { items.splice(idx, 1); onChange(items); rebuild(); };
          row.appendChild(del);
          container.appendChild(row);
        });

        var addBtn = _ce('button', 'be-btn-add', '+ Add Phase');
        addBtn.onclick = function() { items.push({phase: '', duration: '', activities: []}); onChange(items); rebuild(); };
        container.appendChild(addBtn);
      }
      rebuild();
      return container;
    }
  });
})();
