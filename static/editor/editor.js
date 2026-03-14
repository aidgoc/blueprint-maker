// static/editor/editor.js
// Block Editor Engine — MUST load before block type files
// Manages: block type registration, toolbar, edit mode, drag-drop, insert palette, auto-save

(function() {
  'use strict';

  var blockTypes = {};
  var currentEditBlock = null;
  var blueprintId = null;
  var sectionId = null;
  var sectionBlocks = [];
  var saveTimeout = null;
  var saving = false;

  function _ce(tag, cls, text) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text) el.textContent = text;
    return el;
  }

  window.BlockEditor = {
    // --- Registration ---
    registerBlockType: function(name, config) {
      // config: { render: fn(data, style) -> HTMLElement, editor: fn(data, style, onChange) -> HTMLElement }
      blockTypes[name] = config;
    },

    getBlockType: function(name) {
      return blockTypes[name] || null;
    },

    // --- Init ---
    init: function(bpId, secId, blocks) {
      blueprintId = bpId;
      sectionId = secId;
      sectionBlocks = JSON.parse(JSON.stringify(blocks)); // deep copy
      currentEditBlock = null;
      this.renderAll();
      this._initDragDrop();
    },

    getBlocks: function() {
      return sectionBlocks;
    },

    setSection: function(secId, blocks) {
      sectionId = secId;
      sectionBlocks = JSON.parse(JSON.stringify(blocks));
      currentEditBlock = null;
      this.renderAll();
      this._initDragDrop();
    },

    // --- Rendering ---
    renderAll: function() {
      var container = document.getElementById('editorBlocks');
      if (!container) return;
      while (container.firstChild) container.removeChild(container.firstChild);

      for (var i = 0; i < sectionBlocks.length; i++) {
        var block = sectionBlocks[i];
        var wrapper = this._createBlockWrapper(block, i);
        container.appendChild(wrapper);

        // Insert "+" button between blocks
        if (i < sectionBlocks.length - 1) {
          container.appendChild(this._createInsertButton(i));
        }
      }

      // "+" at the end
      container.appendChild(this._createInsertButton(sectionBlocks.length - 1));

      this._updateSaveIndicator('saved');
    },

    _createBlockWrapper: function(block, index) {
      var self = this;
      var wrapper = _ce('div', 'be-block-wrapper');
      wrapper.setAttribute('data-block-id', block.id);
      wrapper.setAttribute('data-block-index', index);

      // Toolbar (appears on hover)
      var toolbar = _ce('div', 'be-toolbar');
      var editBtn = _ce('button', 'be-tb-btn', 'Edit');
      editBtn.title = 'Edit block';
      editBtn.onclick = function(e) { e.stopPropagation(); self._enterEditMode(block.id); };

      var dupBtn = _ce('button', 'be-tb-btn', 'Dup');
      dupBtn.title = 'Duplicate block';
      dupBtn.onclick = function(e) { e.stopPropagation(); self._duplicateBlock(block.id); };

      var delBtn = _ce('button', 'be-tb-btn be-tb-del', 'Del');
      delBtn.title = 'Delete block';
      delBtn.onclick = function(e) { e.stopPropagation(); self._deleteBlock(block.id); };

      var styleBtn = _ce('button', 'be-tb-btn', 'Style');
      styleBtn.title = 'Block style';
      styleBtn.onclick = function(e) { e.stopPropagation(); if (window.StylePanel) StylePanel.show(block, e.target); };

      var dragHandle = _ce('span', 'be-drag-handle', '\u2630');
      dragHandle.title = 'Drag to reorder';

      toolbar.appendChild(dragHandle);
      toolbar.appendChild(editBtn);
      toolbar.appendChild(dupBtn);
      toolbar.appendChild(styleBtn);
      toolbar.appendChild(delBtn);
      wrapper.appendChild(toolbar);

      // Block content
      var content = _ce('div', 'be-block-content');
      if (currentEditBlock === block.id) {
        // Edit mode
        var bt = blockTypes[block.type];
        if (bt && bt.editor) {
          var editorEl = bt.editor(block.data, block.style, function(newData) {
            self._updateBlockData(block.id, newData);
          });
          content.appendChild(editorEl);
        } else {
          content.appendChild(_ce('div', 'be-no-editor', 'No editor for ' + block.type));
        }

        // Done button
        var doneBtn = _ce('button', 'be-done-btn', 'Done');
        doneBtn.onclick = function() { self._exitEditMode(); };
        content.appendChild(doneBtn);
      } else {
        // View mode — use registered render or fall back to html_cache
        var bt = blockTypes[block.type];
        if (bt && bt.render) {
          var rendered = bt.render(block.data, block.style);
          content.appendChild(rendered);
        } else if (block.html_cache) {
          var frag = document.createRange().createContextualFragment(block.html_cache);
          content.appendChild(frag);
        } else {
          content.appendChild(_ce('div', null, block.type + ': ' + JSON.stringify(block.data).substring(0, 100)));
        }

        // Click to edit
        content.onclick = function() { self._enterEditMode(block.id); };
        content.style.cursor = 'pointer';
      }

      wrapper.appendChild(content);
      return wrapper;
    },

    _createInsertButton: function(afterIndex) {
      var self = this;
      var btn = _ce('div', 'be-insert-btn');
      var plus = _ce('button', 'be-insert-plus', '+');
      plus.title = 'Insert block';
      plus.onclick = function() { self._showInsertPalette(afterIndex, btn); };
      btn.appendChild(plus);
      return btn;
    },

    // --- Edit Mode ---
    _enterEditMode: function(blockId) {
      currentEditBlock = blockId;
      this.renderAll();
    },

    _exitEditMode: function() {
      currentEditBlock = null;
      this.renderAll();
    },

    _updateBlockData: function(blockId, newData) {
      for (var i = 0; i < sectionBlocks.length; i++) {
        if (sectionBlocks[i].id === blockId) {
          var before = JSON.parse(JSON.stringify(sectionBlocks[i].data));
          sectionBlocks[i].data = newData;
          sectionBlocks[i].html_cache = ''; // invalidate cache

          // Push to undo stack
          if (window.UndoManager) {
            UndoManager.push({
              sectionId: sectionId,
              blockId: blockId,
              action: 'update',
              before: before,
              after: JSON.parse(JSON.stringify(newData))
            });
          }

          this._scheduleSave();
          break;
        }
      }
    },

    // --- Block Operations ---
    _duplicateBlock: function(blockId) {
      for (var i = 0; i < sectionBlocks.length; i++) {
        if (sectionBlocks[i].id === blockId) {
          var copy = JSON.parse(JSON.stringify(sectionBlocks[i]));
          copy.id = 'b_' + Math.random().toString(36).substr(2, 12);
          copy.html_cache = '';
          sectionBlocks.splice(i + 1, 0, copy);

          if (window.UndoManager) {
            UndoManager.push({sectionId: sectionId, blockId: copy.id, action: 'add', before: null, after: copy.data});
          }

          this.renderAll();
          this._initDragDrop();
          this._scheduleSave();
          break;
        }
      }
    },

    _deleteBlock: function(blockId) {
      if (!confirm('Delete this block?')) return;
      for (var i = 0; i < sectionBlocks.length; i++) {
        if (sectionBlocks[i].id === blockId) {
          var removed = sectionBlocks.splice(i, 1)[0];

          if (window.UndoManager) {
            UndoManager.push({sectionId: sectionId, blockId: blockId, action: 'delete', before: removed.data, after: null});
          }

          if (currentEditBlock === blockId) currentEditBlock = null;
          this.renderAll();
          this._initDragDrop();
          this._scheduleSave();
          break;
        }
      }
    },

    // --- Insert Palette ---
    _showInsertPalette: function(afterIndex, anchorEl) {
      var self = this;
      // Remove any existing palette
      var existing = document.querySelector('.be-palette');
      if (existing) existing.parentNode.removeChild(existing);

      var palette = _ce('div', 'be-palette');
      var types = [
        {type: 'heading', label: 'Heading', data: {text: 'New Heading', level: 2}},
        {type: 'rich-text', label: 'Text', data: {html: '<p>New text block</p>'}},
        {type: 'workflow', label: 'Workflow', data: {steps: [{id: 'b_' + Math.random().toString(36).substr(2,8), title: 'New Step', description: '', type: 'activity', assignee: ''}], connections: []}},
        {type: 'checklist', label: 'Checklist', data: [{text: 'New item', checked: false, priority: 'normal'}]},
        {type: 'kpi-grid', label: 'KPIs', data: [{name: 'New KPI', value: '0', target: '100', unit: '', trend: 'stable'}]},
        {type: 'table', label: 'Table', data: {columns: ['Column 1', 'Column 2'], rows: [['', '']]}},
        {type: 'timeline', label: 'Timeline', data: [{phase: 'Phase 1', duration: '', activities: ['Activity']}]},
        {type: 'divider', label: 'Divider', data: {style: 'solid'}},
      ];

      types.forEach(function(t) {
        var item = _ce('button', 'be-palette-item', t.label);
        item.onclick = function() {
          self._insertBlock(afterIndex, t.type, t.data);
          palette.parentNode.removeChild(palette);
        };
        palette.appendChild(item);
      });

      // Close on outside click
      setTimeout(function() {
        document.addEventListener('click', function handler(e) {
          if (!palette.contains(e.target)) {
            if (palette.parentNode) palette.parentNode.removeChild(palette);
            document.removeEventListener('click', handler);
          }
        });
      }, 10);

      anchorEl.parentNode.appendChild(palette);
    },

    _insertBlock: function(afterIndex, type, data) {
      var newBlock = {
        id: 'b_' + Math.random().toString(36).substr(2, 12),
        type: type,
        data: JSON.parse(JSON.stringify(data)),
        style: {color_scheme: 'default', layout: 'default', custom_css: null},
        html_cache: ''
      };
      sectionBlocks.splice(afterIndex + 1, 0, newBlock);

      if (window.UndoManager) {
        UndoManager.push({sectionId: sectionId, blockId: newBlock.id, action: 'add', before: null, after: newBlock.data});
      }

      this.renderAll();
      this._initDragDrop();
      this._scheduleSave();
    },

    // --- Drag & Drop ---
    _initDragDrop: function() {
      var container = document.getElementById('editorBlocks');
      if (!container || !window.Sortable) return;

      // Destroy previous instance
      if (container._sortable) container._sortable.destroy();

      var self = this;
      container._sortable = Sortable.create(container, {
        animation: 150,
        handle: '.be-drag-handle',
        draggable: '.be-block-wrapper',
        ghostClass: 'be-ghost',
        onEnd: function(evt) {
          // Reorder sectionBlocks array
          var oldIdx = Math.floor(evt.oldIndex / 2); // account for insert buttons
          var newIdx = Math.floor(evt.newIndex / 2);
          if (oldIdx === newIdx) return;

          var moved = sectionBlocks.splice(oldIdx, 1)[0];
          sectionBlocks.splice(newIdx, 0, moved);

          self.renderAll();
          self._initDragDrop();
          self._scheduleSave();
        }
      });
    },

    // --- Auto-Save ---
    _scheduleSave: function() {
      var self = this;
      this._updateSaveIndicator('saving');
      if (saveTimeout) clearTimeout(saveTimeout);
      saveTimeout = setTimeout(function() { self._save(); }, 1500);
    },

    _save: function() {
      if (saving || !blueprintId || !sectionId) return;
      saving = true;
      var self = this;

      fetchWithAuth('/api/blueprints/' + blueprintId + '/sections/' + sectionId, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify({blocks: sectionBlocks})
      })
      .then(function() {
        saving = false;
        self._updateSaveIndicator('saved');
      })
      .catch(function(e) {
        saving = false;
        self._updateSaveIndicator('error');
        // Queue for offline save
        self._queueOfflineSave();
        console.error('Save failed:', e);
      });
    },

    _updateSaveIndicator: function(status) {
      var indicator = document.getElementById('saveIndicator');
      if (!indicator) {
        indicator = _ce('div', 'be-save-indicator');
        indicator.id = 'saveIndicator';
        var editorMain = document.getElementById('editorMain');
        if (editorMain) editorMain.insertBefore(indicator, editorMain.firstChild);
      }
      indicator.className = 'be-save-indicator be-save-' + status;
      if (status === 'saving') indicator.textContent = 'Saving...';
      else if (status === 'saved') indicator.textContent = 'Saved';
      else if (status === 'error') indicator.textContent = 'Save failed — retrying...';
    },

    _queueOfflineSave: function() {
      try {
        var queue = JSON.parse(localStorage.getItem('blueprint_save_queue') || '[]');
        queue.push({sectionId: sectionId, blueprintId: blueprintId, blocks: sectionBlocks, timestamp: Date.now()});
        localStorage.setItem('blueprint_save_queue', JSON.stringify(queue));
      } catch(e) {}
    },

    flushOfflineQueue: function() {
      try {
        var queue = JSON.parse(localStorage.getItem('blueprint_save_queue') || '[]');
        if (!queue.length) return;
        localStorage.removeItem('blueprint_save_queue');
        queue.forEach(function(item) {
          fetchWithAuth('/api/blueprints/' + item.blueprintId + '/sections/' + item.sectionId, {
            method: 'PUT', headers: authHeaders(),
            body: JSON.stringify({blocks: item.blocks})
          }).catch(function() {});
        });
      } catch(e) {}
    },

    // --- Undo support (called by UndoManager) ---
    applyUndo: function(entry) {
      for (var i = 0; i < sectionBlocks.length; i++) {
        if (sectionBlocks[i].id === entry.blockId) {
          if (entry.action === 'update') {
            sectionBlocks[i].data = JSON.parse(JSON.stringify(entry.before));
            sectionBlocks[i].html_cache = '';
          } else if (entry.action === 'add') {
            sectionBlocks.splice(i, 1);
          }
          break;
        }
      }
      if (entry.action === 'delete' && entry.before) {
        // Re-insert deleted block (at end for simplicity)
        sectionBlocks.push({
          id: entry.blockId, type: 'rich-text', data: entry.before,
          style: {color_scheme: 'default', layout: 'default', custom_css: null}, html_cache: ''
        });
      }
      this.renderAll();
      this._initDragDrop();
      this._scheduleSave();
    },

    applyRedo: function(entry) {
      if (entry.action === 'update') {
        for (var i = 0; i < sectionBlocks.length; i++) {
          if (sectionBlocks[i].id === entry.blockId) {
            sectionBlocks[i].data = JSON.parse(JSON.stringify(entry.after));
            sectionBlocks[i].html_cache = '';
            break;
          }
        }
      } else if (entry.action === 'add') {
        sectionBlocks.push({
          id: entry.blockId, type: 'rich-text', data: entry.after,
          style: {color_scheme: 'default', layout: 'default', custom_css: null}, html_cache: ''
        });
      } else if (entry.action === 'delete') {
        for (var i = 0; i < sectionBlocks.length; i++) {
          if (sectionBlocks[i].id === entry.blockId) {
            sectionBlocks.splice(i, 1);
            break;
          }
        }
      }
      this.renderAll();
      this._initDragDrop();
      this._scheduleSave();
    }
  };

  // Flush offline queue on load
  window.addEventListener('load', function() { BlockEditor.flushOfflineQueue(); });
})();
