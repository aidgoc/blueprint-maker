// static/editor/blocks/checklist.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  BlockEditor.registerBlockType('checklist', {
    render: function(data, style) {
      var ul = _ce('ul', 'be-checklist');
      (data || []).forEach(function(item) {
        var li = _ce('li', item.priority === 'high' ? 'be-cl-high' : '');
        var chk = _ce('span', 'be-cl-check' + (item.checked ? ' checked' : ''));
        li.appendChild(chk);
        li.appendChild(_ce('span', null, item.text || ''));
        ul.appendChild(li);
      });
      return ul;
    },
    editor: function(data, style, onChange) {
      var items = JSON.parse(JSON.stringify(data || []));
      var container = _ce('div', 'be-editor-checklist');

      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        items.forEach(function(item, idx) {
          var row = _ce('div', 'be-cl-row');

          var chk = document.createElement('input');
          chk.type = 'checkbox';
          chk.checked = item.checked;
          chk.onchange = function() { items[idx].checked = chk.checked; onChange(items); };
          row.appendChild(chk);

          var input = document.createElement('input');
          input.type = 'text';
          input.className = 'be-input be-cl-input';
          input.value = item.text || '';
          input.oninput = function() { items[idx].text = input.value; onChange(items); };
          row.appendChild(input);

          var priSel = document.createElement('select');
          priSel.className = 'be-select-sm';
          ['normal','high','low'].forEach(function(p) {
            var o = document.createElement('option'); o.value = p; o.textContent = p;
            if (p === item.priority) o.selected = true; priSel.appendChild(o);
          });
          priSel.onchange = function() { items[idx].priority = priSel.value; onChange(items); };
          row.appendChild(priSel);

          var delBtn = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          delBtn.onclick = function() { items.splice(idx, 1); onChange(items); rebuild(); };
          row.appendChild(delBtn);

          container.appendChild(row);
        });

        var addBtn = _ce('button', 'be-btn-add', '+ Add Item');
        addBtn.onclick = function() {
          items.push({text: '', checked: false, priority: 'normal'});
          onChange(items); rebuild();
        };
        container.appendChild(addBtn);
      }
      rebuild();
      return container;
    }
  });
})();
