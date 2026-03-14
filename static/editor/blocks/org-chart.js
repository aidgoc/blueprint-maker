// static/editor/blocks/org-chart.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }
  BlockEditor.registerBlockType('org-chart', {
    render: function(data, style) {
      var div = _ce('div', 'be-org');
      (data.roles || []).forEach(function(role) {
        var card = _ce('div', 'be-org-role');
        card.appendChild(_ce('div', 'be-org-title', role.title || ''));
        if (role.reports_to) card.appendChild(_ce('div', 'be-org-reports', 'Reports to: ' + role.reports_to));
        (role.responsibilities || []).forEach(function(r) { card.appendChild(_ce('div', 'be-org-resp', '\u2022 ' + r)); });
        div.appendChild(card);
      });
      return div;
    },
    editor: function(data, style, onChange) {
      var roles = JSON.parse(JSON.stringify(data.roles || []));
      var container = _ce('div', 'be-editor-org');
      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        roles.forEach(function(role, idx) {
          var row = _ce('div', 'be-org-edit');
          var titleIn = document.createElement('input');
          titleIn.className = 'be-input'; titleIn.placeholder = 'Role title'; titleIn.value = role.title || '';
          titleIn.oninput = function() { roles[idx].title = titleIn.value; onChange({roles: roles}); };
          row.appendChild(titleIn);
          var reportsIn = document.createElement('input');
          reportsIn.className = 'be-input be-input-sm'; reportsIn.placeholder = 'Reports to'; reportsIn.value = role.reports_to || '';
          reportsIn.oninput = function() { roles[idx].reports_to = reportsIn.value; onChange({roles: roles}); };
          row.appendChild(reportsIn);
          var respIn = document.createElement('textarea');
          respIn.className = 'be-textarea-sm'; respIn.placeholder = 'Responsibilities (one per line)'; respIn.rows = 2;
          respIn.value = (role.responsibilities || []).join('\n');
          respIn.oninput = function() { roles[idx].responsibilities = respIn.value.split('\n').filter(Boolean); onChange({roles: roles}); };
          row.appendChild(respIn);
          var del = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          del.onclick = function() { roles.splice(idx, 1); onChange({roles: roles}); rebuild(); };
          row.appendChild(del);
          container.appendChild(row);
        });
        var addBtn = _ce('button', 'be-btn-add', '+ Add Role');
        addBtn.onclick = function() { roles.push({id: 'b_'+Math.random().toString(36).substr(2,8), title: '', reports_to: '', responsibilities: []}); onChange({roles: roles}); rebuild(); };
        container.appendChild(addBtn);
      }
      rebuild(); return container;
    }
  });
})();
