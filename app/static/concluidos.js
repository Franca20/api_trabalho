(() => {
  const busca = document.getElementById('busca-concluidos');
  const lista = document.getElementById('concluidos-list');
  const modalLimpar = document.getElementById('modal-limpar-concluidos');
  const senhaLimpar = document.getElementById('senha-limpar-concluidos');
  const cancelarLimpar = document.getElementById('cancelar-limpar-concluidos');
  const confirmarLimpar = document.getElementById('confirmar-limpar-concluidos');

  let dadosConcluidos = [];

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function formatPlacas(plates) {
    if (!Array.isArray(plates) || plates.length === 0) {
      return '—';
    }
    return plates.map((plate) => escapeHtml(plate)).join(', ');
  }

  function criarCard(item) {
    const placas = formatPlacas(item.plates);
    return `
      <article class="concluido-card">
        <h3>LT: ${escapeHtml(item.LT || item.lt || 'Sem LT')}</h3>
        <div class="concluido-meta">
          <span><strong>Driver:</strong> ${escapeHtml(item.driver || 'Sem motorista')}</span>
          <span><strong>Placas:</strong> ${placas}</span>
          <span><strong>ETA:</strong> ${escapeHtml(item.schedule || '—')}</span>
          <span class="concluido-chip">Status: ${escapeHtml(item.status || 'Concluído')}</span>
          <span><strong>Concluído em:</strong> ${escapeHtml(item.concluido_em || '—')}</span>
        </div>
      </article>
    `;
  }

  function filtrarConcluidos(query) {
    const termo = String(query || '').trim().toLowerCase();
    if (!termo) return dadosConcluidos;

    return dadosConcluidos.filter((item) => {
      const lt = String(item.LT || item.lt || '').toLowerCase();
      const driver = String(item.driver || '').toLowerCase();
      const placas = formatPlacas(item.plates || []).toLowerCase();
      return lt.includes(termo) || driver.includes(termo) || placas.includes(termo);
    });
  }

  async function carregarConcluidos() {
    try {
      const response = await fetch('/api/concluidos', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const dados = await response.json();

      if (!Array.isArray(dados) || dados.length === 0) {
        lista.innerHTML = '<div class="empty-state">Nenhum motorista concluído encontrado hoje.</div>';
        return;
      }

      dadosConcluidos = dados;
      lista.innerHTML = dadosConcluidos.map(criarCard).join('');
    } catch (error) {
      console.error('Erro ao carregar concluídos:', error);
      lista.innerHTML = '<div class="empty-state">Não foi possível carregar os dados.</div>';
    }
  }

  function fecharModalLimpar() {
    modalLimpar.classList.remove('show');
    modalLimpar.setAttribute('aria-hidden', 'true');
    senhaLimpar.value = '';
    document.body.style.overflow = '';
  }

  window.limparConcluidos = () => {
    modalLimpar.classList.add('show');
    modalLimpar.setAttribute('aria-hidden', 'false');
    senhaLimpar.focus();
    document.body.style.overflow = 'hidden';
  };

  async function confirmarLimpeza() {
    const password = senhaLimpar.value;
    if (!password) return;

    try {
      const response = await fetch('/api/concluidos/limpar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });
      const resultado = await response.json();
      if (!response.ok) throw new Error(resultado.message || 'Não foi possível limpar os concluídos.');
      dadosConcluidos = [];
      lista.innerHTML = '<div class="empty-state">Nenhum motorista concluído encontrado.</div>';
      fecharModalLimpar();
      window.alert(resultado.message);
    } catch (error) {
      window.alert(error.message);
    }
  }

  cancelarLimpar.addEventListener('click', fecharModalLimpar);
  confirmarLimpar.addEventListener('click', confirmarLimpeza);
  senhaLimpar.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') confirmarLimpeza();
  });
  modalLimpar.addEventListener('click', (event) => {
    if (event.target === modalLimpar) fecharModalLimpar();
  });

  if (busca) {
    busca.addEventListener('input', () => {
      const filtrados = filtrarConcluidos(busca.value);
      if (!filtrados.length) {
        lista.innerHTML = '<div class="empty-state">Nenhum motorista concluído encontrado.</div>';
        return;
      }
      lista.innerHTML = filtrados.map(criarCard).join('');
    });
  }

  carregarConcluidos();
})();
