const API = '/api/v1';
let token = localStorage.getItem('access_token');
let currentUser = null;
let selectedChildId = null;
let selectedExercise = null;
let selectedAnswer = '';
let ws = null;

// ── Sound Effects ───────────────────────────────────────────────────────────

function playSound(type) {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();

  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);

  switch (type) {
    case 'click':
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(400, audioContext.currentTime + 0.1);
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.1);
      break;
    case 'success':
      oscillator.frequency.setValueAtTime(523, audioContext.currentTime); // C5
      oscillator.frequency.setValueAtTime(659, audioContext.currentTime + 0.1); // E5
      oscillator.frequency.setValueAtTime(784, audioContext.currentTime + 0.2); // G5
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
      break;
    case 'error':
      oscillator.frequency.setValueAtTime(200, audioContext.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(150, audioContext.currentTime + 0.2);
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
      break;
  }
}

// ── Enhanced Interactions ────────────────────────────────────────────────────

function selectChild(childId) {
  selectedChildId = childId;
  document.querySelectorAll('.child-card').forEach(card => card.classList.remove('selected'));
  document.getElementById(`child-card-${childId}`).classList.add('selected');
  playSound('click');
  // Load child details or exercises
  loadChildExercises(childId);
}

function addClickSounds() {
  document.querySelectorAll('button, .action-card, .activity-item').forEach(el => {
    el.addEventListener('click', () => playSound('click'));
  });
}

function addHoverEffects() {
  document.querySelectorAll('.activity-item, .action-card').forEach(el => {
    el.addEventListener('mouseenter', () => {
      el.style.transform = 'scale(1.02)';
    });
    el.addEventListener('mouseleave', () => {
      el.style.transform = 'scale(1)';
    });
  });
}

// ── Particle Effects ─────────────────────────────────────────────────────────

function createParticles() {
  const particlesContainer = document.getElementById('particles');
  for (let i = 0; i < 20; i++) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.left = Math.random() * 100 + '%';
    particle.style.animationDelay = Math.random() * 6 + 's';
    particle.style.animationDuration = (Math.random() * 4 + 4) + 's';
    particlesContainer.appendChild(particle);
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

async function api(path, method = 'GET', body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API + path, { method, headers, body: body ? JSON.stringify(body) : null });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail?.message || JSON.stringify(data.detail) || 'Request failed');
  return data;
}

function showToast(msg, type = '') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast ${type}`;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 4000);
  if (type === 'success') playSound('success');
  if (type === 'error') playSound('error');
}

function showView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(name + '-view').classList.add('active');
  document.querySelector(`[data-view="${name}"]`)?.classList.add('active');
  if (name === 'dashboard') loadDashboard();
  if (name === 'children') loadChildren();
  if (name === 'curriculum') loadUnits();
  if (name === 'leaderboard') loadLeaderboard();
  if (name === 'notifications') loadNotifications();
  if (name === 'admin') loadAdmin();
}

function timeAgo(dateStr) {
  const d = new Date(dateStr);
  const diff = (Date.now() - d) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
  return d.toLocaleDateString();
}

// ── Auth ─────────────────────────────────────────────────────────────────────

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab + '-panel').classList.add('active');
  });
});

document.getElementById('login-btn').addEventListener('click', async () => {
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  try {
    const data = await api('/auth/login', 'POST', { email, password });
    token = data.access_token;
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', data.refresh_token);
    await afterLogin();
  } catch (e) {
    document.getElementById('auth-error').textContent = e.message;
    document.getElementById('auth-error').classList.remove('hidden');
  }
});

document.getElementById('register-btn').addEventListener('click', async () => {
  const full_name = document.getElementById('reg-name').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  try {
    const data = await api('/auth/register', 'POST', { full_name, email, password });
    token = data.access_token;
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', data.refresh_token);
    await afterLogin();
  } catch (e) {
    document.getElementById('auth-error').textContent = e.message;
    document.getElementById('auth-error').classList.remove('hidden');
  }
});

async function afterLogin() {
  const payload = JSON.parse(atob(token.split('.')[1]));
  currentUser = { id: parseInt(payload.sub), role: payload.role };
  document.getElementById('auth-error').classList.add('hidden');
  document.getElementById('auth-screen').classList.remove('active');
  document.getElementById('main-screen').classList.add('active');

  try {
    const parent = await api(`/parents/${currentUser.id}`);
    document.getElementById('user-name').textContent = parent.full_name;
    document.getElementById('dash-name').textContent = parent.full_name.split(' ')[0];
  } catch {}

  // Показываем Admin кнопку если роль admin
  const adminBtn = document.getElementById('admin-nav-btn');
  if (adminBtn) {
    adminBtn.style.display = currentUser.role === 'admin' ? '' : 'none';
  }

  connectWS();
  addClickSounds();
  addHoverEffects();
  createParticles();
  showView('dashboard');
}

// Auto-login
if (token) { afterLogin(); }

// ── WebSocket ─────────────────────────────────────────────────────────────────

function connectWS() {
  if (!token || ws) return;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/notifications?token=${token}`);
  ws.onopen = () => console.log('WebSocket connected');
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'lesson_complete') {
      showToast(`🎉 ${msg.child} completed "${msg.lesson}"! +${msg.xp_earned} XP`, 'success');
      updateNotifBadge();
      // Refresh dashboard if visible
      if (document.getElementById('dashboard-view').classList.contains('active')) loadDashboard();
    } else if (msg.type === 'badge_earned') {
      showToast(`🏆 ${msg.child} earned "${msg.badge}" badge!`, 'success');
    }
  };
  ws.onclose = () => { ws = null; setTimeout(connectWS, 5000); };
  ws.onerror = (e) => console.error('WebSocket error:', e);
}

async function updateNotifBadge() {
  try {
    const data = await api('/notifications?unread_only=true&page_size=1');
    const badge = document.getElementById('notif-badge');
    if (data.total > 0) {
      badge.textContent = data.total > 99 ? '99+' : data.total;
      badge.classList.remove('hidden');
    } else badge.classList.add('hidden');
  } catch (e) { console.error('Failed to update notification badge:', e); }
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

async function loadDashboard() {
  try {
    const children = await api('/children?page_size=100');
    const cards = document.getElementById('dashboard-cards');
    const total = children.total;
    const totalXP = children.items.reduce((s, c) => s + c.xp, 0);
    const maxStreak = children.items.reduce((m, c) => Math.max(m, c.streak), 0);
    cards.innerHTML = `
      <div class="stat-card"><div class="stat-label">Children</div><div class="stat-value">${total}</div></div>
      <div class="stat-card"><div class="stat-label">Total XP</div><div class="stat-value">${totalXP}</div></div>
      <div class="stat-card"><div class="stat-label">Best Streak</div><div class="stat-value">${maxStreak}🔥</div></div>
    `;
    updateNotifBadge();
  } catch (e) { console.error(e); }
}

// ── Children ──────────────────────────────────────────────────────────────────

async function loadChildren() {
  document.getElementById('child-detail').classList.add('hidden');
  const list = document.getElementById('children-list');
  list.style.display = '';
  document.getElementById('add-child-btn').style.display = '';
  try {
    const data = await api('/children?page_size=50');
    list.innerHTML = data.items.length === 0
      ? '<p style="color:var(--text-muted)">No children yet. Add your first child!</p>'
      : data.items.map(c => childCard(c)).join('');
    list.querySelectorAll('.child-card').forEach((card, i) => {
      card.style.animationDelay = `${i * 0.1}s`;
      card.classList.add('fade-in');
    });
  } catch (e) { list.innerHTML = `<p class="error-msg">${e.message}</p>`; }
}

function childCard(c) {
  const initials = c.display_name.substring(0, 2).toUpperCase();
  const xpInLevel = c.xp % 200;
  const pct = Math.min(100, (xpInLevel / 200) * 100);
  return `<div class="child-card" id="child-card-${c.id}">
    <div class="child-card-header">
      <div class="child-avatar">${c.avatar ? `<img src="${c.avatar}" style="width:100%;height:100%;border-radius:50%;object-fit:cover" onerror="this.style.display='none'">` : initials}</div>
      <div><div class="child-name">${c.name}</div><div class="child-age">Age ${c.age} · Level ${c.level}</div></div>
    </div>
    <div style="font-size:.8rem;color:var(--text-muted);margin-bottom:.3rem">XP: ${c.xp}</div>
    <div class="child-xp-bar" style="--xp-percent: ${pct}%">
      <div class="xp-fill"></div>
    </div>
    <div class="child-meta">
      <span>🔥 <strong>${c.streak}</strong> day streak</span>
      <span>📊 <strong>${c.progress_percentage}%</strong> progress</span>
    </div>
  </div>`;
}

document.getElementById('add-child-btn').addEventListener('click', () => {
  document.getElementById('child-modal').classList.remove('hidden');
});
document.getElementById('cancel-child').addEventListener('click', () => {
  document.getElementById('child-modal').classList.add('hidden');
});
document.getElementById('save-child').addEventListener('click', async () => {
  const name = document.getElementById('child-name').value.trim();
  const display_name = document.getElementById('child-display').value.trim();
  const age = parseInt(document.getElementById('child-age').value);
  const avatar = document.getElementById('child-avatar').value.trim() || null;
  try {
    await api('/children', 'POST', { name, display_name, age, avatar });
    document.getElementById('child-modal').classList.add('hidden');
    ['child-name','child-display','child-age','child-avatar'].forEach(id => document.getElementById(id).value = '');
    showToast('Child added!', 'success');
    loadChildren();
  } catch (e) {
    document.getElementById('child-error').textContent = e.message;
    document.getElementById('child-error').classList.remove('hidden');
  }
});

async function openChildDetail(childId) {
  selectedChildId = childId;
  document.getElementById('children-list').style.display = 'none';
  document.getElementById('add-child-btn').style.display = 'none';
  const detail = document.getElementById('child-detail');
  detail.classList.remove('hidden');
  try {
    const child = await api(`/children/${childId}`);
    document.getElementById('detail-child-name').textContent = child.name;
    document.getElementById('child-stats').innerHTML = `
      <div class="stat-pill">XP: <strong>${child.xp}</strong></div>
      <div class="stat-pill">Level: <strong>${child.level}</strong></div>
      <div class="stat-pill">Streak: <strong>${child.streak}🔥</strong></div>
      <div class="stat-pill">Progress: <strong>${child.progress_percentage}%</strong></div>
    `;
    const badges = await api(`/children/${childId}/badges`);
    const BADGE_EMOJI = { first_lesson:'🎓', streak_7:'🔥', streak_30:'🌟', xp_100:'💯', xp_500:'🏆', unit_complete:'📚', perfect_lesson:'⭐' };
    document.getElementById('child-badges').innerHTML = badges.length
      ? badges.map(b => `<div class="badge-chip">${BADGE_EMOJI[b.badge_type] || '🏅'} ${b.description}</div>`).join('')
      : '<p style="color:var(--text-muted);font-size:.9rem">No badges yet. Keep learning!</p>';
    const progress = await api(`/children/${childId}/progress?page_size=10`);
    document.getElementById('child-progress-list').innerHTML = progress.items.length
      ? progress.items.map(p => {
          const pct = p.score * 100;
          return `<div class="progress-item">
            <div class="progress-item-header">
              <span class="progress-item-title">Lesson #${p.lesson_id}</span>
              <span class="progress-item-score">${p.is_completed ? '✓ Completed' : 'In progress'} · +${p.xp_earned} XP</span>
            </div>
            <div class="progress-bar" style="--progress-percent: ${pct}%"></div>
          </div>`;
        }).join('')
      : '<p style="color:var(--text-muted);font-size:.9rem">No lessons completed yet.</p>';
    loadLessonSelectorForChild();
  } catch (e) { showToast(e.message, 'error'); }
}

async function loadLessonSelectorForChild() {
  const container = document.getElementById('lesson-selector');
  try {
    const lessons = await api('/lessons?is_published=true&page_size=20');
    container.innerHTML = lessons.items.length
      ? lessons.items.map(l => `<button class="lesson-select-btn" data-lesson-id="${l.id}" data-lesson-xp="${l.xp_reward}">${l.title}</button>`).join('')
      : '<p style="color:var(--text-muted);font-size:.9rem">No published lessons yet.</p>';
    container.querySelectorAll('.lesson-select-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        try {
          const result = await api(`/lessons/${btn.dataset.lessonId}/complete`, 'POST', { child_id: selectedChildId });
          showToast(`🎉 +${result.xp_earned} XP! ${result.new_badges.length ? 'New badge: ' + result.new_badges.join(', ') : ''}`, 'success');
          openChildDetail(selectedChildId);
        } catch (e) { showToast(e.message, 'error'); }
      });
    });
  } catch {}
}

document.getElementById('back-to-children').addEventListener('click', loadChildren);

// ── Curriculum ────────────────────────────────────────────────────────────────

async function loadUnits() {
  document.getElementById('units-list').classList.remove('hidden');
  document.getElementById('lessons-panel').classList.add('hidden');
  document.getElementById('exercises-panel').classList.add('hidden');
  try {
    const data = await api('/units?page_size=50');
    const list = document.getElementById('units-list');
    list.innerHTML = data.items.length === 0
      ? '<p style="color:var(--text-muted)">No units available yet.</p>'
      : data.items.map(u => `<div class="unit-card fade-in" data-unit-id="${u.id}" data-unit-title="${u.title}">
          <h4>${u.title}</h4>
          <p>${u.description || ''}</p>
          <span class="unit-badge">${u.difficulty}</span>
          ${u.is_published ? '<span class="unit-badge" style="background:#d1fae5;color:#065f46;margin-left:.3rem">Published</span>' : ''}
        </div>`).join('');
    list.querySelectorAll('.unit-card').forEach(card => {
      card.addEventListener('click', () => loadLessons(card.dataset.unitId, card.dataset.unitTitle));
    });
  } catch (e) { showToast(e.message, 'error'); }
}

async function loadLessons(unitId, unitTitle) {
  document.getElementById('units-list').classList.add('hidden');
  const panel = document.getElementById('lessons-panel');
  panel.classList.remove('hidden');
  document.getElementById('unit-title').textContent = unitTitle;
  try {
    const data = await api(`/lessons?unit_id=${unitId}&page_size=50`);
    const list = document.getElementById('lessons-list');
    list.innerHTML = data.items.length === 0
      ? '<p style="color:var(--text-muted)">No lessons in this unit.</p>'
      : data.items.map((l, i) => `<div class="lesson-card fade-in" data-lesson-id="${l.id}" data-lesson-title="${l.title}" style="animation-delay: ${i * 0.1}s">
          <div class="lesson-info"><h4>${l.title}</h4><p>${l.description || ''} · ${l.difficulty}</p></div>
          <span class="lesson-xp">+${l.xp_reward} XP</span>
        </div>`).join('');
    list.querySelectorAll('.lesson-card').forEach(card => {
      card.addEventListener('click', () => loadExercises(card.dataset.lessonId, card.dataset.lessonTitle));
    });
  } catch (e) { showToast(e.message, 'error'); }
}

async function loadExercises(lessonId, lessonTitle) {
  document.getElementById('lessons-panel').classList.add('hidden');
  document.getElementById('exercises-panel').classList.remove('hidden');
  document.getElementById('lesson-title').textContent = lessonTitle;
  document.getElementById('exercise-runner').classList.add('hidden');
  document.getElementById('ex-feedback').classList.add('hidden');
  try {
    const data = await api(`/lessons/${lessonId}/exercises`);
    const list = document.getElementById('exercises-list');
    list.innerHTML = data.length === 0
      ? '<p style="color:var(--text-muted)">No exercises in this lesson.</p>'
      : data.map(e => `<div class="exercise-item" data-exercise-id="${e.id}">
          <div>
            <span class="ex-type-tag">${e.exercise_type}</span>
            <strong style="margin-left:.5rem">${e.question}</strong>
          </div>
          <span style="color:var(--text-muted);font-size:.85rem">Try it →</span>
        </div>`).join('');
    list.querySelectorAll('.exercise-item').forEach(item => {
      item.addEventListener('click', async () => {
        const ex = data.find(e => e.id == item.dataset.exerciseId);
        openExercise(ex);
      });
    });
    await populateChildSelect();
  } catch (e) { showToast(e.message, 'error'); }
}

function openExercise(ex) {
  selectedExercise = ex;
  selectedAnswer = '';
  document.getElementById('exercise-runner').classList.remove('hidden');
  document.getElementById('ex-type').textContent = ex.exercise_type;
  document.getElementById('ex-question').textContent = ex.question;
  document.getElementById('ex-instructions').textContent = ex.instructions || '';
  document.getElementById('ex-answer').value = '';
  document.getElementById('ex-feedback').classList.add('hidden');
  const optContainer = document.getElementById('ex-options');
  if (ex.options && ex.options.length) {
    optContainer.style.display = '';
    optContainer.innerHTML = ex.options.map(o => `<button class="ex-option-btn" data-val="${o}">${o}</button>`).join('');
    optContainer.querySelectorAll('.ex-option-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        optContainer.querySelectorAll('.ex-option-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedAnswer = btn.dataset.val;
        document.getElementById('ex-answer').value = selectedAnswer;
      });
    });
  } else { optContainer.style.display = 'none'; }
}

async function populateChildSelect() {
  const sel = document.getElementById('ex-child-select');
  try {
    const data = await api('/children?page_size=50');
    sel.innerHTML = '<option value="">Select child...</option>' + data.items.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    if (selectedChildId) sel.value = selectedChildId;
  } catch {}
}

document.getElementById('submit-exercise').addEventListener('click', async () => {
  if (!selectedExercise) return;
  const child_id = parseInt(document.getElementById('ex-child-select').value);
  const answer = document.getElementById('ex-answer').value.trim();
  if (!child_id) { showToast('Please select a child', 'error'); return; }
  if (!answer) { showToast('Please enter an answer', 'error'); return; }
  try {
    const result = await api(`/exercises/${selectedExercise.id}/submit`, 'POST', { child_id, answer });
    const fb = document.getElementById('ex-feedback');
    fb.textContent = result.message + (result.is_correct ? '' : ` Correct answer: ${result.correct_answer}`);
    fb.className = 'ex-feedback ' + (result.is_correct ? 'correct' : 'incorrect');
    fb.classList.remove('hidden');
  } catch (e) { showToast(e.message, 'error'); }
});

document.getElementById('back-to-units').addEventListener('click', loadUnits);
document.getElementById('back-to-lessons').addEventListener('click', () => {
  document.getElementById('exercises-panel').classList.add('hidden');
  document.getElementById('lessons-panel').classList.remove('hidden');
});

// ── Leaderboard ───────────────────────────────────────────────────────────────

async function loadLeaderboard() {
  const [ageMin, ageMax] = document.getElementById('lb-age-group').value.split(',');
  try {
    const data = await api(`/leaderboard?age_min=${ageMin}&age_max=${ageMax}&limit=20`);
    const container = document.getElementById('leaderboard-list');
    if (!data.length) { container.innerHTML = '<p style="padding:1.5rem;color:var(--text-muted)">No data yet.</p>'; return; }
    container.innerHTML = `
      <div class="lb-row header"><div>Rank</div><div>Name</div><div>XP</div><div>Level</div><div>Streak</div></div>
      ${data.map(e => `<div class="lb-row">
        <div class="lb-rank ${e.rank===1?'gold':e.rank===2?'silver':e.rank===3?'bronze':''}">${e.rank===1?'🥇':e.rank===2?'🥈':e.rank===3?'🥉':e.rank}</div>
        <div>${e.display_name}</div>
        <div class="lb-xp">${e.xp}</div>
        <div>Lvl ${e.level}</div>
        <div>🔥 ${e.streak}</div>
      </div>`).join('')}
    `;
  } catch (e) { showToast(e.message, 'error'); }
}

document.getElementById('lb-age-group').addEventListener('change', loadLeaderboard);
document.getElementById('refresh-lb').addEventListener('click', loadLeaderboard);

// ── Notifications ─────────────────────────────────────────────────────────────

async function loadNotifications() {
  const list = document.getElementById('notifications-list');
  try {
    const data = await api('/notifications?page_size=50');
    list.innerHTML = data.items.length === 0
      ? '<p style="color:var(--text-muted)">No notifications yet.</p>'
      : data.items.map(n => `<div class="notif-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
          <h4>${n.title}</h4><p>${n.message}</p>
          <div class="notif-time">${timeAgo(n.created_at)}</div>
        </div>`).join('');
    updateNotifBadge();
  } catch (e) { list.innerHTML = `<p class="error-msg">${e.message}</p>`; }
}

document.getElementById('mark-all-read').addEventListener('click', async () => {
  const ids = [...document.querySelectorAll('.notif-item.unread')].map(el => parseInt(el.dataset.id));
  if (!ids.length) return;
  try {
    await api('/notifications', 'PATCH', { notification_ids: ids });
    loadNotifications();
  } catch (e) { showToast(e.message, 'error'); }
});

// ── Child Exercises ───────────────────────────────────────────────────────────

async function loadChildExercises(childId) {
  try {
    const child = await api(`/children/${childId}`);
    const exercises = await api(`/exercises?child_id=${childId}&page_size=20`);
    const container = document.getElementById('child-exercises');
    container.innerHTML = `
      <h3>Exercises for ${child.name}</h3>
      <div class="exercise-list">
        ${exercises.items.length === 0 ? '<p>No exercises yet.</p>' : exercises.items.map(ex => `
          <div class="exercise-item" onclick="startExercise(${ex.id})">
            <div class="exercise-icon">${getExerciseIcon(ex.exercise_type)}</div>
            <div class="exercise-info">
              <h4>${ex.question}</h4>
              <p>${ex.exercise_type} • ${ex.difficulty}</p>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    document.getElementById('child-detail').classList.remove('hidden');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

function getExerciseIcon(type) {
  const icons = {
    phonics: '🔤',
    handwriting: '✍️',
    sight_words: '👁️',
    vocabulary: '📚'
  };
  return icons[type] || '❓';
}

async function startExercise(exerciseId) {
  try {
    const exercise = await api(`/exercises/${exerciseId}`);
    selectedExercise = exercise;
    selectedAnswer = '';
    document.getElementById('exercise-runner').classList.remove('hidden');
    document.getElementById('ex-type').textContent = exercise.exercise_type;
    document.getElementById('ex-question').textContent = exercise.question;
    document.getElementById('ex-instructions').textContent = exercise.instructions || '';
    document.getElementById('ex-answer').value = '';
    document.getElementById('ex-feedback').classList.add('hidden');
    const optContainer = document.getElementById('ex-options');
    if (exercise.options && exercise.options.length) {
      optContainer.style.display = '';
      optContainer.innerHTML = exercise.options.map(o => `<button class="ex-option-btn" data-val="${o}">${o}</button>`).join('');
      optContainer.querySelectorAll('.ex-option-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          optContainer.querySelectorAll('.ex-option-btn').forEach(b => b.classList.remove('selected'));
          btn.classList.add('selected');
          selectedAnswer = btn.dataset.val;
          document.getElementById('ex-answer').value = selectedAnswer;
        });
      });
    } else { optContainer.style.display = 'none'; }
    populateChildSelect();
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// ── Nav bindings ──────────────────────────────────────────────────────────────

document.querySelectorAll('.nav-btn[data-view]').forEach(btn => {
  btn.addEventListener('click', () => showView(btn.dataset.view));
});
document.querySelectorAll('.nav-btn[data-view]').forEach(btn => {
  btn.addEventListener('click', () => showView(btn.dataset.view));
});
document.addEventListener('click', (e) => {
  if (e.target.id === 'add-unit-btn') {
    document.getElementById('unit-modal').classList.remove('hidden');
  }
  if (e.target.id === 'cancel-unit') {
    document.getElementById('unit-modal').classList.add('hidden');
  }
  if (e.target.id === 'save-unit') {
    const title = document.getElementById('unit-title-input').value.trim();
    const description = document.getElementById('unit-desc-input').value.trim();
    const difficulty = document.getElementById('unit-difficulty-input').value;
    const is_published = document.getElementById('unit-published-input').checked;
    if (!title) { showToast('Title required', 'error'); return; }
    api('/units', 'POST', { title, description, difficulty, is_published, order_index: 1 })
      .then(() => {
        document.getElementById('unit-modal').classList.add('hidden');
        document.getElementById('unit-title-input').value = '';
        document.getElementById('unit-desc-input').value = '';
        showToast('Unit created!', 'success');
        loadAdmin();
      })
      .catch(e => showToast(e.message, 'error'));
  }
  if (e.target.id === 'save-lesson-btn') {
    const title = document.getElementById('lesson-title-input').value.trim();
    const unit_id = parseInt(document.getElementById('lesson-unit-select').value);
    const difficulty = document.getElementById('lesson-difficulty-input').value;
    const xp_reward = parseInt(document.getElementById('lesson-xp-input').value) || 50;
    const is_published = document.getElementById('lesson-published-input').checked;
    if (!title || !unit_id) { showToast('Title and unit required', 'error'); return; }
    api('/lessons', 'POST', { title, unit_id, difficulty, xp_reward, is_published, order_index: 1 })
      .then(() => {
        showToast('Lesson created!', 'success');
        document.getElementById('lesson-title-input').value = '';
        loadAdmin();
      })
      .catch(e => showToast(e.message, 'error'));
  }
});
async function loadAdmin() {
  try {
    const stats = await api('/admin/stats');
    document.getElementById('admin-stats-cards').innerHTML = `
      <div class="stat-card"><div class="stat-label">Total Parents</div><div class="stat-value">${stats.total_parents}</div></div>
      <div class="stat-card"><div class="stat-label">Total Children</div><div class="stat-value">${stats.total_children}</div></div>
      <div class="stat-card"><div class="stat-label">Total Lessons</div><div class="stat-value">${stats.total_lessons}</div></div>
      <div class="stat-card"><div class="stat-label">Active Today</div><div class="stat-value">${stats.active_children_today}</div></div>
      <div class="stat-card"><div class="stat-label">Total XP</div><div class="stat-value">${stats.total_xp_awarded}</div></div>
      <div class="stat-card"><div class="stat-label">Completions</div><div class="stat-value">${stats.total_lesson_completions}</div></div>
    `;
  } catch(e) { showToast('Failed to load stats', 'error'); }

  try {
    const data = await api('/units?page_size=50');
    const sel = document.getElementById('lesson-unit-select');
    sel.innerHTML = '<option value="">Select unit...</option>' + data.items.map(u => `<option value="${u.id}">${u.title}</option>`).join('');
    document.getElementById('admin-units-list').innerHTML = data.items.length
      ? data.items.map(u => `
          <div class="unit-card" style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <strong>${u.title}</strong>
              <span class="unit-badge" style="margin-left:.5rem">${u.difficulty}</span>
              ${u.is_published ? '<span class="unit-badge" style="background:#d1fae5;color:#065f46;margin-left:.3rem">Published</span>' : '<span class="unit-badge" style="background:#fee2e2;color:#991b1b;margin-left:.3rem">Draft</span>'}
            </div>
            <button class="btn-secondary" onclick="deleteUnit(${u.id})" style="font-size:.8rem;padding:.3rem .7rem">Delete</button>
          </div>`).join('')
      : '<p style="color:var(--text-muted)">No units yet.</p>';
  } catch(e) {}

  try {
    const logs = await api('/admin/logs?page_size=20');
    document.getElementById('admin-logs-list').innerHTML = logs.items.length
      ? logs.items.map(l => `
          <div class="notif-item">
            <strong>${l.action} ${l.resource_type} #${l.resource_id}</strong>
            <div class="notif-time">${timeAgo(l.created_at)}</div>
          </div>`).join('')
      : '<p style="color:var(--text-muted)">No logs yet.</p>';
  } catch(e) {}
}

async function deleteUnit(unitId) {
  if (!confirm('Delete this unit?')) return;
  try {
    await api(`/units/${unitId}`, 'DELETE');
    showToast('Unit deleted', 'success');
    loadAdmin();
  } catch(e) { showToast(e.message, 'error'); }
}
// ── Logout ────────────────────────────────────────────────────────────────────

document.getElementById('logout-btn').addEventListener('click', async () => {
  try {
    await api('/auth/logout', 'POST');
  } catch (e) {
    // игнорируем ошибку — всё равно разлогиниваем
  } finally {
    token = null;
    currentUser = null;
    selectedChildId = null;
    if (ws) { ws.close(); ws = null; }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    document.getElementById('main-screen').classList.remove('active');
    document.getElementById('auth-screen').classList.add('active');
  }
});