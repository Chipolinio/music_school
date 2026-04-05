// Дашборд преподавателя

let currentWeekStart = null;

async function renderTeacherDashboard(app) {
    let user;
    try {
        user = await API.get('/auth/me');
    } catch (e) {
        window.location.hash = '#login';
        return;
    }

    // Устанавливаем начало недели — понедельник текущей недели
    if (!currentWeekStart) {
        const today = new Date();
        const dayOfWeek = today.getDay();
        const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
        currentWeekStart = new Date(today);
        currentWeekStart.setDate(today.getDate() + mondayOffset);
        currentWeekStart.setHours(0, 0, 0, 0);
    }

    app.innerHTML = `
        <div class="page">
            <div class="page-content">
                <div class="container">
                    <div class="teacher-header">
                        <h2>Моё расписание</h2>
                    </div>
                    <div class="week-navigation">
                        <button class="btn btn-outline btn-sm" id="prev-week">&larr; Пред. неделя</button>
                        <h3 id="week-label"></h3>
                        <button class="btn btn-outline btn-sm" id="next-week">След. неделя &rarr;</button>
                    </div>
                    <div id="schedule-grid" class="loading">Загрузка расписания...</div>
                </div>
            </div>
        </div>
    `;

    // Обработчики навигации
    document.getElementById('prev-week').addEventListener('click', () => {
        currentWeekStart.setDate(currentWeekStart.getDate() - 7);
        loadTeacherSchedule(user.id);
    });

    document.getElementById('next-week').addEventListener('click', () => {
        currentWeekStart.setDate(currentWeekStart.getDate() + 7);
        loadTeacherSchedule(user.id);
    });

    await loadTeacherSchedule(user.id);
}

async function loadTeacherSchedule(teacherId) {
    const grid = document.getElementById('schedule-grid');
    const label = document.getElementById('week-label');

    if (!grid) return;

    // Обновляем метку недели
    const weekEnd = new Date(currentWeekStart);
    weekEnd.setDate(weekEnd.getDate() + 4);
    label.textContent = `${formatDate(currentWeekStart)} — ${formatDate(weekEnd)}`;

    grid.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        const slotsData = await API.get(`/schedule/teacher/${teacherId}`);
        const allSlots = slotsData.slots || slotsData.items || [];

        // Фильтруем слоты текущей недели
        const weekEnd = new Date(currentWeekStart);
        weekEnd.setDate(weekEnd.getDate() + 5);

        const weekSlots = allSlots.filter(slot => {
            const slotDate = new Date(slot.start_time);
            return slotDate >= currentWeekStart && slotDate < weekEnd;
        });

        // Загружаем всех студентов и их бронирования
        const usersData = await API.get('/users/', { role: 'STUDENT', limit: 200 });
        const students = usersData.users || usersData.items || [];

        const bookingsBySlotId = {};
        const studentNames = {};
        
        for (const student of students) {
            try {
                const bData = await API.get(`/bookings/student/${student.id}`);
                const bookings = bData.bookings || bData.items || [];
                for (const b of bookings) {
                    if (b.status === 'BOOKED') {
                        bookingsBySlotId[b.slot_id] = b;
                        studentNames[b.student_id] = student.full_name;
                    }
                }
            } catch (e) {}
        }

        // Дни недели
        const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт'];
        const dayColumns = [];

        for (let i = 0; i < 5; i++) {
            const dayDate = new Date(currentWeekStart);
            dayDate.setDate(dayDate.getDate() + i);

            const daySlots = weekSlots.filter(slot => {
                const slotDate = new Date(slot.start_time);
                return slotDate.toDateString() === dayDate.toDateString();
            });

            daySlots.sort((a, b) => new Date(a.start_time) - new Date(b.start_time));

            let slotsHtml = '';
            for (const slot of daySlots) {
                const booking = bookingsBySlotId[slot.id];
                const isBooked = !!booking;
                
                if (isBooked) {
                    const sName = studentNames[booking.student_id] || '';
                    slotsHtml += `
                        <div class="day-slot occupied">
                            <div class="day-slot-time">${formatTime(slot.start_time)}</div>
                            <div class="day-slot-student">${escapeHtml(sName)}</div>
                        </div>
                    `;
                } else {
                    slotsHtml += `
                        <div class="day-slot free">
                            <div class="day-slot-time">${formatTime(slot.start_time)}</div>
                        </div>
                    `;
                }
            }

            if (!slotsHtml) {
                slotsHtml = '<div class="day-slot free">Нет уроков</div>';
            }

            dayColumns.push(`
                <div class="day-column">
                    <div class="day-header">${days[i]}, ${formatDate(dayDate)}</div>
                    ${slotsHtml}
                </div>
            `);
        }

        grid.innerHTML = `<div class="week-grid">${dayColumns.join('')}</div>`;
    } catch (e) {
        grid.innerHTML = '<div class="empty-state">Ошибка загрузки расписания</div>';
    }
}
