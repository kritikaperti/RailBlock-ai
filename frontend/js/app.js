/**
 * RailBlock AI - Frontend Controller & Application State Manager
 * Indian Railways AI-Powered Automatic Block Planning System
 * Integrated with data.gov.in / NTES Timetables
 */

const AppState = {
  currentUser: null,
  authToken: null,
  activeHorizon: 'DAILY',
  activeCorridor: 'CORRIDOR_GRAND_CHORD',
  network: null,
  corridors: null,
  timetableMaster: [],
  filteredTimetable: [],
  feedsSummary: null,
  tmsDefects: [],
  smmsDefects: [],
  tdmsDefects: [],
  coaTrains: [],
  bdmsReqs: [],
  prioritizedTasks: [],
  currentPlan: null,
  benchmarks: null,
  dataGovCatalog: null,
  mareyChart: null,
  schematic: null,
};

document.addEventListener('DOMContentLoaded', async () => {
  initUIEvents();
  initVisualizers();
  await initAuth();
});

function initVisualizers() {
  AppState.mareyChart = new MareyStringChart('mareyCanvas', 'chartTooltip');
  AppState.schematic = new CorridorTrackSchematic('schematicContainer');
}

// ==========================================================================
// AUTHENTICATION & SESSION MANAGEMENT
// ==========================================================================

async function initAuth() {
  loadQuickLoginOfficials();

  const formLogin = document.getElementById('formLogin');
  if (formLogin) {
    formLogin.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('loginUsername').value;
      const password = document.getElementById('loginPassword').value;
      await performLogin(username, password);
    });
  }

  const btnLogout = document.getElementById('btnLogout');
  if (btnLogout) {
    btnLogout.addEventListener('click', performLogout);
  }

  const savedToken = localStorage.getItem('railblock_auth_token');
  if (savedToken) {
    try {
      const res = await fetch(`/api/auth/me?token=${savedToken}`);
      if (res.ok) {
        const data = await res.json();
        AppState.authToken = savedToken;
        AppState.currentUser = data.user;
        showAppScreen();
        await loadInitialData();
        return;
      }
    } catch (err) {
      console.warn('Session verification failed, showing login screen:', err);
    }
  }

  showLoginScreen();
}

async function loadQuickLoginOfficials() {
  const container = document.getElementById('quickLoginContainer');
  if (!container) return;

  try {
    const res = await fetch('/api/auth/officials');
    const officials = await res.json();

    container.innerHTML = officials.map(off => `
      <div class="quick-role-chip" onclick="quickLogin('${off.username}', '${off.username === 'admin' ? 'admin123' : 'rail123'}')">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
          <div style="width: 26px; height: 26px; border-radius: 50%; background: ${off.avatar_color}; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold;">
            ${off.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
          </div>
          <div>
            <div style="font-size: 0.78rem; font-weight: 700; color: var(--text-primary);">${off.name}</div>
            <div style="font-size: 0.68rem; color: var(--text-muted);">${off.designation}</div>
          </div>
        </div>
        <span style="font-size: 0.72rem; color: var(--ir-gold); font-weight: bold;">Login ➔</span>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error loading demo officials:', err);
  }
}

async function quickLogin(username, password) {
  document.getElementById('loginUsername').value = username;
  document.getElementById('loginPassword').value = password;
  await performLogin(username, password);
}

async function performLogin(username, password) {
  const errDiv = document.getElementById('loginErrorMsg');
  const btn = document.getElementById('btnLoginSubmit');
  
  if (errDiv) errDiv.style.display = 'none';
  if (btn) {
    btn.disabled = true;
    btn.innerText = 'Verifying Credentials...';
  }

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Login failed');
    }

    const data = await res.json();
    AppState.authToken = data.token;
    AppState.currentUser = data;
    localStorage.setItem('railblock_auth_token', data.token);

    showToast(`Welcome, ${data.name} (${data.designation})`, 'success');
    showAppScreen();
    await loadInitialData();
  } catch (err) {
    if (errDiv) {
      errDiv.innerText = err.message;
      errDiv.style.display = 'block';
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = '🔐 Secure Officer Login';
    }
  }
}

async function performLogout() {
  if (AppState.authToken) {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: AppState.authToken })
      });
    } catch (e) {
      console.warn('Logout notification failed');
    }
  }

  AppState.authToken = null;
  AppState.currentUser = null;
  localStorage.removeItem('railblock_auth_token');
  showLoginScreen();
  showToast('Successfully signed out of RailBlock AI', 'info');
}

function showLoginScreen() {
  document.getElementById('loginScreen').style.display = 'flex';
  document.getElementById('appContainer').style.display = 'none';
}

function showAppScreen() {
  document.getElementById('loginScreen').style.display = 'none';
  document.getElementById('appContainer').style.display = 'block';

  const user = AppState.currentUser;
  if (user) {
    const avatar = document.getElementById('userAvatar');
    const name = document.getElementById('userName');
    const roleTag = document.getElementById('userRoleTag');

    if (avatar) {
      avatar.style.background = user.avatar_color || '#10b981';
      avatar.innerText = user.name.split(' ').map(n => n[0]).join('').slice(0, 2);
    }
    if (name) name.innerText = user.name;
    if (roleTag) roleTag.innerText = `${user.designation} (${user.department})`;
  }

  setTimeout(() => {
    if (AppState.mareyChart) AppState.mareyChart.resize();
  }, 200);
}

// ==========================================================================
// UI EVENTS & ROUTING
// ==========================================================================

function initUIEvents() {
  // Horizon Buttons
  document.querySelectorAll('.horizon-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.horizon-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      AppState.activeHorizon = btn.dataset.horizon;
      switchHorizon(AppState.activeHorizon);
    });
  });

  // Tab Navigation
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      
      btn.classList.add('active');
      const targetId = btn.dataset.target;
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) targetPanel.classList.add('active');
      
      if (targetId === 'tabMarey') {
        setTimeout(() => AppState.mareyChart.resize(), 100);
      }
    });
  });

  // Optimize Button
  const optBtn = document.getElementById('btnRunOptimizer');
  if (optBtn) {
    optBtn.addEventListener('click', async () => {
      optBtn.disabled = true;
      optBtn.innerHTML = '⚡ Optimizing Corridor Blocks...';
      try {
        const res = await fetch('/api/optimize', { method: 'POST' });
        const data = await res.json();
        AppState.benchmarks = data.benchmarks;
        await switchHorizon(AppState.activeHorizon);
        showToast('AI Multi-Department Optimization Completed Successfully!', 'success');
      } catch (err) {
        showToast('Optimization failed: ' + err.message, 'error');
      } finally {
        optBtn.disabled = false;
        optBtn.innerHTML = '⚡ Run AI Auto-Block Optimizer';
      }
    });
  }

  // Theme Toggle
  const themeBtn = document.getElementById('btnToggleTheme');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const current = document.body.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.body.setAttribute('data-theme', next);
      themeBtn.innerHTML = next === 'dark' ? '☀️' : '🌙';
      setTimeout(() => AppState.mareyChart.render(), 100);
    });
  }

  // Corridor Selector
  const corridorSelect = document.getElementById('corridorSelector');
  if (corridorSelect) {
    corridorSelect.addEventListener('change', async (e) => {
      AppState.activeCorridor = e.target.value;
      showToast(`Switched active corridor to ${e.target.options[e.target.selectedIndex].text}`, 'info');
      await loadInitialData();
    });
  }

  // Timetable Filters
  const ttSearch = document.getElementById('timetableSearchInput');
  const ttType = document.getElementById('timetableTypeFilter');
  const ttDir = document.getElementById('timetableDirectionFilter');

  if (ttSearch) ttSearch.addEventListener('input', applyTimetableFilters);
  if (ttType) ttType.addEventListener('change', applyTimetableFilters);
  if (ttDir) ttDir.addEventListener('change', applyTimetableFilters);

  // What-If Simulation Form
  const simBtn = document.getElementById('btnTriggerSimulation');
  if (simBtn) {
    simBtn.addEventListener('click', triggerWhatIfSimulation);
  }

  // Domain Configuration Form
  const domainForm = document.getElementById('formChangeDomain');
  if (domainForm) {
    domainForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const domainName = document.getElementById('inputCustomDomain').value;
      const appName = document.getElementById('inputCustomAppName').value;
      await updateSystemDomain(domainName, appName);
    });
  }

  // Custom Defect Form
  const defectForm = document.getElementById('formAddDefect');
  if (defectForm) {
    defectForm.addEventListener('submit', handleAddCustomDefect);
  }
}

// ==========================================================================
// DATA LOADING & RENDERING
// ==========================================================================

async function loadInitialData() {
  try {
    const [netRes, sumRes, tasksRes, planRes, benchRes, coaRes, tmsRes, smmsRes, tdmsRes, ttRes, catRes] = await Promise.all([
      fetch(`/api/network?corridor_id=${AppState.activeCorridor}`).then(r => r.json()),
      fetch('/api/feeds/summary').then(r => r.json()),
      fetch('/api/tasks/prioritized').then(r => r.json()),
      fetch(`/api/plans/${AppState.activeHorizon}`).then(r => r.json()),
      fetch('/api/benchmarks').then(r => r.json()),
      fetch('/api/feeds/coa').then(r => r.json()),
      fetch('/api/feeds/tms').then(r => r.json()),
      fetch('/api/feeds/smms').then(r => r.json()),
      fetch('/api/feeds/tdms').then(r => r.json()),
      fetch('/api/timetable').then(r => r.json()),
      fetch('/api/data-gov-in/catalog').then(r => r.json()),
    ]);

    AppState.network = netRes;
    AppState.feedsSummary = sumRes;
    AppState.prioritizedTasks = tasksRes;
    AppState.currentPlan = planRes;
    AppState.benchmarks = benchRes;
    AppState.coaTrains = coaRes;
    AppState.tmsDefects = tmsRes;
    AppState.smmsDefects = smmsRes;
    AppState.tdmsDefects = tdmsRes;
    AppState.timetableMaster = ttRes.trains || [];
    AppState.filteredTimetable = AppState.timetableMaster;
    AppState.dataGovCatalog = catRes;

    renderKPIs();
    renderTimetableMaster();
    renderBlockScheduleTable();
    renderPrioritizedTasksTable();
    renderFeedsTables();
    renderDataGovCatalog();
    
    AppState.mareyChart.setData(AppState.network.stations, AppState.coaTrains, AppState.currentPlan.blocks);
    AppState.schematic.setData(AppState.network.stations, AppState.currentPlan.blocks);
    
  } catch (err) {
    console.error('Error loading initial data:', err);
    showToast('Failed to connect to backend: ' + err.message, 'error');
  }
}

async function switchHorizon(horizon) {
  AppState.activeHorizon = horizon;
  try {
    const res = await fetch(`/api/plans/${horizon}`);
    AppState.currentPlan = await res.json();
    renderKPIs();
    renderBlockScheduleTable();
    AppState.mareyChart.setData(AppState.network.stations, AppState.coaTrains, AppState.currentPlan.blocks);
    AppState.schematic.setData(AppState.network.stations, AppState.currentPlan.blocks);
  } catch (err) {
    console.error('Error switching horizon:', err);
  }
}

function renderKPIs() {
  const plan = AppState.currentPlan;
  const bench = AppState.benchmarks;
  if (!plan) return;

  document.getElementById('kpiAssetAvail').innerText = `${plan.projected_asset_availability_pct}%`;
  document.getElementById('kpiAssetAvailDelta').innerText = bench ? `+${bench.asset_availability_gain_pct}% vs Legacy` : '+15.4%';
  
  document.getElementById('kpiMegaBlocks').innerText = `${plan.integrated_mega_blocks} / ${plan.total_blocks_scheduled}`;
  document.getElementById('kpiDeptUtil').innerText = `${plan.multi_department_utilization_pct}%`;
  
  document.getElementById('kpiTrainDelay').innerText = `${plan.estimated_train_delay_hours} hrs`;
  document.getElementById('kpiTrainDelayDelta').innerText = bench ? `-${bench.train_delay_reduction_pct}% delay` : '-44.6%';
  
  document.getElementById('kpiTotalBlockHours').innerText = `${plan.total_block_hours} hrs`;
  document.getElementById('kpiBundledTasks').innerText = `${plan.shadow_bundled_tasks_count} tasks`;
}

// ==========================================================================
// TIMETABLE EXPLORER & DATA.GOV.IN CATALOG
// ==========================================================================

function applyTimetableFilters() {
  const query = (document.getElementById('timetableSearchInput').value || '').toLowerCase().trim();
  const typeFilter = document.getElementById('timetableTypeFilter').value;
  const dirFilter = document.getElementById('timetableDirectionFilter').value;

  AppState.filteredTimetable = AppState.timetableMaster.filter(t => {
    const matchQuery = !query || 
      t.train_no.toLowerCase().includes(query) || 
      t.name.toLowerCase().includes(query) ||
      t.origin.toLowerCase().includes(query) ||
      t.destination.toLowerCase().includes(query);

    const matchType = !typeFilter || t.type === typeFilter || (t.type && t.type.value === typeFilter);
    const matchDir = !dirFilter || t.direction === dirFilter;

    return matchQuery && matchType && matchDir;
  });

  renderTimetableMaster();
}

function renderTimetableMaster() {
  const tbody = document.getElementById('tableTimetableMasterBody');
  if (!tbody) return;

  const trains = AppState.filteredTimetable;
  if (!trains.length) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No train schedules match the selected filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = trains.map(tr => {
    let typeBadge = 'badge-low';
    if (tr.type === 'VANDE_BHARAT') typeBadge = 'badge-gold';
    else if (tr.type === 'RAJDHANI_SHATABDI') typeBadge = 'badge-eng';
    else if (tr.type === 'SUPERFAST_MAIL') typeBadge = 'badge-snt';
    else if (tr.type && tr.type.includes('FREIGHT')) typeBadge = 'badge-medium';

    return `
      <tr>
        <td><b style="font-family: var(--font-mono); font-size: 0.95rem; color: var(--ir-gold);">${tr.train_no}</b></td>
        <td>
          <b>${tr.name}</b><br>
          <span class="badge ${typeBadge}" style="font-size: 0.68rem;">${tr.type}</span>
        </td>
        <td><b style="color: ${tr.direction === 'DOWN' ? '#38bdf8' : '#f5a623'};">${tr.direction}</b></td>
        <td><b>${tr.origin}</b> ➔ <b>${tr.destination}</b></td>
        <td><small>${tr.days}</small></td>
        <td><small style="color: var(--text-muted);">${tr.rakes}</small></td>
        <td><b>${tr.speed} km/h</b></td>
        <td><b style="color: #10b981;">On Time (±${tr.max_delay_min}m)</b></td>
        <td>
          <button class="btn-secondary" style="padding: 0.25rem 0.65rem; font-size: 0.75rem;" onclick="viewTrainHalts('${tr.train_no}')">
            🕒 Halts & Route
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function viewTrainHalts(trainNo) {
  const train = AppState.timetableMaster.find(t => t.train_no === trainNo);
  if (!train) return;

  const title = document.getElementById('modalTrainTitle');
  const body = document.getElementById('modalTrainBody');

  if (title) title.innerHTML = `🚆 ${train.train_no} - ${train.name} (${train.direction} Line)`;
  if (body) {
    body.innerHTML = `
      <div style="margin-bottom: 1rem; font-size: 0.84rem; color: var(--text-secondary);">
        <b>Rake Type:</b> ${train.rakes} | <b>Operational Speed:</b> ${train.speed} km/h | <b>Days of Run:</b> ${train.days}
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th>Station Code</th>
            <th>Arrival</th>
            <th>Departure</th>
            <th>Halt Duration</th>
            <th>Platform</th>
            <th>Distance (KM)</th>
          </tr>
        </thead>
        <tbody>
          ${train.halts.map(h => `
            <tr>
              <td><b>${h.stn}</b></td>
              <td>${h.arr}</td>
              <td>${h.dep}</td>
              <td><b>${h.halt}</b></td>
              <td><span class="badge badge-low">PF ${h.pf}</span></td>
              <td>KM ${h.km}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  openModal('modalTrainHalts');
}

function renderDataGovCatalog() {
  const grid = document.getElementById('dataGovCatalogGrid');
  if (!grid || !AppState.dataGovCatalog) return;

  grid.innerHTML = AppState.dataGovCatalog.datasets.map(ds => `
    <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 10px; padding: 1.25rem; display: flex; flex-direction: column; justify-content: space-between;">
      <div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <span class="badge badge-low" style="font-family: var(--font-mono);">${ds.id}</span>
          <span class="badge badge-mega">${ds.format}</span>
        </div>
        <h4 style="margin-top: 0.6rem; font-size: 0.95rem; color: var(--text-primary);">${ds.title}</h4>
        <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.35rem;">
          <b>Source:</b> ${ds.source_system}<br>
          <b>Records Integrated:</b> ${ds.records_count} records | <b>Update:</b> ${ds.frequency}
        </div>
      </div>

      <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
        <a href="/api/data-gov-in/export/${ds.id === 'IR-DATA-001' ? 'timetable' : (ds.id === 'IR-DATA-002' ? 'tms_defects' : (ds.id === 'IR-DATA-003' ? 'smms_defects' : (ds.id === 'IR-DATA-004' ? 'tdms_defects' : 'blocks_daily')))}" target="_blank" class="btn-secondary" style="font-size: 0.75rem; text-decoration: none; flex: 1; text-align: center;">
          📥 Download JSON
        </a>
        <a href="${ds.data_gov_link}" target="_blank" class="btn-primary" style="font-size: 0.75rem; text-decoration: none; padding: 0.4rem 0.8rem;">
          data.gov.in ➔
        </a>
      </div>
    </div>
  `).join('');
}

function renderBlockScheduleTable() {
  const tbody = document.getElementById('tableBlocksBody');
  if (!tbody || !AppState.currentPlan) return;

  const blocks = AppState.currentPlan.blocks;
  if (!blocks.length) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">No blocks scheduled for this horizon.</td></tr>`;
    return;
  }

  tbody.innerHTML = blocks.map((b, idx) => {
    const isMega = b.is_integrated_mega_block;
    const deptsHtml = b.participating_departments.map(d => {
      const cls = d === 'ENGINEERING' ? 'badge-eng' : (d === 'SNT' ? 'badge-snt' : 'badge-trd');
      return `<span class="badge ${cls}">${d}</span>`;
    }).join(' ');

    const machines = b.allocated_machines.length ? b.allocated_machines.join(', ') : 'None (Manual)';

    return `
      <tr>
        <td><b>${b.block_id}</b></td>
        <td><span class="badge ${isMega ? 'badge-mega' : 'badge-low'}">${isMega ? 'INTEGRATED MEGA' : 'SINGLE DEPT'}</span></td>
        <td>${b.station_from} ➔ ${b.station_to}<br><small style="color: var(--text-muted);">${b.line} (KM ${b.start_km}-${b.end_km})</small></td>
        <td><b>${b.start_time} - ${b.end_time}</b><br><small style="color: var(--text-muted);">${b.duration_minutes} mins</small></td>
        <td>${deptsHtml}</td>
        <td><small>${machines}</small></td>
        <td><b style="color: var(--ir-green);">+${b.coordination_efficiency_gain_pct}%</b></td>
        <td>${b.impacted_trains_count} trains<br><small style="color: var(--text-muted);">${b.total_train_delay_minutes}m delay</small></td>
        <td>
          <button class="btn-secondary" style="padding: 0.25rem 0.6rem; font-size: 0.75rem;" onclick="viewBlockMemo('${b.block_id}')">
            📋 Form B
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function renderPrioritizedTasksTable() {
  const tbody = document.getElementById('tablePrioritizedTasksBody');
  if (!tbody || !AppState.prioritizedTasks) return;

  tbody.innerHTML = AppState.prioritizedTasks.slice(0, 30).map(t => {
    const deptBadge = t.department === 'ENGINEERING' ? 'badge-eng' : (t.department === 'SNT' ? 'badge-snt' : 'badge-trd');
    const sevBadge = `badge-${t.severity.toLowerCase()}`;
    const scoreColor = t.composite_criticality_score >= 80 ? '#ef4444' : (t.composite_criticality_score >= 60 ? '#f59e0b' : '#10b981');

    return `
      <tr>
        <td><b>${t.task_id}</b></td>
        <td><span class="badge ${deptBadge}">${t.department}</span></td>
        <td><b>${t.title}</b><br><small style="color: var(--text-muted);">${t.station_from}-${t.station_to} [${t.line}] KM ${t.start_km}-${t.end_km}</small></td>
        <td><span class="badge ${sevBadge}">${t.severity}</span></td>
        <td><b style="color: ${scoreColor}; font-size: 1.05rem;">${t.composite_criticality_score}</b></td>
        <td><small>Safety: ${t.safety_risk_index}<br>Punct: ${t.punctuality_impact_index}</small></td>
        <td>${t.required_duration_minutes}m</td>
        <td><small>${t.required_machine}</small></td>
        <td><span class="badge badge-low">${t.recommended_horizon}</span></td>
      </tr>
    `;
  }).join('');
}

function renderFeedsTables() {
  const tmsTbody = document.getElementById('tableTMSFeedBody');
  if (tmsTbody && AppState.tmsDefects) {
    tmsTbody.innerHTML = AppState.tmsDefects.slice(0, 10).map(d => `
      <tr>
        <td><b>${d.id}</b></td>
        <td>${d.station_from}-${d.station_to} (${d.line})</td>
        <td>KM ${d.start_km}-${d.end_km}</td>
        <td><span class="badge badge-${d.severity.toLowerCase()}">${d.severity}</span></td>
        <td>${d.speed_restriction_if_deferred_kmph ? d.speed_restriction_if_deferred_kmph + ' km/h' : 'None'}</td>
        <td>${d.urgency_days_remaining} days</td>
        <td><small>${d.description}</small></td>
      </tr>
    `).join('');
  }

  const coaTbody = document.getElementById('tableCOAFeedBody');
  if (coaTbody && AppState.coaTrains) {
    coaTbody.innerHTML = AppState.coaTrains.slice(0, 10).map(tr => `
      <tr>
        <td><b>${tr.train_number}</b></td>
        <td><b>${tr.train_name}</b></td>
        <td><span class="badge badge-low">${tr.train_type}</span></td>
        <td><b>${tr.direction}</b> (${tr.origin} ➔ ${tr.destination})</td>
        <td>${tr.average_speed_kmph} km/h</td>
        <td><b style="color: ${tr.delay_minutes > 0 ? '#f59e0b' : '#10b981'};">+${tr.delay_minutes}m</b></td>
      </tr>
    `).join('');
  }
}

async function triggerWhatIfSimulation() {
  const scenarioType = document.getElementById('simScenarioSelect').value;
  const resultContainer = document.getElementById('simResultsContainer');
  const btn = document.getElementById('btnTriggerSimulation');

  btn.disabled = true;
  btn.innerText = '⏳ Simulating & Re-Optimizing...';
  resultContainer.innerHTML = `<div style="text-align:center; padding: 2rem; color: var(--text-secondary);">Simulating corridor dynamic response...</div>`;

  try {
    const payload = {
      scenario_type: scenarioType,
      station_from: document.getElementById('simStnFrom').value || "TDL",
      station_to: document.getElementById('simStnTo').value || "ETW",
      km_location: parseFloat(document.getElementById('simKm').value || 214.5),
      line: "UP_MAIN",
      freight_increase_pct: 35
    };

    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    let trainsHtml = '';
    if (data.affected_trains && data.affected_trains.length) {
      trainsHtml = `
        <h4 style="margin-top: 1rem; color: var(--text-primary);">⚡ Dynamically Regulated Trains</h4>
        <table class="data-table" style="margin-top: 0.5rem;">
          <thead>
            <tr><th>Train No</th><th>Train Name</th><th>AI Dispatch Action</th><th>Delay Delta</th><th>Punctuality Status</th></tr>
          </thead>
          <tbody>
            ${data.affected_trains.map(t => `
              <tr>
                <td><b>${t.train_no}</b></td>
                <td>${t.name}</td>
                <td><b style="color: var(--ir-gold);">${t.action}</b></td>
                <td><b style="color: #ef4444;">${t.delay}</b></td>
                <td><span class="badge badge-low">${t.punctuality_impact}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }

    let emBlockHtml = '';
    if (data.emergency_block_granted) {
      const eb = data.emergency_block_granted;
      emBlockHtml = `
        <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; border-radius: 8px; padding: 1rem; margin-top: 1rem;">
          <h4 style="color: #f87171; display: flex; align-items: center; gap: 0.5rem;">
            🚨 Emergency Block Sanctioned: ${eb.block_id}
          </h4>
          <div style="font-size: 0.85rem; margin-top: 0.4rem; color: #f1f5f9;">
            <b>Section:</b> ${eb.station_from} - ${eb.station_to} [${eb.line} KM ${eb.start_km}-${eb.end_km}] | 
            <b>Duration:</b> ${eb.start_time} - ${eb.end_time} (${eb.duration_minutes} mins) |
            <b>Notice:</b> ${eb.disconnection_notice_number}
          </div>
          <div style="font-size: 0.85rem; color: #34d399; margin-top: 0.3rem;">
            <b>Co-bundled:</b> ${eb.bundled_tasks.map(bt => bt.title).join(' + ')}
          </div>
        </div>
      `;
    }

    resultContainer.innerHTML = `
      <div style="background: var(--bg-inset); border: 1px solid var(--border-color); border-radius: 8px; padding: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="color: var(--ir-gold);">${data.scenario_title}</h3>
          <span class="badge badge-mega">AI Auto-Resolved</span>
        </div>
        <p style="color: var(--text-secondary); margin-top: 0.5rem;">${data.impact_summary}</p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-top: 1rem;">
          <div style="background: var(--bg-card); padding: 0.75rem; border-radius: 6px; border: 1px solid var(--border-color);">
            <div style="font-size: 0.75rem; color: var(--text-muted);">Asset Uptime Delta</div>
            <div style="font-size: 1.2rem; font-weight: bold; color: ${data.asset_uptime_delta_pct >= 0 ? '#10b981' : '#f59e0b'};">
              ${data.asset_uptime_delta_pct > 0 ? '+' : ''}${data.asset_uptime_delta_pct}%
            </div>
          </div>
          <div style="background: var(--bg-card); padding: 0.75rem; border-radius: 6px; border: 1px solid var(--border-color);">
            <div style="font-size: 0.75rem; color: var(--text-muted);">Corridor Delay Delta</div>
            <div style="font-size: 1.2rem; font-weight: bold; color: #38bdf8;">+${data.train_delay_delta_minutes} mins</div>
          </div>
        </div>

        ${emBlockHtml}
        ${trainsHtml}

        <div style="margin-top: 1rem; background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 0.75rem;">
          <b>AI Resolution Strategy:</b>
          <div style="font-size: 0.85rem; color: var(--text-primary); margin-top: 0.25rem;">
            ${data.ai_resolution_strategy}
          </div>
        </div>
      </div>
    `;

    showToast('Simulation evaluated and re-optimized!', 'success');
  } catch (err) {
    showToast('Simulation error: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerText = '⚡ Trigger Scenario Simulation';
  }
}

async function handleAddCustomDefect(e) {
  e.preventDefault();
  const form = e.target;
  const payload = {
    department: form.dept.value,
    section_id: form.section.value,
    start_km: parseFloat(form.start_km.value),
    end_km: parseFloat(form.end_km.value),
    severity: form.severity.value,
    defect_type: form.defect_type.value,
    urgency_days_remaining: parseInt(form.urgency.value),
    description: form.description.value
  };

  try {
    const res = await fetch('/api/feeds/defect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    showToast('Custom defect injected & schedule re-optimized!', 'success');
    closeModal('modalAddDefect');
    await loadInitialData();
  } catch (err) {
    showToast('Failed to add defect: ' + err.message, 'error');
  }
}

async function viewBlockMemo(blockId) {
  try {
    const res = await fetch(`/api/block/${blockId}/memo`);
    const memo = await res.json();
    
    const memoContainer = document.getElementById('memoContent');
    if (!memoContainer) return;

    memoContainer.innerHTML = `
      <div class="form-b-memo-doc">
        <div class="form-b-header">
          <h2>INDIAN RAILWAYS</h2>
          <h3>${memo.railway_zone} - ${memo.division}</h3>
          <h4>${memo.subject}</h4>
        </div>
        
        <div class="form-b-meta">
          <div><b>Sanction Memo No:</b> ${memo.memo_number}</div>
          <div><b>Date:</b> ${memo.date_of_issue}</div>
        </div>
        
        <p><b>1. Section & Line:</b> ${memo.section} | <b>Line:</b> ${memo.line_affected} (${memo.location_km})</p>
        <p><b>2. Block Window:</b> ${memo.block_timing.start_time} to ${memo.block_timing.end_time} (${memo.block_timing.duration_minutes} Minutes / ${memo.block_timing.duration_hours} Hours)</p>
        <p><b>3. Integrated Mega-Block:</b> ${memo.is_integrated_mega_block ? 'YES (Multi-Department Shadow Coordinated)' : 'NO'}</p>
        <p><b>4. Allocated Track Machines / Wagons:</b> ${memo.allocated_heavy_machines.join(', ') || 'Manual Maintenance Squads'}</p>
        
        <h4 style="margin-top: 1rem;">5. Bundled Coordinated Works:</h4>
        <table class="form-b-table">
          <thead>
            <tr><th>Sl</th><th>Department</th><th>Task ID</th><th>Work Title</th><th>Machine</th><th>Gangs</th><th>Scope</th></tr>
          </thead>
          <tbody>
            ${memo.bundled_departmental_works.map(w => `
              <tr>
                <td>${w.sl_no}</td>
                <td><b>${w.dept}</b></td>
                <td>${w.task_id}</td>
                <td>${w.title}</td>
                <td>${w.machine}</td>
                <td>${w.gangs}</td>
                <td><small>${w.scope}</small></td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <h4 style="margin-top: 1rem;">6. Train Regulation & Operations Instructions:</h4>
        <ul style="margin-left: 1.5rem; font-size: 0.88rem;">
          <li><b>Total Trains Regulated:</b> ${memo.train_regulation_instructions.total_impacted_trains}</li>
          <li><b>Cumulative Corridor Delay:</b> ${memo.train_regulation_instructions.total_delay_minutes} minutes</li>
          ${memo.train_regulation_instructions.regulated_trains.map(rt => `<li>${rt}</li>`).join('')}
          ${memo.train_regulation_instructions.diverted_freight.map(df => `<li>${df}</li>`).join('')}
          <li><b>Safety Margin Buffer:</b> ${memo.train_regulation_instructions.safety_interlock_buffer}</li>
        </ul>

        <h4 style="margin-top: 1rem;">7. Mandatory Safety Certifications:</h4>
        <ol style="margin-left: 1.5rem; font-size: 0.88rem;">
          ${memo.safety_certifications.map(sc => `<li>${sc}</li>`).join('')}
        </ol>

        <div class="form-b-signatures">
          ${memo.joint_signatories.map(s => `
            <div class="sig-box">
              <div>${s.role}</div>
              <div style="color: #059669; font-size: 0.78rem;">[${s.status}]</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    openModal('modalBlockMemo');
  } catch (err) {
    showToast('Failed to load memo: ' + err.message, 'error');
  }
}

function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('active');
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('active');
}

function showToast(msg, type = 'info') {
  const toast = document.createElement('div');
  toast.style.position = 'fixed';
  toast.style.bottom = '25px';
  toast.style.right = '25px';
  toast.style.background = type === 'success' ? '#10b981' : (type === 'error' ? '#ef4444' : '#19456b');
  toast.style.color = '#fff';
  toast.style.padding = '0.75rem 1.25rem';
  toast.style.borderRadius = '6px';
  toast.style.boxShadow = '0 4px 15px rgba(0,0,0,0.5)';
  toast.style.zIndex = '9999';
  toast.style.fontWeight = '600';
  toast.style.fontSize = '0.88rem';
  toast.innerText = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

async function updateSystemDomain(domainName, appName) {
  try {
    const res = await fetch('/api/config/domain', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain_name: domainName, app_name: appName })
    });
    const config = await res.json();
    
    // Update UI elements
    const domainPill = document.getElementById('currentDomainPill');
    if (domainPill) domainPill.innerText = config.domain_name;
    document.title = `${config.app_name} (${config.domain_name}) - Indian Railways`;

    showToast(`Domain name updated to https://${config.domain_name}`, 'success');
    closeModal('modalChangeDomain');
  } catch (err) {
    showToast('Failed to update domain: ' + err.message, 'error');
  }
}

function setPresetDomain(domain, appName) {
  document.getElementById('inputCustomDomain').value = domain;
  document.getElementById('inputCustomAppName').value = appName;
}

window.viewBlockMemo = viewBlockMemo;
window.viewTrainHalts = viewTrainHalts;
window.openModal = openModal;
window.closeModal = closeModal;
window.quickLogin = quickLogin;
window.setPresetDomain = setPresetDomain;
window.updateSystemDomain = updateSystemDomain;
