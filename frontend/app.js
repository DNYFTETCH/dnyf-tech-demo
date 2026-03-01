const API_BASE = "http://localhost:8000/api";
let currentTaskId = null;
let ws = null;

// DOM Elements
const form = document.getElementById('taskForm');
const goalInput = document.getElementById('goalInput');
const submitBtn = document.getElementById('submitBtn');
const logStream = document.getElementById('logStream');
const serverStatus = document.getElementById('serverStatus');
const presetSelect = document.getElementById('presetTask');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await checkHealth();
  setupEventListeners();
});

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    serverStatus.textContent = `🟢 ${data.mode.toUpperCase()} MODE`;
    serverStatus.style.color = data.status === 'ok' ? 'var(--success)' : 'var(--error)';
  } catch {
    serverStatus.textContent = '🔴 Offline';
    serverStatus.style.color = 'var(--error)';
  }
}

function setupEventListeners() {
  form.addEventListener('submit', handleSubmit);
  presetSelect.addEventListener('change', (e) => {
    if (e.target.value) goalInput.value = e.target.value;
  });
  
  // Tab switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(tab.dataset.tab).classList.add('active');
    });
  });
  
  document.getElementById('clearLogs').addEventListener('click', () => {
    logStream.innerHTML = '';
  });
    document.getElementById('healthLink').addEventListener('click', (e) => {
    e.preventDefault();
    checkHealth();
  });
}

async function handleSubmit(e) {
  e.preventDefault();
  const goal = goalInput.value.trim();
  if (!goal) return;
  
  submitBtn.disabled = true;
  submitBtn.textContent = '🚀 Launching...';
  logStream.innerHTML = '<div class="log-entry">⏳ Connecting to DNYF TECH agent...</div>';
  
  try {
    const res = await fetch(`${API_BASE}/task`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal, mock_mode: document.getElementById('mockMode').checked })
    });
    
    const data = await res.json();
    currentTaskId = data.task_id;
    
    // Start log streaming
    connectWebSocket(data.task_id);
    
    // Poll for completion
    pollTaskStatus(data.task_id);
    
  } catch (err) {
    addLog(`❌ Error: ${err.message}`, 'error');
    submitBtn.disabled = false;
    submitBtn.textContent = '🚀 Launch Agent';
  }
}

function connectWebSocket(taskId) {
  const wsUrl = `ws://localhost:8000/ws/logs/${taskId}`;
  ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    const log = JSON.parse(event.data);
    if (log.msg) addLog(log.msg, log.level);
  };
  
  ws.onclose = () => {
    console.log('WebSocket closed');
  };}

async function pollTaskStatus(taskId, interval = 1000) {
  const poll = async () => {
    try {
      const res = await fetch(`${API_BASE}/task/${taskId}`);
      const task = await res.json();
      
      if (task.status === 'completed') {
        showResult(task.result);
        submitBtn.disabled = false;
        submitBtn.textContent = '🚀 Launch Agent';
        return;
      }
      
      if (task.status === 'failed') {
        addLog(`❌ Task failed: ${task.error}`, 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = '🚀 Launch Agent';
        return;
      }
      
      setTimeout(poll, interval);
    } catch (err) {
      console.error('Poll error:', err);
      setTimeout(poll, interval);
    }
  };
  poll();
}

function addLog(message, level = 'info') {
  const entry = document.createElement('div');
  entry.className = `log-entry ${level}`;
  const ts = new Date().toLocaleTimeString();
  entry.innerHTML = `<div class="ts">[${ts}]</div><div>${escapeHtml(message)}</div>`;
  logStream.appendChild(entry);
  logStream.scrollTop = logStream.scrollHeight;
}

function showResult(result) {
  const resultContent = document.getElementById('resultContent');
  resultContent.innerHTML = `
    <div class="result-summary">
      <h3>✅ Task Completed</h3>
      <p><strong>Summary:</strong> ${result.summary}</p>
      <p><strong>Files Modified:</strong></p>
      <ul>${result.files_modified.map(f => `<li><code>${f}</code></li>`).join('')}</ul>
      <p><strong>Next Suggestions:</strong></p>
      <ul>${result.next_suggestions.map(s => `<li>${s}</li>`).join('')}</ul>    </div>
  `;
  // Switch to result tab
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.querySelector('[data-tab="result"]').classList.add('active');
  document.getElementById('result').classList.add('active');
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
