import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "../api/client";
import StatusPill from "../components/StatusPill";

export default function Listings() {
  const [listings, setListings] = useState([]);
  const [city, setCity] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (city) params.city = city;
      if (status) params.status = status;
      const results = await api.listListings(params);
      setListings(results);
    } catch {
      setError("Couldn't load listings.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleFilterSubmit(e) {
    e.preventDefault();
    load();
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="eyebrow">Inventory</div>
          <h1>Listings</h1>
        </div>
      </div>

      <form className="filters" onSubmit={handleFilterSubmit}>
        <input
          placeholder="City"
          value={city}
          onChange={(e) => setCity(e.target.value)}
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Any status</option>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="pending">Pending</option>
          <option value="under_contract">Under contract</option>
          <option value="sold">Sold</option>
          <option value="off_market">Off market</option>
        </select>
        <button className="btn secondary small" type="submit">
          Apply filters
        </button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="empty-state">Loading…</div>
      ) : listings.length === 0 ? (
        <div className="empty-state">No listings match these filters.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Address</th>
              <th>City</th>
              <th>Status</th>
              <th>Price</th>
              <th>Beds / Baths</th>
            </tr>
          </thead>
          <tbody>
            {listings.map((listing) => (
              <tr key={listing.id} className="row-link">
                <td>
                  <Link to={`/listings/${listing.id}`}>{listing.address}</Link>
                </td>
                <td>{listing.city}</td>
                <td>
                  <StatusPill status={listing.status} />
                </td>
                <td className="mono">${listing.price?.toLocaleString()}</td>
                <td className="mono">
                  {listing.bedrooms} / {listing.bathrooms}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
