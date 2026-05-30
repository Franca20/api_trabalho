// api.js
// Sugestões com Station Name, Driver, Schedule Arrival Time e TO

async function pegarDados() {
  try {
    const resp = await fetch('/api/data', { cache: 'no-store' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (err) {
    console.error('Erro ao buscar dados:', err);
    return null;
  }
}

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}

function debounce(fn, wait) {
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}

document.addEventListener('DOMContentLoaded', () => {
  const campo = document.getElementById('consulta');
  if (!campo) {
    console.error('Elemento #consulta não encontrado.');
    return;
  }

  // Cria container de sugestão logo abaixo do input
  let sugestBox = document.getElementById('sugestoes');
  if (!sugestBox) {
    sugestBox = document.createElement('div');
    sugestBox.id = 'sugestoes';
    sugestBox.setAttribute('role', 'listbox');
    sugestBox.style.marginTop = '6px';
    sugestBox.style.maxWidth = '720px';
    sugestBox.style.background = '#fff';
    sugestBox.style.border = '1px solid #ddd';
    sugestBox.style.borderRadius = '6px';
    sugestBox.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)';
    sugestBox.style.padding = '6px';
    sugestBox.style.display = 'none';
    campo.insertAdjacentElement('afterend', sugestBox);
  }

  // Estado
  let registros = []; // array original
  let ultimaBusca = 0;
  const MIN_FETCH_MS = 2000;
  const REFRESH_MS = 30_000;

  // Normaliza driver (remove prefixo [id])
  function parseDriver(raw) {
    if (!raw) return '';
    return String(raw).replace(/^\[.*?\]\s*/,'').trim();
  }

  // Extrai placas (separadas por vírgula)
  function parsePlates(raw) {
    if (!raw) return [];
    return String(raw).split(',').map(p => p.trim()).filter(Boolean);
  }

  async function atualizarRegistros(force = false) {
    const agora = Date.now();
    if (!force && agora - ultimaBusca < MIN_FETCH_MS) return;
    ultimaBusca = agora;

    const dados = await pegarDados();
    if (!Array.isArray(dados)) {
      registros = [];
      return;
    }
    // normaliza e guarda
    registros = dados.map(item => ({
      original: item,
      station: item['Station Name'] ?? '',
      driver: parseDriver(item.Driver ?? ''),
      plates: parsePlates(item['Vehicle Plate Number'] ?? ''),
      schedule: item['Schedule Arrival Time'] ?? '',
      to: item.TO ?? ''
    }));
  }

  // Gera sugestões a partir da query: procura em placas e driver
  function gerarSugestoes(q, max = 8) {
    const query = (q ?? '').trim().toLowerCase();
    if (!query) return [];

    const resultados = [];
    // Primeiro placas (prefixo, depois contains)
    for (const rec of registros) {
      for (const plate of rec.plates) {
        const p = plate.toLowerCase();
        if (p.startsWith(query) || p.includes(query)) {
          resultados.push({ type: 'plate', key: plate, rec });
          if (resultados.length >= max) return resultados;
        }
      }
    }
    // Depois drivers
    for (const rec of registros) {
      const d = rec.driver.toLowerCase();
      if (d.startsWith(query) || d.includes(query)) {
        resultados.push({ type: 'driver', key: rec.driver, rec });
        if (resultados.length >= max) return resultados;
      }
    }
    return resultados;
  }

  // Renderiza sugestões com os campos solicitados
  function renderSugestoes(q) {
    const items = gerarSugestoes(q, 12);
    if (!items.length) {
      sugestBox.style.display = 'none';
      sugestBox.innerHTML = '';
      return;
    }

    const qEsc = q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    const re = new RegExp(`(${qEsc})`, 'ig');

    const html = items.map(it => {
      const r = it.rec;
      // destaque para placa/driver
      const highlightedKey = escapeHtml(it.key).replace(re, '<mark>$1</mark>');
      const station = escapeHtml(r.station);
      const driver = escapeHtml(r.driver);
      const schedule = escapeHtml(r.schedule);
      const to = escapeHtml(r.to);
      return `
        <div role="option" data-value="${escapeHtml(it.key)}" style="padding:8px; cursor:pointer; border-radius:6px; margin-bottom:6px; border:1px solid #f0f0f0;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-weight:700; font-size:0.95em;">${highlightedKey}</div>
            <div style="font-size:0.8em; color:#666;">${it.type === 'plate' ? 'Placa' : 'Motorista'}</div>
          </div>
          <div style="margin-top:6px; font-size:0.9em; color:#333;">
            <div><strong>Station Name:</strong> ${station}</div>
            <div><strong>Driver:</strong> ${driver}</div>
            <div><strong>Schedule Arrival Time:</strong> ${schedule}</div>
            <div><strong>TO:</strong> ${to}</div>
          </div>
        </div>
      `;
    }).join('');
    sugestBox.innerHTML = html;
    sugestBox.style.display = 'block';
  }

  // Clique em sugestão preenche o campo e mantém a sugestão visível por um instante
  sugestBox.addEventListener('click', (ev) => {
    const opt = ev.target.closest('[role="option"]');
    if (!opt) return;
    const val = opt.getAttribute('data-value') || '';
    campo.value = val;
    // opcional: mover foco de volta ao input
    campo.focus();
    // dispara input para que outros handlers reajam
    campo.dispatchEvent(new Event('input', { bubbles: true }));
    // esconde sugestões
    sugestBox.style.display = 'none';
  });

  // Fecha sugestões ao clicar fora
  document.addEventListener('click', (ev) => {
    if (!sugestBox.contains(ev.target) && ev.target !== campo) {
      sugestBox.style.display = 'none';
    }
  });

  // Debounced input handler
  const onInput = debounce((e) => {
    const v = e.target.value;
    renderSugestoes(v);
  }, 120);

  campo.addEventListener('input', onInput);

  // Inicialização
  (async () => {
    await atualizarRegistros(true);
    setInterval(() => atualizarRegistros(false), REFRESH_MS);
  })();
});
