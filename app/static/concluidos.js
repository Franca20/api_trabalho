document.addEventListener('DOMContentLoaded', async () => {
  const lista = document.getElementById('concluidos-list');

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

  async function carregarConcluidos() {
    try {
      const response = await fetch('/api/concluidos', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const dados = await response.json();

      if (!Array.isArray(dados) || dados.length === 0) {
        lista.innerHTML = '<div class="empty-state">Nenhum motorista concluído encontrado hoje.</div>';
        return;
      }

      lista.innerHTML = dados.map(criarCard).join('');
    } catch (error) {
      console.error('Erro ao carregar concluídos:', error);
      lista.innerHTML = '<div class="empty-state">Não foi possível carregar os dados.</div>';
    }
  }

  carregarConcluidos();
});
