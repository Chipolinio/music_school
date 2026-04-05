const protectedRoutes = {
    '#dashboard': 'STUDENT',
    '#teacher': 'TEACHER',
    '#admin': 'ADMIN',
    '#booking': 'STUDENT',
    '#rehearsal': 'STUDENT',
    '#my-bookings': 'STUDENT',
};

const roleRedirects = {
    'STUDENT': '#dashboard',
    'TEACHER': '#teacher',
    'ADMIN': '#admin',
};

let currentUser = null;

async function navigate(hash) {
    if (!hash || hash === '' || hash === '#') {
        window.location.hash = '#home';
        return;
    }

    // Проверяем защищённые маршруты
    const requiredRole = protectedRoutes[hash];
    if (requiredRole) {
        try {
            if (typeof currentUser === 'undefined' || !currentUser) {
                currentUser = await API.get('/auth/me');
            }
            if (!currentUser) {
                window.location.hash = '#login';
                return;
            }
            if (currentUser.role !== requiredRole) {
                showAccessDenied();
                return;
            }
        } catch (e) {
            window.location.hash = '#login';
            return;
        }
    }
    
    renderView(hash);
}

function renderView(hash) {
    const app = document.getElementById('app');
    
    // Определяем какой view рендерить
    switch (hash) {
        case '#home':
            renderHome(app);
            break;
        case '#login':
            renderLogin(app);
            break;
        case '#register':
            renderRegister(app);
            break;
        case '#dashboard':
            renderDashboard(app);
            break;
        case '#booking':
            renderBooking(app);
            break;
        case '#rehearsal':
            renderRehearsal(app);
            break;
        case '#my-bookings':
            renderMyBookings(app);
            break;
        case '#teacher':
            renderTeacherDashboard(app);
            break;
        case '#admin':
            renderAdmin(app);
            break;
        default:
            renderHome(app);
    }
    
    // Рендерим навбар
    renderNavbar();
}

function redirectTo(hash) {
    window.location.hash = hash;
}

function showAccessDenied() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="container page-content text-center">
            <h2>Доступ запрещён</h2>
            <p class="text-muted mt-md">У вас нет прав для доступа к этой странице.</p>
            <a href="#home" class="btn btn-primary mt-lg">На главную</a>
        </div>
    `;
}

// Инициализация роутера
function initRouter() {
    window.addEventListener('hashchange', () => {
        navigate(window.location.hash);
    });
    
    // Начальная навигация
    navigate(window.location.hash);
}
