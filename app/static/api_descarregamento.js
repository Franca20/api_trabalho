document.addEventListener('DOMContentLoaded', () => {
  const campo = document.getElementById('consulta');
  const lista = document.getElementById('lista-descarregar');
  const status = document.getElementById('status-descarregar');
  const modal = document.getElementById('modal-confirmacao');
  const modalMensagem = document.getElementById('modal-mensagem');
  const modalConfirmar = document.getElementById('modal-confirmar');
  const modalCancelar = document.getElementById('modal-cancelar');
  const vagasModal = document.getElementById('modal-vagas');
  const vagasMensagem = document.getElementById('modal-vagas-mensagem');
  const vagasClose = document.getElementById('modal-vagas-close');
  const vagaGrid = document.getElementById('vaga-grid');

  if (!campo || !lista || !status || !modal || !modalMensagem || !modalConfirmar || !modalCancelar || !vagasModal || !vagasMensagem || !vagasClose || !vagaGrid) {
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

  function getPlates(item) {
    if (!item) return [];
    if (Array.isArray(item.plates)) return item.plates;
    if (item['Vehicle Plate Number']) return parsePlates(item['Vehicle Plate Number']);
    return [];
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
        <div class="item-actions">
          <button class="btn-concluir btn-adicionar-vaga" data-lt="${escapeHtml(item.lt)}" type="button">Adicionar na vaga</button>
          <button class="btn-concluir" data-lt="${escapeHtml(item.lt)}" type="button">Marcar como concluído</button>
        </div>
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
            raw: item,
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

  function abrirModalVagas(item) {
    selectedItemForVaga = item;
    const plates = getPlates(item).join(', ') || 'sem placa';
    vagasMensagem.textContent = `Selecione uma vaga para o motorista ${escapeHtml(item.driver || item.Driver || 'Motorista')} (${escapeHtml(plates)}).`;
    buildVagaGrid();
    vagasModal.classList.add('show');
    vagasModal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function fecharModalVagas() {
    vagasModal.classList.remove('show');
    vagasModal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    selectedItemForVaga = null;
  }

  async function buildVagaGrid() {
    const assigned = await fetchVagasFromDb();
    const totalVagas = 67;
    const leftButtons = [];
    const rightButtons = [];

    for (let index = 0; index < totalVagas; index += 1) {
      const vagaIndex = String(index + 1);
      const item = assigned[vagaIndex];
      const platesText = item?.platesString || (Array.isArray(item?.plates) ? item.plates.join(', ') : item?.['Vehicle Plate Number'] || '');
      const label = platesText ? platesText : `Vaga ${vagaIndex}`;
      const assignedClass = platesText ? ' assigned' : '';
      const buttonHtml = `
        <button type="button" class="btn btn-vaga${assignedClass}" data-index="${vagaIndex}">${escapeHtml(label)}</button>
      `;

      if (index < 33) {
        leftButtons.push(buttonHtml);
      } else {
        rightButtons.push(buttonHtml);
      }
    }

    vagaGrid.innerHTML = `
      <div class="vaga-column vaga-column-left">${leftButtons.join('')}</div>
      <div class="vaga-column vaga-column-right">${rightButtons.join('')}</div>
    `;
  }

  async function assignVaga(vagaIndex) {
    if (!selectedItemForVaga) return;
    const plates = getPlates(selectedItemForVaga).join(', ') || 'sem placa';
    const assigned = {
      raw: selectedItemForVaga.raw || selectedItemForVaga,
      lt: selectedItemForVaga.lt,
      driver: selectedItemForVaga.driver,
      station: selectedItemForVaga.station,
      schedule: selectedItemForVaga.schedule,
      to: selectedItemForVaga.to,
      plates: selectedItemForVaga.plates,
      platesString: plates,
      'Vehicle Plate Number': plates
    };
    await saveAssignedVaga(vagaIndex, assigned);
    status.textContent = `Motorista ${selectedItemForVaga.driver} atribuído à vaga ${vagaIndex}.`;
    fecharModalVagas();
    await buildVagaGrid();
  }

  let selectedItemForVaga = null;

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

  vagasClose.addEventListener('click', (e) => {
    console.debug('[modal] fechar vagas click', e);
    fecharModalVagas();
  });
  vagasModal.addEventListener('click', (event) => {
    if (event.target === vagasModal) {
      fecharModalVagas();
    }
  });

  vagaGrid.addEventListener('click', (event) => {
    const button = event.target.closest('.btn-vaga');
    if (!button) return;
    assignVaga(button.dataset.index);
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
      await removeAssignedVagaByLt(item.lt);
      const nomeMotorista = item.driver.replace(/^Motorista\s+/i, '');
      status.textContent = `Motorista ${nomeMotorista} concluído`;
    } catch (error) {
      console.error('Erro ao concluir motorista:', error);
      status.textContent = 'Não foi possível marcar como concluído.';
    }
  });

  campo.addEventListener('input', (event) => {
    renderLista(event.target.value);
  });

  async function fetchVagasFromDb() {
    try {
      const response = await fetch('/api/vagas', { cache: 'no-store' });
      if (!response.ok) return {};
      const vagas = await response.json();
      return Object.fromEntries((Array.isArray(vagas) ? vagas : []).map((vaga) => {
        const vagaKey = String(vaga.vaga_index ?? vaga['vagaIndex']);
        const plates = Array.isArray(vaga.plates) ? vaga.plates : [vaga['Vehicle Plate Number'] || vaga.platesString || ''];
        const normalized = {
          ...vaga,
          lt: vaga.lt ?? vaga.LT ?? '',
          driver: vaga.driver ?? vaga.Driver ?? '',
          station: vaga.station ?? vaga['Station Name'] ?? '',
          schedule: vaga.schedule ?? vaga['Schedule Arrival Time'] ?? '',
          to: vaga.to ?? vaga.TO ?? '',
          plates,
          platesString: vaga.platesString || (Array.isArray(vaga.plates) ? vaga.plates.join(', ') : vaga['Vehicle Plate Number'] || ''),
          'Vehicle Plate Number': vaga['Vehicle Plate Number'] || vaga.platesString || ''
        };
        return [vagaKey, normalized];
      }));
    } catch (error) {
      console.error('Erro ao carregar vagas do banco:', error);
      return {};
    }
  }

  async function saveAssignedVaga(vagaIndex, item) {
    const response = await fetch('/api/vagas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vaga_index: Number(vagaIndex), item })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.message || 'Erro ao salvar vaga no banco.');
    return result.vaga;
  }

  async function removeAssignedVagaByLt(lt) {
    const response = await fetch('/api/vagas/remover', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lt })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.message || 'Erro ao remover vaga do banco.');
    return result.removed ? result.vaga_index || null : null;
  }

  lista.addEventListener('click', (event) => {
    const btnAdd = event.target.closest('.btn-adicionar-vaga');
    if (btnAdd) {
      const item = registros.find((registro) => registro.lt === btnAdd.dataset.lt);
      if (!item) return;

      abrirModalVagas(item);
      return;
    }

    const button = event.target.closest('.btn-concluir');
    if (!button) return;
    concluirMotorista(button.dataset.lt);
  });

  carregarRegistros();
});
