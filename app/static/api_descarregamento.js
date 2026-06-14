// api_descarregar.js
// Sugestões para a aba de descarregar (fetch /api/descarregar)

document.addEventListener('DOMContentLoaded', () => {
  const campo = document.getElementById('consulta');
  if (!campo) {
    console.error('Elemento #consulta não encontrado.');
    return;
  }

  // scoped helpers for 'descarregar' module
  async function pegarDados() {
    try {
      const resp = await fetch('/api/descarregar', { cache: 'no-store' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return await resp.json();
    } catch (err) {
      console.error('Erro ao buscar dados:', err);
      return null;
    }
  }

  function escapeHtml(s) {
    return String(s ?? '')
      .replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;')
      .replace(/'/g,'&#039;');
  }

  function debounce(fn, wait) {
    let t = null;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), wait);
    };
  }

  // Cria container de sugestão logo abaixo do input
  let sugestBox = document.getElementById('sugestoes-descarregar');
  if (!sugestBox) {
    sugestBox = document.createElement('div');
    sugestBox.id = 'sugestoes-descarregar';
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
  let registros = [];
  let ultimaBusca = 0;
  const MIN_FETCH_MS = 2000;
  const REFRESH_MS = 30_000;

  function parseDriver(raw) {
    if (!raw) return '';
    return String(raw).replace(/\[.*?\]/, '').trim();
  }

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
    registros = dados.map(item => ({
      original: item,
      station: item['Station Name'] ?? '',
      driver: parseDriver(item.Driver ?? ''),
      plates: parsePlates(item['Vehicle Plate Number'] ?? ''),
      schedule: item['Schedule Arrival Time'] ?? '',
      to: item.TO ?? ''
    }));
  }

  function gerarSugestoes(q, max = 12) {
    const query = (q ?? '').trim().toLowerCase();
    if (!query) return [];

    const resultados = [];
    for (const rec of registros) {
      if (resultados.length >= max) break;
      const driver = rec.driver.toLowerCase();
      if (driver.includes(query)) {
        resultados.push({ type: 'driver', key: rec.driver, rec });
        continue;
      }
      for (const plate of rec.plates) {
        const plateLower = plate.toLowerCase();
        if (plateLower.includes(query)) {
          resultados.push({ type: 'plate', key: plate, rec });
          break;
        }
      }
    }
    return resultados;
  }

  function renderSugestoes(q) {
    const items = gerarSugestoes(q, 12);
    if (!items.length) {
      sugestBox.style.display = 'none';
      sugestBox.innerHTML = '';
      return;
    }

    const qEsc = q.replace(/[.*+?^${}()|[\\]\\]/g,'\\$&');
    const re = new RegExp(`(${qEsc})`, 'ig');

    const html = items.map(it => {
      const r = it.rec;
      const highlightedKey = escapeHtml(it.key).replace(re, '<mark>$1</mark>');
      const station = escapeHtml(r.station);
      const driver = escapeHtml(r.driver);
      const schedule = escapeHtml(r.schedule);
      const to = escapeHtml(r.to);
      return `\n        <div role="option" data-value="${escapeHtml(it.key)}" style="padding:8px; cursor:pointer; border-radius:6px; margin-bottom:6px; border:1px solid #f0f0f0;">\n          <div style="display:flex; justify-content:space-between; align-items:center;">\n            <div style="font-weight:700; font-size:0.95em;">${highlightedKey}</div>\n            <div style="font-size:0.8em; color:#666;">${it.type === 'plate' ? 'Placa' : 'Motorista'}</div>\n          </div>\n          <div style="margin-top:6px; font-size:0.9em; color:#333;">\n            <div><strong>Station Name:</strong> ${station}</div>\n            <div><strong>Driver:</strong> ${driver}</div>\n            <div><strong>Schedule Arrival Time:</strong> ${schedule}</div>\n            <div><strong>TO:</strong> ${to}</div>\n          </div>\n        </div>\n      `;
    }).join('');
    sugestBox.innerHTML = html;
    sugestBox.style.display = 'block';
  }

  sugestBox.addEventListener('click', (ev) => {
    const opt = ev.target.closest('[role="option"]');
    if (!opt) return;
    const val = opt.getAttribute('data-value') || '';
    campo.value = val;
    campo.focus();
    campo.dispatchEvent(new Event('input', { bubbles: true }));
    sugestBox.style.display = 'none';
  });

  document.addEventListener('click', (ev) => {
    if (!sugestBox.contains(ev.target) && ev.target !== campo) {
      sugestBox.style.display = 'none';
    }
  });

  const onInput = debounce((e) => {
    const v = e.target.value;
    renderSugestoes(v);
  }, 120);

  campo.addEventListener('input', onInput);

  (async () => {
    await atualizarRegistros(true);
    setInterval(() => atualizarRegistros(false), REFRESH_MS);
  })();
});
