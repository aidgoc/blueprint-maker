// static/editor/undo.js
(function() {
  var undoStack = [];
  var redoStack = [];
  var MAX_STACK = 50;

  window.UndoManager = {
    push: function(entry) {
      entry.timestamp = Date.now();
      undoStack.push(entry);
      if (undoStack.length > MAX_STACK) undoStack.shift();
      redoStack = []; // clear redo on new action
    },

    undo: function() {
      if (!undoStack.length) return;
      var entry = undoStack.pop();
      redoStack.push(entry);
      BlockEditor.applyUndo(entry);
    },

    redo: function() {
      if (!redoStack.length) return;
      var entry = redoStack.pop();
      undoStack.push(entry);
      BlockEditor.applyRedo(entry);
    },

    canUndo: function() { return undoStack.length > 0; },
    canRedo: function() { return redoStack.length > 0; },
    clear: function() { undoStack = []; redoStack = []; }
  };

  // Keyboard shortcuts
  document.addEventListener('keydown', function(e) {
    // Only when editor is visible
    var editor = document.getElementById('editorScreen');
    if (!editor || editor.style.display === 'none') return;

    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
      e.preventDefault();
      UndoManager.undo();
    } else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
      e.preventDefault();
      UndoManager.redo();
    }
  });
})();
