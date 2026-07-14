import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: BASE_URL,
});

// Attach the JWT to every outgoing request, if we have one.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("keystone_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If the token is rejected, clear it and send the user back to login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("keystone_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

/* -----------------------------------------------------------------
   Auth
-------------------------------------------------------------------- */
export async function login(email, password) {
  const { data } = await api.post("/auth/login", { email, password });
  return data; // expected shape: { access_token, token_type }
}

export async function getMe() {
  const { data } = await api.get("/users/me");
  return data;
}

/* -----------------------------------------------------------------
   Listings
-------------------------------------------------------------------- */
export async function listListings(params = {}) {
  const { data } = await api.get("/listings/", { params });
  return data;
}

export async function getListing(id) {
  const { data } = await api.get(`/listings/${id}`);
  return data;
}

export async function createListing(payload) {
  const { data } = await api.post("/listings/", payload);
  return data;
}

export async function updateListingStatus(id, payload) {
  const { data } = await api.patch(`/listings/${id}/status`, payload);
  return data;
}

export async function getListingHistory(id) {
  const { data } = await api.get(`/listings/${id}/history`);
  return data;
}

/* -----------------------------------------------------------------
   Contacts
-------------------------------------------------------------------- */
export async function listContacts(params = {}) {
  const { data } = await api.get("/contacts/", { params });
  return data;
}

export async function createContact(payload) {
  const { data } = await api.post("/contacts/", payload);
  return data;
}

/* -----------------------------------------------------------------
   Pipeline
-------------------------------------------------------------------- */
export async function listPipeline(params = {}) {
  const { data } = await api.get("/pipeline/", { params });
  return data;
}

export async function addToPipeline(payload) {
  const { data } = await api.post("/pipeline/", payload);
  return data;
}

export async function updatePipelineEntry(id, payload) {
  const { data } = await api.patch(`/pipeline/${id}`, payload);
  return data;
}

/* -----------------------------------------------------------------
   Documents
-------------------------------------------------------------------- */
export async function listDocuments(params = {}) {
  const { data } = await api.get("/documents/", { params });
  return data;
}

export async function getDocument(id) {
  const { data } = await api.get(`/documents/${id}`);
  return data;
}

export function documentDownloadUrl(id) {
  return `${BASE_URL}/documents/${id}/download`;
}

export async function updateDocumentStatus(id, newStatus) {
  const { data } = await api.post(`/documents/${id}/status`, {
    new_status: newStatus,
  });
  return data;
}

export async function generateDocument(payload) {
  const { data } = await api.post("/documents", payload);
  return data;
}

/* -----------------------------------------------------------------
   Analytics
-------------------------------------------------------------------- */
export async function getComps(params = {}) {
  const { data } = await api.get("/analytics/comps", { params });
  return data;
}

export async function getPricePerSqft(params = {}) {
  const { data } = await api.get("/analytics/price-per-sqft", { params });
  return data;
}

export async function getDaysOnMarket(params = {}) {
  const { data } = await api.get("/analytics/days-on-market", { params });
  return data;
}

export async function getAgentSummary(agentId) {
  const { data } = await api.get(`/analytics/agent/${agentId}/summary`);
  return data;
}

export async function getListingReport(listingId) {
  const { data } = await api.get(`/analytics/listings/${listingId}/report`);
  return data;
}
