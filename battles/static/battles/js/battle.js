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
    return cookieValue;
}

// 使用技能的主函数
async function useMove(moveId, moveName) {
    // 1. 禁用所有按钮防连点
    document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = true);

    // 2. 发送 POST 请求（路径对应 urls.py：/battles/move/1/）
    const res = await fetch(`/battles/move/${moveId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        }
    });

    const data = await res.json();

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

    // 5. 战斗结束判断
    if (data.status !== 'ongoing') {
        setTimeout(() => {
            alert(data.status === 'won' ? '🎉 胜利！' : '💀 失败...');
        }, 500);
    } else {
        // 没结束，恢复按钮
        document.querySelectorAll('.move-btn').forEach(btn => btn.disabled = false);
    }
}

// 更新血条颜色和宽度
function updateHpBar(elementId, currentHp) {
    const bar = document.getElementById(elementId);
    const maxHp = parseInt(bar.getAttribute('data-max'));
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