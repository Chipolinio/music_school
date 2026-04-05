// Авторизация и регистрация

// Главная страница
function renderHome(app) {
    app.innerHTML = `
        <div class="page">
            <div class="page-content">
                <div class="container">
                    <div class="home-hero">
                        <h1>Музыкальная школа</h1>
                        <p>Записывайтесь на уроки, бронируйте репетиционные комнаты и отслеживайте своё расписание</p>
                        <a href="#register" class="btn btn-primary btn-lg">Начать обучение</a>
                    </div>
                    <div class="home-features">
                        <div class="home-feature-card">
                            <h3>Индивидуальные уроки</h3>
                            <p>Занимайтесь с опытными преподавателями по вашему направлению</p>
                        </div>
                        <div class="home-feature-card">
                            <h3>Репетиционные комнаты</h3>
                            <p>Бронируйте оборудованные залы для самостоятельных занятий</p>
                        </div>
                        <div class="home-feature-card">
                            <h3>Удобное расписание</h3>
                            <p>Выбирайте удобное время и отслеживайте свои записи онлайн</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Страница входа
function renderLogin(app) {
    app.innerHTML = `
        <div class="auth-page">
            <div class="auth-card">
                <h2 class="auth-title">Вход в аккаунт</h2>
                <form id="login-form" class="auth-form">
                    <div class="form-group">
                        <label class="form-label" for="login-phone">Телефон</label>
                        <input type="tel" id="login-phone" name="phone" placeholder="+7 (___) ___-__-__" required class="form-input">
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="login-password">Пароль</label>
                        <input type="password" id="login-password" name="password" placeholder="Пароль" required class="form-input">
                    </div>
                    <button type="submit" class="btn btn-primary">Войти</button>
                </form>
                <div class="auth-link">
                    Нет аккаунта? <a href="#register">Зарегистрироваться</a>
                </div>
            </div>
        </div>
    `;
    
    // Инициализация маски телефона
    const phoneInput = document.getElementById('login-phone');
    phoneInput.addEventListener('input', (e) => {
        e.target.value = applyPhoneMask(e.target.value);
    });
    
    // Обработка формы
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target));
        data.phone = phoneToE164(data.phone);
        
        try {
            const result = await API.post('/auth/login', data);
            const redirect = roleRedirects[result.user.role];
            if (redirect) {
                window.location.hash = redirect;
            } else {
                showToast('Вход выполнен', 'success');
                window.location.hash = '#home';
            }
        } catch (err) {
            const detail = err.detail || 'Ошибка при входе';
            showError(detail);
        }
    });
}

// Страница регистрации
function renderRegister(app) {
    app.innerHTML = `
        <div class="auth-page">
            <div class="auth-card">
                <h2 class="auth-title">Регистрация</h2>
                <form id="register-form" class="auth-form">
                    <div class="form-group">
                        <label class="form-label" for="register-phone">Телефон</label>
                        <input type="tel" id="register-phone" name="phone" placeholder="+7 (___) ___-__-__" required class="form-input">
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="register-name">ФИО</label>
                        <input type="text" id="register-name" name="full_name" placeholder="Иванов Иван Иванович" required class="form-input">
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="register-password">Пароль</label>
                        <input type="password" id="register-password" name="password" placeholder="Минимум 8 символов" required minlength="8" class="form-input">
                    </div>
                    <input type="hidden" name="role" value="STUDENT">
                    <button type="submit" class="btn btn-primary">Зарегистрироваться</button>
                </form>
                <div class="auth-link">
                    Уже есть аккаунт? <a href="#login">Войти</a>
                </div>
            </div>
        </div>
    `;
    
    // Инициализация маски телефона
    const phoneInput = document.getElementById('register-phone');
    phoneInput.addEventListener('input', (e) => {
        e.target.value = applyPhoneMask(e.target.value);
    });
    
    // Обработка формы
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target));
        data.phone = phoneToE164(data.phone);
        
        if (!isValidPassword(data.password)) {
            showError('Пароль должен содержать минимум 8 символов');
            return;
        }
        
        try {
            const result = await API.post('/auth/register', data);
            showToast('Регистрация успешна!', 'success');
            const redirect = roleRedirects[result.user.role];
            if (redirect) {
                window.location.hash = redirect;
            } else {
                window.location.hash = '#home';
            }
        } catch (err) {
            const detail = err.detail || 'Ошибка при регистрации';
            showError(detail);
        }
    });
}
