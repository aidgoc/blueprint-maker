// static/editor/chat-panel.js
// Chat panel UI for blueprint editing
// SECURITY: All user content rendered via textContent, never innerHTML

(function() {
  'use strict';

  var chatMessages = [];
  var chatBlueprintId = null;
  var chatSectionId = null;
  var chatLoading = false;

  function createEl(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text) el.textContent = text;
    return el;
  }

  window.ChatPanel = {
    init: function(blueprintId, sectionId) {
      chatBlueprintId = blueprintId;
      chatSectionId = sectionId;
      chatMessages = [];
      this.render();
    },

    setSectionId: function(sectionId) {
      chatSectionId = sectionId;
    },

    render: function() {
      var panel = document.getElementById('chatPanel');
      if (!panel) return;
      while (panel.firstChild) panel.removeChild(panel.firstChild);

      // Header
      var header = createEl('div', 'chat-header');
      header.appendChild(createEl('h4', null, 'Edit with AI'));
      header.appendChild(createEl('span', 'chat-hint', 'Describe what you want to change'));
      panel.appendChild(header);

      // Messages area
      var msgArea = createEl('div', 'chat-messages');
      msgArea.id = 'chatMessages';
      chatMessages.forEach(function(msg) {
        var el = createEl('div', 'chat-msg chat-msg-' + msg.role, msg.content);
        msgArea.appendChild(el);
      });
      panel.appendChild(msgArea);

      // Input area
      var inputArea = createEl('div', 'chat-input-area');

      var input = document.createElement('textarea');
      input.className = 'chat-input';
      input.id = 'chatInput';
      input.placeholder = 'e.g., "Add a quality check step after dispatch"';
      input.rows = 2;
      input.onkeydown = function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          ChatPanel.send();
        }
      };
      inputArea.appendChild(input);

      var sendBtn = createEl('button', 'chat-send-btn', 'Send');
      sendBtn.id = 'chatSendBtn';
      sendBtn.onclick = function() { ChatPanel.send(); };
      inputArea.appendChild(sendBtn);

      panel.appendChild(inputArea);

      // Scroll to bottom
      setTimeout(function() { msgArea.scrollTop = msgArea.scrollHeight; }, 50);
    },

    send: function() {
      if (chatLoading || !chatBlueprintId) return;
      var input = document.getElementById('chatInput');
      var message = input.value.trim();
      if (!message) return;

      // Add user message
      chatMessages.push({role: 'user', content: message});
      input.value = '';
      this.render();

      // Show loading
      chatLoading = true;
      var sendBtn = document.getElementById('chatSendBtn');
      if (sendBtn) { sendBtn.disabled = true; sendBtn.textContent = 'Thinking...'; }

      var msgArea = document.getElementById('chatMessages');
      var loadingEl = createEl('div', 'chat-msg chat-msg-loading');
      var typing = createEl('div', 'chat-typing');
      typing.appendChild(createEl('span'));
      typing.appendChild(createEl('span'));
      typing.appendChild(createEl('span'));
      loadingEl.appendChild(typing);
      if (msgArea) msgArea.appendChild(loadingEl);

      fetchWithAuth('/api/blueprints/' + chatBlueprintId + '/chat', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({message: message, section_id: chatSectionId})
      })
      .then(function(data) {
        chatLoading = false;
        chatMessages.push({role: 'assistant', content: data.response || 'Changes applied.'});
        ChatPanel.render();

        // If changes were made, reload the current section
        if (data.sections && data.sections.length > 0) {
          if (window.EditorScreen && window.EditorScreen.reloadSection) {
            window.EditorScreen.reloadSection(chatSectionId);
          }
        }
      })
      .catch(function(e) {
        chatLoading = false;
        chatMessages.push({role: 'assistant', content: 'Error: ' + e.message});
        ChatPanel.render();
      });
    }
  };
})();
