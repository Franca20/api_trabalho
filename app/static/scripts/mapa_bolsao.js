
const assignedDrivers = new Map();

function loadAssignedDrivers() {
  const saved = JSON.parse(localStorage.getItem('assignedVagas') || '{}');
  Object.entries(saved).forEach(([vagaIndex, item]) => {
    assignedDrivers.set(vagaIndex, item);
    const vagaBtn = document.querySelector(`.infoBtn[data-index="${vagaIndex}"]`);
    if (vagaBtn) {
      const platesText = item.platesString
        || (Array.isArray(item.plates)
          ? item.plates.join(', ')
          : item['Vehicle Plate Number'] || item.plates || 'sem placa');
      vagaBtn.textContent = platesText;
      vagaBtn.dataset.title = platesText;
      vagaBtn.dataset.body = `Motorista atribuído à vaga ${vagaIndex}`;
    }
  });
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatDriverCard(item) {
  if (!item) return '<div>Sem informações.</div>';
  const driverName = item.driver || item.Driver || 'Sem motorista';
  const lt = item.lt || item.LT || '—';
  const station = item.station || item['Station Name'] || '—';
  const plates = item.platesString
    || (Array.isArray(item.plates)
      ? item.plates.join(', ')
      : item['Vehicle Plate Number'] || item.plates || '—');
  const schedule = item.schedule || item['Schedule Arrival Time'] || '—';
  const to = item.to || item.TO || '—';

  return `
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">${escapeHtml(driverName)}</h5>
        <p><strong>LT:</strong> ${escapeHtml(lt)}</p>
        <p><strong>Estação:</strong> ${escapeHtml(station)}</p>
        <p><strong>Placa(s):</strong> ${escapeHtml(plates)}</p>
        <p><strong>Horário de chegada:</strong> ${escapeHtml(schedule)}</p>
        <p><strong>TO:</strong> ${escapeHtml(to)}</p>
      </div>
    </div>
  `;
}

function updateVagaButton(vagaIndex) {
  const vagaBtn = document.querySelector(`.infoBtn[data-index="${vagaIndex}"]`);
  if (!vagaBtn) return;
  vagaBtn.textContent = `Vaga ${vagaIndex}`;
  vagaBtn.dataset.title = `Vaga ${vagaIndex}`;
  vagaBtn.dataset.body = `Sem motorista atribuído à vaga ${vagaIndex}.`;
}

function removeAssignedVaga(vagaIndex) {
  const saved = JSON.parse(localStorage.getItem('assignedVagas') || '{}');
  if (!saved[vagaIndex]) return false;
  delete saved[vagaIndex];
  localStorage.setItem('assignedVagas', JSON.stringify(saved));
  assignedDrivers.delete(vagaIndex);
  updateVagaButton(vagaIndex);
  return true;
}

function openVagaModal(button) {
  const title = button.dataset.title || 'Vaga';
  const index = button.dataset.index || '';
  const assigned = assignedDrivers.get(index);
  const modalBody = document.getElementById('infoModalBody');
  const modalActions = document.getElementById('infoModalActions');
  document.getElementById('infoModalLabel').textContent = title;

  if (assigned) {
    modalBody.innerHTML = formatDriverCard(assigned);
    modalActions.innerHTML = `<button type="button" class="btn btn-danger" id="remove-vaga-button" data-index="${escapeHtml(index)}">Remover motorista da vaga</button>`;
  } else {
    modalBody.innerHTML = `<div class="card"><div class="card-body"><p>Sem motorista atribuído à vaga ${escapeHtml(index)}.</p></div></div>`;
    modalActions.innerHTML = '';
  }

  const modalEl = document.getElementById('infoModal');
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  modal.show();
}

// Event delegation: um listener para todo o documento
document.addEventListener('click', function (e) {
  const removeBtn = e.target.closest('#remove-vaga-button');
  if (removeBtn) {
    const vagaIndex = removeBtn.dataset.index;
    if (removeAssignedVaga(vagaIndex)) {
      const modalEl = document.getElementById('infoModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
    }
    return;
  }

  const btn = e.target.closest('.infoBtn');
  if (!btn) return;
  openVagaModal(btn);
});

window.addEventListener('storage', function (event) {
  if (event.key !== 'assignedVagas') return;
  assignedDrivers.clear();
  loadAssignedDrivers();
});

loadAssignedDrivers();

// Escuta evento customizado vindo da lista de descarregar para adicionar motorista a uma vaga
document.addEventListener('add-to-vaga', function (e) {
  const item = e.detail?.item;
  if (!item) return;

  const driver = item.driver || item.Driver || 'Motorista';
  const plates = Array.isArray(item.plates) ? item.plates.join(', ') : item['Vehicle Plate Number'] || '';
  const vagaIndex = prompt(`Adicionar ${driver} (${plates}) em qual vaga? Informe o número da vaga:`);
  if (vagaIndex === null) return;

  const vagaBtn = document.querySelector(`.infoBtn[data-index="${vagaIndex}"]`);
  if (!vagaBtn) {
    alert('Vaga não encontrada.');
    return;
  }

  assignedDrivers.set(vagaIndex, item);
  const platesText = plates || 'sem placa';
  vagaBtn.dataset.title = platesText;
  vagaBtn.dataset.body = `Motorista ${driver} atribuído(a) à vaga ${vagaIndex}.`;
  vagaBtn.textContent = platesText;

  openVagaModal(vagaBtn);
});

// Fecha o modal ao pressionar ESC e garante foco (Bootstrap já faz isso, mas você pode customizar)
// (opcional) fechar ao clicar fora do card já é tratado pelo modal do Bootstrap
