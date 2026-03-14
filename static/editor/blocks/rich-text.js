// static/editor/blocks/rich-text.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  BlockEditor.registerBlockType('rich-text', {
    render: function(data, style) {
      var el = _ce('div', 'be-rendered-richtext');
      // html_cache is trusted server content — use fragment
      if (data.html) {
        var frag = document.createRange().createContextualFragment(data.html);
        el.appendChild(frag);
      }
      return el;
    },
    editor: function(data, style, onChange) {
      var container = _ce('div', 'be-editor-richtext');
      var ta = document.createElement('textarea');
      ta.className = 'be-textarea';
      ta.rows = 5;
      // Strip HTML tags for editing, show as plain text
      var temp = document.createElement('div');
      var frag = document.createRange().createContextualFragment(data.html || '');
      temp.appendChild(frag);
      ta.value = temp.textContent || '';
      ta.oninput = function() {
        // Wrap plain text in <p> tags
        var lines = ta.value.split('\n').filter(function(l) { return l.trim(); });
        var html = lines.map(function(l) { return '<p>' + l.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</p>'; }).join('\n');
        onChange({html: html});
      };
      container.appendChild(ta);
      container.appendChild(_ce('div', 'be-hint', 'Plain text. Each line becomes a paragraph.'));
      setTimeout(function() { ta.focus(); }, 50);
      return container;
    }
  });
})();
