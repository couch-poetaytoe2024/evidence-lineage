const form = document.querySelector('#investigation-form');
const running = document.querySelector('#running');
const results = document.querySelector('#results');
const errorBox = document.querySelector('#error');
const liveActivity = document.querySelector('#live-activity');
const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

form.addEventListener('submit', async event => {
  event.preventDefault();
  const button = form.querySelector('button');
  running.classList.remove('hidden');
  results.classList.add('hidden');
  errorBox.classList.add('hidden');
  liveActivity.innerHTML = '';
  button.disabled = true;
  try {
    const claimText = document.querySelector('#claim-text').value.trim();
    const response = await fetch('/investigations/paper/stream', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        identifier:document.querySelector('#identifier').value,
        claim_text:claimText || null,
        max_references:4,
        use_llm:true
      })
    });
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    if (!response.body) throw new Error('Streaming is unavailable in this browser.');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const {value,done} = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), {stream:!done});
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.trim()) handleStreamMessage(JSON.parse(line));
      }
      if (done) break;
    }
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.classList.remove('hidden');
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
  const row = document.createElement('div');
  row.className = 'live-event';
  row.innerHTML = `<div><strong>${esc(event.agent.replaceAll('_',' '))}</strong><br><small>${esc(event.detail)}</small></div><b class="state-${esc(event.status)}">${esc(event.status)}</b>`;
  liveActivity.appendChild(row);
  row.scrollIntoView({behavior:'smooth',block:'nearest'});
}

function render(data) {
  const verdict = data.verdicts?.[0];
  const support = data.support_arguments?.[0];
  const skeptic = data.skeptic_arguments?.[0];
  const eventFor = agent => [...(data.execution_trace||[])].reverse().find(e => e.agent === agent);
  const papers = new Map((data.papers||[]).map(p => [p.id,p]));
  const paperLabel = id => papers.get(id)?.title || id;
  const paperDoi = id => papers.get(id)?.doi || '';
  const supportText = support?.conclusion || eventFor('evidence_agent')?.detail || 'No argument available.';
  const skepticText = skeptic?.conclusion || eventFor('skeptic_agent')?.detail || 'No challenge available.';
  const score = verdict?.support_score;
  const lineageScore = verdict?.lineage_score;
  const meter = (label,value,description) => value == null ? '' : `<h3>${label}: ${value}/100</h3><div class="meter" role="meter" aria-valuenow="${value}" aria-valuemin="0" aria-valuemax="100"><div style="width:${value}%"></div></div><p class="muted">${description}</p>`;
  const scoreHtml = meter('Your claim supported by cited paper',score,"Direct support for your claim's scope, conditions, and magnitude.") + meter('Cited paper supported by its references',lineageScore,'Upstream evidence-lineage support based on retrieved references.');
  results.innerHTML = `
    <section class="card"><span class="status">${esc(data.status)}</span><h2>${esc(data.source_paper?.title || 'Paper unavailable')}</h2><p class="muted">${esc(data.source_paper?.doi || '')}</p>${verdict ? `<div class="verdict">${esc(verdict.verdict)}</div>${scoreHtml}<p>${esc(verdict.reason)}</p><p class="muted">Judge confidence ${Math.round(verdict.confidence*100)}% — uncalibrated model estimate</p>` : '<p>No adjudicated verdict was available.</p>'}</section>
    <section class="card"><h2>Target claim</h2><p>${esc(data.claims?.[0]?.text || 'No claim could be extracted from available text.')}</p></section>
    <section class="card"><h2>Independent agent debate</h2><div class="debate"><div class="side"><strong>Evidence Agent</strong><p>${esc(supportText)}</p></div><div class="side skeptic"><strong>Skeptic Agent</strong><p>${esc(skepticText)}</p></div></div></section>
    <section class="card"><h2>Evidence passages</h2>${(data.evidence||[]).map(e => `<article class="evidence"><strong>${esc(paperLabel(e.source_paper_id))}</strong><div class="muted">${esc(paperDoi(e.source_paper_id) || e.source_paper_id)}</div><span class="status">${e.evidence_role==='direct_cited_paper'?'DIRECT CITED PAPER':'UPSTREAM REFERENCE'}</span>${e.used_by_agents?'<span class="status">USED BY AGENTS</span>':'<span class="muted">Retrieved but not selected for model context</span>'}<p class="passage">${esc(e.passage)}</p><span class="muted">${esc(e.locator)}</span></article>`).join('') || '<p>No passages retrieved.</p>'}</section>
    <section class="card"><h2>Citation lineage</h2>${(data.citation_chain||[]).map(edge => `<div class="paper"><strong>${esc(paperLabel(edge.citing_paper_id))}</strong><br>↓ cites<br><strong>${esc(paperLabel(edge.cited_paper_id))}</strong><div class="muted">${esc(paperDoi(edge.cited_paper_id))} · ${edge.association_verified?'verified context':'bibliographic edge; context unverified'}</div></div>`).join('') || '<p>No citation edges retrieved.</p>'}</section>
    <section class="card"><h2>Agent execution trace</h2>${(data.execution_trace||[]).map(e => `<div class="event"><strong>${esc(e.agent)} · ${esc(e.status)}</strong><div class="muted">${esc(e.detail)}</div></div>`).join('')}</section>
    <section class="card"><h2>What this investigation could not verify</h2><ul>${(data.limitations||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul></section>`;
  results.classList.remove('hidden');
}
