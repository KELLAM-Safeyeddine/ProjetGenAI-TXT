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
  let conversationId = null;
  let busy = false;
  let uncertain = false;
  const older=document.getElementById('older-messages');
  let olderCursor=null;

  function lock(value) {
    busy = value;
    send.disabled = value || uncertain;
    fresh.disabled = value;
    vehicle.disabled = value;
    older.disabled=value;
    input.disabled = value || uncertain;
    document.querySelectorAll('.suggestion, .conversation-button').forEach(b => { b.disabled = value; });
    form.setAttribute('aria-busy', String(value));
    messages.setAttribute('aria-busy',String(value));
    document.getElementById('chat-progress').hidden=!value;
    document.querySelectorAll('.conversation-action').forEach(b=>{b.disabled=value;});
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
    const messageId = metadata.id || metadata.message_id;
    if (role === 'assistant' && messageId) {
      const controls = document.createElement('fieldset');
      const legend = document.createElement('legend'); legend.className='small'; legend.textContent='Cette réponse vous aide ?';
      const comment=document.createElement('input'); comment.className='form-control form-control-sm'; comment.maxLength=1000; comment.placeholder='Commentaire facultatif'; comment.setAttribute('aria-label','Commentaire sur cette réponse'); comment.value=metadata.feedback?.comment||'';
      controls.append(legend,comment);
      for (const [value,label] of [[true,'Utile'],[false,'Pas utile']]) {
        const button=document.createElement('button'); button.type='button'; button.className='btn btn-sm btn-outline-secondary'; button.textContent=label;
        button.setAttribute('aria-pressed',String(metadata.feedback?.helpful===value));
        button.addEventListener('click',async()=>{button.disabled=true;try{await api(`/api/messages/${messageId}/feedback`,{method:'POST',body:JSON.stringify({helpful:value,comment:comment.value})});controls.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));status.textContent='Retour enregistré.';}catch(error){status.textContent=error.message;}finally{button.disabled=false;}});
        controls.append(button);
      }
      item.append(controls);
    }
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
  async function history(before=null) {
    const data = await api('/api/conversations'+(before?`?before_id=${before}`:''));
    if(!before)list.replaceChildren();
    list.querySelector('.load-more')?.remove();
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
      const title=document.createElement('input');title.type='text';title.maxLength=80;title.value=c.title;title.className='form-control form-control-sm';title.setAttribute('aria-label','Nouveau titre de la conversation');title.hidden=true;
      const rename=document.createElement('button');rename.type='button';rename.className='btn btn-sm btn-outline-secondary conversation-action';rename.textContent='Renommer';
      rename.addEventListener('click',async()=>{if(busy)return;if(title.hidden){title.hidden=false;title.focus();return;}try{await api(`/api/conversations/${c.id}`,{method:'PATCH',body:JSON.stringify({title:title.value})});await history();status.textContent='Conversation renommée.';}catch(error){status.textContent=error.message;}});
      const remove=document.createElement('button');remove.type='button';remove.className='btn btn-sm btn-outline-danger conversation-action';remove.textContent='Supprimer';remove.setAttribute('aria-label',`Supprimer la conversation ${c.title}`);
      remove.addEventListener('click',async()=>{if(busy||!window.confirm('Supprimer cette conversation et ses retours ?'))return;try{await api(`/api/conversations/${c.id}`,{method:'DELETE'});if(c.id===conversationId)newConversation();else await history();status.textContent='Conversation supprimée.';}catch(error){status.textContent=error.message;}});
      list.append(title,rename,remove);
    }
    if(data.next_before_id){const more=document.createElement('button');more.type='button';more.className='btn btn-sm btn-outline-primary conversation-action load-more';more.textContent='Conversations précédentes';more.addEventListener('click',()=>{more.disabled=true;history(data.next_before_id).catch(error=>{status.textContent=error.message;more.disabled=false;});});list.append(more);}
  }
  async function load(id) {
    if (busy) return;
    lock(true);
    try {
      const data = await api(`/api/conversations/${id}/messages`);
      conversationId = data.conversation_id;
      messages.replaceChildren();
      data.messages.forEach(m => add(m.role, m.content, m));
      olderCursor=data.next_before_id;older.hidden=!olderCursor;
      const lastVehicle = data.messages.at(-1)?.vehicle?.id;
      vehicle.value = [...vehicle.options].some(option => option.value === String(lastVehicle)) ? String(lastVehicle) : '';
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
    olderCursor=null;older.hidden=true;
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
  older.addEventListener('click',async()=>{if(busy||!olderCursor||!conversationId)return;lock(true);const height=messages.scrollHeight,top=messages.scrollTop,first=messages.firstChild;try{const data=await api(`/api/conversations/${conversationId}/messages?before_id=${olderCursor}`);data.messages.forEach(m=>{const item=add(m.role,m.content,m);messages.insertBefore(item,first);});olderCursor=data.next_before_id;older.hidden=!olderCursor;messages.scrollTop=top+messages.scrollHeight-height;}catch(error){status.textContent=error.message;}finally{lock(false);}});
  document.querySelectorAll('.suggestion').forEach(button => button.addEventListener('click', () => { if (!busy && !uncertain) { input.value = button.textContent; input.focus(); } }));
  newConversation();
})();
