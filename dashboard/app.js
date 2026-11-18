const STAKEHOLDER_CODE = "MOFA-GULF-DEMO";
let briefsCache = [];
let currentConfig = null;

// All AI-generated and user-submitted text is escaped before being inserted into the page,
// so a malicious feed item or model output can't inject scripts into the dashboard.
function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// Only allow image sources that are https URLs or data:image URIs.
function safeImageSrc(uri) {
  const u = String(uri || "").trim();
  if (u.startsWith("https://") || u.startsWith("data:image/")) return esc(u);
  return "";
}

function pct(x) {
  return Math.round((Number(x) || 0) * 100);
}

function toggleModal(id) {
  document.getElementById(id).classList.toggle("hidden");
}

function badgeColor(priority) {
  const map = {
    CRITICAL: "bg-rose-500/20 text-rose-300 border-rose-500/40",
    HIGH: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    MEDIUM: "bg-sky-500/20 text-sky-300 border-sky-500/40",
    WATCH: "bg-slate-700 text-slate-300 border-slate-600",
  };
  return map[priority] || map.WATCH;
}

async function loadDashboard() {
  const [cfgResp, briefsResp, auditResp] = await Promise.all([
    fetch(`/api/stakeholder/${STAKEHOLDER_CODE}`),
    fetch(`/api/briefs?stakeholder_code=${STAKEHOLDER_CODE}`),
    fetch(`/api/audit-logs`),
  ]);

  if (cfgResp.ok) {
    currentConfig = await cfgResp.json();
    document.getElementById("ministry-title").textContent = currentConfig.ministry_name;
    const editable = { ...currentConfig };
    delete editable.gemini_live_configured;
    document.getElementById("config-json").value = JSON.stringify(editable, null, 2);

    const sdkBadge = document.getElementById("api-status-badge");
    if (currentConfig.gemini_live_configured) {
      sdkBadge.textContent = "Live SDK Ready";
      sdkBadge.className = "px-2 py-0.5 text-xs font-medium rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
    } else {
      sdkBadge.textContent = "Demo Seed Mode (Set GEMINI_API_KEY for Live Runs)";
      sdkBadge.className = "px-2 py-0.5 text-xs font-medium rounded bg-amber-500/20 text-amber-300 border border-amber-500/30";
    }

    const pills = document.getElementById("priority-pills");
    pills.innerHTML = (currentConfig.priority_sectors || [])
      .map(s => `<span class="px-2 py-1 text-xs rounded bg-slate-800 border border-slate-700 text-sky-300">HS ${esc(s.hs_code || s.hs_chapter)}: ${esc(s.name)}</span>`)
      .join("");
    document.getElementById("counterpart-summary").textContent =
      `Counterpart Markets: ${(currentConfig.key_counterpart_markets || []).join(" • ")} | Risk Tolerance: ${currentConfig.risk_tolerance}`;
  }

  if (briefsResp.ok) {
    briefsCache = await briefsResp.json();
    document.getElementById("brief-count").textContent = `${briefsCache.length} Briefs`;
    renderBriefList();
    if (briefsCache.length > 0) {
      selectBrief(briefsCache[0].id);
    }
  }

  if (auditResp.ok) {
    const logs = await auditResp.json();
    document.getElementById("audit-list").innerHTML = logs
      .map(l => `<div class="border-b border-slate-800/80 pb-1"><span class="text-sky-400">[${esc(l.created_at?.slice(0, 19))}]</span> <span class="text-emerald-300">${esc(l.actor)}</span> → ${esc(l.action)} (${esc(l.entity_type)} #${esc(l.entity_id)})</div>`)
      .join("");
  }
}

function reviewColor(status) {
  if (status === "APPROVED") return "text-emerald-400";
  if (status === "REJECTED") return "text-rose-400";
  return "text-amber-300";
}

function renderBriefList() {
  const container = document.getElementById("briefs-list");
  container.innerHTML = briefsCache
    .map(b => `
      <div onclick="selectBrief(${Number(b.id)})" class="p-4 rounded-xl bg-slate-900 hover:bg-slate-800/90 border border-slate-800 cursor-pointer transition space-y-2">
        <div class="flex items-center justify-between gap-2">
          <span class="px-2 py-0.5 text-xs font-bold rounded border ${badgeColor(b.priority_level)}">${esc(b.priority_level)} • Alignment ${esc(b.alignment_score)}/100</span>
          <span class="text-xs ${reviewColor(b.review_status)}">${esc(b.review_status)}</span>
        </div>
        <h3 class="text-sm font-semibold text-white leading-snug">${esc(b.headline)}</h3>
        <div class="flex items-center justify-between text-xs text-slate-400">
          <span>HS ${esc(b.signal.hs_chapter || "N/A")} → ${esc(b.signal.affected_market || "Global")}</span>
          <span>Fact-Check: ${esc(b.verification.verified_status)} (${pct(b.confidence_score)}%)</span>
        </div>
      </div>
    `)
    .join("");
}

function listItems(items) {
  return (items || []).map(i => `<li>${esc(i)}</li>`).join("");
}

function selectBrief(id) {
  const b = briefsCache.find(x => x.id === id);
  if (!b) return;

  const satHtml = b.satellite_observations.length
    ? b.satellite_observations.map(s => `
        <div class="p-3 rounded-lg bg-slate-950 border border-emerald-500/30 text-xs space-y-1">
          <div class="font-semibold text-emerald-300">🛰️ ${esc(s.provider)} — ${esc(s.region_name)}</div>
          <div class="text-slate-300">Metric: <span class="font-mono">${esc(s.metric_type)}</span> = ${esc(s.metric_value)} (<span class="text-rose-400 font-semibold">${esc(s.baseline_delta_pct)}% vs baseline</span>)</div>
          <div class="text-slate-400">Cloud Cover: ${esc(s.cloud_cover_pct)}% | Sensor Confidence: ${pct(s.imagery_confidence)}%</div>
        </div>
      `).join("")
    : `<p class="text-xs text-slate-500">No satellite anomaly attached to this signal.</p>`;

  const evidenceHtml = b.evidence_items.length
    ? b.evidence_items.map(e => {
        const src = safeImageSrc(e.uri_or_path);
        return `
        <div class="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
          <div class="text-xs text-sky-300 font-medium">${esc(e.modality)}: ${esc(e.caption)}</div>
          ${src ? `<img src="${src}" alt="${esc(e.caption)}" class="rounded border border-slate-800 max-h-44" />` : ""}
        </div>`;
      }).join("")
    : "";

  const provenanceHtml = (b.provenance || [])
    .map(p => `<li class="text-xs text-slate-300"><span class="font-semibold text-sky-300">[${esc(p.modality)}]</span> ${esc(p.source)} (${esc(p.timestamp)}) — <span class="text-slate-400">${esc(p.verification_note)}</span></li>`)
    .join("");

  const steps = b.recommended_next_steps || {};

  document.getElementById("brief-detail").innerHTML = `
    <div class="space-y-5">
      <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-4">
        <div>
          <span class="px-2.5 py-1 text-xs font-bold rounded border ${badgeColor(b.priority_level)}">${esc(b.priority_level)} • Alignment ${esc(b.alignment_score)}/100</span>
          <span class="ml-2 text-xs text-slate-400">30d Prob: ${pct(b.signal.prob_30d)}% | 90d Prob: ${pct(b.signal.prob_90d)}%</span>
        </div>
        <div class="text-xs font-semibold px-2.5 py-1 rounded bg-slate-800 text-slate-200">
          Confidence: ${pct(b.confidence_score)}% (${esc(b.verification.verified_status)})
        </div>
      </div>

      <h2 class="text-lg font-bold text-white">${esc(b.headline)}</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        <div class="p-3 rounded-lg bg-slate-950 border border-slate-800">
          <div class="font-semibold text-slate-400 uppercase mb-1">What Changed & Why Now</div>
          <p class="text-slate-200 leading-relaxed">${esc(b.what_changed)}</p>
        </div>
        <div class="p-3 rounded-lg bg-slate-950 border border-slate-800">
          <div class="font-semibold text-slate-400 uppercase mb-1">Quantified Opportunity Window</div>
          <p class="text-emerald-300 leading-relaxed font-medium">${esc(b.quantified_window)}</p>
        </div>
      </div>

      <div class="space-y-2">
        <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400">Multi-Modal & Satellite Verification Layer</h4>
        <p class="text-xs text-slate-300 bg-slate-950 p-3 rounded border border-slate-800">${esc(b.verification.multimodal_evaluation)}</p>
        ${satHtml}
        ${evidenceHtml}
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        <div class="p-3 rounded bg-slate-950 border border-slate-800">
          <div class="font-semibold text-sky-400 mb-1">Diplomatic Track</div>
          <ul class="list-disc list-inside space-y-1 text-slate-300">${listItems(steps.diplomatic)}</ul>
        </div>
        <div class="p-3 rounded bg-slate-950 border border-slate-800">
          <div class="font-semibold text-emerald-400 mb-1">Commercial Track</div>
          <ul class="list-disc list-inside space-y-1 text-slate-300">${listItems(steps.commercial)}</ul>
        </div>
        <div class="p-3 rounded bg-slate-950 border border-slate-800">
          <div class="font-semibold text-amber-400 mb-1">Monitoring Track</div>
          <ul class="list-disc list-inside space-y-1 text-slate-300">${listItems(steps.monitoring)}</ul>
        </div>
      </div>

      <div>
        <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Uncertainties</h4>
        <ul class="list-disc list-inside space-y-1 text-xs text-slate-300 bg-slate-950 p-3 rounded border border-slate-800">${listItems(b.main_uncertainties)}</ul>
      </div>

      <div>
        <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Full Provenance & Corroboration Chain</h4>
        <ul class="space-y-1.5 bg-slate-950 p-3 rounded border border-slate-800">${provenanceHtml}</ul>
      </div>

      <!-- Human-in-the-Loop Governance Gate -->
      <div class="p-4 rounded-xl bg-slate-950 border border-amber-500/30 space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-amber-300">Human-in-the-Loop Governance Gate</span>
          <span class="text-xs font-mono text-slate-300">Status: ${esc(b.review_status)}</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <input id="reviewer-name" type="text" placeholder="Approving Officer Name / Title (required)" value="${esc(b.reviewed_by || "")}" class="flex-1 px-3 py-1.5 text-xs rounded bg-slate-900 border border-slate-700" />
          <button onclick="submitReview(${Number(b.id)}, 'APPROVED')" class="px-3 py-1.5 text-xs font-semibold rounded bg-emerald-600 hover:bg-emerald-500 text-white">Approve Brief</button>
          <button onclick="submitReview(${Number(b.id)}, 'REJECTED')" class="px-3 py-1.5 text-xs font-semibold rounded bg-rose-700 hover:bg-rose-600 text-white">Hold / Reject</button>
        </div>
        <div id="review-feedback" class="text-xs text-rose-300"></div>
      </div>
    </div>
  `;
}

async function submitReview(briefId, decision) {
  const reviewer = document.getElementById("reviewer-name").value.trim();
  const feedback = document.getElementById("review-feedback");
  if (!reviewer) {
    feedback.textContent = "Enter the approving officer's name before recording a decision.";
    return;
  }
  const resp = await fetch(`/api/briefs/${briefId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, reviewer_name: reviewer, notes: `Marked ${decision} via Executive Dashboard` }),
  });
  if (resp.ok) {
    await loadDashboard();
    selectBrief(briefId);
  } else {
    feedback.textContent = "Could not record the decision. Please try again.";
  }
}

async function submitNewSignal() {
  const title = document.getElementById("sig-title").value.trim();
  const feed_source = document.getElementById("sig-source").value.trim() || "Executive Manual Feed";
  const raw_content = document.getElementById("sig-content").value.trim();
  const imgUrl = document.getElementById("sig-image").value.trim();
  const feedback = document.getElementById("ingest-feedback");
  const btn = document.getElementById("ingest-submit-btn");

  if (!title || !raw_content) {
    feedback.textContent = "Please provide both a headline and raw intelligence text.";
    return;
  }

  btn.disabled = true;
  feedback.textContent = "Running Predictive Signal → Multi-Modal Fact-Checker → Strategy Alignment → Synthesis. This can take a minute or two...";

  const evidence_inputs = imgUrl
    ? [{ modality: "DOCUMENT_IMAGE", mime_type: "image/png", uri_or_path: imgUrl, caption: "User-attached visual evidence" }]
    : [];

  try {
    const resp = await fetch("/api/signals/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        raw_content,
        feed_source,
        stakeholder_code: STAKEHOLDER_CODE,
        evidence_inputs,
      }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      feedback.textContent = `Error: ${data.detail || "Pipeline failed"}`;
      return;
    }
    if (!data.brief_id) {
      feedback.textContent = `The fact-checker discarded this signal (status: ${data.status}). No brief was generated.`;
      await loadDashboard();
      return;
    }
    feedback.textContent = "";
    toggleModal("ingest-modal");
    await loadDashboard();
  } catch (err) {
    feedback.textContent = "Network error while running the pipeline.";
  } finally {
    btn.disabled = false;
  }
}

async function saveStakeholderConfig() {
  const feedback = document.getElementById("config-feedback");
  feedback.textContent = "";
  let parsed;
  try {
    parsed = JSON.parse(document.getElementById("config-json").value);
  } catch (err) {
    feedback.textContent = "Invalid JSON in stakeholder configuration.";
    return;
  }
  const resp = await fetch("/api/stakeholder", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(parsed),
  });
  if (resp.ok) {
    toggleModal("config-modal");
    await loadDashboard();
  } else {
    feedback.textContent = "The server rejected this configuration. Check required fields.";
  }
}

loadDashboard();
