# Plan 3B: Visual Inline Editor + Auto-Save/Undo

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add click-to-edit visual editing for all 12 block types, drag-to-reorder via SortableJS, block toolbar (edit/move/duplicate/delete), style panel, and auto-save with undo/redo.

**Architecture:** A global `BlockEditor` object manages block registration, toolbar, drag-drop, and edit mode. Each block type registers a `render()` and `editor()` function. Auto-save debounces edits and PUTs to the section endpoint. Undo/redo stores client-side patches.

**Tech Stack:** Vanilla JS, SortableJS (CDN, ~8KB), existing FastAPI section endpoints

**Spec:** `docs/superpowers/specs/2026-03-14-blueprint-editor-design.md` — Sections 5 and 6

**Depends on:** Plan 1 (section API endpoints), Plan 2 (EditorScreen in index.html)

**Security:** All user content rendered via `textContent`. Only server-generated `html_cache` uses trusted DOM insertion.

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `static/editor/editor.js` | BlockEditor engine: registration, toolbar, drag-drop, edit mode, insert palette |
| `static/editor/blocks/heading.js` | Heading block render + editor |
| `static/editor/blocks/rich-text.js` | Rich text block render + editor |
| `static/editor/blocks/workflow.js` | Workflow block render + editor |
| `static/editor/blocks/kpi-grid.js` | KPI grid block render + editor |
| `static/editor/blocks/checklist.js` | Checklist block render + editor |
| `static/editor/blocks/table.js` | Table block render + editor |
| `static/editor/blocks/timeline.js` | Timeline block render + editor |
| `static/editor/blocks/card-grid.js` | Card grid block render + editor |
| `static/editor/blocks/glossary.js` | Glossary block render + editor |
| `static/editor/blocks/org-chart.js` | Org chart block render + editor |
| `static/editor/blocks/flow-diagram.js` | Flow diagram block render + editor |
| `static/editor/blocks/divider.js` | Divider block render + editor |
| `static/editor/style-panel.js` | Block style popover (colors, layout) |
| `static/editor/undo.js` | Undo/redo manager with keyboard shortcuts |

### Modified Files
| File | Changes |
|------|---------|
| `static/index.html` | Add script tags for all editor files, add SortableJS CDN, update EditorScreen.renderBlocks to use BlockEditor |

---

## Chunk 1: Block Editor Engine

### Task 1: Create the core BlockEditor engine

**Files:**
- Create: `static/editor/editor.js`

- [ ] **Step 1: Create editor.js**

This is the core engine that all block types register with. It must load first.

```javascript
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
```

- [ ] **Step 2: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/editor/editor.js
git commit -m "feat: add BlockEditor engine with toolbar, drag-drop, insert palette, auto-save"
```

---

## Chunk 2: Basic Block Type Editors (heading, rich-text, divider, checklist)

### Task 2: Implement editors for the simplest block types

**Files:**
- Create: `static/editor/blocks/heading.js`
- Create: `static/editor/blocks/rich-text.js`
- Create: `static/editor/blocks/divider.js`
- Create: `static/editor/blocks/checklist.js`

- [ ] **Step 1: Create heading.js**

```javascript
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
```

- [ ] **Step 2: Create rich-text.js**

```javascript
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
```

- [ ] **Step 3: Create divider.js**

```javascript
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
```

- [ ] **Step 4: Create checklist.js**

```javascript
// static/editor/blocks/checklist.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  BlockEditor.registerBlockType('checklist', {
    render: function(data, style) {
      var ul = _ce('ul', 'be-checklist');
      (data || []).forEach(function(item) {
        var li = _ce('li', item.priority === 'high' ? 'be-cl-high' : '');
        var chk = _ce('span', 'be-cl-check' + (item.checked ? ' checked' : ''));
        li.appendChild(chk);
        li.appendChild(_ce('span', null, item.text || ''));
        ul.appendChild(li);
      });
      return ul;
    },
    editor: function(data, style, onChange) {
      var items = JSON.parse(JSON.stringify(data || []));
      var container = _ce('div', 'be-editor-checklist');

      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        items.forEach(function(item, idx) {
          var row = _ce('div', 'be-cl-row');

          var chk = document.createElement('input');
          chk.type = 'checkbox';
          chk.checked = item.checked;
          chk.onchange = function() { items[idx].checked = chk.checked; onChange(items); };
          row.appendChild(chk);

          var input = document.createElement('input');
          input.type = 'text';
          input.className = 'be-input be-cl-input';
          input.value = item.text || '';
          input.oninput = function() { items[idx].text = input.value; onChange(items); };
          row.appendChild(input);

          var priSel = document.createElement('select');
          priSel.className = 'be-select-sm';
          ['normal','high','low'].forEach(function(p) {
            var o = document.createElement('option'); o.value = p; o.textContent = p;
            if (p === item.priority) o.selected = true; priSel.appendChild(o);
          });
          priSel.onchange = function() { items[idx].priority = priSel.value; onChange(items); };
          row.appendChild(priSel);

          var delBtn = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          delBtn.onclick = function() { items.splice(idx, 1); onChange(items); rebuild(); };
          row.appendChild(delBtn);

          container.appendChild(row);
        });

        var addBtn = _ce('button', 'be-btn-add', '+ Add Item');
        addBtn.onclick = function() {
          items.push({text: '', checked: false, priority: 'normal'});
          onChange(items); rebuild();
        };
        container.appendChild(addBtn);
      }
      rebuild();
      return container;
    }
  });
})();
```

- [ ] **Step 5: Create blocks directory and commit**

```bash
mkdir -p /home/harshwardhan/blueprint_maker/static/editor/blocks
cd /home/harshwardhan/blueprint_maker
git add static/editor/blocks/heading.js static/editor/blocks/rich-text.js static/editor/blocks/divider.js static/editor/blocks/checklist.js
git commit -m "feat: add block editors for heading, rich-text, divider, checklist"
```

---

## Chunk 3: Complex Block Type Editors (workflow, kpi-grid, table, timeline)

### Task 3: Implement editors for structured block types

**Files:**
- Create: `static/editor/blocks/workflow.js`
- Create: `static/editor/blocks/kpi-grid.js`
- Create: `static/editor/blocks/table.js`
- Create: `static/editor/blocks/timeline.js`

- [ ] **Step 1: Create workflow.js**

```javascript
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
```

- [ ] **Step 2: Create kpi-grid.js**

```javascript
// static/editor/blocks/kpi-grid.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  BlockEditor.registerBlockType('kpi-grid', {
    render: function(data, style) {
      var grid = _ce('div', 'be-kpi-grid');
      (data || []).forEach(function(kpi) {
        var card = _ce('div', 'be-kpi-card');
        card.appendChild(_ce('div', 'be-kpi-name', kpi.name || ''));
        card.appendChild(_ce('div', 'be-kpi-value', (kpi.unit || '') + (kpi.value || '')));
        card.appendChild(_ce('div', 'be-kpi-target', 'Target: ' + (kpi.unit || '') + (kpi.target || '')));
        grid.appendChild(card);
      });
      return grid;
    },
    editor: function(data, style, onChange) {
      var items = JSON.parse(JSON.stringify(data || []));
      var container = _ce('div', 'be-editor-kpi');

      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        items.forEach(function(kpi, idx) {
          var row = _ce('div', 'be-kpi-row');
          ['name','value','target','unit'].forEach(function(field) {
            var inp = document.createElement('input');
            inp.className = 'be-input be-input-sm'; inp.placeholder = field; inp.value = kpi[field] || '';
            inp.oninput = function() { items[idx][field] = inp.value; onChange(items); };
            row.appendChild(inp);
          });
          var trendSel = document.createElement('select');
          trendSel.className = 'be-select-sm';
          ['stable','up','down'].forEach(function(t) {
            var o = document.createElement('option'); o.value = t; o.textContent = t;
            if (t === (kpi.trend || 'stable')) o.selected = true; trendSel.appendChild(o);
          });
          trendSel.onchange = function() { items[idx].trend = trendSel.value; onChange(items); };
          row.appendChild(trendSel);
          var del = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          del.onclick = function() { items.splice(idx, 1); onChange(items); rebuild(); };
          row.appendChild(del);
          container.appendChild(row);
        });
        var addBtn = _ce('button', 'be-btn-add', '+ Add KPI');
        addBtn.onclick = function() { items.push({name:'',value:'',target:'',unit:'',trend:'stable'}); onChange(items); rebuild(); };
        container.appendChild(addBtn);
      }
      rebuild();
      return container;
    }
  });
})();
```

- [ ] **Step 3: Create table.js**

```javascript
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
```

- [ ] **Step 4: Create timeline.js**

```javascript
// static/editor/blocks/timeline.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  BlockEditor.registerBlockType('timeline', {
    render: function(data, style) {
      var div = _ce('div', 'be-timeline');
      (data || []).forEach(function(item) {
        var row = _ce('div', 'be-tl-item');
        row.appendChild(_ce('div', 'be-tl-phase', item.phase || ''));
        if (item.duration) row.appendChild(_ce('div', 'be-tl-dur', item.duration));
        (item.activities || []).forEach(function(a) { row.appendChild(_ce('div', 'be-tl-act', a)); });
        div.appendChild(row);
      });
      return div;
    },
    editor: function(data, style, onChange) {
      var items = JSON.parse(JSON.stringify(data || []));
      var container = _ce('div', 'be-editor-timeline');

      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        items.forEach(function(item, idx) {
          var row = _ce('div', 'be-tl-edit-row');
          var phaseIn = document.createElement('input');
          phaseIn.className = 'be-input'; phaseIn.placeholder = 'Phase'; phaseIn.value = item.phase || '';
          phaseIn.oninput = function() { items[idx].phase = phaseIn.value; onChange(items); };
          row.appendChild(phaseIn);

          var durIn = document.createElement('input');
          durIn.className = 'be-input be-input-sm'; durIn.placeholder = 'Duration'; durIn.value = item.duration || '';
          durIn.oninput = function() { items[idx].duration = durIn.value; onChange(items); };
          row.appendChild(durIn);

          // Activities as comma-separated
          var actIn = document.createElement('input');
          actIn.className = 'be-input'; actIn.placeholder = 'Activities (comma-separated)';
          actIn.value = (item.activities || []).join(', ');
          actIn.oninput = function() { items[idx].activities = actIn.value.split(',').map(function(a) { return a.trim(); }).filter(Boolean); onChange(items); };
          row.appendChild(actIn);

          var del = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          del.onclick = function() { items.splice(idx, 1); onChange(items); rebuild(); };
          row.appendChild(del);
          container.appendChild(row);
        });

        var addBtn = _ce('button', 'be-btn-add', '+ Add Phase');
        addBtn.onclick = function() { items.push({phase: '', duration: '', activities: []}); onChange(items); rebuild(); };
        container.appendChild(addBtn);
      }
      rebuild();
      return container;
    }
  });
})();
```

- [ ] **Step 5: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/editor/blocks/workflow.js static/editor/blocks/kpi-grid.js static/editor/blocks/table.js static/editor/blocks/timeline.js
git commit -m "feat: add block editors for workflow, kpi-grid, table, timeline"
```

---

## Chunk 4: Remaining Block Type Editors

### Task 4: Implement editors for card-grid, glossary, org-chart, flow-diagram

**Files:**
- Create: `static/editor/blocks/card-grid.js`
- Create: `static/editor/blocks/glossary.js`
- Create: `static/editor/blocks/org-chart.js`
- Create: `static/editor/blocks/flow-diagram.js`

- [ ] **Step 1: Create card-grid.js**

```javascript
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
```

- [ ] **Step 2: Create glossary.js**

```javascript
// static/editor/blocks/glossary.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }
  BlockEditor.registerBlockType('glossary', {
    render: function(data, style) {
      var div = _ce('div', 'be-glossary');
      (data || []).forEach(function(entry) {
        var el = _ce('div', 'be-gl-entry');
        el.appendChild(_ce('span', 'be-gl-term', entry.term || ''));
        el.appendChild(_ce('span', null, ' — '));
        el.appendChild(_ce('span', 'be-gl-def', entry.definition || ''));
        div.appendChild(el);
      });
      return div;
    },
    editor: function(data, style, onChange) {
      var terms = JSON.parse(JSON.stringify(data || []));
      var container = _ce('div', 'be-editor-glossary');
      function rebuild() {
        while (container.firstChild) container.removeChild(container.firstChild);
        terms.forEach(function(t, idx) {
          var row = _ce('div', 'be-gl-row');
          var termIn = document.createElement('input');
          termIn.className = 'be-input be-input-sm'; termIn.placeholder = 'Term'; termIn.value = t.term || '';
          termIn.oninput = function() { terms[idx].term = termIn.value; onChange(terms); };
          row.appendChild(termIn);
          var defIn = document.createElement('input');
          defIn.className = 'be-input'; defIn.placeholder = 'Definition'; defIn.value = t.definition || '';
          defIn.oninput = function() { terms[idx].definition = defIn.value; onChange(terms); };
          row.appendChild(defIn);
          var del = _ce('button', 'be-btn-sm be-btn-del', '\u00d7');
          del.onclick = function() { terms.splice(idx, 1); onChange(terms); rebuild(); };
          row.appendChild(del);
          container.appendChild(row);
        });
        var addBtn = _ce('button', 'be-btn-add', '+ Add Term');
        addBtn.onclick = function() { terms.push({term: '', definition: '', related: []}); onChange(terms); rebuild(); };
        container.appendChild(addBtn);
      }
      rebuild(); return container;
    }
  });
})();
```

- [ ] **Step 3: Create org-chart.js**

```javascript
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
```

- [ ] **Step 4: Create flow-diagram.js**

```javascript
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
```

- [ ] **Step 5: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/editor/blocks/card-grid.js static/editor/blocks/glossary.js static/editor/blocks/org-chart.js static/editor/blocks/flow-diagram.js
git commit -m "feat: add block editors for card-grid, glossary, org-chart, flow-diagram"
```

---

## Chunk 5: Style Panel + Undo Manager

### Task 5: Create style panel and undo/redo

**Files:**
- Create: `static/editor/style-panel.js`
- Create: `static/editor/undo.js`

- [ ] **Step 1: Create style-panel.js**

```javascript
// static/editor/style-panel.js
(function() {
  function _ce(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el;
  }

  window.StylePanel = {
    show: function(block, anchor) {
      this.hide();
      var panel = _ce('div', 'be-style-panel');
      panel.id = 'stylePanel';

      panel.appendChild(_ce('div', 'be-style-title', 'Block Style'));

      // Color scheme
      panel.appendChild(_ce('label', 'be-style-label', 'Color'));
      var colors = ['default','blue','green','orange','red','purple','teal'];
      var colorRow = _ce('div', 'be-style-colors');
      colors.forEach(function(c) {
        var swatch = _ce('button', 'be-swatch be-swatch-' + c);
        if (c === (block.style.color_scheme || 'default')) swatch.classList.add('active');
        swatch.onclick = function() {
          block.style.color_scheme = c;
          block.html_cache = '';
          BlockEditor.renderAll();
          BlockEditor._scheduleSave();
          StylePanel.hide();
        };
        colorRow.appendChild(swatch);
      });
      panel.appendChild(colorRow);

      // Layout
      panel.appendChild(_ce('label', 'be-style-label', 'Layout'));
      var layouts = ['default','compact','wide'];
      var layoutSel = document.createElement('select');
      layoutSel.className = 'be-select';
      layouts.forEach(function(l) {
        var o = document.createElement('option'); o.value = l; o.textContent = l;
        if (l === (block.style.layout || 'default')) o.selected = true;
        layoutSel.appendChild(o);
      });
      layoutSel.onchange = function() {
        block.style.layout = layoutSel.value;
        block.html_cache = '';
        BlockEditor.renderAll();
        BlockEditor._scheduleSave();
      };
      panel.appendChild(layoutSel);

      // Position near anchor
      document.body.appendChild(panel);
      var rect = anchor.getBoundingClientRect();
      panel.style.top = (rect.bottom + 5) + 'px';
      panel.style.left = rect.left + 'px';

      // Close on outside click
      setTimeout(function() {
        document.addEventListener('click', function handler(e) {
          if (!panel.contains(e.target) && e.target !== anchor) {
            StylePanel.hide();
            document.removeEventListener('click', handler);
          }
        });
      }, 10);
    },

    hide: function() {
      var existing = document.getElementById('stylePanel');
      if (existing) existing.parentNode.removeChild(existing);
    }
  };
})();
```

- [ ] **Step 2: Create undo.js**

```javascript
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
```

- [ ] **Step 3: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/editor/style-panel.js static/editor/undo.js
git commit -m "feat: add style panel and undo/redo manager with keyboard shortcuts"
```

---

## Chunk 6: Wire Everything into index.html

### Task 6: Add script tags, SortableJS CDN, editor CSS, and update EditorScreen

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add SortableJS CDN**

In the `<head>` section of `index.html`, add:

```html
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js"></script>
```

- [ ] **Step 2: Add all editor script tags**

At the end of `<body>`, before `</body>`, add the script tags in the correct loading order (editor.js first, block types next, utilities last):

```html
<!-- Block Editor -->
<script src="/static/editor/editor.js"></script>
<!-- Block Types (register with BlockEditor) -->
<script src="/static/editor/blocks/heading.js"></script>
<script src="/static/editor/blocks/rich-text.js"></script>
<script src="/static/editor/blocks/workflow.js"></script>
<script src="/static/editor/blocks/kpi-grid.js"></script>
<script src="/static/editor/blocks/checklist.js"></script>
<script src="/static/editor/blocks/table.js"></script>
<script src="/static/editor/blocks/timeline.js"></script>
<script src="/static/editor/blocks/card-grid.js"></script>
<script src="/static/editor/blocks/glossary.js"></script>
<script src="/static/editor/blocks/org-chart.js"></script>
<script src="/static/editor/blocks/flow-diagram.js"></script>
<script src="/static/editor/blocks/divider.js"></script>
<!-- Editor utilities (attach to BlockEditor) -->
<script src="/static/editor/style-panel.js"></script>
<script src="/static/editor/undo.js"></script>
```

- [ ] **Step 3: Add editor CSS to index.html**

Add comprehensive CSS for the block editor in the `<style>` section:

```css
/* Block Editor */
.be-block-wrapper { position: relative; margin-bottom: 0.5rem; border: 1px solid transparent; border-radius: 6px; transition: border-color 0.15s; }
.be-block-wrapper:hover { border-color: var(--border); }
.be-block-wrapper:hover .be-toolbar { opacity: 1; }
.be-toolbar { position: absolute; top: -32px; right: 0; display: flex; gap: 2px; opacity: 0; transition: opacity 0.15s; background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 2px; z-index: 10; box-shadow: var(--shadow); }
.be-tb-btn { background: none; border: none; padding: 4px 8px; cursor: pointer; font-size: 0.75rem; border-radius: 4px; color: var(--text-light); }
.be-tb-btn:hover { background: var(--blue-bg); color: var(--brand); }
.be-tb-del:hover { background: var(--red-bg); color: var(--red); }
.be-drag-handle { cursor: grab; padding: 4px 6px; font-size: 0.9rem; color: var(--text-light); }
.be-block-content { padding: 0.5rem; }
.be-ghost { opacity: 0.4; }
.be-insert-btn { text-align: center; height: 20px; position: relative; }
.be-insert-plus { width: 24px; height: 24px; border-radius: 50%; border: 1px dashed var(--border); background: var(--surface); color: var(--text-light); cursor: pointer; font-size: 1rem; line-height: 1; opacity: 0; transition: opacity 0.15s; }
.be-insert-btn:hover .be-insert-plus { opacity: 1; }
.be-insert-plus:hover { border-color: var(--brand); color: var(--brand); background: var(--blue-bg); }
.be-palette { position: absolute; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; box-shadow: var(--shadow); padding: 0.5rem; display: flex; flex-wrap: wrap; gap: 4px; z-index: 20; max-width: 300px; }
.be-palette-item { background: none; border: 1px solid var(--border); padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
.be-palette-item:hover { background: var(--blue-bg); border-color: var(--brand); }
.be-done-btn { margin-top: 0.75rem; background: var(--brand); color: white; border: none; padding: 6px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; }
.be-input { width: 100%; border: 1px solid var(--border); border-radius: 4px; padding: 6px 8px; font-size: 0.9rem; margin-bottom: 4px; font-family: inherit; }
.be-input:focus { outline: none; border-color: var(--brand); }
.be-input-sm { width: auto; min-width: 100px; }
.be-textarea { width: 100%; border: 1px solid var(--border); border-radius: 4px; padding: 6px 8px; font-size: 0.9rem; font-family: inherit; resize: vertical; }
.be-textarea-sm { width: 100%; border: 1px solid var(--border); border-radius: 4px; padding: 4px 6px; font-size: 0.85rem; font-family: inherit; resize: vertical; }
.be-select { border: 1px solid var(--border); border-radius: 4px; padding: 4px 8px; font-size: 0.85rem; }
.be-select-sm { border: 1px solid var(--border); border-radius: 4px; padding: 2px 4px; font-size: 0.8rem; }
.be-btn-add { background: none; border: 1px dashed var(--border); color: var(--text-light); padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 0.85rem; margin-top: 4px; }
.be-btn-add:hover { border-color: var(--brand); color: var(--brand); }
.be-btn-sm { background: none; border: none; cursor: pointer; padding: 2px 6px; font-size: 0.85rem; color: var(--text-light); }
.be-btn-del:hover { color: var(--red); }
.be-hint { font-size: 0.8rem; color: var(--text-light); margin-top: 2px; }
.be-section-label { font-weight: 600; margin: 0.5rem 0 0.25rem; font-size: 0.85rem; }
.be-no-editor { color: var(--text-light); font-style: italic; padding: 1rem; }
.be-save-indicator { padding: 4px 12px; font-size: 0.8rem; color: var(--text-light); text-align: right; }
.be-save-saving { color: var(--amber); }
.be-save-saved { color: var(--green); }
.be-save-error { color: var(--red); }
/* Block type specific render styles */
.be-wf-step { display: flex; gap: 0.5rem; padding: 0.5rem; background: var(--surface); border: 1px solid var(--border); border-radius: 4px; margin-bottom: 4px; }
.be-wf-num { width: 24px; height: 24px; border-radius: 50%; background: var(--brand); color: white; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; flex-shrink: 0; }
.be-wf-title { font-weight: 600; } .be-wf-desc { font-size: 0.85rem; color: var(--text-light); } .be-wf-assignee { font-size: 0.8rem; color: var(--accent); }
.be-wf-edit-row { display: flex; gap: 0.5rem; align-items: flex-start; margin-bottom: 0.5rem; padding: 0.5rem; background: var(--bg); border-radius: 4px; }
.be-wf-fields { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.be-cl-row { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 4px; }
.be-cl-input { flex: 1; }
.be-kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 0.75rem; }
.be-kpi-card { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 0.75rem; }
.be-kpi-name { font-size: 0.8rem; color: var(--text-light); text-transform: uppercase; }
.be-kpi-value { font-size: 1.25rem; font-weight: 700; color: var(--brand); }
.be-kpi-target { font-size: 0.8rem; color: var(--text-light); }
.be-kpi-row { display: flex; gap: 4px; align-items: center; margin-bottom: 4px; }
.be-table { width: 100%; border-collapse: collapse; }
.be-table th { background: var(--brand); color: white; padding: 0.5rem; text-align: left; }
.be-table td { padding: 0.5rem; border-bottom: 1px solid var(--border); }
.be-table-row { display: flex; gap: 4px; margin-bottom: 4px; }
.be-timeline .be-tl-item { padding: 0.5rem 0; border-left: 2px solid var(--brand); padding-left: 1rem; margin-bottom: 0.25rem; }
.be-tl-phase { font-weight: 600; color: var(--brand); }
.be-tl-dur { font-size: 0.85rem; color: var(--text-light); }
.be-tl-act { font-size: 0.9rem; }
.be-tl-edit-row { display: flex; gap: 4px; margin-bottom: 4px; flex-wrap: wrap; }
.be-card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 0.5rem; }
.be-card { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 0.5rem; border-left: 3px solid var(--accent); }
.be-card-activity { border-left-color: var(--accent); }
.be-card-title { font-weight: 600; font-size: 0.9rem; }
.be-card-item { font-size: 0.85rem; color: var(--text-light); }
.be-card-edit { margin-bottom: 0.75rem; padding: 0.5rem; background: var(--bg); border-radius: 4px; }
.be-glossary .be-gl-entry { padding: 0.35rem 0; border-bottom: 1px solid var(--border); }
.be-gl-term { font-weight: 600; color: var(--brand); }
.be-gl-def { color: var(--text); }
.be-gl-row { display: flex; gap: 4px; margin-bottom: 4px; }
.be-org .be-org-role { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 0.75rem; margin-bottom: 0.5rem; }
.be-org-title { font-weight: 700; color: var(--brand); }
.be-org-reports { font-size: 0.85rem; color: var(--text-light); }
.be-org-resp { font-size: 0.9rem; padding-left: 0.5rem; }
.be-org-edit { margin-bottom: 0.75rem; padding: 0.5rem; background: var(--bg); border-radius: 4px; }
.be-flow-nodes { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.5rem; }
.be-flow-node { background: var(--surface); border: 2px solid var(--brand); border-radius: 6px; padding: 4px 10px; font-weight: 600; font-size: 0.85rem; }
.be-flow-center { background: var(--brand); color: white; }
.be-flow-edge { font-size: 0.85rem; color: var(--text-light); padding: 2px 0; }
.be-flow-row { display: flex; gap: 4px; margin-bottom: 4px; }
.be-checklist { list-style: none; padding: 0; }
.be-checklist li { padding: 0.35rem 0; display: flex; align-items: center; gap: 0.5rem; border-bottom: 1px solid var(--border); }
.be-cl-check { width: 14px; height: 14px; border: 2px solid var(--border); border-radius: 3px; flex-shrink: 0; }
.be-cl-check.checked { background: var(--green); border-color: var(--green); }
.be-cl-high { border-left: 3px solid var(--red); padding-left: 0.5rem; }
.be-divider { border: none; }
.be-divider-solid { border-top: 2px solid var(--border); margin: 1rem 0; }
.be-divider-dashed { border-top: 2px dashed var(--border); margin: 1rem 0; }
.be-divider-dotted { border-top: 2px dotted var(--border); margin: 1rem 0; }
.be-rendered-heading { margin-bottom: 0; }
/* Style panel */
.be-style-panel { position: fixed; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); padding: 1rem; z-index: 100; min-width: 200px; }
.be-style-title { font-weight: 600; margin-bottom: 0.5rem; }
.be-style-label { display: block; font-size: 0.8rem; color: var(--text-light); margin: 0.5rem 0 0.25rem; }
.be-style-colors { display: flex; gap: 6px; }
.be-swatch { width: 24px; height: 24px; border-radius: 50%; border: 2px solid var(--border); cursor: pointer; }
.be-swatch.active { border-color: var(--brand); box-shadow: 0 0 0 2px var(--brand); }
.be-swatch-default { background: var(--surface); }
.be-swatch-blue { background: #3B82F6; }
.be-swatch-green { background: #10B981; }
.be-swatch-orange { background: #F59E0B; }
.be-swatch-red { background: #EF4444; }
.be-swatch-purple { background: #8B5CF6; }
.be-swatch-teal { background: #14B8A6; }
```

- [ ] **Step 4: Update EditorScreen.renderBlocks to use BlockEditor**

Find the existing `EditorScreen.renderBlocks` function in `index.html` and replace it to use `BlockEditor.init()`:

```javascript
renderBlocks: function(section) {
  // Initialize the block editor with this section's data
  BlockEditor.init(editorBlueprintId, section.id, section.blocks || []);
  // Clear undo stack for new section
  if (window.UndoManager) UndoManager.clear();
},
```

Also update `EditorScreen.reloadSection` to re-init:

```javascript
reloadSection: function(sectionId) {
  if (sectionId === editorCurrentSection) {
    this.loadSection(sectionId);
  }
},
```

- [ ] **Step 5: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/index.html
git commit -m "feat: wire block editor, style panel, undo into index.html with SortableJS"
```

---

## Summary

After completing this plan:
1. **BlockEditor engine** with toolbar, drag-drop (SortableJS), insert palette, auto-save
2. **12 block type editors** — click any block to edit with type-specific UI
3. **Style panel** — change color scheme and layout per block
4. **Undo/redo** — Ctrl+Z/Ctrl+Y with 50-entry stack
5. **Auto-save** — debounced 1.5s, save indicator, offline queue
6. **Insert palette** — "+" buttons between blocks to add new blocks from a palette

All vanilla JS, no build step, SortableJS from CDN as the only dependency.
