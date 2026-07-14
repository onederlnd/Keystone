// Maps a status string to a visual tone. Unknown statuses fall back
// to neutral rather than guessing.
const TONE_BY_STATUS = {
  // listings
  draft: "neutral",
  active: "positive",
  pending: "warn",
  under_contract: "warn",
  sold: "positive",
  off_market: "neutral",
  // pipeline
  new: "neutral",
  contacted: "neutral",
  showing_scheduled: "warn",
  offer_submitted: "warn",
  negotiating: "warn",
  closed: "positive",
  lost: "alert",
  // documents / approval queue
  sent: "warn",
  signed: "positive",
  voided: "alert",
  rejected: "alert",
  expired: "alert",
};

export default function StatusPill({ status }) {
  if (!status) return null;
  const tone = TONE_BY_STATUS[status] || "neutral";
  const label = status.replaceAll("_", " ");
  return <span className={`pill ${tone}`}>{label}</span>;
}
