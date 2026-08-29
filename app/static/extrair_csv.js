document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('csv-file');
  const extractBtn = document.getElementById('extract-btn');
  const clearBtn = document.getElementById('clear-btn');
  const status = document.getElementById('csv-status');
  const info = document.getElementById('csv-info');
  const tableContainer = document.getElementById('csv-table-container');

  function atualizarStatus(text, isError = false) {
    status.textContent = text;
    status.style.color = isError ? '#b00' : '#333';
  }

  function criarTabela(dados) {
    if (!Array.isArray(dados) || dados.length === 0) {
      tableContainer.innerHTML = '<div class="empty-state">Nenhum dado extraído.</div>';
      return;
    }

    const colunas = Object.keys(dados[0]);
    const thead = colunas
      .map((coluna) => `<th>${coluna}</th>`)
      .join('');

    const linhas = dados
      .map((linha) => `
        <tr>
          ${colunas
            .map((coluna) => `<td>${String(linha[coluna] ?? '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</td>`)
            .join('')}
        </tr>
      `)
      .join('');

    tableContainer.innerHTML = `
      <table class="csv-result-table">
        <thead><tr>${thead}</tr></thead>
        <tbody>${linhas}</tbody>
      </table>
    `;
  }

  extractBtn.addEventListener('click', async () => {
    const arquivo = fileInput.files?.[0];
    if (!arquivo) {
      atualizarStatus('Selecione um arquivo CSV primeiro.', true);
      return;
    }

    const formulario = new FormData();
    formulario.append('file', arquivo);

    atualizarStatus('Enviando arquivo...');
    info.textContent = '';
    tableContainer.innerHTML = '';

    try {
      const response = await fetch('/api/extrair-csv', {
        method: 'POST',
        body: formulario,
      });

      const resultado = await response.json();
      if (!response.ok || !resultado.success) {
        throw new Error(resultado.message || 'Erro desconhecido');
      }

      atualizarStatus(`${resultado.count} motorista(s) extraído(s)`);
      info.textContent = '';
      tableContainer.innerHTML = '';
    } catch (error) {
      console.error('Erro ao extrair CSV:', error);
      atualizarStatus(String(error.message || 'Erro ao processar o CSV.'), true);
    }
  });

  fileInput.addEventListener('change', () => {
    const arquivo = fileInput.files?.[0];
    if (arquivo) {
      atualizarStatus(`Arquivo selecionado: ${arquivo.name}`);
    } else {
      atualizarStatus('Nenhum arquivo selecionado.');
    }
  });

    clearBtn.addEventListener('click', async () => {
      atualizarStatus('Limpando descarregamento.json...');
      try {
        const response = await fetch('/api/limpar-descarregamento', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });
        const resultado = await response.json();
        if (!response.ok || !resultado.success) {
          throw new Error(resultado.message || 'Erro desconhecido');
        }

        atualizarStatus('Arquivo limpo. Pronto para nova extração.');
        info.textContent = '';
        tableContainer.innerHTML = '';
      } catch (error) {
        console.error('Erro ao limpar JSON:', error);
        atualizarStatus(String(error.message || 'Erro ao limpar o arquivo.'), true);
      }
    });
  });
