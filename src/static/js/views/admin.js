// Админ-панель

let currentAdminTab = 'users';

async function renderAdmin(app) {
    let user;
    try {
        user = await API.get('/auth/me');
    } catch (e) {
        window.location.hash = '#login';
        return;
    }
    
    app.innerHTML = `
        <div class="page">
            <div class="page-content">
                <div class="container">
                    <h2 class="section-title">Панель администратора</h2>
                    <div id="admin-stats" class="admin-stats"></div>
                    <div class="admin-tabs">
                        <div class="tabs">
                            <button class="tab-btn active" data-tab="users">Пользователи</button>
                            <button class="tab-btn" data-tab="rooms">Комнаты</button>
                            <button class="tab-btn" data-tab="schedule">Расписание</button>
                            <button class="tab-btn" data-tab="reports">Отчёты</button>
                        </div>
                    </div>
                    <div id="tab-content"></div>
                </div>
            </div>
        </div>
    `;
    
    // Обработчики вкладок
    app.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchAdminTab(btn.dataset.tab));
    });
    
    // Загружаем статистику
    await loadAdminStats();
    // Загружаем первую вкладку
    await loadAdminTab('users');
}

function switchAdminTab(tab) {
    currentAdminTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`.tab-btn[data-tab="${tab}"]`).classList.add('active');
    loadAdminTab(tab);
}

async function loadAdminStats() {
    const statsDiv = document.getElementById('admin-stats');
    if (!statsDiv) return;

    try {
        const [usersData, roomsData, scheduleData] = await Promise.all([
            API.get('/users/', { limit: 100 }),
            API.get('/rooms/', { limit: 100 }),
            API.get('/schedule/', { limit: 200 }),
        ]);

        const users = usersData.users || usersData.items || [];
        const rooms = roomsData.rooms || roomsData.items || [];
        const slots = scheduleData.slots || scheduleData.items || [];

        statsDiv.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${users.length}</div>
                    <div class="stat-label">Пользователи</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${rooms.length}</div>
                    <div class="stat-label">Комнаты</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${slots.length}</div>
                    <div class="stat-label">Слоты</div>
                </div>
            </div>
        `;
    } catch (e) {
        statsDiv.innerHTML = '';
    }
}

async function loadAdminTab(tab) {
    const content = document.getElementById('tab-content');
    if (!content) return;
    
    content.innerHTML = '<div class="loading">Загрузка...</div>';
    
    switch (tab) {
        case 'users':
            await loadAdminUsers(content);
            break;
        case 'rooms':
            await loadAdminRooms(content);
            break;
        case 'schedule':
            await loadAdminSchedule(content);
            break;
        case 'reports':
            await loadAdminReports(content);
            break;
    }
}

// Пользователи
async function loadAdminUsers(content) {
    try {
        const data = await API.get('/users/', { limit: 100 });
        const users = data.users || data.items || [];
        
        content.innerHTML = `
            <div class="table-wrapper">
                <table class="table">
                    <thead>
                        <tr>
                            <th>ФИО</th>
                            <th>Телефон</th>
                            <th>Роль</th>
                            <th>Статус</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${users.map(u => `
                            <tr>
                                <td>${escapeHtml(u.full_name)}</td>
                                <td>${escapeHtml(u.phone)}</td>
                                <td>${getRoleName(u.role)}</td>
                                <td>${u.is_active ? '<span class="badge badge-success">Активен</span>' : '<span class="badge badge-danger">Неактивен</span>'}</td>
                                <td>
                                    ${u.is_active 
                                        ? `<button class="btn btn-danger btn-sm" onclick="deactivateUser('${u.id}')">Деактивировать</button>`
                                        : `<button class="btn btn-success btn-sm" onclick="activateUser('${u.id}')">Активировать</button>`
                                    }
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (e) {
        content.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
    }
}

async function deactivateUser(userId) {
    showConfirm('Деактивация', 'Деактивировать пользователя?', async () => {
        try {
            await API.post(`/users/${userId}/deactivate`);
            showToast('Пользователь деактивирован', 'success');
            await loadAdminTab('users');
            await loadAdminStats();
        } catch (e) {
            showToast(e.detail || 'Ошибка', 'error');
        }
    });
}

async function activateUser(userId) {
    try {
        await API.post(`/users/${userId}/activate`);
        showToast('Пользователь активирован', 'success');
        await loadAdminTab('users');
        await loadAdminStats();
    } catch (e) {
        showToast(e.detail || 'Ошибка', 'error');
    }
}

// Комнаты
async function loadAdminRooms(content) {
    try {
        const data = await API.get('/rooms/', { limit: 100 });
        const rooms = data.rooms || data.items || [];
        
        content.innerHTML = `
            <div class="room-form">
                <div class="form-group">
                    <label class="form-label">Название</label>
                    <input type="text" class="form-input" id="room-name" placeholder="Название комнаты">
                </div>
                <div class="form-group">
                    <label class="form-label">Вместимость</label>
                    <input type="number" class="form-input" id="room-capacity" placeholder="3" min="1" max="100" value="3">
                </div>
                <button class="btn btn-primary" id="add-room-btn">Создать</button>
            </div>
            <div id="rooms-list">
                ${rooms.map(r => `
                    <div class="room-item">
                        <div>
                            <strong>${escapeHtml(r.name)}</strong>
                            <span class="text-muted text-sm"> (Вместимость: ${r.capacity})</span>
                        </div>
                        <div>
                            <button class="btn btn-danger btn-sm" onclick="deleteRoom('${r.id}')">Удалить</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        document.getElementById('add-room-btn').addEventListener('click', async () => {
            const name = document.getElementById('room-name').value.trim();
            const capacity = parseInt(document.getElementById('room-capacity').value);
            
            if (!name) {
                showToast('Введите название', 'warning');
                return;
            }
            
            try {
                await API.post('/rooms/', { name, capacity });
                showToast('Комната создана', 'success');
                await loadAdminTab('rooms');
                await loadAdminStats();
            } catch (e) {
                showToast(e.detail || 'Ошибка', 'error');
            }
        });
    } catch (e) {
        content.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
    }
}

async function deleteRoom(roomId) {
    showConfirm('Удаление', 'Удалить комнату?', async () => {
        try {
            await API.delete(`/rooms/${roomId}`);
            showToast('Комната удалена', 'success');
            await loadAdminTab('rooms');
            await loadAdminStats();
        } catch (e) {
            showToast(e.detail || 'Ошибка', 'error');
        }
    });
}

// Расписание
async function loadAdminSchedule(content) {
    try {
        // Загружаем преподавателей, комнаты и существующие слоты
        const [teachersData, roomsData, slotsData] = await Promise.all([
            API.get('/users/', { role: 'TEACHER' }),
            API.get('/rooms/', { limit: 100 }),
            API.get('/schedule/', { limit: 200 }),
        ]);

        const teachers = teachersData.users || teachersData.items || [];
        const rooms = roomsData.rooms || roomsData.items || [];
        const slots = slotsData.slots || slotsData.items || [];

        // Сортируем слоты по времени
        slots.sort((a, b) => new Date(a.start_time) - new Date(b.start_time));

        content.innerHTML = `
            <h3 class="mb-md">Существующие слоты (${slots.length})</h3>
            <div class="table-wrapper mb-lg">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Начало</th>
                            <th>Окончание</th>
                            <th>Преподаватель</th>
                            <th>Комната</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody id="existing-slots-list">
                        ${slots.length === 0 ? '<tr><td colspan="5" class="text-center text-muted">Нет слотов</td></tr>' : ''}
                    </tbody>
                </table>
            </div>
            <h3 class="mb-md">Создать новый слот</h3>
            <div class="schedule-form">
                <div class="form-group">
                    <label class="form-label">Преподаватель</label>
                    <select class="form-select" id="slot-teacher">
                        <option value="">Выберите</option>
                        ${teachers.map(t => `<option value="${t.id}">${escapeHtml(t.full_name)}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Комната</label>
                    <select class="form-select" id="slot-room">
                        <option value="">Выберите</option>
                        ${rooms.map(r => `<option value="${r.id}">${escapeHtml(r.name)}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Дата</label>
                    <input type="date" class="form-input" id="slot-date">
                </div>
                <div class="form-group">
                    <label class="form-label">Начало</label>
                    <select class="form-select" id="slot-start-hour">
                        <option value="">Выберите</option>
                        <option value="8">08:00</option>
                        <option value="9">09:00</option>
                        <option value="10">10:00</option>
                        <option value="11">11:00</option>
                        <option value="12">12:00</option>
                        <option value="13">13:00</option>
                        <option value="14">14:00</option>
                        <option value="15">15:00</option>
                        <option value="16">16:00</option>
                        <option value="17">17:00</option>
                        <option value="18">18:00</option>
                        <option value="19">19:00</option>
                        <option value="20">20:00</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Длительность</label>
                    <select class="form-select" id="slot-duration">
                        <option value="1">1 час</option>
                        <option value="2">2 часа</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Окончание</label>
                    <input type="text" class="form-input" id="slot-end" readonly style="background-color: var(--color-muted);">
                </div>
                <div class="form-group">
                    <label class="form-label">Макс. участников</label>
                    <input type="number" class="form-input" id="slot-max" value="1" min="1" max="20">
                </div>
                <div class="form-group">
                    <button class="btn btn-primary" id="add-slot-btn" style="margin-top: var(--spacing-md);">Создать слот</button>
                </div>
            </div>
        `;

        // Загружаем существующие слоты с именами
        const slotsList = document.getElementById('existing-slots-list');
        if (slotsList && slots.length > 0) {
            const teacherMap = {};
            const roomMap = {};
            teachers.forEach(t => { teacherMap[t.id] = t.full_name; });
            rooms.forEach(r => { roomMap[r.id] = r.name; });

            slotsList.innerHTML = slots.map(s => `
                <tr>
                    <td>${formatDateTime(s.start_time)}</td>
                    <td>${formatDateTime(s.end_time)}</td>
                    <td>${escapeHtml(teacherMap[s.teacher_id] || '—')}</td>
                    <td>${escapeHtml(roomMap[s.room_id] || '—')}</td>
                    <td><button class="btn btn-danger btn-sm" onclick="deleteSlot('${s.id}')">Удалить</button></td>
                </tr>
            `).join('');
        }

        // Auto-fill end time when date or start hour changes
        function updateEndField() {
            const dateVal = document.getElementById('slot-date').value;
            const hourVal = document.getElementById('slot-start-hour').value;
            const duration = parseInt(document.getElementById('slot-duration').value);
            const endField = document.getElementById('slot-end');
            if (dateVal && hourVal) {
                const startHour = parseInt(hourVal);
                const endHour = startHour + duration;
                const startStr = String(startHour).padStart(2, '0') + ':00';
                const endStr = String(endHour).padStart(2, '0') + ':00';
                endField.value = `${startStr} — ${endStr}`;
            } else {
                endField.value = '';
            }
        }
        document.getElementById('slot-date').addEventListener('change', updateEndField);
        document.getElementById('slot-start-hour').addEventListener('change', updateEndField);
        document.getElementById('slot-duration').addEventListener('change', updateEndField);

        document.getElementById('add-slot-btn').addEventListener('click', async () => {
            const teacherId = document.getElementById('slot-teacher').value;
            const roomId = document.getElementById('slot-room').value;
            const dateVal = document.getElementById('slot-date').value;
            const startHour = parseInt(document.getElementById('slot-start-hour').value);
            const duration = parseInt(document.getElementById('slot-duration').value);
            const maxParticipants = parseInt(document.getElementById('slot-max').value);

            if (!teacherId || !roomId || !dateVal || isNaN(startHour)) {
                showToast('Заполните все поля', 'warning');
                return;
            }

            const startHourStr = String(startHour).padStart(2, '0');
            const endHour = startHour + duration;
            const endHourStr = String(endHour).padStart(2, '0');
            const startTime = new Date(`${dateVal}T${startHourStr}:00`).toISOString();
            const endTime = new Date(`${dateVal}T${endHourStr}:00`).toISOString();

            try {
                await API.post('/schedule/', {
                    teacher_id: parseInt(teacherId),
                    room_id: parseInt(roomId),
                    start_time: startTime,
                    end_time: endTime,
                    max_participants: maxParticipants,
                });
                showToast('Слот создан', 'success');
                await loadAdminTab('schedule');
                await loadAdminStats();
            } catch (e) {
                showToast(e.detail || 'Ошибка', 'error');
            }
        });
    } catch (e) {
        content.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
    }
}

async function deleteSlot(slotId) {
    showConfirm('Удаление', 'Удалить слот?', async () => {
        try {
            await API.delete(`/schedule/${slotId}`);
            showToast('Слот удалён', 'success');
            await loadAdminTab('schedule');
            await loadAdminStats();
        } catch (e) {
            showToast(e.detail || 'Ошибка', 'error');
        }
    });
}

// Отчёты
async function loadAdminReports(content) {
    // Устанавливаем даты по умолчанию
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 3);
    
    content.innerHTML = `
        <div class="report-filters">
            <div class="form-group">
                <label class="form-label">Начальная дата</label>
                <input type="date" class="form-input" id="report-start" value="${startDate.toISOString().split('T')[0]}">
            </div>
            <div class="form-group">
                <label class="form-label">Конечная дата</label>
                <input type="date" class="form-input" id="report-end" value="${endDate.toISOString().split('T')[0]}">
            </div>
            <div class="form-group">
                <button class="btn btn-primary" id="run-report-btn" style="margin-top: var(--spacing-md);">Сформировать</button>
            </div>
        </div>
        <div id="report-result"></div>
    `;
    
    document.getElementById('run-report-btn').addEventListener('click', async () => {
        const start = document.getElementById('report-start').value;
        const end = document.getElementById('report-end').value;

        if (!start || !end) {
            showToast('Выберите даты', 'warning');
            return;
        }

        const resultDiv = document.getElementById('report-result');
        resultDiv.innerHTML = '<div class="loading">Загрузка...</div>';

        try {
            const data = await API.get('/reports/lessons-by-teacher', {
                start_date: start,
                end_date: end,
            });

            // API возвращает массив напрямую
            const report = Array.isArray(data) ? data : (data.report || data.items || []);
            console.log('Report data:', data, 'isArray:', Array.isArray(data), 'length:', report ? report.length : 'N/A');

            if (report.length === 0) {
                resultDiv.innerHTML = '<div class="empty-state">Нет данных за выбранный период</div>';
                return;
            }

            resultDiv.innerHTML = `
                <h3 class="mb-md">Уроки по преподавателям</h3>
                <div class="table-wrapper">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Преподаватель</th>
                                <th>Количество уроков</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${report.map(r => `
                                <tr>
                                    <td>${escapeHtml(r.teacher_name)}</td>
                                    <td>${r.lesson_count}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <div class="mt-md">
                    <a href="/reports/lessons-by-teacher/csv?start_date=${start}&end_date=${end}" target="_blank" class="btn btn-outline">Экспорт в CSV</a>
                </div>
            `;
        } catch (e) {
            resultDiv.innerHTML = '<div class="empty-state">Ошибка формирования отчёта</div>';
        }
    });
}
