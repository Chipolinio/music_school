const API = {
    async get(path, params = {}) {
        const url = new URL(path, window.location.origin);
        Object.entries(params).forEach(([k, v]) => {
            if (v !== undefined && v !== null) url.searchParams.set(k, v);
        });
        const res = await fetch(url.toString(), {
            credentials: 'include',
        });
        return handleResponse(res, url.pathname);
    },

    async post(path, body = null) {
        const res = await fetch(path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body ? JSON.stringify(body) : null,
            credentials: 'include',
        });
        return handleResponse(res, path);
    },

    async patch(path, body) {
        const res = await fetch(path, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            credentials: 'include',
        });
        return handleResponse(res, path);
    },

    async delete(path) {
        const res = await fetch(path, {
            method: 'DELETE',
            credentials: 'include',
        });
        return handleResponse(res, path);
    },
};

function handleResponse(res, path) {
    if (!res.ok) {
        if (res.status === 401 && path !== '/auth/me' && path !== '/auth/verify-token') {
            window.location.hash = '#login';
            throw new Error('Необходима авторизация');
        }
        if (res.status === 401) {
            // /auth/me — просто кидаем ошибку, не редиректим
            throw new Error('Не авторизован');
        }
        const errData = res.json().catch(() => ({ detail: 'Ошибка сервера' }));
        throw errData;
    }
    if (res.status === 204) return null;
    return res.json();
}
