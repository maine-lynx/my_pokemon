// ========== CSRF Token 获取 ==========

// ✅ 必须有：设置 Cookie 的辅助函数
function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + value + expires + "; path=/";
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    // ✅ 改动：如果 cookie 里没有，从 input 取，并写入 cookie
    if (!cookieValue) {
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input) {
            cookieValue = input.value;
            setCookie('csrftoken', cookieValue, 1); // 写入 cookie，有效期1天
        }
    }
    return cookieValue;
}

// ========== 控制技能面板显示/隐藏 ==========
function showMoves() {
    const panel = document.getElementById('moves-panel');
    const itemsPanel = document.getElementById('items-panel');
    if (itemsPanel) {
        itemsPanel.style.display = 'none';
    }

    if (panel) {
        panel.style.display = (panel.style.display === 'flex') ? 'none' : 'flex';
    }
}
// ========== 控制道具面板显示/隐藏 ==========
function showItems() {
    const panel = document.getElementById('items-panel');
    const movesPanel = document.getElementById('moves-panel');
    if (movesPanel) {
        movesPanel.style.display = 'none';
    }

    if (panel) {
        panel.style.display = (panel.style.display === 'flex') ? 'none' : 'flex';
    }
}

//===============使用道具================
async function useItem(itemId, itemName) {
    document.querySelectorAll('.item-btn').forEach(btn => btn.disabled = true);
    const token = getCookie('csrftoken');
    if (!token) {
        alert('CSRF Token 未找到，请刷新页面！');
        document.querySelectorAll('.item-use-btn').forEach(btn => btn.disabled = false);
        return;
    }

    try {
        const res = await fetch(`/items/use/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',
            body: JSON.stringify({})
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || `服务器返回 ${res.status}`);
        }

        const data = await res.json();

        if (data.error) {
            alert(data.error);
            document.querySelectorAll('.item-use-btn').forEach(btn => btn.disabled = false);
            return;
        }

        updateHpBar('player-hp', data.player_hp);
        updateHpBar('wild-hp', data.wild_hp);

        const logBox = document.getElementById('battle-log');
        if (logBox) {
            data.log.forEach(msg => {
                const p = document.createElement('p');
                p.textContent = msg;
                logBox.appendChild(p);
            });
            logBox.scrollTop = logBox.scrollHeight;
        }

        if (data.status === 'won' || data.status === 'lost' || data.status === 'caught') {
            const itemsPanel = document.getElementById('items-panel');
            if (itemsPanel) itemsPanel.style.display = 'none';
            setTimeout(() => {
                window.location.href = '/battles/fight/';
            }, 1500);
        } else {
            document.querySelectorAll('.item-use-btn').forEach(btn => btn.disabled = false);
        }

    } catch (error) {
        console.error('道具使用失败:', error);
        alert('道具使用失败：' + error.message);
        document.querySelectorAll('.item-use-btn').forEach(btn => btn.disabled = false);
    }
}

// ... existing code ...
// ========== 使用技能 ==========
async function useMove(moveId, moveName) {
    document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = true);

    const token = getCookie('csrftoken');
    if (!token) {
        alert('CSRF Token 未找到，请刷新页面！');
        document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = false);
        return;
    }

    try {
        const res = await fetch(`/battles/move/${moveId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin', // ✅ 必须有：确保携带同源 cookie
            body: JSON.stringify({})
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || `服务器返回 ${res.status}`);
        }

        const data = await res.json();

        if (data.error) {
            alert(data.error);
            document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = false);
            return;
        }

        // ---- 更新血条 ----
        updateHpBar('player-hp', data.player_hp);
        updateHpBar('wild-hp', data.wild_hp);

        // ---- 追加日志 ----
        const logBox = document.getElementById('battle-log');
        if (logBox) {
            data.log.forEach(msg => {
                const p = document.createElement('p');
                p.textContent = msg;
                logBox.appendChild(p);
            });
            logBox.scrollTop = logBox.scrollHeight;
        }

        // ---- ✅ 更新经验条和等级 ----
        if (data.player_exp !== undefined && data.exp_to_next !== undefined) {
            const expFill = document.getElementById('exp-fill');
            const expText = document.getElementById('exp-text');
            const pct = Math.min(100, (data.player_exp / data.exp_to_next * 100).toFixed(1));
            if (expFill) expFill.style.width = pct + '%';
            if (expText) expText.textContent = `EXP: ${data.player_exp} / ${data.exp_to_next}`;
        }
        if (data.player_level !== undefined) {
            const lvlText = document.getElementById('player-level');
            if (lvlText) lvlText.textContent = `Lv.${data.player_level}`;
        }

        // ---- 战斗结束判断 ----
        if (data.status === 'won' || data.status === 'lost') {
            const panel = document.getElementById('moves-panel');
            if (panel) panel.style.display = 'none';

            setTimeout(() => {
                window.location.href = '/battles/fight/';
            }, 1500);
        } else {
            document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = false);
        }

    } catch (error) {
        console.error('请求失败:', error);
        alert('技能释放失败：' + error.message);
        document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = false);
    }
}

// ========== 更新血条 ==========
function updateHpBar(elementId, currentHp) {
    const bar = document.getElementById(elementId);
    if (!bar) return;
    const maxHp = parseInt(bar.getAttribute('data-max'));
    if (isNaN(maxHp) || maxHp <= 0) return;
    const percent = Math.max(0, (currentHp / maxHp) * 100);
    bar.style.width = percent + '%';

    if (percent > 50) {
        bar.style.background = 'linear-gradient(90deg, #4caf50, #8bc34a)';
    } else if (percent > 20) {
        bar.style.background = 'linear-gradient(90deg, #ff9800, #ffc107)';
    } else {
        bar.style.background = 'linear-gradient(90deg, #f44336, #ef5350)';
    }
}