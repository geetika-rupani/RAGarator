const app = document.getElementById("app");

const FACTOR_LABELS = {
  top1_similarity: "Top-1 retrieval",
  top3_similarity: "Top-3 retrieval",
  best_retrieval: "Best retrieval",
  chunk_size_suitability: "Chunk size",
  chunk_consistency: "Consistency",
  efficiency: "Efficiency",
};

const COMPARE_METRICS = [
  { key: "avg_top1", label: "Top-1 similarity", format: (v) => v.toFixed(3) },
  { key: "avg_top3", label: "Top-3 similarity", format: (v) => v.toFixed(3) },
  { key: "gold_hit_rate", label: "Gold-span hit rate", format: (v) => pct(v * 100) },
  { key: "avg_chunk_chars", label: "Avg chunk size", format: (v) => `${Math.round(v)} chars` },
  { key: "consistency", label: "Consistency", format: (v) => v.toFixed(3) },
  { key: "efficiency", label: "Efficiency", format: (v) => v.toFixed(3) },
];

const LOAD_STEPS = [
  "Reading and cleaning the document",
  "Applying four chunking strategies",
  "Running grounded retrieval queries",
  "Scoring, ranking, and explaining",
];

const state = {
  file: null,
  loading: false,
  loadStep: 0,
  error: "",
  result: null,
  tab: "why",
  selected: null,
  health: "checking",
};

init();

async function init() {
  render();
  try {
    const response = await fetch("/api/health");
    state.health = response.ok ? "ready" : "down";
  } catch {
    state.health = "down";
  }
  render();
}

function render() {
  const rec = state.result?.recommendation;
  app.innerHTML = `
    <div class="shell">
      ${renderNav()}
      ${renderHero()}
      ${renderUploader()}
      ${state.error ? `<div class="notice error">${escapeHtml(state.error)}</div>` : ""}
      ${state.loading ? renderProgress() : ""}
      ${rec ? renderRecommendation(state.result, rec) : ""}
      <div class="footer">
        <span>Scores are min-max normalized across strategies. Confidence uses margin, stability, and evidence — not the winning score.</span>
        <span>PDF, DOCX, TXT · text-layer documents only</span>
      </div>
    </div>
  `;
  bind();
}

function renderNav() {
  const healthLabel =
    state.health === "ready" ? "Engine ready" : state.health === "down" ? "Engine unreachable" : "Checking engine";
  return `
    <nav class="nav">
      <div class="brand">
        <div class="mark">R</div>
        <div>
          <h1>RAGarator</h1>
          <p>Chunking decision engine</p>
        </div>
      </div>
      <div class="status">
        <span class="dot" style="${state.health === "down" ? "background:#ff7b93;box-shadow:none" : ""}"></span>
        ${healthLabel}
      </div>
    </nav>
  `;
}

function renderHero() {
  return `
    <header class="hero">
      <div>
        <p class="eyebrow">Explainable RAG benchmarking</p>
        <h2>Find the chunking strategy that actually fits <em>this</em> document.</h2>
        <p class="lede">
          Upload a PDF, DOCX, or TXT. RAGarator chunks it four ways, retrieves
          against queries taken from the text itself, then recommends a winner
          with numbers, evidence, and uncertainty — not a generic slogan.
        </p>
      </div>
      <div class="steps">
        <div class="step"><b>01</b> Load and clean the document</div>
        <div class="step"><b>02</b> Chunk with fixed, recursive, sentence, and token windows</div>
        <div class="step"><b>03</b> Retrieve with grounded gold spans</div>
        <div class="step"><b>04</b> Rank with a transparent multi-factor score</div>
      </div>
    </header>
  `;
}

function renderUploader() {
  const file = state.file;
  return `
    <section class="panel dropzone">
      <div class="drop" id="drop" role="button" tabindex="0">
        <h3>${file ? "File ready to analyze" : "Drop a document here"}</h3>
        <p>PDF, DOCX, or TXT. Max 10 MB. Scanned image-only PDFs will not work.</p>
        <div class="chips">
          <span class="chip">Fixed-size</span>
          <span class="chip">Recursive</span>
          <span class="chip">Sentence</span>
          <span class="chip">Token</span>
        </div>
        ${
          file
            ? `<div class="filechip">
                <div>
                  <strong>${escapeHtml(file.name)}</strong>
                  <span>${formatBytes(file.size)}</span>
                </div>
                <button class="btn btn-ghost" type="button" id="clear-file">Remove</button>
              </div>`
            : ""
        }
        <input id="file" type="file" accept=".pdf,.docx,.txt,application/pdf,text/plain" hidden />
      </div>
      <div class="actions">
        <button class="btn btn-primary" id="run" ${state.loading || !file ? "disabled" : ""}>
          ${state.loading ? "Analyzing…" : "Analyze chunking"}
        </button>
        <button class="btn btn-ghost" id="sample" ${state.loading ? "disabled" : ""}>Try the sample memo</button>
      </div>
    </section>
  `;
}

function renderProgress() {
  return `
    <section class="panel progress">
      <div class="bar"><span></span></div>
      ${LOAD_STEPS.map(
        (label, index) => `
        <div class="progress-row ${index < state.loadStep ? "done" : index === state.loadStep ? "active" : ""}">
          <span class="pulse"></span>
          ${escapeHtml(label)}
        </div>`
      ).join("")}
    </section>
  `;
}

function renderRecommendation(result, rec) {
  const selectedKey = state.selected || rec.recommended_strategy;
  const selectedScore = rec.scores[selectedKey];
  const conf = rec.confidence;
  const maxScore = Math.max(...rec.ranking.map((row) => row.score), 0.0001);
  const circumference = 2 * Math.PI * 46;
  const dash = (conf.percentage / 100) * circumference;

  return `
    <section class="panel rec">
      <div class="gauge" aria-label="Confidence ${conf.percentage} percent">
        <svg viewBox="0 0 108 108">
          <circle cx="54" cy="54" r="46" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="8"></circle>
          <circle cx="54" cy="54" r="46" fill="none" stroke="#3ee0c5" stroke-width="8"
            stroke-linecap="round"
            stroke-dasharray="${dash} ${circumference}"></circle>
        </svg>
        <div class="gauge-copy">
          <b>${conf.percentage.toFixed(0)}%</b>
          <span>${escapeHtml(conf.level)}</span>
        </div>
      </div>
      <div>
        <div class="badge ${escapeHtml(conf.level)}">Recommended</div>
        <h3>${escapeHtml(rec.recommended_label)}</h3>
        <p class="meta">${escapeHtml(conf.summary)}</p>
      </div>
      <div class="stats">
        <div class="stat"><span>Document</span><b>${formatNumber(result.document.char_count)}c</b></div>
        <div class="stat"><span>Queries</span><b>${result.queries.length}</b></div>
        <div class="stat"><span>Margin</span><b>${conf.margin.toFixed(3)}</b></div>
        <div class="stat"><span>Sentences</span><b>${result.document.sentence_count}</b></div>
      </div>
    </section>

    <div class="rank-grid">
      ${rec.ranking
        .map((row) => {
          const active = row.strategy === selectedKey ? "active" : "";
          const width = Math.max(8, (row.score / maxScore) * 100);
          return `
            <button class="panel rank-card ${active}" data-strategy="${row.strategy}" type="button">
              <div class="top">
                <h4>${escapeHtml(row.label)}</h4>
                <span class="place">#${row.rank}</span>
              </div>
              <div class="score">${row.score.toFixed(3)}</div>
              <div class="meter"><span style="width:${width}%"></span></div>
              <p>Top-1 ${row.avg_top1.toFixed(3)} · ${row.chunk_count} chunks · ${Math.round(row.avg_chunk_chars)} chars</p>
            </button>`;
        })
        .join("")}
    </div>

    <div class="tabs">
      ${tabButton("why", "Why this winner")}
      ${tabButton("compare", "Compare factors")}
      ${tabButton("evidence", "Evidence")}
      ${tabButton("uncertainty", "Uncertainty")}
      ${tabButton("document", "Document & queries")}
    </div>

    <section class="panel body">
      ${renderTab(result, rec, selectedScore)}
    </section>
  `;
}

function tabButton(id, label) {
  return `<button class="tab ${state.tab === id ? "active" : ""}" data-tab="${id}" type="button">${label}</button>`;
}

function renderTab(result, rec, selectedScore) {
  if (state.tab === "compare") return renderCompare(rec, selectedScore);
  if (state.tab === "evidence") return renderEvidence(rec);
  if (state.tab === "uncertainty") return renderUncertainty(rec);
  if (state.tab === "document") return renderDocument(result);
  return renderWhy(rec, selectedScore);
}

function renderWhy(rec, selectedScore) {
  const factors = selectedScore
    ? Object.values(selectedScore.factors).sort((a, b) => b.weighted - a.weighted)
    : [];
  return `
    <div class="split">
      <div>
        <h3 class="section">Why ${escapeHtml(rec.recommended_label)} won</h3>
        <ol class="reasons">
          ${rec.reasons.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
        </ol>
      </div>
      <div>
        <h3 class="section">${escapeHtml(selectedScore?.label || "Strategy")} factor mix</h3>
        ${factors
          .map((factor) => {
            const width = Math.round(factor.normalized * 100);
            return `
              <div class="factor">
                <div class="factor-head">
                  <b>${FACTOR_LABELS[factor.name] || factor.name}</b>
                  <span>raw ${factor.raw.toFixed(3)} · w ${factor.weighted.toFixed(3)}</span>
                </div>
                <div class="meter"><span style="width:${width}%"></span></div>
              </div>`;
          })
          .join("")}
        <p class="meta" style="margin-top:12px">Bars show min-max normalized values across the four strategies. Click a ranking card to inspect another strategy.</p>
      </div>
    </div>
  `;
}

function renderCompare(rec) {
  const order = rec.ranking.map((row) => row.strategy);
  return `
    <h3 class="section">Same document, four strategies</h3>
    <div class="compare">
      ${COMPARE_METRICS.map((metric) => {
        const values = order.map((key) => rec.scores[key].metrics[metric.key]);
        const max = Math.max(...values.map((value) => Math.abs(value)), 0.0001);
        return `
          <div class="compare-row">
            <div class="compare-label">${metric.label}</div>
            <div class="lanes">
              ${order
                .map((key, index) => {
                  const value = rec.scores[key].metrics[metric.key];
                  const width = Math.max(6, (value / max) * 100);
                  return `
                    <div class="lane">
                      <span class="name">${escapeHtml(rec.scores[key].label)}</span>
                      <div class="meter"><span style="width:${width}%;opacity:${index === 0 ? 1 : 0.7}"></span></div>
                      <span class="val">${metric.format(value)}</span>
                    </div>`;
                })
                .join("")}
            </div>
          </div>`;
      }).join("")}
    </div>
  `;
}

function renderEvidence(rec) {
  if (!rec.evidence.length) {
    return `<p class="meta">No retrieved spans were distinctive enough to quote.</p>`;
  }
  return `
    <h3 class="section">Retrieved spans from this document</h3>
    <div class="evidence">
      ${rec.evidence
        .map(
          (item) => `
        <article class="panel evidence-card">
          <p class="q">${escapeHtml(item.query)}</p>
          <p class="meta">${escapeHtml(item.note)}</p>
          <div class="pair">
            <div class="spanbox">
              <div class="lbl">Winner · ${item.winner_similarity.toFixed(3)}</div>
              ${escapeHtml(item.winner_preview || "—")}
            </div>
            <div class="spanbox">
              <div class="lbl">${item.runner_up_similarity != null ? `Runner-up · ${item.runner_up_similarity.toFixed(3)}` : "Gold excerpt"}</div>
              ${escapeHtml(item.runner_up_preview || item.gold_excerpt || "—")}
            </div>
          </div>
        </article>`
        )
        .join("")}
    </div>
    ${
      rec.trade_offs.length
        ? `<h3 class="section" style="margin-top:22px">Trade-offs</h3>
           <ul class="note-list">${rec.trade_offs
             .map((item) => `<li><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.detail)}</small></li>`)
             .join("")}</ul>`
        : ""
    }
  `;
}

function renderUncertainty(rec) {
  return `
    <div class="split">
      <div>
        <h3 class="section">Why confidence is ${escapeHtml(rec.confidence.level)}</h3>
        <ul class="note-list">
          ${rec.uncertainty
            .map(
              (item) => `
            <li>
              <strong class="${item.severity === "high" ? "warn" : ""}">${escapeHtml(item.severity)}</strong>
              <small>${escapeHtml(item.statement)}</small>
            </li>`
            )
            .join("")}
        </ul>
      </div>
      <div>
        <h3 class="section">Calibration signals</h3>
        <div class="stats" style="grid-template-columns:1fr">
          <div class="stat"><span>Ranking stability</span><b>${rec.confidence.ranking_stability.toFixed(2)}</b></div>
          <div class="stat"><span>Evidence quality</span><b>${rec.confidence.evidence_quality.toFixed(2)}</b></div>
          <div class="stat"><span>Score margin</span><b>${rec.confidence.margin.toFixed(3)}</b></div>
        </div>
        ${
          rec.caveats.length
            ? `<h3 class="section" style="margin-top:18px">Caveats</h3>
               <ul class="note-list">${rec.caveats
                 .map((item) => `<li><small>${escapeHtml(item)}</small></li>`)
                 .join("")}</ul>`
            : ""
        }
      </div>
    </div>
  `;
}

function renderDocument(result) {
  const doc = result.document;
  return `
    <div class="split">
      <div>
        <h3 class="section">${escapeHtml(doc.filename)}</h3>
        <div class="stats" style="grid-template-columns:repeat(2,1fr);margin-bottom:16px">
          <div class="stat"><span>Characters</span><b>${formatNumber(doc.char_count)}</b></div>
          <div class="stat"><span>Words</span><b>${formatNumber(doc.word_count)}</b></div>
          <div class="stat"><span>Paragraphs</span><b>${doc.paragraph_count}</b></div>
          <div class="stat"><span>Headings</span><b>${doc.heading_count}</b></div>
        </div>
        <div class="spanbox">
          <div class="lbl">Preview</div>
          ${escapeHtml(doc.preview)}
        </div>
      </div>
      <div>
        <h3 class="section">Grounded benchmark queries</h3>
        <ul class="query-list">
          ${result.queries
            .map(
              (query) => `
            <li>
              ${escapeHtml(query.query)}
              <small>Gold: ${escapeHtml(query.gold_excerpt)}</small>
            </li>`
            )
            .join("")}
        </ul>
      </div>
    </div>
  `;
}

function bind() {
  const drop = document.getElementById("drop");
  const input = document.getElementById("file");
  const run = document.getElementById("run");
  const sample = document.getElementById("sample");
  const clear = document.getElementById("clear-file");

  drop?.addEventListener("click", (event) => {
    if (event.target.closest("button")) return;
    input?.click();
  });
  drop?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      input?.click();
    }
  });
  drop?.addEventListener("dragover", (event) => {
    event.preventDefault();
    drop.classList.add("hot");
  });
  drop?.addEventListener("dragleave", () => drop.classList.remove("hot"));
  drop?.addEventListener("drop", (event) => {
    event.preventDefault();
    drop.classList.remove("hot");
    const next = event.dataTransfer.files?.[0];
    if (next) setFile(next);
  });
  input?.addEventListener("change", (event) => {
    const next = event.target.files?.[0];
    if (next) setFile(next);
  });
  clear?.addEventListener("click", (event) => {
    event.stopPropagation();
    state.file = null;
    state.error = "";
    render();
  });
  run?.addEventListener("click", () => analyze());
  sample?.addEventListener("click", loadSample);

  document.querySelectorAll("[data-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.tab = button.getAttribute("data-tab");
      render();
    });
  });
  document.querySelectorAll("[data-strategy]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selected = button.getAttribute("data-strategy");
      if (state.tab === "evidence" || state.tab === "document") state.tab = "why";
      render();
    });
  });
}

function setFile(file) {
  const allowed = [".pdf", ".docx", ".txt"];
  const name = file.name.toLowerCase();
  if (!allowed.some((ext) => name.endsWith(ext))) {
    state.error = "Please upload a PDF, DOCX, or TXT file.";
    state.file = null;
    render();
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    state.error = "That file is larger than 10 MB.";
    state.file = null;
    render();
    return;
  }
  state.file = file;
  state.error = "";
  render();
}

async function loadSample() {
  try {
    const response = await fetch("/sample.txt");
    if (!response.ok) throw new Error("Sample document is unavailable.");
    const blob = await response.blob();
    const file = new File([blob], "rag_methods.txt", { type: "text/plain" });
    state.file = file;
    state.error = "";
    await analyze();
  } catch (error) {
    state.error = error.message || "Could not load the sample document.";
    render();
  }
}

async function analyze() {
  if (!state.file) return;
  state.loading = true;
  state.loadStep = 0;
  state.error = "";
  state.result = null;
  state.selected = null;
  state.tab = "why";
  render();

  const timer = setInterval(() => {
    state.loadStep = Math.min(state.loadStep + 1, LOAD_STEPS.length - 1);
    const rows = document.querySelectorAll(".progress-row");
    rows.forEach((row, index) => {
      row.classList.toggle("done", index < state.loadStep);
      row.classList.toggle("active", index === state.loadStep);
    });
  }, 700);

  try {
    const body = new FormData();
    body.append("file", state.file);
    const uploaded = await fetch("/api/upload", { method: "POST", body });
    const uploadJson = await readJson(uploaded);
    if (!uploaded.ok) throw new Error(detailMessage(uploadJson, "Upload failed."));
    state.loadStep = 2;
    const analyzed = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_id: uploadJson.file_id }),
    });
    const analyzeJson = await readJson(analyzed);
    if (!analyzed.ok) throw new Error(detailMessage(analyzeJson, "Analysis failed."));
    state.result = analyzeJson;
    state.selected = analyzeJson.recommendation.recommended_strategy;
    state.loadStep = LOAD_STEPS.length - 1;
  } catch (error) {
    state.error = error.message || String(error);
  } finally {
    clearInterval(timer);
    state.loading = false;
    render();
    if (state.result) {
      document.querySelector(".rec")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }
}

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function detailMessage(payload, fallback) {
  const detail = payload?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  return fallback;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function pct(value) {
  return `${Math.round(value)}%`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
