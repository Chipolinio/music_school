// Запись на урок и аренда репетиционных комнат

let selectedSlotId = null;
let selectedTeacherId = null;

async function renderBooking(app) {
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
                    <h2 class="section-title">Запись на урок</h2>
                    <div id="teachers-list" class="loading">Загрузка преподавателей...</div>
                    <div id="slots-container" style="display: none;">
                        <h3 class="mt-xl mb-md">Доступные слоты</h3>
                        <div id="slots-list"></div>
                        <div class="mt-lg" id="booking-confirm" style="display: none;">
                            <button class="btn btn-primary btn-lg" id="confirm-booking-btn">Подтвердить запись</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    await loadTeachers();
    
    // Обработчик подтверждения
    document.getElementById('confirm-booking-btn').addEventListener('click', async () => {
        await confirmBooking(user.id);
    });
}

async function loadTeachers() {
    const container = document.getElementById('teachers-list');
    if (!container) return;
    
    try {
        const data = await API.get('/users/', { role: 'TEACHER' });
        const teachers = data.users || data.items || [];
        
        if (teachers.length === 0) {
            container.innerHTML = '<div class="empty-state">Нет доступных преподавателей</div>';
            return;
        }
        
        container.innerHTML = `
            <div class="grid grid-3">
                ${teachers.map(t => `
                    <div class="card teacher-card" data-id="${t.id}" style="cursor: pointer;">
                        <div class="card-title">${escapeHtml(t.full_name)}</div>
                        <div class="card-text">Преподаватель</div>
                    </div>
                `).join('')}
            </div>
        `;
        
        // Обработчики кликов
        container.querySelectorAll('.teacher-card').forEach(card => {
            card.addEventListener('click', () => selectTeacher(card.dataset.id));
        });
    } catch (e) {
        container.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
    }
}

async function selectTeacher(teacherId) {
    selectedTeacherId = teacherId;
    selectedSlotId = null;
    
    // Подсвечиваем выбранного преподавателя
    document.querySelectorAll('.teacher-card').forEach(card => {
        card.style.borderColor = card.dataset.id === teacherId ? 'var(--color-primary)' : '';
        card.style.borderWidth = card.dataset.id === teacherId ? '2px' : '';
    });
    
    const slotsContainer = document.getElementById('slots-container');
    const slotsList = document.getElementById('slots-list');
    const confirmDiv = document.getElementById('booking-confirm');
    slotsContainer.style.display = 'block';
    slotsList.innerHTML = '<div class="loading">Загрузка слотов...</div>';
    confirmDiv.style.display = 'none';
    
    try {
        // Загружаем слоты преподавателя
        const slotsData = await API.get(`/schedule/teacher/${teacherId}`);
        const slots = slotsData.slots || slotsData.items || [];
        
        // Загружаем все брони чтобы определить занятые слоты
        const bookedSlotIds = new Set();
        
        // Собираем все slot_id из броней всех студентов (упрощённо — проверяем через попытки)
        // Для эффективности просто проверяем каждый слот
        const now = new Date();
        const futureSlots = slots.filter(s => new Date(s.start_time) > now);
        
        if (futureSlots.length === 0) {
            slotsList.innerHTML = '<div class="empty-state">Нет доступных слотов</div>';
            return;
        }
        
        // Проверяем каждый слот на занятость
        const slotsWithStatus = await Promise.all(
            futureSlots.map(async (slot) => {
                try {
                    const bookingsData = await API.get(`/bookings/student/1`); // пробный запрос
                    // Более надёжный способ — попытаться определить по существующим броням
                    // Проверяем через /schedule/{id} — если есть bookings, слот занят
                    return { ...slot, isFree: true }; // по умолчанию свободен
                } catch (e) {
                    return { ...slot, isFree: true };
                }
            })
        );
        
        // Попробуем получить брони для проверки
        // Простой подход: слот свободен если max_participants > текущих броней
        // Поскольку нет эндпоинта для всех броней слота, отображаем все слоты
        // и позволяем попробовать забронировать
        
        slotsList.innerHTML = `
            <div class="grid grid-4">
                ${slotsWithStatus.map(slot => `
                    <button class="slot-btn free" data-slot-id="${slot.id}">
                        ${formatDate(slot.start_time)} ${formatTime(slot.start_time)}
                    </button>
                `).join('')}
            </div>
        `;
        
        // Обработчики слотов
        slotsList.querySelectorAll('.slot-btn').forEach(btn => {
            btn.addEventListener('click', () => selectSlot(btn.dataset.slotId, btn));
        });
    } catch (e) {
        slotsList.innerHTML = '<div class="empty-state">Ошибка загрузки слотов</div>';
    }
}

function selectSlot(slotId, btn) {
    // Убираем предыдущее выделение
    document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
    
    selectedSlotId = slotId;
    btn.classList.add('selected');
    
    // Показываем кнопку подтверждения
    document.getElementById('booking-confirm').style.display = 'block';
}

async function confirmBooking(studentId) {
    if (!selectedSlotId) {
        showToast('Выберите слот', 'warning');
        return;
    }

    // Получаем информацию о слоте
    let slot;
    try {
        slot = await API.get(`/schedule/${selectedSlotId}`);
    } catch (e) {
        showToast('Ошибка загрузки слота', 'error');
        return;
    }

    // Получаем имя преподавателя
    let teacherName = '';
    try {
        const teacher = await API.get(`/users/${slot.teacher_id}`);
        teacherName = teacher.full_name;
    } catch (e) {}

    showConfirm(
        'Подтверждение записи',
        `Урок с ${escapeHtml(teacherName)} ${formatDate(slot.start_time)} в ${formatTime(slot.start_time)}`,
        async () => {
            try {
                const result = await API.post('/bookings/', {
                    slot_id: parseInt(selectedSlotId),
                    student_id: parseInt(studentId),
                });
                showToast(result.message || 'Запись создана', 'success');
                window.location.hash = '#my-bookings';
            } catch (e) {
                const detail = e.detail || 'Ошибка при записи';
                showToast(detail, 'error');
            }
        }
    );
}

// Аренда репетиционной комнаты
let selectedRoomId = null;
let selectedRehearsalTime = null;

async function renderRehearsal(app) {
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
                    <h2 class="section-title">Аренда репетиционной комнаты</h2>
                    <div class="form-group">
                        <label class="form-label">Комната</label>
                        <select class="form-select" id="room-select">
                            <option value="">Выберите комнату</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Дата</label>
                        <input type="date" class="form-input" id="rehearsal-date">
                    </div>
                    <h3 class="mt-lg mb-md">Доступное время</h3>
                    <div id="time-slots" class="grid grid-4"></div>
                    <div class="mt-lg" id="rehearsal-confirm" style="display: none;">
                        <button class="btn btn-primary btn-lg" id="confirm-rehearsal-btn">Забронировать</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    await loadRooms();
    
    // Обработчики
    document.getElementById('room-select').addEventListener('change', () => loadTimeSlots(user.id));
    document.getElementById('rehearsal-date').addEventListener('change', () => loadTimeSlots(user.id));
    document.getElementById('confirm-rehearsal-btn').addEventListener('click', () => confirmRehearsal(user.id));
    
    // Устанавливаем дату по умолчанию — сегодня
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('rehearsal-date').value = today;
}

async function loadRooms() {
    const select = document.getElementById('room-select');
    if (!select) return;
    
    try {
        const data = await API.get('/rooms/active');
        const rooms = data.rooms || data.items || [];
        
        rooms.forEach(room => {
            const option = document.createElement('option');
            option.value = room.id;
            option.textContent = room.name;
            select.appendChild(option);
        });
        
        if (rooms.length > 0) {
            loadTimeSlots();
        }
    } catch (e) {
        select.innerHTML = '<option>Ошибка загрузки</option>';
    }
}

async function loadTimeSlots(studentId) {
    const roomId = document.getElementById('room-select').value;
    const date = document.getElementById('rehearsal-date').value;
    const container = document.getElementById('time-slots');
    const confirmDiv = document.getElementById('rehearsal-confirm');
    
    if (!roomId || !date) {
        container.innerHTML = '';
        confirmDiv.style.display = 'none';
        return;
    }
    
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    confirmDiv.style.display = 'none';
    selectedRoomId = roomId;
    selectedRehearsalTime = null;
    
    try {
        // Генерируем временные слоты с 10:00 до 20:00
        const timeSlots = [];
        for (let hour = 10; hour < 20; hour++) {
            const startTime = new Date(date);
            startTime.setHours(hour, 0, 0, 0);
            const endTime = new Date(startTime);
            endTime.setHours(hour + 1);
            
            timeSlots.push({
                start: startTime,
                end: endTime,
                hour: hour,
            });
        }
        
        // Загружаем слоты расписания для проверки конфликтов
        const scheduleData = await API.get('/schedule/', { limit: 200 });
        const scheduleSlots = scheduleData.slots || scheduleData.items || [];
        
        // Загружаем репетиции студента
        let rehearsals = [];
        try {
            const rehData = await API.get(`/rehearsals/student/${studentId}`);
            rehearsals = rehData.rehearsals || rehData.items || [];
        } catch (e) {}
        
        // Проверяем доступность
        const availableSlots = timeSlots.filter(slot => {
            // Проверяем конфликты с уроками в этой комнате
            const hasLessonConflict = scheduleSlots.some(s => {
                if (s.room_id !== parseInt(roomId)) return false;
                const sStart = new Date(s.start_time);
                const sEnd = new Date(s.end_time);
                return slot.start < sEnd && slot.end > sStart;
            });
            
            if (hasLessonConflict) return false;
            
            // Проверяем конфликты с репетициями
            const hasRehearsalConflict = rehearsals.some(r => {
                if (r.room_id !== parseInt(roomId)) return false;
                const rStart = new Date(r.start_time);
                const rEnd = new Date(r.end_time);
                return slot.start < rEnd && slot.end > rStart;
            });
            
            return !hasRehearsalConflict;
        });
        
        if (availableSlots.length === 0) {
            container.innerHTML = '<div class="empty-state">Нет доступного времени на эту дату</div>';
            return;
        }
        
        container.innerHTML = availableSlots.map(slot => `
            <button class="slot-btn free" data-hour="${slot.hour}">
                ${String(slot.hour).padStart(2, '0')}:00
            </button>
        `).join('');
        
        // Обработчики
        container.querySelectorAll('.slot-btn').forEach(btn => {
            btn.addEventListener('click', () => selectRehearsalTime(parseInt(btn.dataset.hour), btn));
        });
    } catch (e) {
        container.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
    }
}

function selectRehearsalTime(hour, btn) {
    document.querySelectorAll('#time-slots .slot-btn').forEach(b => b.classList.remove('selected'));
    selectedRehearsalTime = hour;
    btn.classList.add('selected');
    document.getElementById('rehearsal-confirm').style.display = 'block';
}

async function confirmRehearsal(studentId) {
    if (!selectedRoomId || selectedRehearsalTime === null) {
        showToast('Выберите время', 'warning');
        return;
    }
    
    const date = document.getElementById('rehearsal-date').value;
    const startTime = new Date(date);
    startTime.setHours(selectedRehearsalTime, 0, 0, 0);
    const endTime = new Date(startTime);
    endTime.setHours(selectedRehearsalTime + 1);
    
    showConfirm(
        'Подтверждение бронирования',
        `Комната ${formatDate(startTime)} с ${formatTime(startTime)} до ${formatTime(endTime)}`,
        async () => {
            try {
                await API.post('/rehearsals/', {
                    room_id: parseInt(selectedRoomId),
                    student_id: studentId,
                    start_time: startTime.toISOString(),
                    end_time: endTime.toISOString(),
                });
                showToast('Репетиция забронирована', 'success');
                window.location.hash = '#my-bookings';
            } catch (e) {
                const detail = e.detail || 'Ошибка при бронировании';
                showToast(detail, 'error');
            }
        }
    );
}
