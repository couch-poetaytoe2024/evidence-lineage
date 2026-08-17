const form = document.querySelector('#investigation-form');
const running = document.querySelector('#running');
const results = document.querySelector('#results');
const errorBox = document.querySelector('#error');
const liveActivity = document.querySelector('#live-activity');
const systemPill = document.querySelector('#system-pill');
const claimInput = document.querySelector('#claim-text');
const identifierInput = document.querySelector('#identifier');
const diagnosticAgents = document.querySelector('#diagnostic-agents');
const diagnosticNotes = document.querySelector('#diagnostic-notes');
const diagnosticSummary = document.querySelector('#diagnostic-summary');
const agentOrder = ['source_tracer','claim_miner','evidence_agent','skeptic_agent','judge_agent'];
const progressStates = new Map();
let currentProgress = 0;
const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

claimInput.addEventListener('input', () => document.querySelector('#claim-count').textContent = `${claimInput.value.length} / 3000`);
identifierInput.addEventListener('input', () => document.querySelector('#citation-count').textContent = `${identifierInput.value.length} / 500`);

function setSystem(state, text) {
  systemPill.className = `system-pill ${state}`;
  systemPill.innerHTML = `<i></i> ${esc(text)}`;
}

function resetDiagnostics() {
  progressStates.clear();
  updateProgress(0);
  diagnosticSummary.textContent = 'Investigation in progress';
  document.querySelector('#stat-agents').textContent = '0 / 5';
  document.querySelector('#stat-sources').textContent = '0';
  document.querySelector('#stat-evidence').textContent = '0';
  document.querySelector('#stat-failures').textContent = '0';
  diagnosticAgents.innerHTML = agentOrder.map((agent, index) => `<article id="diagnostic-${agent}" class="diagnostic-agent"><b>${String(index + 1).padStart(2,'0')}</b><div><strong>${esc(agent.replaceAll('_',' '))}</strong><small>Waiting to begin</small></div><span class="diagnostic-state">PENDING</span></article>`).join('');
  diagnosticNotes.innerHTML = '<p>The workflow has started. Each completed, failed, or fallback step will be recorded here.</p>';
}

function updateProgress(explicitValue = null) {
  const completed = [...progressStates.values()].filter(status => ['DONE','FAILED','FALLBACK'].includes(status)).length;
  const runningNow = [...progressStates.values()].some(status => status === 'RUNNING');
  const calculated = explicitValue ?? Math.min(95, completed * 20 + (runningNow ? 8 : 0));
  currentProgress = explicitValue === 0 ? 0 : Math.max(currentProgress, calculated);
  const value = currentProgress;
  document.querySelector('#progress-percent').textContent = `${value}%`;
  document.querySelector('#workflow-progress-fill').style.width = `${value}%`;
  document.querySelector('.workflow-progress').setAttribute('aria-valuenow', String(value));
}

async function runNonStreaming(payload) {
  const response = await fetch('/investigations/paper', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  if (!response.ok) throw new Error(`Both investigation endpoints were unavailable (${response.status}). Restart the backend with: uvicorn backend.main:app --reload`);
  render(await response.json());
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const button = document.querySelector('.engraved-action');
  running.classList.remove('hidden');
  results.classList.add('hidden');
  errorBox.classList.add('hidden');
  liveActivity.innerHTML = '';
  button.disabled = true;
  setSystem('busy', 'Investigation active');
  resetDiagnostics();
  running.scrollIntoView({behavior:'smooth', block:'start'});
  try {
    const payload = {identifier:identifierInput.value.trim(), claim_text:claimInput.value.trim() || null, max_references:4, use_llm:true};
    const response = await fetch('/investigations/paper/stream', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    });
    if (response.status === 404) {
      diagnosticNotes.innerHTML = '<p><strong>Live stream route unavailable.</strong> Retrying through the standard investigation endpoint. Restart the backend to restore live progress updates.</p>';
      await runNonStreaming(payload);
      setSystem('', 'Investigation complete');
      return;
    }
    if (!response.ok) throw new Error(`Investigation request failed (${response.status}).`);
    if (!response.body) throw new Error('Live investigation streaming is unavailable in this browser.');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const {value, done} = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), {stream:!done});
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) if (line.trim()) handleStreamMessage(JSON.parse(line));
      if (done) break;
    }
    setSystem('', 'Investigation complete');
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.classList.remove('hidden');
    setSystem('failed', 'Investigation interrupted');
    diagnosticSummary.textContent = 'Investigation interrupted';
    diagnosticNotes.innerHTML = `<p><strong>Request failure:</strong> ${esc(error.message)}</p><p>Your entered claim and source were not judged. Confirm the backend was launched with <code>uvicorn backend.main:app --reload</code>, then try again.</p>`;
    document.querySelector('#stat-failures').textContent = '1';
  } finally {
    running.classList.add('hidden');
    button.disabled = false;
  }
});

function handleStreamMessage(message) {
  if (message.type === 'event') appendLiveEvent(message.event);
  if (message.type === 'result') render(message.result);
  if (message.type === 'error') throw new Error(message.message);
}

function appendLiveEvent(event) {
  progressStates.set(event.agent, event.status);
  updateProgress();
  const key = `agent-${event.agent}`;
  let row = document.getElementById(key);
  if (!row) {
    row = document.createElement('article');
    row.id = key;
    row.className = 'live-event';
    liveActivity.appendChild(row);
  }
  row.innerHTML = `<strong>${esc(event.agent.replaceAll('_',' '))}</strong><small>${esc(event.detail)}</small><b class="state-${esc(event.status)}">${esc(event.status)}</b>`;
  const diagnostic = document.querySelector(`#diagnostic-${event.agent}`);
  if (diagnostic) {
    diagnostic.className = `diagnostic-agent diagnostic-${event.status}`;
    diagnostic.querySelector('small').textContent = event.detail;
    diagnostic.querySelector('.diagnostic-state').textContent = event.status;
  }
}

function render(data) {
  updateProgress(100);
  const verdict = data.verdicts?.[0];
  const support = data.support_arguments?.[0];
  const skeptic = data.skeptic_arguments?.[0];
  const trace = data.execution_trace || [];
  const eventFor = agent => [...trace].reverse().find(e => e.agent === agent);
  const papers = new Map((data.papers || []).map(p => [p.id, p]));
  const paperLabel = id => papers.get(id)?.title || id;
  const paperDoi = id => papers.get(id)?.doi || '';
  const source = data.source_paper;
  const supportText = support?.conclusion || eventFor('evidence_agent')?.detail || 'No evidence argument was available.';
  const skepticText = skeptic?.conclusion || eventFor('skeptic_agent')?.detail || 'No skeptical challenge was available.';
  const badge = text => `<span class="status">${esc(text)}</span>`;
  const scoreBlock = (label, value) => value == null ? '' : `<div class="score-block"><div class="score-label"><span>${esc(label)}</span><strong>${value}/100</strong></div><div class="meter" role="meter" aria-valuenow="${value}" aria-valuemin="0" aria-valuemax="100"><div style="width:${Math.max(0,Math.min(100,value))}%"></div></div></div>`;
  const evidence = data.evidence || [];
  const edges = data.citation_chain || [];
  updateDiagnostics(data, trace, evidence);

  results.innerHTML = `<div class="results-shell">
    <div class="results-main">
      <section class="result-panel">
        <div class="section-head"><h2>Research question</h2><small>Claim under examination</small></div>
        <p class="kicker">Target claim</p><p class="verdict-reason">${esc(data.claims?.[0]?.text || 'No claim could be extracted from the available record.')}</p>
        <div>${badge(data.status)} ${source?.doi ? badge(source.doi) : ''}</div>
      </section>
      <section class="result-panel">
        <div class="section-head"><h2>Evidence lineage</h2><small>${edges.length} bibliographic connection${edges.length === 1 ? '' : 's'}</small></div>
        ${source ? `<article class="lineage-root"><div class="lineage-title">${esc(source.title)}</div><div class="lineage-meta">Cited paper · ${esc(source.doi || source.id)}</div></article>` : ''}
        ${edges.map(edge => `<article class="lineage-node"><div class="lineage-title">${esc(paperLabel(edge.cited_paper_id))}</div><div class="lineage-meta">Upstream reference · ${esc(paperDoi(edge.cited_paper_id) || edge.cited_paper_id)} · ${edge.association_verified ? 'citation context verified' : 'context not yet verified'}</div></article>`).join('') || '<p class="empty">No upstream citation edges were retrieved.</p>'}
      </section>
      <section class="result-panel">
        <div class="section-head"><h2>Source evidence</h2><small>${evidence.length} retrieved passage${evidence.length === 1 ? '' : 's'}</small></div>
        <div class="evidence-grid">${evidence.map(item => `<article class="evidence-card">${badge(item.evidence_role === 'direct_cited_paper' ? 'Primary cited source' : 'Upstream source')}${item.used_by_agents ? badge('Reviewed by agents') : ''}<h3>${esc(paperLabel(item.source_paper_id))}</h3><div class="lineage-meta source-doi">${esc(paperDoi(item.source_paper_id) || item.source_paper_id)}</div><p class="passage">${esc(item.passage)}</p><small class="muted">${esc(item.locator)}</small></article>`).join('') || '<p class="empty">No evidence passages were available.</p>'}</div>
      </section>
    </div>
    <aside class="results-side">
      <section class="result-panel">
        <div class="section-head"><h2>Judge verdict</h2><small>Auditable synthesis</small></div>
        ${verdict ? `<div class="verdict-word"><span>${esc(verdict.verdict.replaceAll('_',' '))}</span>${verdict.support_score == null ? '' : `<strong class="verdict-score">${verdict.support_score}% <small>claim support</small></strong>`}</div><p class="verdict-reason">${esc(verdict.reason)}</p>${scoreBlock('Claim supported by cited paper', verdict.support_score)}${scoreBlock('Cited paper supported upstream', verdict.lineage_score)}<p class="muted">Judge confidence ${Math.round(verdict.confidence * 100)}% · uncalibrated model estimate</p>` : '<p class="empty">No adjudicated verdict was available.</p>'}
      </section>
      <section class="result-panel">
        <div class="section-head"><h2>Independent review</h2><small>Evidence and challenge</small></div>
        <article class="debate-card"><strong>Evidence Agent</strong><p>${esc(supportText)}</p></article>
        <article class="debate-card skeptic"><strong>Skeptic Agent</strong><p>${esc(skepticText)}</p></article>
      </section>
      <section id="agent-monitor" class="result-panel">
        <div class="section-head"><h2>Agent trace</h2><small>${trace.length} recorded events</small></div>
        ${trace.map((item, index) => `<article class="trace-event"><span class="trace-icon">${index + 1}</span><div><strong>${esc(item.agent.replaceAll('_',' '))}</strong><p>${esc(item.detail)}</p></div><b class="state-${esc(item.status)}">${esc(item.status)}</b></article>`).join('') || '<p class="empty">No execution events were recorded.</p>'}
      </section>
      <section class="result-panel">
        <div class="section-head"><h2>Boundaries of the record</h2><small>Not verified</small></div>
        <ul class="limitations">${(data.limitations || []).map(item => `<li>${esc(item)}</li>`).join('') || '<li>No limitations were reported.</li>'}</ul>
      </section>
    </aside>
  </div>`;
  results.classList.remove('hidden');
  results.scrollIntoView({behavior:'smooth', block:'start'});
}

function updateDiagnostics(data, trace, evidence) {
  const latest = new Map();
  for (const event of trace) latest.set(event.agent, event);
  const completed = [...latest.values()].filter(item => item.status === 'DONE').length;
  const failures = [...latest.values()].filter(item => ['FAILED','FALLBACK'].includes(item.status));
  document.querySelector('#stat-agents').textContent = `${completed} / 5`;
  document.querySelector('#stat-sources').textContent = String((data.papers || []).length);
  document.querySelector('#stat-evidence').textContent = String(evidence.length);
  document.querySelector('#stat-failures').textContent = String(failures.length);
  diagnosticSummary.textContent = failures.length ? `Completed with ${failures.length} warning${failures.length === 1 ? '' : 's'}` : 'Workflow completed successfully';
  for (const agent of agentOrder) {
    const event = latest.get(agent);
    const card = document.querySelector(`#diagnostic-${agent}`);
    if (!card || !event) continue;
    card.className = `diagnostic-agent diagnostic-${event.status}`;
    card.querySelector('small').textContent = event.detail;
    card.querySelector('.diagnostic-state').textContent = event.status;
  }
  const limitations = data.limitations || [];
  diagnosticNotes.innerHTML = `
    <section class="diagnostic-group">
      <h3>What succeeded</h3>
      <ul>${[...latest.values()].filter(item => item.status === 'DONE').map(item => `<li><strong>${esc(item.agent.replaceAll('_',' '))}:</strong> ${esc(item.detail)}</li>`).join('') || '<li>No successful agent step was recorded.</li>'}</ul>
    </section>
    <section class="diagnostic-group">
      <h3>What failed or fell back</h3>
      <ul>${failures.map(item => `<li><strong>${esc(item.agent.replaceAll('_',' '))}:</strong> ${esc(item.detail)}</li>`).join('') || '<li>No agent failures or fallbacks were reported.</li>'}</ul>
    </section>
    <section class="diagnostic-group">
      <h3>Verification boundaries</h3>
      <ul>${limitations.map(item => `<li>${esc(item)}</li>`).join('') || '<li>No additional limitations were reported.</li>'}</ul>
    </section>`;
}
