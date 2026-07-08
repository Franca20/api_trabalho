document.addEventListener('DOMContentLoaded', () => {
  const campo = document.getElementById('consulta');
  const lista = document.getElementById('lista-descarregar');
  const status = document.getElementById('status-descarregar');
  const modal = document.getElementById('modal-confirmacao');
  const modalMensagem = document.getElementById('modal-mensagem');
  const modalConfirmar = document.getElementById('modal-confirmar');
  const modalCancelar = document.getElementById('modal-cancelar');

  if (!campo || !lista || !status || !modal || !modalMensagem || !modalConfirmar || !modalCancelar) {
    return;
  }

  let registros = [];
  let motoristaParaConcluir = null;

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function parseDriver(raw) {
    if (!raw) return '';
    return String(raw).replace(/\[.*?\]/, '').trim();
  }

  function parsePlates(raw) {
    if (!raw) return [];
    return String(raw).split(',').map((p) => p.trim()).filter(Boolean);
  }

  function renderLista(query = '') {
    const q = query.trim().toLowerCase();
    const filtrados = registros.filter((item) => {
      if (!q) return true;
      const driver = item.driver.toLowerCase();
      const station = item.station.toLowerCase();
      const plates = item.plates.join(' ').toLowerCase();
      return driver.includes(q) || station.includes(q) || plates.includes(q);
    });

    if (!filtrados.length) {
      lista.innerHTML = '<div class="empty-state">Nenhum motorista pendente encontrado.</div>';
      return;
    }

    lista.innerHTML = filtrados.map((item) => `
      <article class="item-card">
        <div class="item-info">
          <h3>${escapeHtml(item.driver || 'Sem motorista')}</h3>
          <p><strong>Estação:</strong> ${escapeHtml(item.station)}</p>
          <p><strong>Placa:</strong> ${escapeHtml(item.plates.join(', ') || '—')}</p>
          <p><strong>Horário:</strong> ${escapeHtml(item.schedule)}</p>
          <p><strong>TO:</strong> ${escapeHtml(item.to)}</p>
        </div>
        <button class="btn-concluir" data-lt="${escapeHtml(item.lt)}" type="button">Marcar como concluído</button>
      </article>
    `).join('');
  }

  async function carregarRegistros() {
    status.textContent = 'Carregando...';
    try {
      const response = await fetch('/api/descarregar', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const dados = await response.json();

      registros = Array.isArray(dados)
        ? dados.map((item) => ({
            lt: item.LT ?? '',
            station: item['Station Name'] ?? '',
            driver: parseDriver(item.Driver ?? ''),
            plates: parsePlates(item['Vehicle Plate Number'] ?? ''),
            schedule: item['Schedule Arrival Time'] ?? '',
            to: item.TO ?? ''
          }))
        : [];

      renderLista(campo.value);
      status.textContent = registros.length
        ? `${registros.length} motorista(s) pendente(s)`
        : 'Nenhum motorista pendente.';
    } catch (error) {
      console.error('Erro ao buscar dados:', error);
      status.textContent = 'Não foi possível carregar os dados.';
    }
  }

  function abrirModalConfirmacao(item) {
    motoristaParaConcluir = item;
    const nomeMotorista = item.driver || 'este motorista';
    modalMensagem.textContent = `Deseja mesmo descer ${nomeMotorista}?`;
    console.debug('[modal] abrir:', nomeMotorista);
    modal.classList.add('show');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function fecharModalConfirmacao() {
    console.debug('[modal] fechar');
    modal.classList.remove('show');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    motoristaParaConcluir = null;
  }

  async function concluirMotorista(lt) {
    const item = registros.find((registro) => registro.lt === lt);
    if (!item) return;

    console.debug('[action] solicitar concluir lt=', lt);
    abrirModalConfirmacao(item);
  }

  modalCancelar.addEventListener('click', (e) => {
    console.debug('[modal] cancelar click', e);
    fecharModalConfirmacao();
  });
  modal.addEventListener('click', (event) => {
    if (event.target === modal) {
      fecharModalConfirmacao();
    }
  });

  modalConfirmar.addEventListener('click', async (e) => {
    console.debug('[modal] confirmar click', e);
    if (!motoristaParaConcluir) return;

    const item = motoristaParaConcluir;
    fecharModalConfirmacao();

    try {
      const response = await fetch('/api/descarregar/concluir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item: { ...item, LT: item.lt } })
      });

      const resultado = await response.json();
      if (!response.ok) throw new Error(resultado.message || 'Erro ao concluir');

      registros = registros.filter((registro) => registro.lt !== item.lt);
      renderLista(campo.value);
      status.textContent = resultado.message;
    } catch (error) {
      console.error('Erro ao concluir motorista:', error);
      status.textContent = 'Não foi possível marcar como concluído.';
    }
  });

  campo.addEventListener('input', (event) => {
    renderLista(event.target.value);
  });

  lista.addEventListener('click', (event) => {
    const button = event.target.closest('.btn-concluir');
    if (!button) return;
    concluirMotorista(button.dataset.lt);
  });

  carregarRegistros();
});
