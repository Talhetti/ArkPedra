const INITIAL_STATE = {
  step: 0,
  maxUnlockedStep: 0,
  stone: 'Granito escuro',
  stonePrice: 480,
};

const state = { ...INITIAL_STATE };
const steps = [...document.querySelectorAll('.step')];
const stepButtons = [...document.querySelectorAll('[data-go-step]')];
let stoneButtons = [...document.querySelectorAll('[data-stone]')];
const money = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
});

const stepNames = ['Pedra', 'Medidas', 'Cuba', 'Acabamentos', 'Estimativa'];
const validationRules = {
  length: { min: 30, max: 900, label: 'O comprimento' },
  depth: { min: 20, max: 180, label: 'A profundidade' },
  quantity: { min: 1, max: 20, label: 'A quantidade' },
};

function field(id) {
  return document.getElementById(id);
}

function labelOf(select) {
  return select.options[select.selectedIndex].text;
}

function numberValue(id, fallback) {
  const value = Number(field(id).value);
  return Number.isFinite(value) ? value : fallback;
}

function projectValues() {
  const length = Math.max(30, numberValue('length', 30));
  const depth = Math.max(20, numberValue('depth', 20));
  const quantity = Math.max(1, numberValue('quantity', 1));
  const sink = Number(field('sink').value);
  const frontHeight = Number(field('backsplash').value);
  const install = Number(field('installation').value);
  const quote = window.ArkPedraPricing.calculateQuote({
    length,
    depth,
    quantity,
    stonePrice: state.stonePrice,
    sink,
    backsplash: frontHeight,
    finish: Number(field('finish').value),
    installation: install,
  });

  return {
    length,
    depth,
    quantity,
    ...quote,
  };
}

function buildMessage(values) {
  return window.ArkPedraPricing.buildWhatsAppMessage({
    stone: state.stone,
    length: values.length,
    depth: values.depth,
    quantity: values.quantity,
    sink: labelOf(field('sink')),
    sinkPosition: Number(field('sink').value) === 0 ? '' : labelOf(field('sinkPosition')),
    backsplash: labelOf(field('backsplash')),
    finish: labelOf(field('finish')),
    installation: labelOf(field('installation')),
    formattedTotal: money.format(values.total),
  });
}

function updateSinkPosition() {
  const hasSink = Number(field('sink').value) !== 0;
  field('sinkPosition').disabled = !hasSink;
  field('sinkPosition').closest('.field').hidden = !hasSink;
}

function calculate() {
  const values = projectValues();
  const message = buildMessage(values);

  field('materialValue').textContent = money.format(values.material);
  field('extrasValue').textContent = money.format(values.extras);
  field('totalValue').textContent = money.format(values.total);
  field('summaryStone').textContent = state.stone;
  field('summaryMeasures').textContent = `${values.length} × ${values.depth} cm · ${values.quantity} peça${values.quantity > 1 ? 's' : ''}`;
  field('summarySink').textContent = labelOf(field('sink'));
  field('summaryFinish').textContent = labelOf(field('finish'));
  field('summaryTotal').textContent = money.format(values.total);
  field('messagePreview').textContent = message;

  return { values, message };
}

function setFieldError(input, message) {
  input.setAttribute('aria-invalid', message ? 'true' : 'false');
  field(`${input.id}Error`).textContent = message;
}

function validateMeasurements() {
  const invalid = [];

  Object.entries(validationRules).forEach(([id, rule]) => {
    const input = field(id);
    const value = Number(input.value);
    let message = '';

    if (input.value.trim() === '' || !Number.isFinite(value)) {
      message = `${rule.label} precisa ser informado.`;
    } else if (!Number.isInteger(value)) {
      message = `${rule.label} deve usar um número inteiro.`;
    } else if (value < rule.min || value > rule.max) {
      message = `${rule.label} deve ficar entre ${rule.min} e ${rule.max}.`;
    }

    setFieldError(input, message);
    if (message) invalid.push(input);
  });

  if (invalid.length) invalid[0].focus();
  return invalid.length === 0;
}

function refreshStepNavigation() {
  stepButtons.forEach((button, index) => {
    button.disabled = index > state.maxUnlockedStep;
    if (index === state.step) button.setAttribute('aria-current', 'step');
    else button.removeAttribute('aria-current');
  });
  field('stepStatus').textContent = stepNames[state.step];
}

function showStep(nextStep, shouldFocus = true) {
  const boundedStep = Math.max(0, Math.min(steps.length - 1, nextStep));
  state.step = boundedStep;
  state.maxUnlockedStep = Math.max(state.maxUnlockedStep, boundedStep);

  steps.forEach((step, index) => {
    const active = index === state.step;
    step.hidden = !active;
    step.classList.toggle('active', active);
  });

  refreshStepNavigation();
  calculate();

  if (shouldFocus) {
    const heading = steps[state.step].querySelector('h3');
    heading.setAttribute('tabindex', '-1');
    heading.focus({ preventScroll: true });
  }
}

function resetSimulator() {
  field('quoteForm').reset();
  Object.assign(state, INITIAL_STATE);
  stoneButtons.forEach((button, index) => {
    const selected = index === 0;
    button.classList.toggle('selected', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
  Object.keys(validationRules).forEach((id) => setFieldError(field(id), ''));
  updateSinkPosition();
  showStep(0);
}

function selectStoneButton(button) {
  stoneButtons.forEach((item) => {
    item.classList.remove('selected');
    item.setAttribute('aria-pressed', 'false');
  });
  button.classList.add('selected');
  button.setAttribute('aria-pressed', 'true');
  state.stone = button.dataset.stone;
  state.stonePrice = Number(button.dataset.price);
  calculate();
}

function bindStoneButtons() {
  stoneButtons.forEach((button) => {
    button.addEventListener('click', () => selectStoneButton(button));
  });
}

function replaceSelectOptions(selectId, options) {
  const select = field(selectId);
  if (!select || !Array.isArray(options) || options.length === 0) return;

  select.replaceChildren(...options.map((option) => {
    const element = document.createElement('option');
    element.value = String(option.value);
    element.textContent = option.label;
    element.selected = Boolean(option.is_default);
    return element;
  }));

  if (!options.some((option) => option.is_default)) select.selectedIndex = 0;
}

function applyStoneConfiguration(stones) {
  if (!Array.isArray(stones) || stones.length === 0) return;

  const fallbackSwatches = ['stone-dark', 'stone-white', 'stone-marble', 'stone-exotic'];
  const configuredButtons = stones.map((stone, index) => {
    const button = document.createElement('button');
    button.className = `stone-option${index === 0 ? ' selected' : ''}`;
    button.type = 'button';
    button.dataset.stone = stone.name;
    button.dataset.price = String(stone.price_per_m2);
    button.setAttribute('aria-pressed', String(index === 0));

    const swatch = document.createElement('span');
    swatch.className = `stone-swatch ${fallbackSwatches[index % fallbackSwatches.length]}`;
    swatch.setAttribute('aria-hidden', 'true');
    if (stone.image_url) {
      swatch.style.backgroundImage = `url("${stone.image_url.replaceAll('"', '%22')}")`;
      swatch.style.backgroundSize = 'cover';
      swatch.style.backgroundPosition = 'center';
    }

    const copy = document.createElement('span');
    const name = document.createElement('strong');
    const description = document.createElement('small');
    name.textContent = stone.name;
    description.textContent = `${money.format(stone.price_per_m2)}/m² · ${stone.description}`;
    copy.append(name, description);
    button.append(swatch, copy);
    return button;
  });

  field('stonePicker').replaceChildren(
    Object.assign(document.createElement('legend'), { className: 'sr-only', textContent: 'Escolha a pedra' }),
    ...configuredButtons,
  );
  stoneButtons = configuredButtons;
  bindStoneButtons();

  INITIAL_STATE.stone = stones[0].name;
  INITIAL_STATE.stonePrice = Number(stones[0].price_per_m2);
  state.stone = INITIAL_STATE.stone;
  state.stonePrice = INITIAL_STATE.stonePrice;
}

function applySiteImages(images) {
  const bindings = {
    hero: '.hero-media img',
    stone_archive: '.material-image img',
    process: '.process-visual img',
    result: '.result-photo img',
  };

  Object.entries(bindings).forEach(([slot, selector]) => {
    const configured = images?.[slot];
    const image = document.querySelector(selector);
    if (!configured?.url || !image) return;
    image.src = configured.url;
    if (slot !== 'hero' && configured.alt_text) image.alt = configured.alt_text;
  });
}

async function loadRemoteConfiguration() {
  try {
    const response = await fetch('/api/config', { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error('Configuração indisponível');
    const configuration = await response.json();

    applyStoneConfiguration(configuration.stones);
    replaceSelectOptions('sink', configuration.options?.sink);
    replaceSelectOptions('backsplash', configuration.options?.backsplash);
    replaceSelectOptions('finish', configuration.options?.finish);
    replaceSelectOptions('installation', configuration.options?.installation);
    applySiteImages(configuration.images);
    updateSinkPosition();
    calculate();
  } catch (_) {
    // A versão estática continua funcional quando a API não está em execução.
  }
}

bindStoneButtons();

document.querySelectorAll('.next').forEach((button) => {
  button.addEventListener('click', () => {
    if (state.step === 1 && !validateMeasurements()) return;
    showStep(state.step + 1);
  });
});

document.querySelectorAll('.back').forEach((button) => {
  button.addEventListener('click', () => showStep(state.step - 1));
});

stepButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const destination = Number(button.dataset.goStep);
    if (destination <= state.maxUnlockedStep) showStep(destination);
  });
});

document.querySelectorAll('input, select').forEach((control) => {
  control.addEventListener('input', () => {
    if (control.id in validationRules) setFieldError(control, '');
    if (control.id === 'sink') updateSinkPosition();
    calculate();
  });
});

Object.keys(validationRules).forEach((id) => {
  field(id).addEventListener('blur', () => {
    if (state.step === 1) validateMeasurements();
  });
});

field('quoteForm').addEventListener('submit', (event) => event.preventDefault());
field('resetSimulator').addEventListener('click', resetSimulator);

field('sendWhatsapp').addEventListener('click', () => {
  const { message } = calculate();
  const url = `https://wa.me/?text=${encodeURIComponent(message)}`;
  window.open(url, '_blank', 'noopener,noreferrer');

  navigator.clipboard?.writeText(message).catch(() => {});
  field('toast').classList.add('show');
  window.setTimeout(() => field('toast').classList.remove('show'), 2400);
});

const materialTabs = [...document.querySelectorAll('[role="tab"]')];

function selectMaterial(tab) {
  materialTabs.forEach((item) => item.setAttribute('aria-selected', String(item === tab)));
  field('materialName').textContent = tab.dataset.material;
  field('materialText').textContent = tab.dataset.description;
}

materialTabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectMaterial(tab));
  tab.addEventListener('keydown', (event) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const offset = event.key === 'ArrowRight' ? 1 : -1;
    const nextIndex = (index + offset + materialTabs.length) % materialTabs.length;
    materialTabs[nextIndex].focus();
    selectMaterial(materialTabs[nextIndex]);
  });
});

const revealItems = [...document.querySelectorAll('[data-reveal]')];
revealItems.forEach((item, index) => item.style.setProperty('--reveal-delay', `${(index % 4) * 70}ms`));

if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: .12 });

  revealItems.forEach((item) => observer.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add('is-visible'));
}

updateSinkPosition();
refreshStepNavigation();
calculate();
loadRemoteConfiguration();
