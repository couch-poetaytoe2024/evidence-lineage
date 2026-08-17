const form = document.querySelector('#investigation-form');
const running = document.querySelector('#running');
const results = document.querySelector('#results');
const errorBox = document.querySelector('#error');
const liveActivity = document.querySelector('#live-activity');
const systemPill = document.querySelector('#system-pill');
const claimInput = document.querySelector('#claim-text');
const identifierInput = document.querySelector('#identifier');
const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

claimInput.addEventListener('input', () => document.querySelector('#claim-count').textContent = `${claimInput.value.length} / 3000`);
identifierInput.addEventListener('input', () => document.querySelector('#citation-count').textContent = `${identifierInput.value.length} / 500`);

function setSystem(state, text) {
  systemPill.className = `system-pill ${state}`;
  systemPill.innerHTML = `<i></i> ${esc(text)}`;
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
  running.scrollIntoView({behavior:'smooth', block:'start'});
  try {
    const response = await fetch('/investigations/paper/stream', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({identifier:identifierInput.value.trim(), claim_text:claimInput.value.trim() || null, max_references:4, use_llm:true})
    });
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
  const key = `agent-${event.agent}`;
  let row = document.getElementById(key);
  if (!row) {
    row = document.createElement('article');
    row.id = key;
    row.className = 'live-event';
    liveActivity.appendChild(row);
  }
  row.innerHTML = `<strong>${esc(event.agent.replaceAll('_',' '))}</strong><small>${esc(event.detail)}</small><b class="state-${esc(event.status)}">${esc(event.status)}</b>`;
}

function render(data) {
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
        ${verdict ? `<div class="verdict-word">${esc(verdict.verdict.replaceAll('_',' '))}</div><p class="verdict-reason">${esc(verdict.reason)}</p>${scoreBlock('Claim supported by cited paper', verdict.support_score)}${scoreBlock('Cited paper supported upstream', verdict.lineage_score)}<p class="muted">Judge confidence ${Math.round(verdict.confidence * 100)}% · uncalibrated model estimate</p>` : '<p class="empty">No adjudicated verdict was available.</p>'}
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
