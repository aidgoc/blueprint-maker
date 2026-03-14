// static/editor/blocks/card-grid.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }
  BlockEditor.registerBlockType('card-grid', {
    render: function(data, style) {
      var grid = _ce('div', 'be-card-grid');
      (data || []).forEach(function(card) {
        var el = _ce('div', 'be-card be-card-' + (card.type || 'activity'));
        el.appendChild(_ce('div', 'be-card-title', card.title || ''));
        (card.items || []).forEach(function(item) { el.appendChild(_ce('div', 'be-card-item', item)); });
        grid.appendChild(el);
      });
      return grid;
    },
    editor: function(data, style, onChange) {
      var cards = JSON.parse(JSON.stringify(data || []));
      var container = _ce('div', 'be-editor-cards');
      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        cards.forEach(function(card, idx) {
          var row = _ce('div', 'be-card-edit');
          var titleIn = document.createElement('input');
          titleIn.className = 'be-input'; titleIn.placeholder = 'Card title'; titleIn.value = card.title || '';
          titleIn.oninput = function() { cards[idx].title = titleIn.value; onChange(cards); };
          row.appendChild(titleIn);
          var itemsIn = document.createElement('textarea');
          itemsIn.className = 'be-textarea-sm'; itemsIn.placeholder = 'Items (one per line)';
          itemsIn.value = (card.items || []).join('\n'); itemsIn.rows = 3;
          itemsIn.oninput = function() { cards[idx].items = itemsIn.value.split('\n').filter(Boolean); onChange(cards); };
          row.appendChild(itemsIn);
          var del = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          del.onclick = function() { cards.splice(idx, 1); onChange(cards); rebuild(); };
          row.appendChild(del);
          container.appendChild(row);
        });
        var addBtn = _ce('button', 'be-btn-add', '+ Add Card');
        addBtn.onclick = function() { cards.push({title: '', type: 'activity', items: []}); onChange(cards); rebuild(); };
        container.appendChild(addBtn);
      }
      rebuild(); return container;
    }
  });
})();
