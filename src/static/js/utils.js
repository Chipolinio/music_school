// Форматирование даты в DD.MM.YYYY
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
    });
}

// Форматирование времени в HH:MM
function formatTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
    });
}

// Форматирование даты и времени
function formatDateTime(dateStr) {
    return `${formatDate(dateStr)}, ${formatTime(dateStr)}`;
}

// Форматирование для input[type=datetime-local]
function toLocalISOString(date) {
    const offset = date.getTimezoneOffset();
    const localDate = new Date(date.getTime() - offset * 60 * 1000);
    return localDate.toISOString().slice(0, 16);
}

// Маска телефона: +7 (___) ___-__-__
function applyPhoneMask(value) {
    // Убираем все кроме цифр
    const digits = value.replace(/\D/g, '');
    
    // Если начинается с 8, заменяем на 7
    let cleaned = digits;
    if (cleaned.startsWith('8') && cleaned.length > 1) {
        cleaned = '7' + cleaned.slice(1);
    }
    if (!cleaned.startsWith('7') && cleaned.length > 0) {
        cleaned = '7' + cleaned;
    }
    
    // Ограничиваем 11 символами (+7 и 10 цифр)
    cleaned = cleaned.slice(0, 11);
    
    // Формируем маску
    let formatted = '';
    if (cleaned.length > 0) {
        formatted = '+' + cleaned[0];
    }
    if (cleaned.length > 1) {
        formatted += ' (' + cleaned.slice(1, 4);
    }
    if (cleaned.length > 4) {
        formatted += ') ' + cleaned.slice(4, 7);
    }
    if (cleaned.length > 7) {
        formatted += '-' + cleaned.slice(7, 9);
    }
    if (cleaned.length > 9) {
        formatted += '-' + cleaned.slice(9, 11);
    }
    
    return formatted;
}

// Конвертация замаскированного телефона в E164
function phoneToE164(masked) {
    const digits = masked.replace(/\D/g, '');
    if (digits.length === 11 && digits.startsWith('7')) {
        return '+' + digits;
    }
    return masked;
}

// Валидация email
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Валидация пароля (минимум 8 символов)
function isValidPassword(password) {
    return password.length >= 8;
}

// Склонение слов
function pluralize(n, one, few, many) {
    const mod10 = n % 10;
    const mod100 = n % 100;
    
    if (mod100 >= 11 && mod100 <= 14) return many;
    if (mod10 === 1) return one;
    if (mod10 >= 2 && mod10 <= 4) return few;
    return many;
}

// Получить роль в читаемом виде
function getRoleName(role) {
    const roles = {
        'STUDENT': 'Ученик',
        'TEACHER': 'Преподаватель',
        'ADMIN': 'Администратор',
    };
    return roles[role] || role;
}

// Получить статус брони
function getBookingStatusName(status) {
    const statuses = {
        'BOOKED': 'Забронировано',
        'FREE': 'Свободно',
        'TAKEN': 'Занято',
    };
    return statuses[status] || status;
}
