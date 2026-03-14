// static/editor/blocks/flow-diagram.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }
  BlockEditor.registerBlockType('flow-diagram', {
    render: function(data, style) {
      var div = _ce('div', 'be-flow');
      var nodesDiv = _ce('div', 'be-flow-nodes');
      (data.nodes || []).forEach(function(n) {
        nodesDiv.appendChild(_ce('span', 'be-flow-node' + (n.type === 'center' ? ' be-flow-center' : ''), n.label || ''));
      });
      div.appendChild(nodesDiv);
      (data.edges || []).forEach(function(e) {
        div.appendChild(_ce('div', 'be-flow-edge', (e.from || '') + ' \u2192 ' + (e.to || '') + ': ' + (e.label || '')));
      });
      return div;
    },
    editor: function(data, style, onChange) {
      var nodes = JSON.parse(JSON.stringify(data.nodes || []));
      var edges = JSON.parse(JSON.stringify(data.edges || []));
      var container = _ce('div', 'be-editor-flow');

      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        container.appendChild(_ce('div', 'be-section-label', 'Nodes'));
        nodes.forEach(function(n, idx) {
          var row = _ce('div', 'be-flow-row');
          var labelIn = document.createElement('input');
          labelIn.className = 'be-input be-input-sm'; labelIn.placeholder = 'Label'; labelIn.value = n.label || '';
          labelIn.oninput = function() { nodes[idx].label = labelIn.value; onChange({nodes: nodes, edges: edges}); };
          row.appendChild(labelIn);
          var del = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          del.onclick = function() { nodes.splice(idx, 1); onChange({nodes: nodes, edges: edges}); rebuild(); };
          row.appendChild(del);
          container.appendChild(row);
        });
        var addNode = _ce('button', 'be-btn-add', '+ Add Node');
        addNode.onclick = function() { nodes.push({id: 'n_'+Math.random().toString(36).substr(2,6), label: '', type: 'external'}); onChange({nodes: nodes, edges: edges}); rebuild(); };
        container.appendChild(addNode);

        container.appendChild(_ce('div', 'be-section-label', 'Connections'));
        edges.forEach(function(e, idx) {
          var row = _ce('div', 'be-flow-row');
          ['from','to','label'].forEach(function(f) {
            var inp = document.createElement('input');
            inp.className = 'be-input be-input-sm'; inp.placeholder = f; inp.value = e[f] || '';
            inp.oninput = function() { edges[idx][f] = inp.value; onChange({nodes: nodes, edges: edges}); };
            row.appendChild(inp);
          });
          var del = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          del.onclick = function() { edges.splice(idx, 1); onChange({nodes: nodes, edges: edges}); rebuild(); };
          row.appendChild(del);
          container.appendChild(row);
        });
        var addEdge = _ce('button', 'be-btn-add', '+ Add Connection');
        addEdge.onclick = function() { edges.push({from: '', to: '', label: ''}); onChange({nodes: nodes, edges: edges}); rebuild(); };
        container.appendChild(addEdge);
      }
      rebuild(); return container;
    }
  });
})();
