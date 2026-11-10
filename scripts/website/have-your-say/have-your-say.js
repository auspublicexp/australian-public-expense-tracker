(() => {
    'use strict';
    const status = document.getElementById('action-status');
    const announce = message => { status.textContent = message; };
    const copyButtons = document.querySelectorAll('[data-copy]');
    for (const button of copyButtons) {
        button.hidden = false;
        button.addEventListener('click', async () => {
            const field = document.getElementById(button.dataset.copy);
            try {
                if (!navigator.clipboard || !window.isSecureContext) throw new Error('Manual copy needed');
                await navigator.clipboard.writeText(field.value);
                announce(button.dataset.copy === 'letter-draft' ? 'Letter copied. Review it and send it using the recipient’s official contact details.' : 'Figures and source copied. Paste the note into your letter.');
            } catch {
                field.focus();
                field.select();
                announce('The text is selected. Use your device’s Copy command (Ctrl+C or Command+C on a keyboard).');
            }
            // Keep feedback beside the control, including the evidence worksheet.
            button.parentElement.insertAdjacentElement('afterend', status);
        });
    }
    const download = document.getElementById('download-letter');
    download.hidden = false;
    download.addEventListener('click', () => {
        const draft = document.getElementById('letter-draft').value;
        const blob = new Blob([draft], {type: 'text/plain;charset=utf-8'});
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'my-public-spending-letter.txt';
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        download.parentElement.insertAdjacentElement('afterend', status);
        announce('Letter download requested. Review your saved draft before sending.');
    });
    const print = document.getElementById('print-guide');
    print.hidden = false;
    print.addEventListener('click', () => window.print());
    let opened = [];
    window.addEventListener('beforeprint', () => {
        opened = [...document.querySelectorAll('.say-page details:not([open])')];
        opened.forEach(detail => { detail.open = true; });
        document.querySelectorAll('.say-page textarea').forEach(field => {
            if (field.classList.contains('say-print-ready')) return;
            const text = document.createElement('div');
            text.className = 'say-print-text';
            text.textContent = field.value;
            field.insertAdjacentElement('afterend', text);
            field.classList.add('say-print-ready');
        });
    });
    window.addEventListener('afterprint', () => {
        document.querySelectorAll('.say-print-text').forEach(text => text.remove());
        document.querySelectorAll('.say-print-ready').forEach(field => field.classList.remove('say-print-ready'));
        opened.forEach(detail => { detail.open = false; });
        opened = [];
    });
})();
