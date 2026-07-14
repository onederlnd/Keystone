import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "../api/client";
import { useAuth } from "../context/AuthContext";
import StatusPill from "../components/StatusPill";

export default function Dashboard() {
  const { user } = useAuth();
  const [listings, setListings] = useState([]);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const listingResults = await api.listListings();
        if (cancelled) return;
        setListings(listingResults);

        if (user?.role === "agent") {
          const s = await api.getAgentSummary(user.id);
          if (!cancelled) setSummary(s);
        }
      } catch (err) {
        if (!cancelled) setError("Couldn't load dashboard data.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [user]);

  const activeCount = listings.filter((l) => l.status === "active").length;
  const underContractCount = listings.filter((l) => l.status === "under_contract").length;

  return (
    <>
      <div className="page-header">
        <div>
          <div className="eyebrow">Overview</div>
          <h1>Welcome back{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}</h1>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="stat-grid">
        <div className="stat">
          <div className="stat-value mono">{loading ? "—" : listings.length}</div>
          <div className="stat-label">Total listings</div>
        </div>
        <div className="stat">
          <div className="stat-value mono">{loading ? "—" : activeCount}</div>
          <div className="stat-label">Active</div>
        </div>
        <div className="stat">
          <div className="stat-value mono">{loading ? "—" : underContractCount}</div>
          <div className="stat-label">Under contract</div>
        </div>
        {summary && (
          <div className="stat">
            <div className="stat-value mono">
              {summary.average_price ? `$${Math.round(summary.average_price).toLocaleString()}` : "—"}
            </div>
            <div className="stat-label">Your average price</div>
          </div>
        )}
      </div>

      <h2 style={{ marginBottom: 12 }}>Recent listings</h2>
      {listings.length === 0 && !loading ? (
        <div className="empty-state">No listings yet. Create one to get started.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Address</th>
              <th>Status</th>
              <th>Price</th>
            </tr>
          </thead>
          <tbody>
            {listings.slice(0, 8).map((listing) => (
              <tr key={listing.id} className="row-link">
                <td>
                  <Link to={`/listings/${listing.id}`}>{listing.address}</Link>
                </td>
                <td>
                  <StatusPill status={listing.status} />
                </td>
                <td className="mono">${listing.price?.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
