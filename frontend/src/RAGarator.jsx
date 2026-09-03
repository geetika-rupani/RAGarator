import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Upload, FileText, ChevronDown, ChevronUp, RotateCcw, ArrowRight,
  CircleCheck, Circle, Loader2, TriangleAlert, ScanLine, FileWarning,
  AlertOctagon,
} from "lucide-react";

/* ---------------------------------------------------------------------- */
/* Design tokens — unchanged from the original design                     */
/* ---------------------------------------------------------------------- */

const C = {
  bg: "#0B0D10",
  panel: "#12151A",
  panel2: "#171B21",
  raised: "#1C2129",
  border: "#262B33",
  borderFaint: "#1B1F26",
  text: "#E9EBEE",
  textMute: "#98A1AC",
  textFaint: "#5B636D",
  signal: "#4FB8AE",
  signalDim: "#2E4A47",
  decision: "#E8A33D",
  decisionDim: "#4A3C24",
  alert: "#D9694F",
  alertDim: "#472E27",
};

const FONTS = (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    .rgx-display { font-family: 'Space Grotesk', system-ui, sans-serif; }
    .rgx-mono { font-family: 'JetBrains Mono', 'SF Mono', monospace; }
    .rgx-range { -webkit-appearance: none; appearance: none; width: 100%; height: 3px; border-radius: 2px; background: ${C.border}; display: block; }
    .rgx-range::-webkit-slider-thumb { -webkit-appearance: none; width: 13px; height: 13px; border-radius: 50%; background: ${C.decision}; cursor: pointer; border: 2px solid #0B0D10; margin-top: -5px; }
    .rgx-range::-webkit-slider-runnable-track { height: 3px; border-radius: 2px; background: ${C.border}; }
    .rgx-range::-moz-range-thumb { width: 13px; height: 13px; border-radius: 50%; background: ${C.decision}; cursor: pointer; border: 2px solid #0B0D10; }
    .rgx-range::-moz-range-track { height: 3px; border-radius: 2px; background: ${C.border}; }
    .rgx-fade-in { animation: rgxFadeIn 0.4s ease both; }
    @keyframes rgxFadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
    .rgx-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
    .rgx-scroll::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 3px; }
    .rgx-spin { animation: rgxSpin 0.9s linear infinite; }
    @keyframes rgxSpin { to { transform: rotate(360deg); } }
  `}</style>
);

/* ========================================================================
   BACKEND API CONTRACT
   ------------------------------------------------------------------------
   This is the shape the frontend expects. Nothing below this comment
   block computes scores, rankings, or explanations — that all comes from
   the backend response. The frontend only visualizes it and (optionally)
   recomputes a disclosed, simple weighted-average for the "what-if"
   sliders — see the note in <RankingPanel>.

   POST {API_BASE_URL}/analyze                (multipart/form-data, field "file")
     -> 202 { jobId: string }

   GET {API_BASE_URL}/analyze/:jobId/status
     -> {
          status: "queued" | "processing" | "complete" | "error",
          stage: string | null,        // one of STAGE_ORDER below
          logs: string[],              // cumulative human-readable log lines
          error: string | null         // present when status === "error"
        }

   GET {API_BASE_URL}/analyze/:jobId/result    // only once status === "complete"
     -> {
          document: { name, sizeLabel, pageCount, chunkCount },
          defaultWeights: { retrieval, quality, consistency, efficiency }, // sums to 100
          recommendedStrategyId: string,
          confidence: { label: string, gap: number, detail: string },
          evidenceQuery: string,
          strategies: [
            {
              id, name, tag,
              overall: number,                    // 0-100, at defaultWeights
              dims: { retrieval, quality, consistency, efficiency }, // each 0-100
              raw: { recall5, mrr, coherence, boundary, variance, embedTimeSec, avgChunks, avgTokens },
              evidence: { clean: boolean, text: string }
            }
          ],
          reasoning: string[],          // explanation bullets for recommendedStrategyId
          uncertainty: { summary: string },
          tradeoffs: { rows: [ { label: string, values: { [strategyId]: string } } ] }
        }
   ======================================================================== */

const API_BASE_URL = "https://ragarator-api.onrender.com/api";
const USE_MOCK_API = false;

const STAGE_META = {
  upload: "Ingesting document",
  extract: "Extracting text",
  clean: "Cleaning text",
  chunk: "Running chunking strategies",
  embed: "Generating embeddings",
  retrieve: "Benchmarking retrieval",
  evaluate: "Scoring quality & consistency",
  decide: "Running Decision Engine",
};
const STAGE_ORDER = Object.keys(STAGE_META);

async function safeErrorMessage(res, fallback) {
  try {
    const body = await res.json();
    const detail = body?.detail;
    if (typeof detail === "string") return detail;
    return detail?.error || detail?.message || body?.error || body?.message || fallback;
  } catch {
    return `${fallback} (${res.status})`;
  }
}

/* ---- real backend calls ---- */
async function realAnalyzeDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE_URL}/analyze`, { method: "POST", body: formData });
  if (!res.ok) throw new Error(await safeErrorMessage(res, "Upload failed"));
  return res.json();
}
async function realGetStatus(jobId) {
  const res = await fetch(`${API_BASE_URL}/analyze/${jobId}/status`);
  if (!res.ok) throw new Error(await safeErrorMessage(res, "Couldn't fetch job status"));
  return res.json();
}
async function realGetResult(jobId) {
  const res = await fetch(`${API_BASE_URL}/analyze/${jobId}/result`);
  if (!res.ok) throw new Error(await safeErrorMessage(res, "Couldn't fetch results"));
  return res.json();
}

/* ---- mock backend (stand-in until the real API is live) ----
   Delete this block and flip USE_MOCK_API to false once the endpoints
   above exist. It returns data in exactly the same shape a real call
   would, so no other code needs to change. */
const mockJobs = new Map();

function buildMockResult(fileMeta) {
  const strategies = [
    { id: "recursive", name: "Recursive Character", tag: "structure-aware",
      dims: { retrieval: 91, quality: 88, consistency: 92, efficiency: 64 },
      raw: { recall5: 0.91, mrr: 0.83, coherence: 0.88, boundary: 0.85, variance: 0.04, embedTimeSec: 3.2, avgChunks: 268, avgTokens: 412 },
      evidence: { clean: true, text: "Meridian Robotics reported Q3 revenue of $184.2 million, a 22% increase year-over-year, driven primarily by expansion in the industrial automation segment. Management attributed the growth to three new manufacturing contracts signed in July." } },
    { id: "sentence", name: "Sentence-based", tag: "linguistic split",
      dims: { retrieval: 86, quality: 91, consistency: 87, efficiency: 58 },
      raw: { recall5: 0.86, mrr: 0.79, coherence: 0.91, boundary: 0.93, variance: 0.07, embedTimeSec: 4.1, avgChunks: 412, avgTokens: 187 },
      evidence: { clean: true, text: "Total revenue for the third quarter reached $184.2 million, up 22% from the same period last year." } },
    { id: "token", name: "Token-based", tag: "fixed token window",
      dims: { retrieval: 84, quality: 72, consistency: 90, efficiency: 82 },
      raw: { recall5: 0.84, mrr: 0.77, coherence: 0.72, boundary: 0.58, variance: 0.05, embedTimeSec: 2.1, avgChunks: 301, avgTokens: 256 },
      evidence: { clean: false, text: "\u22EF revenue of $184.2 million, a 22% increase year-over-\u22EF\u22EF ear, driven primarily by expansion in industrial autom-\u22EF" } },
    { id: "fixed", name: "Fixed-size", tag: "character window",
      dims: { retrieval: 77, quality: 61, consistency: 71, efficiency: 88 },
      raw: { recall5: 0.77, mrr: 0.68, coherence: 0.61, boundary: 0.49, variance: 0.11, embedTimeSec: 1.8, avgChunks: 289, avgTokens: 256 },
      evidence: { clean: false, text: "\u22EFent. In Q2, the company had reported $151.0M in revenue also across th\u22EF\u22EFree main segments: industrial automation, logistics robotics, and consu-\u22EF" } },
  ];
  const weights = { retrieval: 40, quality: 25, consistency: 20, efficiency: 15 };
  const withOverall = strategies.map((s) => ({
    ...s,
    overall: (s.dims.retrieval * weights.retrieval + s.dims.quality * weights.quality +
      s.dims.consistency * weights.consistency + s.dims.efficiency * weights.efficiency) / 100,
  })).sort((a, b) => b.overall - a.overall);
  const gap = withOverall[0].overall - withOverall[1].overall;

  return {
    document: { name: fileMeta.name, sizeLabel: fileMeta.sizeLabel, pageCount: 42, chunkCount: 1270 },
    defaultWeights: weights,
    recommendedStrategyId: withOverall[0].id,
    confidence: {
      label: gap > 6 ? "Moderate-high confidence" : gap > 2 ? "Moderate confidence" : "Low confidence",
      gap,
      detail: gap > 6 ? "clear but not dominant margin" : "a close contest",
    },
    evidenceQuery: "What was the year-over-year revenue growth in Q3?",
    strategies: withOverall,
    reasoning: [
      `Boundary alignment: ${withOverall[0].name} scored ${withOverall[0].raw.boundary.toFixed(2)} on boundary alignment, the highest of any strategy — it followed this document's nested heading structure instead of cutting mid-section.`,
      `Retrieval accuracy: the correct passage appeared in the top 5 results for ${(withOverall[0].raw.recall5 * 100).toFixed(0)}% of test queries (recall@5 = ${withOverall[0].raw.recall5.toFixed(2)}).`,
      `Stability: across 20 repeated query runs, variance stayed at σ = ${withOverall[0].raw.variance.toFixed(2)}, meaning results didn't swing much with query phrasing.`,
      `Cost: ${withOverall[0].name} took ${withOverall[0].raw.embedTimeSec.toFixed(1)}s to embed this document — a real cost the engine weighed against its quality gains.`,
    ],
    uncertainty: {
      summary: `${withOverall[0].name} leads ${withOverall[1].name} by ${gap.toFixed(1)} points under the default weighting, driven mostly by retrieval and boundary alignment — dimensions this document's structured headings favor. If chunk quality were weighted above retrieval, ${withOverall[1].name} closes most of the gap. Try the sliders below to explore that.`,
    },
    tradeoffs: {
      rows: [
        { label: "Best for", values: { recursive: "Structured docs with headings", sentence: "Prose-heavy, few headers", token: "Speed-sensitive pipelines", fixed: "Quick prototyping only" } },
        { label: "Weak point", values: { recursive: "Slower to embed", sentence: "Loses cross-sentence context", token: "Cuts through sentences", fixed: "Ignores structure entirely" } },
        { label: "Avg. chunk size", values: { recursive: "412 tokens", sentence: "187 tokens", token: "256 tokens", fixed: "256 tokens" } },
      ],
    },
  };
}

async function mockAnalyzeDocument(file) {
  await new Promise((r) => setTimeout(r, 450));
  const jobId = `mock-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const sizeLabel = file.size > 1024 * 1024
    ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
    : `${Math.max(1, Math.round(file.size / 1024))} KB`;
  mockJobs.set(jobId, { startedAt: Date.now(), fileMeta: { name: file.name, sizeLabel } });
  return { jobId };
}
async function mockGetStatus(jobId) {
  await new Promise((r) => setTimeout(r, 250));
  const job = mockJobs.get(jobId);
  if (!job) throw new Error("Unknown job id");
  const stageMs = 650;
  const elapsed = Date.now() - job.startedAt;
  const idx = Math.floor(elapsed / stageMs);
  const logsFor = (i) => `${STAGE_META[STAGE_ORDER[i]]} — done`;
  if (idx >= STAGE_ORDER.length) {
    return { status: "complete", stage: null, logs: STAGE_ORDER.map((_, i) => logsFor(i)), error: null };
  }
  return {
    status: "processing",
    stage: STAGE_ORDER[idx],
    logs: STAGE_ORDER.slice(0, idx).map((_, i) => logsFor(i)).concat([`${STAGE_META[STAGE_ORDER[idx]]}…`]),
    error: null,
  };
}
async function mockGetResult(jobId) {
  await new Promise((r) => setTimeout(r, 300));
  const job = mockJobs.get(jobId);
  if (!job) throw new Error("Unknown job id");
  return buildMockResult(job.fileMeta);
}

const apiAnalyzeDocument = USE_MOCK_API ? mockAnalyzeDocument : realAnalyzeDocument;
const apiGetStatus = USE_MOCK_API ? mockGetStatus : realGetStatus;
const apiGetResult = USE_MOCK_API ? mockGetResult : realGetResult;

/* ---------------------------------------------------------------------- */
/* Small building blocks — unchanged                                      */
/* ---------------------------------------------------------------------- */

function SectionLabel({ index, children }) {
  return (
    <div className="flex items-center gap-3 mb-4 min-w-0">
      {index != null && <span className="rgx-mono text-xs shrink-0" style={{ color: C.textFaint }}>{index}</span>}
      <span className="rgx-display text-sm font-medium tracking-tight shrink-0" style={{ color: C.textMute }}>{children}</span>
      <span className="flex-1 h-px min-w-4" style={{ background: C.borderFaint }} />
    </div>
  );
}

function Bar({ value, max = 100, color, track = C.border, height = 8 }) {
  return (
    <div style={{ background: track, height, borderRadius: height }}>
      <div style={{
        width: `${Math.max(0, Math.min(100, (value / max) * 100))}%`,
        background: color, height, borderRadius: height, transition: "width 0.5s ease",
      }} />
    </div>
  );
}

function WeightSlider({ label, desc, value, onChange, color }) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="text-sm" style={{ color: C.text }}>{label}</span>
        <span className="rgx-mono text-xs" style={{ color }}>{value}%</span>
      </div>
      <input type="range" min={0} max={100} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="rgx-range w-full" style={{ accentColor: color }} />
      <p className="text-xs mt-1" style={{ color: C.textFaint }}>{desc}</p>
    </div>
  );
}

const DIM_META = {
  retrieval: { label: "Retrieval quality", desc: "recall@5 & MRR" },
  quality: { label: "Chunk quality", desc: "coherence & boundaries" },
  consistency: { label: "Consistency", desc: "cross-query variance" },
  efficiency: { label: "Efficiency", desc: "embed time & overhead" },
};

/* ---------------------------------------------------------------------- */
/* Upload screen                                                          */
/* ---------------------------------------------------------------------- */

const ACCEPTED_EXT = [".pdf", ".docx", ".txt"];

function UploadScreen({ onFile, uploading, uploadError }) {
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState(null);
  const inputRef = useRef(null);

  const validate = (f) => {
    if (!f) return "No file selected.";
    const okExt = ACCEPTED_EXT.some((ext) => f.name.toLowerCase().endsWith(ext));
    if (!okExt) return "Unsupported file type. Upload a PDF, DOCX, or TXT file.";
    if (f.size > 50 * 1024 * 1024) return "File is larger than 50 MB.";
    return null;
  };

  const pick = (f) => {
    const err = validate(f);
    if (err) { setLocalError(err); return; }
    setLocalError(null);
    onFile(f);
  };

  const loadSampleFile = async () => {
    const res = await fetch("/sample.txt");
    if (!res.ok) throw new Error("Sample document is unavailable.");
    const blob = await res.blob();
    return new File([blob], "rag_methods.txt", { type: "text/plain" });
  };

  const error = localError || uploadError;

  return (
    <div className="min-h-[calc(100vh-57px)] flex flex-col items-center justify-center px-6 py-16">
      <div className="w-full max-w-xl rgx-fade-in">
        <div className="mb-10 text-center">
          <div className="inline-flex items-center gap-2 rgx-mono text-xs mb-4 px-2.5 py-1 rounded-full" style={{ color: C.signal, background: C.signalDim, border: `1px solid ${C.signal}33` }}>
            <ScanLine size={12} /> chunking benchmark
          </div>
          <h1 className="rgx-display text-3xl font-semibold mb-2" style={{ color: C.text }}>
            Which chunking strategy actually fits this document?
          </h1>
          <p className="text-sm max-w-md mx-auto" style={{ color: C.textMute }}>
            Upload a file and RAGarator will run it through four chunking strategies,
            benchmark retrieval on each, and explain which one wins — and why.
          </p>
        </div>

        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); pick(e.dataTransfer.files?.[0]); }}
          onClick={() => !uploading && inputRef.current?.click()}
          className="rounded-lg px-8 py-14 flex flex-col items-center gap-4 transition-colors"
          style={{
            border: `1.5px dashed ${dragging ? C.decision : error ? C.alert : C.border}`,
            background: dragging ? C.decisionDim + "22" : C.panel,
            cursor: uploading ? "wait" : "pointer",
            opacity: uploading ? 0.6 : 1,
          }}
        >
          <input ref={inputRef} type="file" accept={ACCEPTED_EXT.join(",")} className="hidden"
            onChange={(e) => pick(e.target.files?.[0])} disabled={uploading} />
          <div className="w-11 h-11 rounded-full flex items-center justify-center" style={{ background: C.raised }}>
            {uploading
              ? <Loader2 size={18} className="rgx-spin" style={{ color: C.decision }} />
              : <Upload size={18} style={{ color: C.decision }} />}
          </div>
          <div className="text-center">
            <p className="text-sm" style={{ color: C.text }}>
              {uploading ? "Uploading…" : "Drop a document, or click to browse"}
            </p>
            <p className="rgx-mono text-xs mt-1.5" style={{ color: C.textFaint }}>PDF · DOCX · TXT · up to 50 MB</p>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 mt-3 text-xs rgx-fade-in" style={{ color: C.alert }}>
            <AlertOctagon size={13} /> {error}
          </div>
        )}

        <button
          onClick={async () => {
            try {
              pick(await loadSampleFile());
            } catch (err) {
              setLocalError(err.message || "Could not load the sample document.");
            }
          }}
          disabled={uploading}
          className="w-full mt-4 text-xs rgx-mono py-2.5 rounded-md transition-colors"
          style={{ color: C.textMute, border: `1px solid ${C.borderFaint}`, background: "transparent", opacity: uploading ? 0.5 : 1 }}
        >
          or try a sample technical memo →
        </button>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------- */
/* Processing screen — driven entirely by backend status polls            */
/* ---------------------------------------------------------------------- */

function ProcessingScreen({ fileName, status }) {
  const logRef = useRef(null);
  const logs = status?.logs || [];
  const currentStage = status?.stage;
  const currentIdx = currentStage ? STAGE_ORDER.indexOf(currentStage) : STAGE_ORDER.length;

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [logs.length]);

  return (
    <div className="min-h-[calc(100vh-57px)] flex items-center justify-center px-6 py-16">
      <div className="w-full max-w-2xl rgx-fade-in">
        <p className="rgx-mono text-xs mb-1" style={{ color: C.textFaint }}>{fileName}</p>
        <h2 className="rgx-display text-xl font-medium mb-8" style={{ color: C.text }}>
          Running the benchmark pipeline…
        </h2>

        <div className="space-y-3 mb-8">
          {STAGE_ORDER.map((id, idx) => {
            const state = idx < currentIdx ? "done" : idx === currentIdx ? "active" : "pending";
            return (
              <div key={id} className="flex items-center gap-3">
                {state === "done" && <CircleCheck size={16} style={{ color: C.signal }} />}
                {state === "active" && <Loader2 size={16} className="rgx-spin" style={{ color: C.decision }} />}
                {state === "pending" && <Circle size={16} style={{ color: C.textFaint }} />}
                <span className="text-sm" style={{ color: state === "pending" ? C.textFaint : C.text }}>
                  {STAGE_META[id]}
                </span>
              </div>
            );
          })}
        </div>

        <div ref={logRef} className="rgx-mono text-xs rounded-md px-4 py-3 h-36 overflow-y-auto rgx-scroll"
          style={{ background: "#000", border: `1px solid ${C.borderFaint}`, color: C.signal }}>
          {logs.length === 0 && <div style={{ color: C.textFaint }}>Waiting for the pipeline to start…</div>}
          {logs.map((l, idx) => (
            <div key={idx} className="mb-1" style={{ color: idx === logs.length - 1 ? C.signal : C.textFaint }}>
              <span style={{ color: C.textFaint }}>[{String(idx).padStart(2, "0")}]</span> {l}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------- */
/* Error screen                                                           */
/* ---------------------------------------------------------------------- */

function ErrorScreen({ message, onRetry, onStartOver }) {
  return (
    <div className="min-h-[calc(100vh-57px)] flex items-center justify-center px-6 py-20">
      <div className="w-full max-w-md text-center rgx-fade-in">
        <div className="w-11 h-11 rounded-full flex items-center justify-center mx-auto mb-4" style={{ background: C.alertDim }}>
          <AlertOctagon size={18} style={{ color: C.alert }} />
        </div>
        <h2 className="rgx-display text-lg font-medium mb-2" style={{ color: C.text }}>Something went wrong</h2>
        <p className="text-sm mb-6" style={{ color: C.textMute }}>{message || "The backend didn't respond as expected."}</p>
        <div className="flex items-center justify-center gap-3">
          {onRetry && (
            <button onClick={onRetry} className="text-sm px-4 py-2 rounded-md" style={{ background: C.decision, color: "#1a1206" }}>
              Try again
            </button>
          )}
          <button onClick={onStartOver} className="text-sm px-4 py-2 rounded-md" style={{ border: `1px solid ${C.border}`, color: C.textMute }}>
            Start over
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------- */
/* Results: hero recommendation — reads straight off the backend payload  */
/* ---------------------------------------------------------------------- */

function Hero({ result }) {
  const winner = result.strategies.find((s) => s.id === result.recommendedStrategyId);
  if (!winner) return null;
  return (
    <div className="rounded-lg p-7 mb-14" style={{ background: C.panel2, border: `1px solid ${C.decision}44` }}>
      <div className="flex items-center gap-2 rgx-mono text-xs mb-4" style={{ color: C.decision }}>
        <span className="w-1.5 h-1.5 rounded-full" style={{ background: C.decision }} />
        decision engine recommendation
      </div>
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 min-w-0">
        <div className="min-w-0">
          <h2 className="rgx-display text-3xl font-semibold" style={{ color: C.text }}>{winner.name}</h2>
          <p className="text-sm mt-1.5 max-w-xl leading-relaxed" style={{ color: C.textMute }}>
            Leads by {result.confidence.gap.toFixed(1)} points overall — {result.confidence.detail}.
          </p>
        </div>
        <div className="text-left md:text-right shrink-0">
          <div className="rgx-mono text-3xl font-medium" style={{ color: C.decision }}>{winner.overall.toFixed(1)}</div>
          <div className="text-xs mt-1" style={{ color: C.textFaint }}>overall score / 100</div>
        </div>
      </div>
      <div className="mt-5 pt-5 flex items-center gap-2 flex-wrap" style={{ borderTop: `1px solid ${C.border}` }}>
        <span className="text-xs rgx-mono px-2 py-1 rounded" style={{ background: C.decisionDim, color: C.decision }}>
          {result.confidence.label}
        </span>
        <span className="text-xs" style={{ color: C.textFaint }}>
          based on the {result.confidence.gap.toFixed(1)}-point margin over the next-best strategy
        </span>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------- */
/* Results: ranking + weight controls                                     */
/* ---------------------------------------------------------------------- */

function RankingPanel({ result, weights, setWeights, isCustomWeights, expanded, setExpanded }) {
  const sum = weights.retrieval + weights.quality + weights.consistency + weights.efficiency || 1;

  // The only client-side "computation" here is a disclosed, simple weighted
  // average over the dims the backend already scored — used purely so the
  // sliders can preview a what-if scenario. It never invents a score, and
  // it is never used in place of the backend's official recommendation
  // above (Hero) or its reasoning/uncertainty text below.
  const ranked = [...result.strategies]
    .map((s) => ({
      ...s,
      previewScore: (s.dims.retrieval * weights.retrieval + s.dims.quality * weights.quality +
        s.dims.consistency * weights.consistency + s.dims.efficiency * weights.efficiency) / sum,
    }))
    .sort((a, b) => b.previewScore - a.previewScore);

  const previewTopId = ranked[0].id;
  const officialTopId = result.recommendedStrategyId;

  return (
    <div className="mb-14">
      <SectionLabel index="01">Ranking</SectionLabel>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_240px] gap-6 items-start">
        <div className="space-y-2 min-w-0">
          {ranked.map((s, idx) => {
            const isOpen = expanded === s.id;
            const isTop = idx === 0;
            return (
              <div key={s.id} className="rounded-md overflow-hidden" style={{ background: isTop ? C.panel2 : C.panel, border: `1px solid ${isTop ? C.decision + "44" : C.borderFaint}` }}>
                <button onClick={() => setExpanded(isOpen ? null : s.id)} className="w-full grid grid-cols-[20px_minmax(108px,160px)_minmax(0,1fr)_44px_16px] items-center gap-3 px-4 py-3.5 text-left">
                  <span className="rgx-mono text-xs" style={{ color: isTop ? C.decision : C.textFaint }}>{idx + 1}</span>
                  <div className="min-w-0">
                    <div className="text-sm flex items-center gap-1.5 min-w-0" style={{ color: C.text }}>
                      <span className="truncate">{s.name}</span>
                      {s.id === officialTopId && (
                        <span className="rgx-mono text-[10px] px-1.5 py-0.5 rounded shrink-0" style={{ background: C.decisionDim, color: C.decision }}>official</span>
                      )}
                    </div>
                    <div className="rgx-mono text-xs truncate" style={{ color: C.textFaint }}>{s.tag}</div>
                  </div>
                  <div className="min-w-0"><Bar value={s.previewScore} color={isTop ? C.decision : C.signal} track={C.border} /></div>
                  <span className="rgx-mono text-sm text-right tabular-nums" style={{ color: isTop ? C.decision : C.textMute }}>{s.previewScore.toFixed(1)}</span>
                  {isOpen ? <ChevronUp size={14} style={{ color: C.textFaint }} /> : <ChevronDown size={14} style={{ color: C.textFaint }} />}
                </button>
                {isOpen && (
                  <div className="px-4 pb-4 pt-1 grid grid-cols-2 gap-3 rgx-fade-in">
                    {Object.entries(DIM_META).map(([key, meta]) => (
                      <div key={key}>
                        <div className="flex items-baseline justify-between mb-1">
                          <span className="text-xs" style={{ color: C.textMute }}>{meta.label}</span>
                          <span className="rgx-mono text-xs" style={{ color: C.textMute }}>{s.dims[key]}</span>
                        </div>
                        <Bar value={s.dims[key]} color={C.textFaint} height={5} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {isCustomWeights && previewTopId !== officialTopId && (
            <div className="flex items-start gap-2 text-xs px-1 pt-2 rgx-fade-in" style={{ color: C.alert }}>
              <TriangleAlert size={13} className="mt-0.5 shrink-0" />
              <span>
                Under your custom weights, the top strategy differs from the backend's official recommendation.
                The reasoning and uncertainty analysis below still describe the official pick, based on its default weighting.
              </span>
            </div>
          )}
        </div>

        <div className="rounded-md p-4 xl:sticky xl:top-6" style={{ background: C.panel, border: `1px solid ${C.borderFaint}` }}>
          <div className="flex items-center justify-between mb-4">
            <p className="rgx-mono text-xs" style={{ color: C.textFaint }}>decision weighting</p>
            {isCustomWeights && (
              <button onClick={() => setWeights(result.defaultWeights)} className="rgx-mono text-xs flex items-center gap-1" style={{ color: C.textMute }}>
                <RotateCcw size={10} /> reset
              </button>
            )}
          </div>
          <div className="space-y-4">
            <WeightSlider label="Retrieval" desc="recall@5 & MRR" value={weights.retrieval} color={C.signal} onChange={(v) => setWeights((w) => ({ ...w, retrieval: v }))} />
            <WeightSlider label="Chunk quality" desc="coherence & boundaries" value={weights.quality} color={C.signal} onChange={(v) => setWeights((w) => ({ ...w, quality: v }))} />
            <WeightSlider label="Consistency" desc="cross-query variance" value={weights.consistency} color={C.signal} onChange={(v) => setWeights((w) => ({ ...w, consistency: v }))} />
            <WeightSlider label="Efficiency" desc="embed time & overhead" value={weights.efficiency} color={C.signal} onChange={(v) => setWeights((w) => ({ ...w, efficiency: v }))} />
          </div>
          <p className="text-xs mt-4 pt-4" style={{ color: C.textFaint, borderTop: `1px solid ${C.borderFaint}` }}>
            This is a preview: a simple weighted average of the backend's own dimension scores.
            It does not re-run the Decision Engine.
          </p>
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------- */
/* Results: reasoning, uncertainty, trade-offs, evidence — all from API   */
/* ---------------------------------------------------------------------- */

function ReasoningPanel({ result }) {
  const winner = result.strategies.find((s) => s.id === result.recommendedStrategyId);
  return (
    <div className="mb-14">
      <SectionLabel index="02">Why {winner?.name || "this strategy"} won on this document</SectionLabel>
      <ul className="space-y-3">
        {result.reasoning.map((r, i) => (
          <li key={i} className="flex gap-3 text-sm" style={{ color: C.textMute }}>
            <span className="rgx-mono text-xs mt-0.5 shrink-0" style={{ color: C.signal }}>{String(i + 1).padStart(2, "0")}</span>
            <span>{r}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function UncertaintyPanel({ result }) {
  return (
    <div className="mb-14">
      <SectionLabel index="03">Uncertainty analysis</SectionLabel>
      <div className="rounded-md p-5" style={{ background: C.panel, border: `1px solid ${C.borderFaint}` }}>
        <div className="flex items-center gap-2 mb-3">
          <TriangleAlert size={14} style={{ color: C.alert }} />
          <span className="text-sm" style={{ color: C.text }}>The margin isn't absolute — here's what would flip it.</span>
        </div>
        <p className="text-sm leading-relaxed" style={{ color: C.textMute }}>{result.uncertainty.summary}</p>
      </div>
    </div>
  );
}

function TradeoffTable({ result }) {
  const strategies = result.strategies;
  return (
    <div className="mb-14">
      <SectionLabel index="04">Trade-offs</SectionLabel>
      <div className="overflow-x-auto rgx-scroll rounded-md" style={{ border: `1px solid ${C.borderFaint}` }}>
        <table className="w-full text-sm table-fixed" style={{ borderCollapse: "collapse", minWidth: 640 }}>
          <thead>
            <tr style={{ background: C.panel2 }}>
              <th className="text-left px-4 py-3 rgx-mono text-xs font-normal w-[140px]" style={{ color: C.textFaint }}> </th>
              {strategies.map((s) => (
                <th key={s.id} className="text-left px-4 py-3 font-medium align-bottom" style={{ color: C.text }}>{s.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.tradeoffs.rows.map((row, i) => (
              <tr key={row.label} style={{ background: i % 2 ? "transparent" : C.panel }}>
                <td className="px-4 py-3 rgx-mono text-xs align-top whitespace-nowrap" style={{ color: C.textFaint, borderTop: `1px solid ${C.borderFaint}` }}>{row.label}</td>
                {strategies.map((s) => (
                  <td key={s.id} className="px-4 py-3 align-top leading-relaxed break-words" style={{ color: C.textMute, borderTop: `1px solid ${C.borderFaint}` }}>
                    {row.values[s.id] ?? "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EvidencePanel({ result }) {
  const [tab, setTab] = useState(result.recommendedStrategyId);
  const strategy = result.strategies.find((s) => s.id === tab) || result.strategies[0];
  const ev = strategy.evidence;
  return (
    <div className="mb-4">
      <SectionLabel index="05">Retrieved-chunk evidence</SectionLabel>
      <p className="text-sm mb-4 leading-relaxed break-words" style={{ color: C.textMute }}>
        Sample query: <span className="rgx-mono" style={{ color: C.text }}>"{result.evidenceQuery}"</span>
      </p>
      <div className="flex gap-1 mb-3 flex-wrap">
        {result.strategies.map((s) => (
          <button key={s.id} onClick={() => setTab(s.id)} className="text-xs rgx-mono px-3 py-1.5 rounded-md transition-colors"
            style={{ background: tab === s.id ? C.raised : "transparent", color: tab === s.id ? C.text : C.textFaint, border: `1px solid ${tab === s.id ? C.border : "transparent"}` }}>
            {s.name}
          </button>
        ))}
      </div>
      <div className="rounded-md p-5" style={{ background: C.panel, border: `1px solid ${ev.clean ? C.borderFaint : C.alert + "55"}` }}>
        <div className="flex items-center gap-2 mb-3">
          {ev.clean ? (
            <><CircleCheck size={13} style={{ color: C.signal }} /><span className="text-xs rgx-mono" style={{ color: C.signal }}>self-contained chunk, boundaries intact</span></>
          ) : (
            <><FileWarning size={13} style={{ color: C.alert }} /><span className="text-xs rgx-mono" style={{ color: C.alert }}>chunk boundary cuts across the sentence</span></>
          )}
        </div>
        <p className="text-sm leading-relaxed rgx-mono break-words whitespace-pre-wrap" style={{ color: ev.clean ? C.text : C.textMute }}>{ev.text}</p>
        <div className="flex gap-8 mt-4 pt-4 flex-wrap" style={{ borderTop: `1px solid ${C.borderFaint}` }}>
          <div>
            <div className="rgx-mono text-xs" style={{ color: C.textFaint }}>boundary alignment</div>
            <div className="rgx-mono text-sm" style={{ color: C.text }}>{strategy.raw.boundary.toFixed(2)}</div>
          </div>
          <div>
            <div className="rgx-mono text-xs" style={{ color: C.textFaint }}>coherence</div>
            <div className="rgx-mono text-sm" style={{ color: C.text }}>{strategy.raw.coherence.toFixed(2)}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------- */
/* Results dashboard                                                      */
/* ---------------------------------------------------------------------- */

function ResultsDashboard({ result, onReset }) {
  const [weights, setWeights] = useState(result.defaultWeights);
  const [expanded, setExpanded] = useState(null);
  const isCustomWeights = JSON.stringify(weights) !== JSON.stringify(result.defaultWeights);

  return (
    <div className="max-w-5xl mx-auto px-6 py-10 rgx-fade-in min-w-0">
      <div className="flex items-start sm:items-center justify-between gap-4 mb-10">
        <div className="flex items-center gap-2.5 min-w-0">
          <FileText size={15} className="shrink-0" style={{ color: C.textFaint }} />
          <div className="min-w-0">
            <div className="text-sm truncate" style={{ color: C.text }}>{result.document.name}</div>
            <div className="rgx-mono text-xs" style={{ color: C.textFaint }}>
              {result.document.sizeLabel} • {result.document.pageCount} pages • {result.document.chunkCount} chunks generated
            </div>
          </div>
        </div>
        <button onClick={onReset} className="flex items-center gap-1.5 text-xs rgx-mono px-3 py-2 rounded-md transition-colors shrink-0" style={{ color: C.textMute, border: `1px solid ${C.borderFaint}` }}>
          <RotateCcw size={12} /> new document
        </button>
      </div>

      <Hero result={result} />
      <RankingPanel result={result} weights={weights} setWeights={setWeights} isCustomWeights={isCustomWeights} expanded={expanded} setExpanded={setExpanded} />
      <ReasoningPanel result={result} />
      <UncertaintyPanel result={result} />
      <TradeoffTable result={result} />
      <EvidencePanel result={result} />
    </div>
  );
}

/* ---------------------------------------------------------------------- */
/* App shell — owns the API lifecycle                                     */
/* ---------------------------------------------------------------------- */

export default function RAGarator() {
  const [stage, setStage] = useState("upload"); // upload | uploading | processing | results | error
  const [fileMeta, setFileMeta] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const pendingFileRef = useRef(null);
  const pollRef = useRef(null);

  const startAnalysis = useCallback(async (file) => {
    pendingFileRef.current = file;
    setError(null);
    setStage("uploading");
    try {
      const { jobId: id } = await apiAnalyzeDocument(file);
      setFileMeta({ name: file.name });
      setJobId(id);
      setStage("processing");
    } catch (e) {
      setError(e.message || "Upload failed. Check your connection and try again.");
      setStage("error");
    }
  }, []);

  // Poll job status while processing
  useEffect(() => {
    if (stage !== "processing" || !jobId) return;
    let cancelled = false;

    const poll = async () => {
      try {
        const s = await apiGetStatus(jobId);
        if (cancelled) return;
        setStatus(s);
        if (s.status === "complete") {
          const r = await apiGetResult(jobId);
          if (cancelled) return;
          setResult(r);
          setStage("results");
          return;
        }
        if (s.status === "error") {
          setError(s.error || "The backend reported an error while processing this document.");
          setStage("error");
          return;
        }
        pollRef.current = setTimeout(poll, 700);
      } catch (e) {
        if (cancelled) return;
        setError(e.message || "Lost connection while checking job status.");
        setStage("error");
      }
    };
    poll();

    return () => { cancelled = true; clearTimeout(pollRef.current); };
  }, [stage, jobId]);

  const reset = useCallback(() => {
    setStage("upload"); setFileMeta(null); setJobId(null);
    setStatus(null); setResult(null); setError(null);
    pendingFileRef.current = null;
  }, []);

  const retry = useCallback(() => {
    if (pendingFileRef.current) startAnalysis(pendingFileRef.current);
    else reset();
  }, [startAnalysis, reset]);

  return (
    <div className="min-h-screen w-full overflow-x-hidden" style={{ background: C.bg }}>
      {FONTS}
      <header className="px-6 py-4" style={{ borderBottom: `1px solid ${C.borderFaint}` }}>
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-baseline gap-2 min-w-0">
            <span className="rgx-display font-semibold text-sm tracking-tight" style={{ color: C.text }}>RAGarator</span>
            <span className="rgx-mono text-xs truncate" style={{ color: C.textFaint }}>/ chunking decision engine</span>
          </div>
          {stage === "results" && (
            <div className="hidden sm:flex items-center gap-1.5 text-xs rgx-mono shrink-0" style={{ color: C.textFaint }}>
              <ArrowRight size={11} /> benchmark complete
            </div>
          )}
        </div>
      </header>

      {(stage === "upload" || stage === "uploading") && (
        <UploadScreen onFile={startAnalysis} uploading={stage === "uploading"} uploadError={null} />
      )}
      {stage === "processing" && <ProcessingScreen fileName={fileMeta?.name} status={status} />}
      {stage === "results" && result && <ResultsDashboard result={result} onReset={reset} />}
      {stage === "error" && <ErrorScreen message={error} onRetry={retry} onStartOver={reset} />}
    </div>
  );
}
