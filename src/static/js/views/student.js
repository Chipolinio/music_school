// Студенческий дашборд

async function renderDashboard(app) {
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
                    <div class="dashboard-header">
                        <h1>Здравствуйте, ${escapeHtml(user.full_name)}!</h1>
                        <p class="dashboard-welcome">Добро пожаловать в личный кабинет</p>
                    </div>
                    
                    <div id="next-lesson-widget"></div>
                    
                    <div class="dashboard-actions">
                        <a href="#booking" class="btn btn-primary">Записаться на урок</a>
                        <a href="#rehearsal" class="btn btn-secondary">Арендовать комнату</a>
                        <a href="#my-bookings" class="btn btn-outline">Мои записи</a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Загружаем виджет ближайшего урока
    await loadNextLessonWidget();
}

async function loadNextLessonWidget() {
    const widget = document.getElementById('next-lesson-widget');
    if (!widget) return;
    
    try {
        const user = await API.get('/auth/me');
        const bookingsData = await API.get(`/bookings/student/${user.id}`);
        const bookings = bookingsData.bookings || bookingsData.items || [];
        
        if (bookings.length === 0) {
            widget.innerHTML = `
                <div class="next-lesson-card">
                    <div class="next-lesson-label">Ближайший урок</div>
                    <div class="next-lesson-empty">У вас пока нет записей на уроки</div>
                </div>
            `;
            return;
        }
        
        // Находим ближайший будущий урок
        const now = new Date();
        let nearestBooking = null;
        let nearestSlot = null;
        
        for (const booking of bookings) {
            try {
                const slot = await API.get(`/schedule/${booking.slot_id}`);
                const startTime = new Date(slot.start_time);
                if (startTime > now) {
                    if (!nearestSlot || startTime < new Date(nearestSlot.start_time)) {
                        nearestBooking = booking;
                        nearestSlot = slot;
                    }
                }
            } catch (e) {
                // Пропускаем ошибки
            }
        }
        
        if (!nearestSlot) {
            widget.innerHTML = `
                <div class="next-lesson-card">
                    <div class="next-lesson-label">Ближайший урок</div>
                    <div class="next-lesson-empty">Нет предстоящих уроков</div>
                </div>
            `;
            return;
        }
        
        // Получаем преподавателя
        let teacherName = '';
        try {
            const teacher = await API.get(`/users/${nearestSlot.teacher_id}`);
            teacherName = teacher.full_name;
        } catch (e) {
            // Игнорируем
        }
        
        widget.innerHTML = `
            <div class="next-lesson-card">
                <div class="next-lesson-label">Ближайший урок</div>
                <div class="next-lesson-info">${formatDate(nearestSlot.start_time)}, ${formatTime(nearestSlot.start_time)}</div>
                <div class="next-lesson-details">Преподаватель: ${escapeHtml(teacherName)}</div>
            </div>
        `;
    } catch (e) {
        widget.innerHTML = `
            <div class="next-lesson-card">
                <div class="next-lesson-label">Ближайший урок</div>
                <div class="next-lesson-empty">Ошибка загрузки данных</div>
            </div>
        `;
    }
}

// Мои записи
async function renderMyBookings(app) {
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
                    <h2 class="section-title">Мои записи</h2>
                    <div id="bookings-list" class="loading">Загрузка...</div>
                </div>
            </div>
        </div>
    `;
    
    await loadMyBookings(user.id);
}

async function loadMyBookings(userId) {
    const list = document.getElementById('bookings-list');
    if (!list) return;
    
    try {
        // Загружаем уроки
        const bookingsData = await API.get(`/bookings/student/${userId}`);
        const bookings = bookingsData.bookings || bookingsData.items || [];
        
        // Загружаем репетиции
        const rehearsalsData = await API.get(`/rehearsals/student/${userId}`);
        const rehearsals = rehearsalsData.rehearsals || rehearsalsData.items || [];
        
        if (bookings.length === 0 && rehearsals.length === 0) {
            list.innerHTML = '<div class="empty-state">У вас пока нет записей</div>';
            return;
        }
        
        let html = '';
        
        // Уроки - фильтруем только BOOKED
        for (const booking of bookings) {
            if (booking.status && booking.status !== 'BOOKED') continue;
            
            let slotInfo = null;
            let teacherName = '';
            try {
                slotInfo = await API.get(`/schedule/${booking.slot_id}`);
                const teacher = await API.get(`/users/${slotInfo.teacher_id}`);
                teacherName = teacher.full_name;
            } catch (e) {
                // Пропускаем
            }
            
            if (slotInfo) {
                html += `
                    <div class="booking-item">
                        <div class="booking-info">
                            <div class="booking-type">Урок</div>
                            <div class="booking-details">
                                Дата: ${formatDate(slotInfo.start_time)}, ${formatTime(slotInfo.start_time)}<br>
                                Преподаватель: ${escapeHtml(teacherName)}
                            </div>
                        </div>
                        <div class="booking-actions">
                            <button class="btn btn-danger btn-sm" onclick="cancelBooking('${booking.id}', 'lesson')">Отменить</button>
                        </div>
                    </div>
                `;
            }
        }
        
        // Репетиции - фильтруем только BOOKED
        for (const rehearsal of rehearsals) {
            if (rehearsal.status && rehearsal.status !== 'BOOKED') continue;
            let roomName = '';
            try {
                const room = await API.get(`/rooms/${rehearsal.room_id}`);
                roomName = room.name;
            } catch (e) {
                // Пропускаем
            }
            
            html += `
                <div class="booking-item">
                    <div class="booking-info">
                        <div class="booking-type">Аренда комнаты</div>
                        <div class="booking-details">
                            Дата: ${formatDate(rehearsal.start_time)}, ${formatTime(rehearsal.start_time)}<br>
                            Комната: ${escapeHtml(roomName)}
                        </div>
                    </div>
                    <div class="booking-actions">
                        <button class="btn btn-danger btn-sm" onclick="cancelBooking('${rehearsal.id}', 'rehearsal')">Отменить</button>
                    </div>
                </div>
            `;
        }
        
        list.innerHTML = html || '<div class="empty-state">Нет активных записей</div>';
    } catch (e) {
        list.innerHTML = '<div class="empty-state">Ошибка загрузки данных</div>';
    }
}

function cancelBooking(id, type) {
    if (!confirm('Вы уверены, что хотите отменить запись?')) return;
    
    const endpoint = type === 'lesson' ? `/bookings/${id}/cancel` : `/rehearsals/${id}/cancel`;
    
    fetch(endpoint, { method: 'POST', credentials: 'include' })
    .then(res => {
        if (!res.ok) return res.json().then(d => { throw d; });
        return res.json();
    })
    .then(() => {
        showToast('Запись отменена', 'success');
        API.get('/auth/me').then(user => loadMyBookings(user.id));
    })
    .catch(e => {
        showToast(e.detail || 'Ошибка при отмене', 'error');
    });
}
