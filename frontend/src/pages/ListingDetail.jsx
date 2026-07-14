import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import * as api from "../api/client";
import StatusPill from "../components/StatusPill";

const ALL_STATUSES = ["draft", "active", "pending", "under_contract", "sold", "off_market"];

export default function ListingDetail() {
  const { id } = useParams();
  const [listing, setListing] = useState(null);
  const [history, setHistory] = useState([]);
  const [nextStatus, setNextStatus] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    const [listingData, historyData] = await Promise.all([
      api.getListing(id),
      api.getListingHistory(id).catch(() => []),
    ]);
    setListing(listingData);
    setHistory(historyData);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleStatusChange(e) {
    e.preventDefault();
    if (!nextStatus) return;
    setSubmitting(true);
    setError(null);
    setInfo(null);
    try {
      const result = await api.updateListingStatus(id, {
        new_status: nextStatus,
        note,
      });
      // requires_approval transitions come back as an ApprovalQueue entry,
      // not the listing itself — surface that distinction rather than
      // silently pretending the status changed.
      if (result?.entity_type === "listing" && result?.status === "pending") {
        setInfo("This change requires approval and has been queued for review.");
      } else {
        setInfo("Status updated.");
      }
      setNote("");
      setNextStatus("");
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || "That transition isn't allowed.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!listing) return <div className="empty-state">Loading…</div>;

  return (
    <>
      <div className="page-header">
        <div>
          <div className="eyebrow">Listing</div>
          <h1>{listing.address}</h1>
        </div>
        <StatusPill status={listing.status} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 24 }}>
        <div>
          <div className="card" style={{ marginBottom: 20 }}>
            <h2>Details</h2>
            <table>
              <tbody>
                <tr>
                  <td>City / State / Zip</td>
                  <td>{listing.city}, {listing.state} {listing.zip}</td>
                </tr>
                <tr>
                  <td>Price</td>
                  <td className="mono">${listing.price?.toLocaleString()}</td>
                </tr>
                <tr>
                  <td>Bed / Bath</td>
                  <td className="mono">{listing.bedrooms} / {listing.bathrooms}</td>
                </tr>
                <tr>
                  <td>Sqft</td>
                  <td className="mono">{listing.sqft?.toLocaleString()}</td>
                </tr>
                <tr>
                  <td>MLS ID</td>
                  <td className="mono">{listing.mls_id}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="card">
            <h2>Status history</h2>
            {history.length === 0 ? (
              <div className="empty-state">No status changes recorded yet.</div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>From</th>
                    <th>To</th>
                    <th>Triggered by</th>
                    <th>When</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.id}>
                      <td><StatusPill status={h.previous_status} /></td>
                      <td><StatusPill status={h.new_status} /></td>
                      <td>{h.triggered_by}</td>
                      <td className="mono">
                        {new Date(h.changed_at || h.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="card" style={{ height: "fit-content" }}>
          <h2>Change status</h2>
          {error && <div className="error-banner">{error}</div>}
          {info && <div className="error-banner" style={{ background: "var(--green-soft)", color: "var(--green)", borderColor: "var(--green)" }}>{info}</div>}
          <form onSubmit={handleStatusChange}>
            <div className="field">
              <label htmlFor="status">New status</label>
              <select id="status" value={nextStatus} onChange={(e) => setNextStatus(e.target.value)}>
                <option value="">Select…</option>
                {ALL_STATUSES.filter((s) => s !== listing.status).map((s) => (
                  <option key={s} value={s}>{s.replaceAll("_", " ")}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="note">Note (optional)</label>
              <textarea id="note" rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
            </div>
            <button className="btn" type="submit" disabled={!nextStatus || submitting} style={{ width: "100%" }}>
              {submitting ? "Submitting…" : "Submit change"}
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
