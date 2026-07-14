import { useEffect, useState } from "react";
import * as api from "../api/client";

// A genuine ordered sequence — numbering the columns reflects the
// real transaction timeline, not decoration.
const STAGES = [
  "new",
  "contacted",
  "showing_scheduled",
  "offer_submitted",
  "negotiating",
  "under_contract",
  "closed",
  "lost",
];

export default function Pipeline() {
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const results = await api.listPipeline();
      setEntries(results);
    } catch {
      setError("Couldn't load the pipeline.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleStageChange(entry, newStage) {
    setError(null);
    setInfo(null);
    try {
      const result = await api.updatePipelineEntry(entry.id, { stage: newStage });
      if (result?.status === "pending" && result?.proposed_state) {
        setInfo("That move requires approval and has been queued for review.");
      }
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || "That stage move isn't allowed.");
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="eyebrow">Deal flow</div>
          <h1>Pipeline</h1>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {info && (
        <div
          className="error-banner"
          style={{ background: "var(--brass-soft)", color: "var(--brass)", borderColor: "var(--brass)" }}
        >
          {info}
        </div>
      )}

      {loading ? (
        <div className="empty-state">Loading…</div>
      ) : (
        <div className="board">
          {STAGES.map((stage, idx) => {
            const stageEntries = entries.filter((e) => e.stage === stage);
            return (
              <div className="board-column" key={stage}>
                <div className="board-column-header">
                  <span className="board-column-index">{String(idx + 1).padStart(2, "0")}</span>
                  <span className="board-column-title">{stage.replaceAll("_", " ")}</span>
                </div>

                {stageEntries.length === 0 && (
                  <div style={{ fontSize: 12, color: "var(--slate)", padding: "4px 4px" }}>
                    Nothing here
                  </div>
                )}

                {stageEntries.map((entry) => (
                  <div className="board-card" key={entry.id}>
                    <div className="board-card-title">
                      {entry.contact_name || `Contact ${entry.contact_id?.slice(0, 8)}`}
                    </div>
                    <div className="board-card-meta">
                      {entry.offer_price ? `$${entry.offer_price.toLocaleString()}` : "no offer yet"}
                    </div>
                    <select
                      style={{ marginTop: 8, width: "100%", fontSize: 11 }}
                      value={entry.stage}
                      onChange={(e) => handleStageChange(entry, e.target.value)}
                    >
                      {STAGES.map((s) => (
                        <option key={s} value={s}>{s.replaceAll("_", " ")}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
