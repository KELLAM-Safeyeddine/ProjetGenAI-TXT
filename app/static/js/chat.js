(() => {
  'use strict';
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const send = document.getElementById('send-message');
  const messages = document.getElementById('chat-messages');
  const list = document.getElementById('conversation-list');
  const status = document.getElementById('chat-status');
  const fresh = document.getElementById('new-conversation');
  const vehicle = document.getElementById('vehicle-select');
  const manualLink = document.getElementById('manual-link');
  let conversationId = null;
  let busy = false;
  let uncertain = false;

  function lock(value) {
    busy = value;
    send.disabled = value || uncertain;
    fresh.disabled = value;
    vehicle.disabled = value;
    input.disabled = value || uncertain;
    document.querySelectorAll('.suggestion, .conversation-button').forEach(b => { b.disabled = value; });
    form.setAttribute('aria-busy', String(value));
  }
  function updateVehicle() {
    const option = vehicle.selectedOptions[0];
    manualLink.hidden = !vehicle.value || option.dataset.manual !== 'oui';
    if (vehicle.value) manualLink.href = `/vehicles/${Number(vehicle.value)}/manuel`;
  }
  function add(role, text, metadata = {}) {
    const item = document.createElement('div');
    item.className = `chat-message ${role === 'user' ? 'user' : 'assistant'}`;
    const label = document.createElement('strong');
    label.textContent = role === 'user' ? 'VOUS' : 'ASSISTANT';
    const content = document.createElement('span');
    content.textContent = text;
    if (role === 'user') item.append(label);
    else item.setAttribute('aria-label', 'Assistant');
    item.append(content);
    if (role === 'assistant' && metadata.source !== 'faq' && metadata.source_line && !text.trimEnd().endsWith(metadata.source_line)) {
      const source = document.createElement('small');
      source.className = 'd-block text-muted';
      source.style.whiteSpace = 'pre-line';
      source.textContent = metadata.source_line;
      item.append(source);
    }
    messages.append(item);
    messages.scrollTop = messages.scrollHeight;
    return item;
  }
  async function api(path, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), Number(document.getElementById('chat-budget').dataset.timeout));
    try {
      const response = await fetch(path, { ...options, signal: controller.signal, credentials: 'same-origin', headers: { 'Content-Type':'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content, ...options.headers } });
      let data;
      try { data = await response.json(); } catch { throw new Error('Réponse serveur illisible. Rechargez votre historique.'); }
      if (!response.ok) {
        const error = new Error(response.status === 401 ? 'Session expirée. Reconnectez-vous pour continuer.' : data.error || 'Erreur du service.');
        error.http = response.status;
        throw error;
      }
      return data;
    } finally { clearTimeout(timer); }
  }
  async function history() {
    const data = await api('/api/conversations');
    list.replaceChildren();
    if (!data.conversations.length) {
      const empty = document.createElement('p');
      empty.textContent = 'Aucune conversation pour le moment.';
      empty.className = 'small text-muted';
      list.append(empty);
    }
    for (const c of data.conversations) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'conversation-button';
      button.textContent = c.title;
      button.setAttribute('aria-pressed', String(c.id === conversationId));
      button.addEventListener('click', () => load(c.id));
      list.append(button);
    }
  }
  async function load(id) {
    if (busy) return;
    lock(true);
    try {
      const data = await api(`/api/conversations/${id}/messages`);
      conversationId = data.conversation_id;
      messages.replaceChildren();
      data.messages.forEach(m => add(m.role, m.content, m));
      const lastVehicle = data.messages.at(-1)?.vehicle?.id;
      vehicle.value = [...vehicle.options].some(option => option.value === String(lastVehicle)) ? String(lastVehicle) : '';
      updateVehicle();
      uncertain = false;
      status.textContent = 'Historique chargé.';
      await history();
    } catch (error) { status.textContent = error.message; }
    finally { lock(false); }
  }
  function newConversation() {
    if (busy) return;
    conversationId = null;
    uncertain = false;
    messages.replaceChildren();
    status.textContent = '';
    lock(false);
    input.focus();
    history().catch(error => { status.textContent = error.message; });
  }
  async function submit(event) {
    event.preventDefault();
    if (busy || uncertain) return;
    const text = input.value.trim();
    if (!text || text.length > 1000) { status.textContent = 'Écrivez une question de 1 à 1 000 caractères.'; return; }
    lock(true);
    const pending = add('user', text);
    status.textContent = 'Un instant…';
    try {
      const payload = { message:text };
      if (conversationId) payload.conversation_id = conversationId;
      if (vehicle.value) payload.vehicle_id = Number(vehicle.value);
      const data = await api('/api/chat', { method:'POST', body:JSON.stringify(payload) });
      conversationId = data.conversation_id;
      add('assistant', data.reply, data);
      input.value = '';
      status.textContent = '';
    } catch (error) {
      if (error.http && error.http < 500) pending.remove();
      else uncertain = true;
      status.textContent = uncertain ? 'Envoi non confirmé. Consultez l’historique ou ouvrez une nouvelle conversation avant de poursuivre ; votre question a peut-être été enregistrée.' : error.message;
    } finally {
      try { await history(); } catch (error) { status.textContent += ' Historique indisponible : ' + error.message; }
      lock(false);
      if (!uncertain) input.focus();
    }
  }
  form.addEventListener('submit', submit);
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); form.requestSubmit(); }
  });
  fresh.addEventListener('click', newConversation);
  vehicle.addEventListener('change', updateVehicle);
  document.querySelectorAll('.suggestion').forEach(button => button.addEventListener('click', () => { if (!busy && !uncertain) { input.value = button.textContent; input.focus(); } }));
  updateVehicle();
  newConversation();
})();
