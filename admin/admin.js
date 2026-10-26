const elements = {
  loginDialog: document.getElementById('loginDialog'),
  loginForm: document.getElementById('loginForm'),
  loginError: document.getElementById('loginError'),
  securityNotice: document.getElementById('securityNotice'),
  loadingState: document.getElementById('loadingState'),
  stonesSection: document.getElementById('pedras'),
  pricesSection: document.getElementById('valores'),
  imagesSection: document.getElementById('imagens'),
  stonesList: document.getElementById('stonesList'),
  pricingGroups: document.getElementById('pricingGroups'),
  imagesList: document.getElementById('imagesList'),
  saveState: document.getElementById('saveState'),
  toast: document.getElementById('adminToast'),
  logoutButton: document.getElementById('logoutButton'),
  addStoneButton: document.getElementById('addStoneButton'),
  stoneDialog: document.getElementById('stoneDialog'),
  stoneCreateForm: document.getElementById('stoneCreateForm'),
  stoneCreateError: document.getElementById('stoneCreateError'),
  optionDialog: document.getElementById('optionDialog'),
  optionCreateForm: document.getElementById('optionCreateForm'),
  optionCreateError: document.getElementById('optionCreateError'),
};

const categoryMeta = {
  sink: { title: 'Cubas e recortes', help: 'Adicionais cobrados por item.', unit: 'R$ por item' },
  backsplash: { title: 'Frontões', help: 'Alturas usadas no cálculo da área.', unit: 'Centímetros' },
  finish: { title: 'Bordas', help: 'Preço aplicado por metro linear.', unit: 'R$ por metro' },
  installation: { title: 'Instalação', help: 'Valor fixo somado ao pedido.', unit: 'R$ por pedido' },
};

const defaultStoneImage = '/assets/images/arkpedra-stone-archive.webp';
const dirtyForms = new Set();
let toastTimer;

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function setSaveState(message, tone = 'ready') {
  elements.saveState.textContent = message;
  elements.saveState.dataset.tone = tone;
}

function showToast(message, tone = 'success') {
  window.clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.dataset.tone = tone;
  elements.toast.classList.add('show');
  toastTimer = window.setTimeout(() => elements.toast.classList.remove('show'), 2800);
}

function showLogin() {
  if (!elements.loginDialog.open) elements.loginDialog.showModal();
  document.getElementById('adminUsername').focus();
}

function confirmDiscardUnsaved() {
  if (!dirtyForms.size) return true;
  const confirmed = window.confirm('Há alterações não salvas. Descartar essas alterações e continuar?');
  if (confirmed) dirtyForms.clear();
  return confirmed;
}

async function apiRequest(url, options = {}) {
  const requestOptions = { credentials: 'same-origin', ...options };
  if (requestOptions.body && !(requestOptions.body instanceof FormData)) {
    requestOptions.headers = { 'Content-Type': 'application/json', ...(requestOptions.headers || {}) };
  }

  const response = await fetch(url, requestOptions);
  if (response.status === 401 && url !== '/api/admin/login') showLogin();

  let payload = {};
  try { payload = await response.json(); } catch (_) {}
  if (!response.ok) throw new Error(payload.detail || 'Não foi possível concluir a operação.');
  return payload;
}

function renderStones(stones) {
  elements.stonesList.innerHTML = stones.map((stone) => `
    <form class="settings-row stone-form" data-stone-id="${stone.id}">
      <div class="row-context">
        <h3>${escapeHtml(stone.name)}</h3>
        <p>Material exibido na primeira etapa do simulador.</p>
        <div class="stone-preview"><img src="${escapeHtml(stone.image_url || defaultStoneImage)}" width="640" height="360" loading="lazy" alt="Prévia de ${escapeHtml(stone.name)}"></div>
      </div>
      <div class="form-grid">
        <div class="field">
          <label for="stone-name-${stone.id}">Nome</label>
          <input id="stone-name-${stone.id}" name="name" value="${escapeHtml(stone.name)}" maxlength="80" autocomplete="off" required>
        </div>
        <div class="field">
          <label for="stone-price-${stone.id}">Preço por m²</label>
          <div class="price-field"><span>R$</span><input id="stone-price-${stone.id}" name="price" type="number" min="0" step="0.01" value="${stone.price_per_m2}" inputmode="decimal" autocomplete="off" required></div>
        </div>
        <div class="field field-wide">
          <label for="stone-description-${stone.id}">Descrição curta</label>
          <textarea id="stone-description-${stone.id}" name="description" maxlength="180" autocomplete="off">${escapeHtml(stone.description)}</textarea>
        </div>
        <label class="toggle-field"><span>Disponível no simulador</span><input name="active" type="checkbox" ${stone.active ? 'checked' : ''}></label>
        <div class="field file-field">
          <label for="stone-image-${stone.id}">Nova textura</label>
          <input id="stone-image-${stone.id}" name="image" type="file" accept="image/png,image/jpeg,image/webp">
          <small>Opcional. JPG, PNG ou WebP, até 5 MB.</small>
        </div>
        <div class="form-actions field-wide"><button class="destructive-button delete-stone" type="button">Excluir pedra</button><button class="primary-button" type="submit">Salvar pedra</button></div>
      </div>
    </form>
  `).join('');
}

function renderPricing(options) {
  const order = ['sink', 'backsplash', 'finish', 'installation'];
  elements.pricingGroups.innerHTML = order.map((category) => {
    const meta = categoryMeta[category];
    const rows = options[category] || [];
    return `
      <form class="pricing-group option-form" data-category="${category}">
        <header><div><h3>${meta.title}</h3><p>${meta.help}</p></div><div class="group-actions"><span class="unit-label">${meta.unit}</span><button class="secondary-button add-option" type="button" data-category="${category}">Adicionar opção</button></div></header>
        <div class="option-list">
          ${rows.map((option) => `
            <div class="option-row" data-option-id="${option.id}">
              <div class="field"><label for="option-label-${option.id}">Nome</label><input id="option-label-${option.id}" name="label-${option.id}" value="${escapeHtml(option.label)}" maxlength="100" autocomplete="off" required></div>
              <div class="field"><label for="option-value-${option.id}">Valor</label><input id="option-value-${option.id}" name="value-${option.id}" type="number" min="0" step="0.01" value="${option.value}" inputmode="decimal" autocomplete="off" required></div>
              <label class="toggle-field"><span>Ativa</span><input name="active-${option.id}" type="checkbox" ${option.active ? 'checked' : ''}></label>
              <button class="destructive-button delete-option" type="button" aria-label="Excluir ${escapeHtml(option.label)}">Excluir</button>
            </div>
          `).join('')}
        </div>
        <div class="form-actions"><button class="primary-button" type="submit">Salvar ${meta.title.toLowerCase()}</button></div>
      </form>
    `;
  }).join('');
}

function renderImages(images) {
  const order = ['hero', 'stone_archive', 'process', 'result'];
  elements.imagesList.innerHTML = order.map((slot) => {
    const image = images[slot];
    return `
      <form class="settings-row image-form" data-slot="${slot}">
        <div class="row-context">
          <h3>${escapeHtml(image.label)}</h3>
          <p>Imagem usada diretamente na landing page.</p>
          <div class="site-image-preview"><img src="${escapeHtml(image.url)}" width="640" height="360" loading="lazy" alt="${escapeHtml(image.alt_text)}"></div>
        </div>
        <div class="form-grid">
          <div class="field field-wide">
            <label for="site-alt-${slot}">Texto alternativo</label>
            <textarea id="site-alt-${slot}" name="alt_text" maxlength="250" autocomplete="off">${escapeHtml(image.alt_text)}</textarea>
            <small>Descreva o conteúdo da imagem para leitores de tela.</small>
          </div>
          <div class="field file-field field-wide">
            <label for="site-image-${slot}">Nova imagem</label>
            <input id="site-image-${slot}" name="image" type="file" accept="image/png,image/jpeg,image/webp" required>
            <small>JPG, PNG ou WebP, até 5 MB.</small>
          </div>
          <div class="form-actions field-wide"><button class="primary-button" type="submit">Trocar imagem</button></div>
        </div>
      </form>
    `;
  }).join('');
}

function bindForms() {
  document.querySelectorAll('.stone-form, .option-form, .image-form').forEach((form) => {
    const markDirty = () => dirtyForms.add(form);
    form.addEventListener('input', markDirty);
    form.addEventListener('change', markDirty);
  });

  document.querySelectorAll('.stone-form').forEach((form) => {
    form.querySelector('.delete-stone').addEventListener('click', async () => {
      const stoneName = form.querySelector('[name="name"]').value;
      if (!window.confirm(`Excluir “${stoneName}” do catálogo?`)) return;
      const button = form.querySelector('.delete-stone');
      button.disabled = true;
      setSaveState('Excluindo pedra…', 'working');
      try {
        await apiRequest(`/api/admin/stones/${form.dataset.stoneId}`, { method: 'DELETE' });
        dirtyForms.delete(form);
        form.remove();
        setSaveState('Tudo atualizado');
        showToast('Pedra excluída.');
      } catch (error) {
        button.disabled = false;
        setSaveState('Não foi possível excluir', 'error');
        showToast(error.message, 'error');
      }
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = form.querySelector('button[type="submit"]');
      const stoneId = form.dataset.stoneId;
      const data = new FormData(form);
      button.disabled = true;
      setSaveState('Salvando pedra…', 'working');
      try {
        let updatedStone = await apiRequest(`/api/admin/stones/${stoneId}`, {
          method: 'PUT',
          body: JSON.stringify({
            name: data.get('name'),
            description: data.get('description'),
            price_per_m2: Number(data.get('price')),
            active: data.get('active') === 'on',
          }),
        });
        const image = data.get('image');
        if (image?.size) {
          const upload = new FormData();
          upload.append('file', image);
          updatedStone = await apiRequest(`/api/admin/stones/${stoneId}/image`, { method: 'POST', body: upload });
        }
        form.querySelector('.row-context h3').textContent = updatedStone.name;
        const preview = form.querySelector('.stone-preview img');
        preview.src = updatedStone.image_url || defaultStoneImage;
        preview.alt = `Prévia de ${updatedStone.name}`;
        form.querySelector('[name="image"]').value = '';
        dirtyForms.delete(form);
        setSaveState('Tudo atualizado');
        showToast('Pedra atualizada.');
      } catch (error) {
        setSaveState('Não foi possível salvar', 'error');
        showToast(error.message, 'error');
      } finally {
        button.disabled = false;
      }
    });
  });

  document.querySelectorAll('.option-form').forEach((form) => {
    form.querySelector('.add-option').addEventListener('click', () => {
      if (!confirmDiscardUnsaved()) return;
      const category = form.dataset.category;
      const meta = categoryMeta[category];
      document.getElementById('newOptionCategory').value = category;
      document.getElementById('newOptionTitle').textContent = `Adicionar em ${meta.title.toLowerCase()}`;
      document.getElementById('newOptionHelp').textContent = `${meta.help} ${meta.unit}.`;
      elements.optionCreateError.textContent = '';
      elements.optionDialog.showModal();
      document.getElementById('newOptionLabel').focus();
    });

    form.querySelectorAll('.delete-option').forEach((button) => {
      button.addEventListener('click', async () => {
        const row = button.closest('[data-option-id]');
        const label = row.querySelector(`[name="label-${row.dataset.optionId}"]`).value;
        if (!window.confirm(`Excluir “${label}” deste grupo?`)) return;
        button.disabled = true;
        setSaveState('Excluindo opção…', 'working');
        try {
          await apiRequest(`/api/admin/options/${row.dataset.optionId}`, { method: 'DELETE' });
          row.remove();
          setSaveState('Tudo atualizado');
          showToast('Opção excluída.');
        } catch (error) {
          button.disabled = false;
          setSaveState('Não foi possível excluir', 'error');
          showToast(error.message, 'error');
        }
      });
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = form.querySelector('button[type="submit"]');
      button.disabled = true;
      setSaveState('Salvando valores…', 'working');
      try {
        const rows = [...form.querySelectorAll('[data-option-id]')];
        for (const row of rows) {
          const optionId = row.dataset.optionId;
          await apiRequest(`/api/admin/options/${optionId}`, {
            method: 'PUT',
            body: JSON.stringify({
              label: row.querySelector(`[name="label-${optionId}"]`).value,
              value: Number(row.querySelector(`[name="value-${optionId}"]`).value),
              active: row.querySelector(`[name="active-${optionId}"]`).checked,
            }),
          });
        }
        dirtyForms.delete(form);
        setSaveState('Tudo atualizado');
        showToast('Valores atualizados.');
      } catch (error) {
        setSaveState('Não foi possível salvar', 'error');
        showToast(error.message, 'error');
      } finally {
        button.disabled = false;
      }
    });
  });

  document.querySelectorAll('.image-form').forEach((form) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = form.querySelector('button[type="submit"]');
      const data = new FormData(form);
      const upload = new FormData();
      upload.append('file', data.get('image'));
      upload.append('alt_text', data.get('alt_text'));
      button.disabled = true;
      setSaveState('Enviando imagem…', 'working');
      try {
        const updatedImage = await apiRequest(`/api/admin/images/${form.dataset.slot}`, { method: 'POST', body: upload });
        const preview = form.querySelector('.site-image-preview img');
        preview.src = updatedImage.url;
        preview.alt = updatedImage.alt_text;
        form.querySelector('[name="image"]').value = '';
        dirtyForms.delete(form);
        setSaveState('Tudo atualizado');
        showToast('Imagem atualizada.');
      } catch (error) {
        setSaveState('Não foi possível enviar', 'error');
        showToast(error.message, 'error');
      } finally {
        button.disabled = false;
      }
    });
  });
}

elements.addStoneButton.addEventListener('click', () => {
  if (!confirmDiscardUnsaved()) return;
  elements.stoneCreateForm.reset();
  elements.stoneCreateError.textContent = '';
  elements.stoneDialog.showModal();
  document.getElementById('newStoneName').focus();
});

document.querySelectorAll('[data-close-dialog]').forEach((button) => {
  button.addEventListener('click', () => document.getElementById(button.dataset.closeDialog).close());
});

elements.stoneCreateForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = elements.stoneCreateForm.querySelector('[type="submit"]');
  const data = new FormData(elements.stoneCreateForm);
  button.disabled = true;
  elements.stoneCreateError.textContent = '';
  try {
    let stone = await apiRequest('/api/admin/stones', {
      method: 'POST',
      body: JSON.stringify({
        name: data.get('name'),
        description: data.get('description'),
        price_per_m2: Number(data.get('price')),
        active: true,
      }),
    });
    const image = data.get('image');
    if (image?.size) {
      const upload = new FormData();
      upload.append('file', image);
      stone = await apiRequest(`/api/admin/stones/${stone.id}/image`, { method: 'POST', body: upload });
    }
    elements.stoneDialog.close();
    await loadConfiguration();
    showToast('Pedra adicionada.');
  } catch (error) {
    elements.stoneCreateError.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

elements.optionCreateForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = elements.optionCreateForm.querySelector('[type="submit"]');
  const data = new FormData(elements.optionCreateForm);
  button.disabled = true;
  elements.optionCreateError.textContent = '';
  try {
    await apiRequest('/api/admin/options', {
      method: 'POST',
      body: JSON.stringify({
        category: data.get('category'),
        label: data.get('label'),
        value: Number(data.get('value')),
        active: true,
      }),
    });
    elements.optionDialog.close();
    elements.optionCreateForm.reset();
    await loadConfiguration();
    showToast('Opção adicionada.');
  } catch (error) {
    elements.optionCreateError.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

async function loadConfiguration() {
  const configuration = await apiRequest('/api/admin/config');
  renderStones(configuration.stones);
  renderPricing(configuration.options);
  renderImages(configuration.images);
  bindForms();
  dirtyForms.clear();
  elements.loadingState.hidden = true;
  elements.stonesSection.hidden = false;
  elements.pricesSection.hidden = false;
  elements.imagesSection.hidden = false;
  setSaveState('Tudo atualizado');
}

elements.loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const username = document.getElementById('adminUsername');
  const password = document.getElementById('adminPassword');
  const button = elements.loginForm.querySelector('button[type="submit"]');
  button.disabled = true;
  elements.loginError.textContent = '';
  try {
    const session = await apiRequest('/api/admin/login', {
      method: 'POST',
      body: JSON.stringify({ username: username.value, password: password.value }),
    });
    elements.loginDialog.close();
    username.value = '';
    password.value = '';
    elements.securityNotice.hidden = !session.using_default_credentials;
    await loadConfiguration();
  } catch (error) {
    elements.loginError.textContent = error.message;
    username.focus();
  } finally {
    button.disabled = false;
  }
});

elements.logoutButton.addEventListener('click', async () => {
  if (dirtyForms.size && !window.confirm('Sair e descartar as alterações que ainda não foram salvas?')) return;
  try { await apiRequest('/api/admin/logout', { method: 'POST' }); } catch (_) {}
  dirtyForms.clear();
  showLogin();
});

window.addEventListener('beforeunload', (event) => {
  if (!dirtyForms.size) return;
  event.preventDefault();
  event.returnValue = '';
});

document.querySelectorAll('.admin-nav a').forEach((link) => {
  link.addEventListener('click', () => {
    document.querySelectorAll('.admin-nav a').forEach((item) => item.classList.toggle('active', item === link));
  });
});

(async function initialize() {
  try {
    const session = await apiRequest('/api/admin/session');
    elements.securityNotice.hidden = !session.using_default_credentials;
    await loadConfiguration();
  } catch (_) {
    elements.loadingState.textContent = 'Entre para carregar as configurações.';
    showLogin();
  }
}());
