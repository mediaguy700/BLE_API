(function () {
  const API_BASE_KEY = 'ble-tracker-api-base';
  const API_KEY_KEY = 'ble-tracker-api-key';
  let apiBase = localStorage.getItem(API_BASE_KEY) || 'https://rkali63t89.execute-api.us-east-2.amazonaws.com/Prod';
  let apiKey = localStorage.getItem(API_KEY_KEY) || '';

  const $ = (id) => document.getElementById(id);
  const apiBaseInput = $('apiBase');
  const apiKeyInput = $('apiKey');
  const readersList = $('readersList');
  const eventsList = $('eventsList');
  const filterReader = $('filterReader');
  const filterDirection = $('filterDirection');
  const readerModal = $('readerModal');
  const eventModal = $('eventModal');

  apiBaseInput.value = apiBase;
  apiKeyInput.value = apiKey;

  function getBase() {
    return apiBase.replace(/\/$/, '');
  }

  $('btnSaveApi').addEventListener('click', () => {
    apiBase = apiBaseInput.value.trim().replace(/\/$/, '');
    apiKey = apiKeyInput.value.trim();
    localStorage.setItem(API_BASE_KEY, apiBase);
    localStorage.setItem(API_KEY_KEY, apiKey);
    apiBaseInput.value = apiBase;
    apiKeyInput.value = apiKey;
    loadReaders();
    loadEvents();
  });

  async function api(path, options = {}) {
    const url = getBase() + path;
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (apiKey) headers['x-api-key'] = apiKey;
    const res = await fetch(url, {
      ...options,
      headers,
    });
    const text = await res.text();
    if (!res.ok) throw new Error(text || res.statusText);
    return text ? JSON.parse(text) : null;
  }

  // ---- READERS ----
  let readers = [];

  async function loadReaders() {
    try {
      readers = await api('/readers');
      renderReaders();
      fillReaderFilter();
    } catch (e) {
      readersList.innerHTML = '<p class="error">Failed to load readers: ' + e.message + '</p>';
    }
  }

  function renderReaders() {
    if (!readers.length) {
      readersList.innerHTML = '<p class="empty">No readers. Add one to get started.</p>';
      return;
    }
    readersList.innerHTML = readers.map((r) => `
      <div class="card" data-reader-name="${escapeAttr(r.readerName)}">
        <div class="row"><span class="key">readerName</span> <span class="value">${escapeHtml(r.readerName)}</span></div>
        ${r.displayName ? `<div class="row"><span class="key">displayName</span> <span class="value">${escapeHtml(r.displayName)}</span></div>` : ''}
        <div class="row"><span class="key">latitude</span> <span class="value">${r.latitude}</span> <span class="key">longitude</span> <span class="value">${r.longitude}</span></div>
        <div class="actions-inline">
          <button type="button" class="edit-reader" data-reader="${escapeAttr(r.readerName)}">Edit</button>
          <button type="button" class="danger delete-reader" data-reader="${escapeAttr(r.readerName)}">Delete</button>
        </div>
      </div>
    `).join('');
    readersList.querySelectorAll('.edit-reader').forEach((btn) => btn.addEventListener('click', () => openReaderModal(btn.dataset.reader)));
    readersList.querySelectorAll('.delete-reader').forEach((btn) => btn.addEventListener('click', () => deleteReader(btn.dataset.reader)));
  }

  function fillReaderFilter() {
    const current = filterReader.value;
    filterReader.innerHTML = '<option value="">All</option>' + readers.map((r) => `<option value="${escapeAttr(r.readerName)}">${escapeHtml(r.readerName)}</option>`).join('');
    if (readers.some((r) => r.readerName === current)) filterReader.value = current;
  }

  $('btnRefreshReaders').addEventListener('click', loadReaders);
  $('btnAddReader').addEventListener('click', () => openReaderModal(null));

  function openReaderModal(readerName) {
    $('readerModalTitle').textContent = readerName ? 'Edit reader' : 'Add reader';
    const form = readerModal.querySelector('form');
    form.querySelector('[name="readerName"]').value = readerName || '';
    form.querySelector('[name="readerName"]').readOnly = !!readerName;
    form.querySelector('[name="displayName"]').value = (readerName && readers.find((r) => r.readerName === readerName))?.displayName || '';
    form.querySelector('[name="description"]').value = (readerName && readers.find((r) => r.readerName === readerName))?.description || '';
    const r = readerName ? readers.find((x) => x.readerName === readerName) : null;
    form.querySelector('[name="latitude"]').value = r?.latitude ?? '';
    form.querySelector('[name="longitude"]').value = r?.longitude ?? '';
    readerModal.showModal();
  }

  readerModal.querySelector('form').addEventListener('submit', async (e) => {
    if (e.submitter?.value !== 'save') return;
    e.preventDefault();
    const fd = new FormData(e.target);
    const readerName = fd.get('readerName').trim();
    const body = {
      readerName,
      displayName: fd.get('displayName').trim() || undefined,
      description: fd.get('description').trim() || undefined,
      latitude: parseFloat(fd.get('latitude')),
      longitude: parseFloat(fd.get('longitude')),
    };
    try {
      if (readers.some((r) => r.readerName === readerName)) {
        await api('/readers/' + encodeURIComponent(readerName), { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await api('/readers', { method: 'POST', body: JSON.stringify(body) });
      }
      readerModal.close();
      loadReaders();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  });
  readerModal.querySelector('button[value="cancel"]').addEventListener('click', () => readerModal.close());

  async function deleteReader(name) {
    if (!confirm('Delete reader "' + name + '" and all its events?')) return;
    try {
      await api('/readers/' + encodeURIComponent(name), { method: 'DELETE' });
      loadReaders();
      loadEvents();
    } catch (e) {
      alert('Error: ' + e.message);
    }
  }

  // ---- EVENTS (full payload, mapped to reader) ----
  let events = [];

  async function loadEvents() {
    try {
      const reader = filterReader.value || '';
      const direction = filterDirection.value || '';
      let path = '/events?limit=100';
      if (reader) path += '&readerName=' + encodeURIComponent(reader);
      if (direction) path += '&direction=' + encodeURIComponent(direction);
      events = await api(path);
      renderEvents();
    } catch (e) {
      eventsList.innerHTML = '<p class="error">Failed to load events: ' + e.message + '</p>';
    }
  }

  function renderEvents() {
    if (!events.length) {
      eventsList.innerHTML = '<p class="empty">No events. Add one or change filters.</p>';
      return;
    }
    eventsList.innerHTML = events.map((ev) => `
      <div class="card">
        <div class="row"><span class="key">id</span> <span class="value">${ev.id}</span> <span class="key">readerName</span> <span class="value">${escapeHtml(ev.readerName)}</span> <span class="key">direction</span> <span class="value">${escapeHtml(ev.direction || 'in')}</span></div>
        <div class="row"><span class="key">mac</span> <span class="value">${escapeHtml(ev.mac)}</span></div>
        <div class="row"><span class="key">distance</span> ${ev.distance ?? '—'} <span class="key">peakRSSI</span> ${ev.peakRSSI ?? '—'} <span class="key">antenna</span> ${ev.antenna ?? '—'} <span class="key">dateTime</span> ${ev.dateTime ? ev.dateTime.slice(0, 19) : '—'}</div>
        <div class="row"><span class="key">data</span> ${ev.data ?? '—'} <span class="key">tagEvent</span> ${ev.tagEvent ?? '—'} <span class="key">uuid</span> ${ev.uuid ?? '—'} <span class="key">major</span> ${ev.major ?? '—'} <span class="key">minor</span> ${ev.minor ?? '—'}</div>
        <div class="row"><span class="key">namespace</span> ${ev.namespace ?? '—'} <span class="key">instance</span> ${ev.instance ?? '—'} <span class="key">voltage</span> ${ev.voltage ?? '—'} <span class="key">temperature</span> ${ev.temperature ?? '—'} <span class="key">url</span> ${ev.url ?? '—'}</div>
        <div class="actions-inline">
          <button type="button" class="edit-event" data-id="${ev.id}">Edit</button>
          <button type="button" class="danger delete-event" data-id="${ev.id}">Delete</button>
        </div>
      </div>
    `).join('');
    eventsList.querySelectorAll('.edit-event').forEach((btn) => btn.addEventListener('click', () => openEventModal(parseInt(btn.dataset.id, 10))));
    eventsList.querySelectorAll('.delete-event').forEach((btn) => btn.addEventListener('click', () => deleteEvent(parseInt(btn.dataset.id, 10))));
  }

  $('btnRefreshEvents').addEventListener('click', loadEvents);
  $('btnAddEvent').addEventListener('click', () => openEventModal(null));
  filterReader.addEventListener('change', loadEvents);
  filterDirection.addEventListener('change', loadEvents);

  function openEventModal(eventId) {
    $('eventModalTitle').textContent = eventId ? 'Edit event' : 'Add event';
    const form = eventModal.querySelector('form');
    form.querySelector('[name="eventId"]').value = eventId || '';
    const ev = eventId ? events.find((e) => e.id === eventId) : null;
    if (ev) {
      form.querySelector('[name="readerName"]').value = ev.readerName || '';
      form.querySelector('[name="mac"]').value = ev.mac || '';
      form.querySelector('[name="direction"]').value = ev.direction || 'in';
      form.querySelector('[name="distance"]').value = ev.distance ?? '';
      form.querySelector('[name="peakRSSI"]').value = ev.peakRSSI ?? '';
      form.querySelector('[name="antenna"]').value = ev.antenna ?? '';
      form.querySelector('[name="dateTime"]').value = ev.dateTime ? ev.dateTime.slice(0, 16) : '';
      form.querySelector('[name="data"]').value = ev.data ?? '';
      form.querySelector('[name="startEvent"]').value = ev.startEvent === true ? 'true' : ev.startEvent === false ? 'false' : '';
      form.querySelector('[name="count"]').value = ev.count ?? '';
      form.querySelector('[name="tagEvent"]').value = ev.tagEvent ?? '';
      form.querySelector('[name="uuid"]').value = ev.uuid ?? '';
      form.querySelector('[name="major"]').value = ev.major ?? '';
      form.querySelector('[name="minor"]').value = ev.minor ?? '';
      form.querySelector('[name="namespace"]').value = ev.namespace ?? '';
      form.querySelector('[name="instance"]').value = ev.instance ?? '';
      form.querySelector('[name="voltage"]').value = ev.voltage ?? '';
      form.querySelector('[name="temperature"]').value = ev.temperature ?? '';
      form.querySelector('[name="url"]').value = ev.url ?? '';
    } else {
      form.querySelector('[name="readerName"]').value = filterReader.value || '';
      form.querySelector('[name="mac"]').value = '';
      form.querySelector('[name="direction"]').value = 'in';
      ['distance', 'peakRSSI', 'antenna', 'dateTime', 'data', 'startEvent', 'count', 'tagEvent', 'uuid', 'major', 'minor', 'namespace', 'instance', 'voltage', 'temperature', 'url'].forEach((n) => { form.querySelector('[name="' + n + '"]').value = ''; });
    }
    eventModal.showModal();
  }

  eventModal.querySelector('form').addEventListener('submit', async (e) => {
    if (e.submitter?.value !== 'save') return;
    e.preventDefault();
    const fd = new FormData(e.target);
    const eventId = fd.get('eventId');
    const body = {
      readerName: fd.get('readerName').trim(),
      mac: fd.get('mac').trim(),
      direction: fd.get('direction') || 'in',
      distance: fd.get('distance') ? parseFloat(fd.get('distance')) : undefined,
      peakRSSI: fd.get('peakRSSI') ? parseInt(fd.get('peakRSSI'), 10) : undefined,
      antenna: fd.get('antenna') ? parseInt(fd.get('antenna'), 10) : undefined,
      dateTime: fd.get('dateTime') || undefined,
      data: fd.get('data') || undefined,
      startEvent: fd.get('startEvent') === 'true' ? true : fd.get('startEvent') === 'false' ? false : undefined,
      count: fd.get('count') ? parseInt(fd.get('count'), 10) : undefined,
      tagEvent: fd.get('tagEvent') || undefined,
      uuid: fd.get('uuid') || undefined,
      major: fd.get('major') ? parseInt(fd.get('major'), 10) : undefined,
      minor: fd.get('minor') ? parseInt(fd.get('minor'), 10) : undefined,
      namespace: fd.get('namespace') || undefined,
      instance: fd.get('instance') || undefined,
      voltage: fd.get('voltage') ? parseFloat(fd.get('voltage')) : undefined,
      temperature: fd.get('temperature') ? parseFloat(fd.get('temperature')) : undefined,
      url: fd.get('url') || undefined,
    };
    try {
      if (eventId) {
        await api('/events/' + eventId, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await api('/events', { method: 'POST', body: JSON.stringify(body) });
      }
      eventModal.close();
      loadEvents();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  });
  eventModal.querySelector('button[value="cancel"]').addEventListener('click', () => eventModal.close());

  async function deleteEvent(id) {
    if (!confirm('Delete this event?')) return;
    try {
      await api('/events/' + id, { method: 'DELETE' });
      loadEvents();
    } catch (e) {
      alert('Error: ' + e.message);
    }
  }

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }
  function escapeAttr(s) {
    return escapeHtml(s).replace(/"/g, '&quot;');
  }

  loadReaders();
  loadEvents();
})();
