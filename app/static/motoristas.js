// motoristas.js
async function carregarMotoristas() {
  try {
    const resp = await fetch('/api/carregamento', { cache: 'no-store' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (err) {
    console.error('Erro ao buscar dados de carregamento:', err);
    return [];
  }
}

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;')
    .replace(/'/g,'&#039;');
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

  let registros = [];
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

  function parseDriver(raw) {
    if (!raw) return '';
    return String(raw).replace(/\[.*?\]/, '').trim();
  }

  function parsePlates(raw) {
    if (!raw) return [];
    return String(raw).split(',').map(p => p.trim()).filter(Boolean);
  }

  async function atualizarRegistros() {
    const dados = await carregarMotoristas();
    registros = dados.map(item => ({
      original: item,
      driver: parseDriver(item.Driver),
      plates: parsePlates(item['Vehicle Plate Number']),
      schedule: item['Schedule Arrival Time'] ?? '',
      station: item['Station Name'] ?? '',
      cpt: item['CPT Type'] ?? ''
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
        resultados.push({ type: 'driver', rec });
        continue;
      }
      for (const plate of rec.plates) {
        const plateLower = plate.toLowerCase();
        if (plateLower.includes(query)) {
          resultados.push({ type: 'plate', rec });
          break;
        }
      }
    }
    return resultados;
  }

  function renderSugestoes(q) {
    const items = gerarSugestoes(q);
    if (!items.length) {
      sugestBox.style.display = 'none';
      sugestBox.innerHTML = '';
      return;
    }

    const qEsc = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp(`(${qEsc})`, 'ig');

    const html = items.map(it => {
      const r = it.rec;
      const key = it.type === 'driver' ? escapeHtml(r.driver) : escapeHtml(r.plates.join(', '));
      const highlightedKey = key.replace(re, '<mark>$1</mark>');
      return `
        <div role="option" style="padding:8px; cursor:pointer; border-radius:6px; margin-bottom:6px; border:1px solid #f0f0f0;">
          <div style="font-weight:700; font-size:0.95em;">${highlightedKey}</div>
          <div style="margin-top:4px; font-size:0.9em; color:#333;">
            <div><strong>Motorista:</strong> ${escapeHtml(r.driver)}</div>
            <div><strong>Station Name:</strong> ${escapeHtml(r.station)}</div>
            <div><strong>Schedule Arrival Time:</strong> ${escapeHtml(r.schedule)}</div>
            <div><strong>CPT Type:</strong> ${escapeHtml(r.cpt)}</div>
          </div>
        </div>
      `;
    }).join('');
    sugestBox.innerHTML = html;
    sugestBox.style.display = 'block';
  }

  campo.addEventListener('input', debounce((e) => renderSugestoes(e.target.value), 140));

  document.addEventListener('click', (ev) => {
    if (!sugestBox.contains(ev.target) && ev.target !== campo) {
      sugestBox.style.display = 'none';
    }
  });

  sugestBox.addEventListener('click', (ev) => {
    const opt = ev.target.closest('[role="option"]');
    if (!opt) return;
    const text = opt.innerText || '';
    campo.value = text.split('\n')[0].trim();
    campo.focus();
    sugestBox.style.display = 'none';
  });

  atualizarRegistros();
});
