document.addEventListener('DOMContentLoaded', () => {
    const ltInput = document.getElementById('lt-input');
    const gerarBtn = document.getElementById('gerar-btn');
    const copiarBtn = document.getElementById('copiar-btn');
    const qrStatus = document.getElementById('qr-status');
    const ltDisplay = document.getElementById('lt-display');
    const qrImage = document.getElementById('qr-image');

    const updateQr = async () => {
        const lt = (ltInput.value || '').trim().toUpperCase();
        if (!lt) {
            qrStatus.textContent = 'Aguardando LT...';
            ltDisplay.textContent = 'LT';
            qrImage.hidden = true;
            return;
        }

        qrStatus.textContent = 'Gerando QR Code...';
        try {
            const response = await fetch('/api/lt/qr', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lt })
            });

            if (!response.ok) {
                throw new Error('Não foi possível gerar o QR Code.');
            }

            const data = await response.json();
            ltDisplay.textContent = data.lt;
            qrImage.src = `data:image/png;base64,${data.qr_image}`;
            qrImage.hidden = false;
            qrStatus.textContent = `QR Code pronto para o coletor. LT: ${data.lt}`;
        } catch (error) {
            qrStatus.textContent = error.message || 'Erro ao gerar o QR Code.';
            qrImage.hidden = true;
        }
    };

    gerarBtn.addEventListener('click', updateQr);
    ltInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            updateQr();
        }
    });

    copiarBtn.addEventListener('click', async () => {
        const lt = (ltInput.value || '').trim().toUpperCase();
        if (!lt) return;

        try {
            await navigator.clipboard.writeText(lt);
            qrStatus.textContent = 'LT copiada para a área de transferência.';
        } catch (error) {
            qrStatus.textContent = 'Não foi possível copiar automaticamente.';
        }
    });
});
