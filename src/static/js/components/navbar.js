// Навигационная панель
// currentUser объявлен в router.js как глобальная переменная

async function renderNavbar() {
    const existing = document.querySelector('.navbar');
    if (existing) existing.remove();
    
    try {
        currentUser = await API.get('/auth/me');
    } catch (e) {
        currentUser = null;
    }
    
    const nav = document.createElement('nav');
    nav.className = 'navbar';
    
    const brandLink = currentUser ? roleRedirects[currentUser.role] || '#home' : '#home';
    
    nav.innerHTML = `
        <div class="container">
            <a href="${brandLink}" class="navbar-brand">Music School</a>
            <div class="navbar-nav">
                ${getNavLinks()}
            </div>
        </div>
    `;
    
    document.body.insertBefore(nav, document.body.firstChild);
    
    // Инициализация уведомлений если пользователь авторизован
    if (currentUser) {
        initNotifications();
    }
}

function getNavLinks() {
    if (!currentUser) {
        return `
            <a href="#home" class="nav-link">Главная</a>
            <a href="#login" class="nav-link">Войти</a>
            <a href="#register" class="nav-link">Регистрация</a>
        `;
    }
    
    let links = '';
    
    switch (currentUser.role) {
        case 'STUDENT':
            links = `
                <a href="#dashboard" class="nav-link">Мой кабинет</a>
                <a href="#booking" class="nav-link">Записаться</a>
                <a href="#rehearsal" class="nav-link">Аренда</a>
                <a href="#my-bookings" class="nav-link">Мои записи</a>
            `;
            break;
        case 'TEACHER':
            links = `
                <a href="#teacher" class="nav-link">Моё расписание</a>
            `;
            break;
        case 'ADMIN':
            links = `
                <a href="#admin" class="nav-link">Админ-панель</a>
            `;
            break;
    }
    
    return `
        ${links}
        <div class="notifications-wrapper" id="notifications-wrapper"></div>
        <span class="text-muted text-sm">${currentUser.full_name}</span>
        <button class="btn btn-outline btn-sm" id="logout-btn">Выйти</button>
    `;
}

// Инициализация кнопки выхода
document.addEventListener('click', (e) => {
    if (e.target.id === 'logout-btn') {
        handleLogout();
    }
});

async function handleLogout() {
    try {
        await API.post('/auth/logout');
    } catch (e) {
        // Игнорируем ошибки при выходе
    }
    currentUser = null;
    window.location.hash = '#home';
}

// Уведомления в навбаре
let notificationsOpen = false;

async function initNotifications() {
    const wrapper = document.getElementById('notifications-wrapper');
    if (!wrapper) return;
    
    // Получаем количество непрочитанных
    let unreadCount = 0;
    try {
        const data = await API.get(`/notifications/user/${currentUser.id}`, { unread_only: true });
        unreadCount = data.unread_count || 0;
    } catch (e) {
        // Игнорируем ошибки
    }
    
    wrapper.innerHTML = `
        <button class="notifications-btn" id="notifications-btn">
            &#9834;
            ${unreadCount > 0 ? `<span class="notifications-badge">${unreadCount}</span>` : ''}
        </button>
        <div class="notifications-dropdown" id="notifications-dropdown">
            <div class="notifications-header">
                <h4>Уведомления</h4>
                <button class="btn btn-sm btn-outline" id="mark-all-read">Прочитать все</button>
            </div>
            <ul class="notifications-list" id="notifications-list"></ul>
        </div>
    `;
    
    // Обработчик кнопки уведомлений
    document.getElementById('notifications-btn').addEventListener('click', toggleNotifications);
    document.getElementById('mark-all-read').addEventListener('click', markAllAsRead);
}

async function toggleNotifications() {
    const dropdown = document.getElementById('notifications-dropdown');
    notificationsOpen = !notificationsOpen;
    
    if (notificationsOpen) {
        dropdown.classList.add('active');
        await loadNotifications();
    } else {
        dropdown.classList.remove('active');
    }
}

async function loadNotifications() {
    const list = document.getElementById('notifications-list');
    if (!list) return;
    
    try {
        const data = await API.get(`/notifications/user/${currentUser.id}`, { unread_only: false });
        const notifications = data.notifications || [];
        
        if (notifications.length === 0) {
            list.innerHTML = '<li class="notifications-empty">Нет уведомлений</li>';
            return;
        }
        
        list.innerHTML = notifications.slice(0, 10).map(n => `
            <li class="${n.is_read ? '' : 'unread'}" data-id="${n.id}">
                <div class="notif-title">${escapeHtml(n.title)}</div>
                <div class="notif-message">${escapeHtml(n.message)}</div>
                <div class="notif-time">${formatDateTime(n.created_at)}</div>
            </li>
        `).join('');
        
        // Обработчик клика по уведомлению
        list.querySelectorAll('li[data-id]').forEach(li => {
            li.addEventListener('click', () => markAsRead(li.dataset.id));
        });
    } catch (e) {
        list.innerHTML = '<li class="notifications-empty">Ошибка загрузки</li>';
    }
}

async function markAsRead(notificationId) {
    try {
        await API.post(`/notifications/${notificationId}/mark-as-read?user_id=${currentUser.id}`);
        await loadNotifications();
        await updateNotificationsBadge();
    } catch (e) {
        showToast('Ошибка при отметке уведомления', 'error');
    }
}

async function markAllAsRead() {
    try {
        await API.post(`/notifications/user/${currentUser.id}/mark-all-as-read`);
        await loadNotifications();
        await updateNotificationsBadge();
        showToast('Все уведомления отмечены как прочитанные', 'success');
    } catch (e) {
        showToast('Ошибка при отметке уведомлений', 'error');
    }
}

async function updateNotificationsBadge() {
    try {
        const data = await API.get(`/notifications/user/${currentUser.id}`, { unread_only: true });
        const badge = document.querySelector('.notifications-badge');
        const wrapper = document.getElementById('notifications-wrapper');
        
        if (data.unread_count > 0) {
            if (!badge) {
                const btn = document.getElementById('notifications-btn');
                btn.innerHTML = `&#9834;<span class="notifications-badge">${data.unread_count}</span>`;
            } else {
                badge.textContent = data.unread_count;
            }
        } else if (badge) {
            badge.remove();
        }
    } catch (e) {
        // Игнорируем
    }
}

// Закрытие dropdown при клике вне
document.addEventListener('click', (e) => {
    const wrapper = document.getElementById('notifications-wrapper');
    if (wrapper && !wrapper.contains(e.target) && notificationsOpen) {
        const dropdown = document.getElementById('notifications-dropdown');
        if (dropdown) {
            dropdown.classList.remove('active');
            notificationsOpen = false;
        }
    }
});

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
