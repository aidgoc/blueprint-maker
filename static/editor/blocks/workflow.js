// static/editor/blocks/workflow.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  BlockEditor.registerBlockType('workflow', {
    render: function(data, style) {
      var div = _ce('div', 'be-workflow');
      (data.steps || []).forEach(function(step, i) {
        var row = _ce('div', 'be-wf-step');
        row.appendChild(_ce('span', 'be-wf-num', String(i + 1)));
        var body = _ce('div', 'be-wf-body');
        body.appendChild(_ce('div', 'be-wf-title', step.title || ''));
        body.appendChild(_ce('div', 'be-wf-desc', step.description || ''));
        if (step.assignee) body.appendChild(_ce('div', 'be-wf-assignee', step.assignee));
        row.appendChild(body);
        div.appendChild(row);
      });
      return div;
    },
    editor: function(data, style, onChange) {
      var steps = JSON.parse(JSON.stringify(data.steps || []));
      var container = _ce('div', 'be-editor-workflow');

      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        steps.forEach(function(step, idx) {
          var row = _ce('div', 'be-wf-edit-row');
          row.appendChild(_ce('span', 'be-wf-num', String(idx + 1)));

          var fields = _ce('div', 'be-wf-fields');
          var titleIn = document.createElement('input');
          titleIn.className = 'be-input'; titleIn.placeholder = 'Step title'; titleIn.value = step.title || '';
          titleIn.oninput = function() { steps[idx].title = titleIn.value; onChange({steps: steps, connections: data.connections || []}); };
          fields.appendChild(titleIn);

          var descIn = document.createElement('input');
          descIn.className = 'be-input'; descIn.placeholder = 'Description'; descIn.value = step.description || '';
          descIn.oninput = function() { steps[idx].description = descIn.value; onChange({steps: steps, connections: data.connections || []}); };
          fields.appendChild(descIn);

          var assignIn = document.createElement('input');
          assignIn.className = 'be-input be-input-sm'; assignIn.placeholder = 'Assignee'; assignIn.value = step.assignee || '';
          assignIn.oninput = function() { steps[idx].assignee = assignIn.value; onChange({steps: steps, connections: data.connections || []}); };
          fields.appendChild(assignIn);

          row.appendChild(fields);

          var delBtn = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          delBtn.onclick = function() { steps.splice(idx, 1); onChange({steps: steps, connections: data.connections || []}); rebuild(); };
          row.appendChild(delBtn);

          container.appendChild(row);
        });

        var addBtn = _ce('button', 'be-btn-add', '+ Add Step');
        addBtn.onclick = function() {
          steps.push({id: 'b_' + Math.random().toString(36).substr(2,8), title: '', description: '', type: 'activity', assignee: ''});
          onChange({steps: steps, connections: data.connections || []}); rebuild();
        };
        container.appendChild(addBtn);
      }
      rebuild();
      return container;
    }
  });
})();
