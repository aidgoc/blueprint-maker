// static/editor/blocks/divider.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  BlockEditor.registerBlockType('divider', {
    render: function(data, style) {
      var hr = document.createElement('hr');
      hr.className = 'be-divider be-divider-' + (data.style || 'solid');
      return hr;
    },
    editor: function(data, style, onChange) {
      var container = _ce('div', 'be-editor-divider');
      container.appendChild(_ce('label', null, 'Style:'));
      var select = document.createElement('select');
      select.className = 'be-select';
      ['solid', 'dashed', 'dotted'].forEach(function(s) {
        var opt = document.createElement('option');
        opt.value = s; opt.textContent = s;
        if (s === (data.style || 'solid')) opt.selected = true;
        select.appendChild(opt);
      });
      select.onchange = function() { onChange({style: select.value}); };
      container.appendChild(select);
      return container;
    }
  });
})();
