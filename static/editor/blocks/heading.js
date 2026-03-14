// static/editor/blocks/heading.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  BlockEditor.registerBlockType('heading', {
    render: function(data, style) {
      var level = Math.min(Math.max(data.level || 1, 1), 4);
      var el = document.createElement('h' + level);
      el.textContent = data.text || '';
      el.className = 'be-rendered-heading';
      return el;
    },
    editor: function(data, style, onChange) {
      var container = _ce('div', 'be-editor-heading');

      var input = document.createElement('input');
      input.type = 'text';
      input.className = 'be-input';
      input.value = data.text || '';
      input.placeholder = 'Heading text';
      input.oninput = function() { onChange({text: input.value, level: parseInt(levelSelect.value)}); };
      container.appendChild(input);

      var levelSelect = document.createElement('select');
      levelSelect.className = 'be-select';
      [1,2,3,4].forEach(function(l) {
        var opt = document.createElement('option');
        opt.value = l; opt.textContent = 'H' + l;
        if (l === (data.level || 1)) opt.selected = true;
        levelSelect.appendChild(opt);
      });
      levelSelect.onchange = function() { onChange({text: input.value, level: parseInt(levelSelect.value)}); };
      container.appendChild(levelSelect);

      setTimeout(function() { input.focus(); }, 50);
      return container;
    }
  });
})();
