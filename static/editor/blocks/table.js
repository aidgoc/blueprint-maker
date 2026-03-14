// static/editor/blocks/table.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  BlockEditor.registerBlockType('table', {
    render: function(data, style) {
      var table = document.createElement('table');
      table.className = 'be-table';
      var thead = document.createElement('thead');
      var hr = document.createElement('tr');
      (data.columns || []).forEach(function(c) { var th = document.createElement('th'); th.textContent = c; hr.appendChild(th); });
      thead.appendChild(hr); table.appendChild(thead);
      var tbody = document.createElement('tbody');
      (data.rows || []).forEach(function(row) {
        var tr = document.createElement('tr');
        row.forEach(function(cell) { var td = document.createElement('td'); td.textContent = cell; tr.appendChild(td); });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      return table;
    },
    editor: function(data, style, onChange) {
      var cols = JSON.parse(JSON.stringify(data.columns || []));
      var rows = JSON.parse(JSON.stringify(data.rows || []));
      var container = _ce('div', 'be-editor-table');

      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        // Column headers
        var headerRow = _ce('div', 'be-table-row');
        cols.forEach(function(c, ci) {
          var inp = document.createElement('input');
          inp.className = 'be-input be-input-sm'; inp.value = c; inp.placeholder = 'Column';
          inp.oninput = function() { cols[ci] = inp.value; onChange({columns: cols, rows: rows}); };
          headerRow.appendChild(inp);
        });
        var addColBtn = _ce('button', 'be-btn-sm', '+Col');
        addColBtn.onclick = function() { cols.push(''); rows.forEach(function(r) { r.push(''); }); onChange({columns: cols, rows: rows}); rebuild(); };
        headerRow.appendChild(addColBtn);
        container.appendChild(headerRow);

        // Data rows
        rows.forEach(function(row, ri) {
          var rowEl = _ce('div', 'be-table-row');
          row.forEach(function(cell, ci) {
            var inp = document.createElement('input');
            inp.className = 'be-input be-input-sm'; inp.value = cell;
            inp.oninput = function() { rows[ri][ci] = inp.value; onChange({columns: cols, rows: rows}); };
            rowEl.appendChild(inp);
          });
          var delRow = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          delRow.onclick = function() { rows.splice(ri, 1); onChange({columns: cols, rows: rows}); rebuild(); };
          rowEl.appendChild(delRow);
          container.appendChild(rowEl);
        });

        var addRowBtn = _ce('button', 'be-btn-add', '+ Add Row');
        addRowBtn.onclick = function() { rows.push(cols.map(function() { return ''; })); onChange({columns: cols, rows: rows}); rebuild(); };
        container.appendChild(addRowBtn);
      }
      rebuild();
      return container;
    }
  });
})();
