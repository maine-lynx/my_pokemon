// ============================================================================
// 一、CSRF Token 相关
// ============================================================================

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
    if (!cookieValue) {
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input) {
            cookieValue = input.value;
            setCookie('csrftoken', cookieValue, 1);
        }
    }
    return cookieValue;
}

// ============================================================================
// 二、通用工具函数（封装重复逻辑）
// ============================================================================

/**
 * 批量设置按钮的禁用/启用状态
 * 类比 Python: for btn in selector: btn.disabled = disabled
 */
function setButtonsDisabled(selector, disabled) {
    document.querySelectorAll(selector).forEach(btn => btn.disabled = disabled);
}

/**
 * 发送带 CSRF Token 的 POST 请求（封装 fetch 通用配置）
 * 类比 Python: requests.post(url, headers={'X-CSRFToken': ...}, json={})
 */
async function postWithCSRF(url) {
    const token = getCookie('csrftoken');
    if (!token) {
        alert('CSRF Token 未找到，请刷新页面！');
        return null;
    }

    const res = await fetch(url, {
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
        return null;
    }

    return data;
}

/**
 * 更新双方血条 + HP 数字 + 追加日志（战斗后的通用 UI 刷新）
 */
function updateBattleUI(data) {
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
}

/**
 * 更新经验条和等级（如果后端返回了相关数据）
 */
function updateExpAndLevel(data) {
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
}

/**
 * 判断战斗是否结束，结束则隐藏面板并跳转
 * @param {string[]} endStatuses - 视为结束的 status 值列表
 * @param {string}   panelId     - 需要隐藏的面板 id
 */
function handleBattleEnd(data, endStatuses, panelId) {
    if (endStatuses.includes(data.status)) {
        const panel = document.getElementById(panelId);
        if (panel) panel.style.display = 'none';
        setTimeout(() => {
            window.location.href = '/battles/fight/';
        }, 1500);
        return true;
    }
    return false;
}

// ============================================================================
// 三、面板切换
// ============================================================================

/**
 * 通用面板切换：打开 targetPanelId，关闭 otherPanelId
 */
function togglePanel(targetPanelId, otherPanelId) {
    const otherPanel = document.getElementById(otherPanelId);
    if (otherPanel) otherPanel.style.display = 'none';

    const panel = document.getElementById(targetPanelId);
    if (panel) {
        panel.style.display = (panel.style.display === 'flex') ? 'none' : 'flex';
    }
}

function showMoves() {
    togglePanel('moves-panel', 'items-panel');
}

function showItems() {
    togglePanel('items-panel', 'moves-panel');
}

// ============================================================================
// 四、使用道具
// ============================================================================

async function useItem(itemId, itemName) {
    const btnSelector = '.item-use-btn';
    setButtonsDisabled(btnSelector, true);

    try {
        const data = await postWithCSRF(`/items/use/${itemId}/`);
        if (!data) {
            setButtonsDisabled(btnSelector, false);
            return;
        }

        updateBattleUI(data);
        updateExpAndLevel(data);

        if (!handleBattleEnd(data, ['won', 'lost', 'caught'], 'items-panel')) {
            setButtonsDisabled(btnSelector, false);
        }

    } catch (error) {
        console.error('道具使用失败:', error);
        alert('道具使用失败：' + error.message);
        setButtonsDisabled(btnSelector, false);
    }
}

// ============================================================================
// 五、使用技能
// ============================================================================

async function useMove(moveId, moveName) {
    const btnSelector = '.move-btn';
    setButtonsDisabled(btnSelector, true);

    try {
        const data = await postWithCSRF(`/battles/move/${moveId}/`);
        if (!data) {
            setButtonsDisabled(btnSelector, false);
            return;
        }

        updateBattleUI(data);
        updateExpAndLevel(data);

        if (!handleBattleEnd(data, ['won', 'lost'], 'moves-panel')) {
            setButtonsDisabled(btnSelector, false);
        }

    } catch (error) {
        console.error('技能释放失败:', error);
        alert('技能释放失败：' + error.message);
        setButtonsDisabled(btnSelector, false);
    }
}

// ============================================================================
// 六、UI 更新工具函数
// ============================================================================

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
