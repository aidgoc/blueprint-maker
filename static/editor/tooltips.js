// static/editor/tooltips.js
// First-use editor tour — 4 tooltip steps shown once per user

(function() {
  'use strict';

  var TOUR_KEY = 'editor_toured';
  var currentStep = 0;
  var overlay = null;
  var tooltip = null;

  var steps = [
    { target: '#chatPanel', message: 'Chat with AI to edit your blueprint', position: 'left' },
    { target: '.be-block-wrapper', message: 'Click any block to edit it directly', position: 'bottom' },
    { target: '.be-drag-handle', message: 'Drag to reorder blocks', position: 'right' },
    { target: null, message: 'Press Ctrl+Z to undo any change', position: 'center' }
  ];

  function _ce(tag, cls, text) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text) el.textContent = text;
    return el;
  }

  function startTour() {
    if (localStorage.getItem(TOUR_KEY)) return;
    setTimeout(function() { currentStep = 0; showStep(); }, 800);
  }

  function showStep() {
    cleanup();
    if (currentStep >= steps.length) { completeTour(); return; }

    var step = steps[currentStep];

    overlay = _ce('div', 'tour-overlay');
    overlay.onclick = function() { completeTour(); };
    document.body.appendChild(overlay);

    var targetEl = null;
    if (step.target) {
      targetEl = document.querySelector(step.target);
      if (targetEl) targetEl.classList.add('tour-highlight');
    }

    tooltip = _ce('div', 'tour-tooltip');
    tooltip.appendChild(_ce('div', 'tour-message', step.message));
    tooltip.appendChild(_ce('div', 'tour-counter', (currentStep + 1) + ' / ' + steps.length));

    var actions = _ce('div', 'tour-actions');
    var skipBtn = _ce('button', 'tour-skip', 'Skip tour');
    skipBtn.onclick = function(e) { e.stopPropagation(); completeTour(); };
    actions.appendChild(skipBtn);

    var isLast = currentStep === steps.length - 1;
    var nextBtn = _ce('button', 'tour-next', isLast ? 'Got it!' : 'Next');
    nextBtn.onclick = function(e) {
      e.stopPropagation();
      if (targetEl) targetEl.classList.remove('tour-highlight');
      currentStep++;
      showStep();
    };
    actions.appendChild(nextBtn);
    tooltip.appendChild(actions);
    document.body.appendChild(tooltip);

    // Position tooltip relative to target
    if (targetEl && step.position !== 'center') {
      var rect = targetEl.getBoundingClientRect();
      if (step.position === 'bottom') {
        tooltip.style.top = (rect.bottom + 12) + 'px';
        tooltip.style.left = rect.left + 'px';
      } else if (step.position === 'left') {
        tooltip.style.top = rect.top + 'px';
        tooltip.style.right = (window.innerWidth - rect.left + 12) + 'px';
      } else if (step.position === 'right') {
        tooltip.style.top = rect.top + 'px';
        tooltip.style.left = (rect.right + 12) + 'px';
      }
    } else {
      tooltip.style.top = '50%';
      tooltip.style.left = '50%';
      tooltip.style.transform = 'translate(-50%, -50%)';
    }
  }

  function cleanup() {
    if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
    if (tooltip && tooltip.parentNode) tooltip.parentNode.removeChild(tooltip);
    var highlighted = document.querySelectorAll('.tour-highlight');
    for (var i = 0; i < highlighted.length; i++) highlighted[i].classList.remove('tour-highlight');
  }

  function completeTour() {
    cleanup();
    localStorage.setItem(TOUR_KEY, 'true');
  }

  window.EditorTour = {
    start: startTour,
    reset: function() { localStorage.removeItem(TOUR_KEY); }
  };
})();
