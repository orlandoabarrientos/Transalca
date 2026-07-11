(function () {
  'use strict';
  const API = '/api/asistente';
  const byId = (id) => document.getElementById(id);
  const text = (value) => String(value == null ? '' : value);

  async function request(path, options) {
    const response = await fetch(API + path, {
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.message || `HTTP ${response.status}`);
    return data;
  }

  function cell(value) {
    const td = document.createElement('td');
    td.textContent = text(value);
    return td;
  }

  function renderSummary(data) {
    const root = byId('summary');
    root.textContent = '';
    const values = [
      ['Modelo activo', data.active_version || 'sin registrar'],
      ['Pendientes', data.feedback && data.feedback.pending || 0],
      ['Aprobados', data.feedback && data.feedback.approved || 0],
      ['Rechazados', data.feedback && data.feedback.rejected || 0],
      ['Promociones', data.models && data.models.promotions || 0],
      ['Rollbacks', data.models && data.models.rollbacks || 0],
    ];
    values.forEach(([label, value]) => {
      const card = document.createElement('div'); card.className = 'card';
      const span = document.createElement('span'); span.textContent = label;
      const strong = document.createElement('strong'); strong.textContent = text(value);
      card.append(span, strong); root.appendChild(card);
    });
  }

  async function act(caseId, action) {
    const correction = action === 'approve' ? {
      intent: window.prompt('Intención principal correcta (obligatoria):', '') || '',
      category: window.prompt('Categoría:', 'continuous_learning_reviewed') || '',
      expected_behavior: window.prompt('Comportamiento esperado:', '') || '',
    } : {};
    if (action === 'approve' && (!correction.intent || !correction.expected_behavior)) {
      byId('notice').textContent = 'Aprobación cancelada: faltan correcciones obligatorias.'; return;
    }
    await request(`/learning-cases/${encodeURIComponent(caseId)}/${action}`, {
      method: 'POST', body: JSON.stringify({ ...correction, confirm: true }),
    });
    await load();
  }

  function renderCases(rows) {
    const body = byId('cases'); body.textContent = '';
    (rows || []).forEach((item) => {
      const tr = document.createElement('tr');
      tr.appendChild(cell(item.case_id));
      const reasons = document.createElement('td');
      (item.candidate_reason || []).forEach((reason) => { const badge=document.createElement('span'); badge.className='badge'; badge.textContent=text(reason); reasons.appendChild(badge); });
      tr.appendChild(reasons);
      tr.appendChild(cell(item.intent_predicted));
      tr.appendChild(cell(item.message_anonymized));
      const actions = document.createElement('td'); actions.className = 'actions';
      [['approve','Aprobar',''],['needs-edit','Editar','secondary'],['reject','Rechazar','danger']].forEach(([action,label,style]) => {
        const button=document.createElement('button'); button.type='button'; button.textContent=label; if(style) button.className=style;
        button.addEventListener('click', () => act(item.case_id, action).catch(showError)); actions.appendChild(button);
      });
      tr.appendChild(actions); body.appendChild(tr);
    });
  }

  function renderModels(rows) {
    const root = byId('models'); root.textContent = '';
    (rows || []).forEach((item) => {
      const row=document.createElement('div'); row.className='model';
      const info=document.createElement('div');
      const title=document.createElement('strong'); title.textContent=`${text(item.version)} · ${text(item.status)}`;
      const detail=document.createElement('div'); detail.textContent=`dataset ${text(item.dataset_hash).slice(0,12)} · score ${text(item.composite_score)}`;
      info.append(title,detail); row.appendChild(info);
      root.appendChild(row);
    });
  }

  function showError(error) { byId('notice').textContent = `No se pudo completar: ${text(error.message)}`; }

  async function load() {
    byId('notice').textContent = 'Actualizando…';
    const [metrics, cases] = await Promise.all([request('/learning-metrics'), request('/learning-cases?status=pending_review')]);
    renderSummary(metrics); renderCases(cases.cases || []); renderModels(metrics.model_versions || []);
    byId('notice').textContent = 'Datos anonimizados y métricas actualizados.';
  }

  byId('refresh').addEventListener('click', () => load().catch(showError));
  load().catch(showError);
})();
