/**
 * NextLeap Chat — frontend logic: send message, display messages and sources.
 */
(function () {
  const API_BASE = ''; // same origin when served from FastAPI

  const messagesEl = document.getElementById('messages');
  const welcomeEl = document.getElementById('welcome');
  const messageInput = document.getElementById('message-input');
  const sendBtn = document.getElementById('send-btn');
  const sourcesList = document.getElementById('sources-list');
  const sourcesEmpty = document.getElementById('sources-empty');

  function hideWelcome() {
    if (welcomeEl) welcomeEl.style.display = 'none';
  }

  function addMessage(role, content, meta) {
    hideWelcome();
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.setAttribute('role', 'listitem');

    const avatar = document.createElement('div');
    avatar.className = role === 'user' ? 'avatar user-avatar' : 'avatar assistant-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'NL';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const p = document.createElement('p');
    p.textContent = content;
    contentDiv.appendChild(p);

    if (meta) {
      const metaSpan = document.createElement('div');
      metaSpan.className = 'message-meta';
      metaSpan.textContent = meta;
      contentDiv.appendChild(metaSpan);
    }

    div.appendChild(avatar);
    div.appendChild(contentDiv);
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  function addLoadingMessage() {
    hideWelcome();
    const div = document.createElement('div');
    div.className = 'message assistant loading';
    div.id = 'loading-msg';
    div.innerHTML = [
      '<div class="avatar assistant-avatar">NL</div>',
      '<div class="message-content">',
      '<div class="typing-dots"><span></span><span></span><span></span></div>',
      '</div>'
    ].join('');
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  function removeLoading() {
    const el = document.getElementById('loading-msg');
    if (el) el.remove();
  }

  function renderSources(sources) {
    if (!sources || sources.length === 0) {
      sourcesEmpty.style.display = 'block';
      sourcesList.querySelectorAll('.source-item').forEach(function (n) { n.remove(); });
      return;
    }
    sourcesEmpty.style.display = 'none';
    sourcesList.querySelectorAll('.source-item').forEach(function (n) { n.remove(); });
    sources.forEach(function (s) {
      const item = document.createElement('div');
      item.className = 'source-item';
      item.innerHTML =
        '<div class="source-course">' + escapeHtml(s.course_name || s.cohort_id || 'Source') + '</div>' +
        '<a class="source-link" href="' + escapeHtml(s.source_url || '#') + '" target="_blank" rel="noopener">' +
        escapeHtml(s.source_url || '') + '</a>';
      sourcesList.appendChild(item);
    });
  }

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function getMeta() {
    var d = new Date();
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function sendMessage() {
    const text = (messageInput.value || '').trim();
    if (!text) return;

    messageInput.value = '';
    sendBtn.disabled = true;

    addMessage('user', text, getMeta());
    addLoadingMessage();

    fetch(API_BASE + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    })
      .then(function (res) {
        if (!res.ok) throw new Error('Request failed: ' + res.status);
        return res.json();
      })
      .then(function (data) {
        removeLoading();
        var answer = data.answer || (data.error ? 'Error: ' + data.error : 'No response.');
        addMessage('assistant', answer, getMeta());
        renderSources(data.sources || []);
      })
      .catch(function (err) {
        removeLoading();
        var msg = err.message || '';
        if (msg.indexOf('fetch') !== -1 || msg === 'Failed to fetch') {
          msg = 'Could not reach the server. Open this app from http://127.0.0.1:8000 (not file://) and ensure the server is running (e.g. bash scripts/start_app.sh).';
        } else {
          msg = 'Sorry, something went wrong. ' + msg;
        }
        addMessage('assistant', msg, getMeta());
        renderSources([]);
      })
      .finally(function () {
        sendBtn.disabled = false;
        messageInput.focus();
      });
  }

  sendBtn.addEventListener('click', sendMessage);
  messageInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  document.querySelectorAll('.question-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var q = this.getAttribute('data-q');
      if (q) {
        messageInput.value = q;
        messageInput.focus();
      }
    });
  });

  function formatLastUpdated(iso) {
    if (!iso) return null;
    try {
      var d = new Date(iso);
      return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (e) {
      return null;
    }
  }

  fetch(API_BASE + '/api/status')
    .then(function (res) { return res.ok ? res.json() : null; })
    .then(function (data) {
      var el = document.getElementById('last-updated');
      if (!el) return;
      var iso = data && data.data_last_refreshed_at;
      var formatted = formatLastUpdated(iso);
      if (formatted) {
        var label = el.querySelector('.last-updated-label');
        var dateEl = el.querySelector('.last-updated-date');
        if (label) label.textContent = 'Data last updated';
        if (dateEl) dateEl.textContent = formatted;
      }
    })
    .catch(function () {});
})();
