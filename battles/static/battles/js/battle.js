// 获取 Django CSRF Token 的辅助函数
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
    // ⚠️ 改动点1：如果 Cookie 里没有，尝试从 {% csrf_token %} 生成的 input 里取（双保险）
    if (!cookieValue) {
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input) cookieValue = input.value;
    }
    return cookieValue;
}

// 使用技能的主函数
async function useMove(moveId, moveName) {
    // 1. 禁用所有按钮防连点
    document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = true);

    // ⚠️ 改动点2：先检查 token 是否存在
    const token = getCookie('csrftoken');
    if (!token) {
        alert('CSRF Token 未找到，请刷新页面！');
        document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = false);
        return;
    }

    try { // ⚠️ 改动点3：用 try-catch 包裹，防止请求失败导致按钮卡死
        // 2. 发送 POST 请求
        const res = await fetch(`/battles/move/${moveId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}) // ⚠️ 改动点4：显式传一个空 body，有些 Django 版本需要
        });

        // ⚠️ 改动点5：检查 HTTP 状态码，如果不是 200 就抛错
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || `服务器返回 ${res.status}`);
        }

        const data = await res.json();

        // ⚠️ 改动点6：如果后端返回了 error 字段（比如战斗已结束），要处理
        if (data.error) {
            alert(data.error);
            document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = false);
            return;
        }

        // 3. 更新血条
        updateHpBar('player-hp', data.player_hp);
        updateHpBar('wild-hp', data.wild_hp);

        // 4. 追加日志
        const logBox = document.getElementById('battle-log');
        data.log.forEach(msg => {
            const p = document.createElement('p');
            p.textContent = msg;
            logBox.appendChild(p);
        });
        logBox.scrollTop = logBox.scrollHeight;

        // 5. 战斗结束判断 → 自动进入下一场
        if (data.status === 'won' || data.status === 'lost') {
            // 800ms 后跳回 battle_view，后端会自动检测 status≠ongoing 并开始新战斗
            setTimeout(() => {
                window.location.href = '/battles/fight/';
            }, 800);
        } else {
            // 没结束，恢复按钮
            document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = false);
        }

    } catch (error) {
        // ⚠️ 改动点7：捕获所有错误，弹窗提示，并恢复按钮
        console.error('请求失败:', error);
        alert('技能释放失败：' + error.message);
        document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = false);
    }
}

// 更新血条颜色和宽度
function updateHpBar(elementId, currentHp) {
    const bar = document.getElementById(elementId);
    const maxHp = parseInt(bar.getAttribute('data-max'));
    // ⚠️ 改动点8：加个防御，防止 maxHp 是 NaN
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