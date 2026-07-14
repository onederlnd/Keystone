import { useEffect, useState } from "react";
import * as api from "../api/client";

const TYPES = ["buyer", "seller", "lead"];

export default function Contacts() {
  const [contacts, setContacts] = useState([]);
  const [typeFilter, setTypeFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", type: "lead", source: "" });
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const params = typeFilter ? { type: typeFilter } : {};
      const results = await api.listContacts(params);
      setContacts(results);
    } catch {
      setError("Couldn't load contacts.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typeFilter]);

  async function handleCreate(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.createContact(form);
      setForm({ full_name: "", email: "", phone: "", type: "lead", source: "" });
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || "Couldn't create contact.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="eyebrow">CRM</div>
          <h1>Contacts</h1>
        </div>
        <button className="btn small" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "New contact"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {showForm && (
        <form className="card" onSubmit={handleCreate} style={{ marginBottom: 20 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div className="field">
              <label>Full name</label>
              <input
                required
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Email</label>
              <input
                required
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Phone</label>
              <input
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Type</label>
              <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                {TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Source</label>
              <input
                value={form.source}
                onChange={(e) => setForm({ ...form, source: e.target.value })}
              />
            </div>
          </div>
          <button className="btn" type="submit" disabled={submitting}>
            {submitting ? "Saving…" : "Save contact"}
          </button>
        </form>
      )}

      <div className="filters">
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All types</option>
          {TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="empty-state">Loading…</div>
      ) : contacts.length === 0 ? (
        <div className="empty-state">No contacts yet.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {contacts.map((c) => (
              <tr key={c.id}>
                <td>{c.full_name}</td>
                <td style={{ textTransform: "capitalize" }}>{c.type}</td>
                <td className="mono">{c.email}</td>
                <td className="mono">{c.phone}</td>
                <td>{c.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
