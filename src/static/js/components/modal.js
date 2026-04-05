// Модальные окна
function showModal(title, message, buttons = [], type = '') {
    const container = document.getElementById('modal-container');
    container.className = 'active';
    
    const typeClass = type ? `modal-${type}` : '';
    
    container.innerHTML = `
        <div class="modal-overlay"></div>
        <div class="modal ${typeClass}">
            <h3 class="modal-title">${title}</h3>
            <p class="modal-text">${message}</p>
            <div class="modal-actions">
                ${buttons.map(b => `<button class="btn ${b.class || 'btn-outline'}" data-action="${b.action}">${b.text}</button>`).join('')}
            </div>
        </div>
    `;
    
    // Обработчик клика по overlay
    container.querySelector('.modal-overlay').addEventListener('click', closeModal);
    
    // Обработчики кнопок
    buttons.forEach(btn => {
        const button = container.querySelector(`[data-action="${btn.action}"]`);
        button.addEventListener('click', () => {
            closeModal();
            if (btn.onClick) btn.onClick();
        });
    });
}

function closeModal() {
    const container = document.getElementById('modal-container');
    container.className = '';
    container.innerHTML = '';
}

function showConfirm(title, message, onConfirm) {
    showModal(title, message, [
        { text: 'Отмена', action: 'cancel', class: 'btn-outline', onClick: () => {} },
        { text: 'Подтвердить', action: 'confirm', class: 'btn-primary', onClick: onConfirm },
    ]);
}

function showError(message) {
    showModal('Ошибка', message, [
        { text: 'Закрыть', action: 'close', class: 'btn-primary', onClick: () => {} },
    ], 'error');
}

function showSuccess(message) {
    showModal('Успех', message, [
        { text: 'OK', action: 'close', class: 'btn-success', onClick: () => {} },
    ], 'success');
    
    // Автозакрытие через 2 секунды
    setTimeout(closeModal, 2000);
}
