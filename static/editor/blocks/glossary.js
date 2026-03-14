// static/editor/blocks/glossary.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }
  BlockEditor.registerBlockType('glossary', {
    render: function(data, style) {
      var div = _ce('div', 'be-glossary');
      (data || []).forEach(function(entry) {
        var el = _ce('div', 'be-gl-entry');
        el.appendChild(_ce('span', 'be-gl-term', entry.term || ''));
        el.appendChild(_ce('span', null, ' \u2014 '));
        el.appendChild(_ce('span', 'be-gl-def', entry.definition || ''));
        div.appendChild(el);
      });
      return div;
    },
    editor: function(data, style, onChange) {
      var terms = JSON.parse(JSON.stringify(data || []));
      var container = _ce('div', 'be-editor-glossary');
      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        terms.forEach(function(t, idx) {
          var row = _ce('div', 'be-gl-row');
          var termIn = document.createElement('input');
          termIn.className = 'be-input be-input-sm'; termIn.placeholder = 'Term'; termIn.value = t.term || '';
          termIn.oninput = function() { terms[idx].term = termIn.value; onChange(terms); };
          row.appendChild(termIn);
          var defIn = document.createElement('input');
          defIn.className = 'be-input'; defIn.placeholder = 'Definition'; defIn.value = t.definition || '';
          defIn.oninput = function() { terms[idx].definition = defIn.value; onChange(terms); };
          row.appendChild(defIn);
          var del = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          del.onclick = function() { terms.splice(idx, 1); onChange(terms); rebuild(); };
          row.appendChild(del);
          container.appendChild(row);
        });
        var addBtn = _ce('button', 'be-btn-add', '+ Add Term');
        addBtn.onclick = function() { terms.push({term: '', definition: '', related: []}); onChange(terms); rebuild(); };
        container.appendChild(addBtn);
      }
      rebuild(); return container;
    }
  });
})();
