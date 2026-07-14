import { useEffect, useState } from "react";
import * as api from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Analytics() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [zip, setZip] = useState("");
  const [comps, setComps] = useState(null);
  const [pricePerSqft, setPricePerSqft] = useState(null);
  const [dom, setDom] = useState(null);
  const [error, setError] = useState(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (user?.id) {
      api.getAgentSummary(user.id).then(setSummary).catch(() => {});
    }
  }, [user]);

  async function handleSearch(e) {
    e.preventDefault();
    if (!zip) return;
    setSearching(true);
    setError(null);
    try {
      const [compsResult, sqftResult, domResult] = await Promise.all([
        api.getComps({ zip }),
        api.getPricePerSqft({ zip }),
        api.getDaysOnMarket({ zip }),
      ]);
      setComps(compsResult);
      setPricePerSqft(sqftResult);
      setDom(domResult);
    } catch {
      setError("Couldn't run that lookup.");
    } finally {
      setSearching(false);
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="eyebrow">Market</div>
          <h1>Analytics</h1>
        </div>
      </div>

      {summary && (
        <div className="stat-grid">
          <div className="stat">
            <div className="stat-value mono">{summary.count}</div>
            <div className="stat-label">Your listings</div>
          </div>
          <div className="stat">
            <div className="stat-value mono">
              {summary.average_price ? `$${Math.round(summary.average_price).toLocaleString()}` : "—"}
            </div>
            <div className="stat-label">Your average price</div>
          </div>
        </div>
      )}

      <div className="card" style={{ marginBottom: 24 }}>
        <h2>Area lookup</h2>
        <form className="filters" onSubmit={handleSearch}>
          <input
            placeholder="Zip code"
            value={zip}
            onChange={(e) => setZip(e.target.value)}
          />
          <button className="btn small" type="submit" disabled={searching}>
            {searching ? "Searching…" : "Search"}
          </button>
        </form>

        {error && <div className="error-banner">{error}</div>}

        {pricePerSqft !== null && (
          <p className="mono" style={{ fontSize: 13 }}>
            Avg price/sqft: {pricePerSqft ? `$${pricePerSqft.toFixed(2)}` : "n/a"}
          </p>
        )}
      </div>

      {comps && comps.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ marginBottom: 12 }}>Comps</h2>
          <table>
            <thead>
              <tr>
                <th>Address</th>
                <th>Price</th>
                <th>Sqft</th>
              </tr>
            </thead>
            <tbody>
              {comps.map((c) => (
                <tr key={c.id}>
                  <td>{c.address}</td>
                  <td className="mono">${c.price?.toLocaleString()}</td>
                  <td className="mono">{c.sqft?.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {dom && dom.length > 0 && (
        <div>
          <h2 style={{ marginBottom: 12 }}>Days on market (sold)</h2>
          <table>
            <thead>
              <tr>
                <th>Address</th>
                <th>Days on market</th>
              </tr>
            </thead>
            <tbody>
              {dom.map((d) => (
                <tr key={d.listing?.id}>
                  <td>{d.listing?.address}</td>
                  <td className="mono">{d.days_on_market ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
