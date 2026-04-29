async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: {"Content-Type": "application/json"},
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text);
  }
  return res.json();
}

function badge(status) {
  const cls = status === 'success' ? 'success' : status === 'failed' ? 'failed' : status === 'running' ? 'running' : '';
  return `<span class="badge ${cls}">${status || '-'}</span>`;
}

async function loadTasks() {
  const tasks = await api('/api/tasks');
  const html = tasks.length ? `
    <table>
      <thead><tr><th>ID</th><th>名称</th><th>类型</th><th>配置</th><th>操作</th></tr></thead>
      <tbody>
        ${tasks.map(t => `
          <tr>
            <td>${t.id}</td>
            <td>${t.name}</td>
            <td>${t.task_type}</td>
            <td><code>${JSON.stringify(t.config)}</code></td>
            <td><button onclick="enqueueTask(${t.id})">执行</button></td>
          </tr>`).join('')}
      </tbody>
    </table>` : '<p>暂无任务。</p>';
  document.getElementById('tasks').innerHTML = html;
}

async function loadRuns() {
  const runs = await api('/api/runs');
  const html = runs.length ? `
    <table>
      <thead><tr><th>时间</th><th>任务</th><th>状态</th><th>指标</th><th>操作</th></tr></thead>
      <tbody>
        ${runs.map(r => {
          const metrics = r.result && r.result.metrics ? JSON.stringify(r.result.metrics) : '-';
          return `<tr>
            <td>${r.started_at}</td>
            <td>${r.task_name}<br><small>${r.run_id}</small></td>
            <td>${badge(r.status)}</td>
            <td><code>${metrics}</code></td>
            <td><button onclick="showRun('${r.run_id}')">详情</button></td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>` : '<p>暂无运行记录。</p>';
  document.getElementById('runs').innerHTML = html;
}

async function refresh() {
  await Promise.all([loadTasks(), loadRuns()]);
}

async function enqueueTask(id) {
  await api(`/api/tasks/${id}/enqueue`, {method: 'POST'});
  setTimeout(refresh, 600);
}

async function showRun(runId) {
  const run = await api(`/api/runs/${runId}`);
  document.getElementById('detail').textContent = JSON.stringify(run, null, 2);
}

async function createDemo() {
  const data = await api('/api/demo/stock-monitor', {method: 'POST'});
  document.getElementById('detail').textContent = JSON.stringify(data, null, 2);
  setTimeout(refresh, 1000);
}

async function createCustom() {
  const name = document.getElementById('taskName').value;
  const task_type = document.getElementById('taskType').value;
  let config = {};
  try {
    config = JSON.parse(document.getElementById('taskConfig').value);
  } catch (e) {
    alert('配置 JSON 不合法：' + e.message);
    return;
  }
  const data = await api('/api/tasks', {
    method: 'POST',
    body: JSON.stringify({name, task_type, config, enqueue_now: true}),
  });
  document.getElementById('detail').textContent = JSON.stringify(data, null, 2);
  setTimeout(refresh, 1000);
}

async function testNotify() {
  const text = document.getElementById('notifyText').value;
  const data = await api('/api/notifications/test', {
    method: 'POST',
    body: JSON.stringify({text}),
  });
  document.getElementById('detail').textContent = JSON.stringify(data, null, 2);
}

document.getElementById('refreshBtn').addEventListener('click', refresh);
document.getElementById('demoBtn').addEventListener('click', createDemo);
document.getElementById('createBtn').addEventListener('click', createCustom);
document.getElementById('notifyBtn').addEventListener('click', testNotify);

refresh();
setInterval(refresh, 5000);
