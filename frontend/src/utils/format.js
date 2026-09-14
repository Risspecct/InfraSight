export function formatData(value, fallback = "—") {
  if (value === null || value === undefined || value === "") return fallback;
  const text = String(value).trim();
  return /^(nan|null|undefined)$/i.test(text) ? fallback : text;
}

export function formatNumber(value, digits = 1, suffix = "") {
  return typeof value === "number" && Number.isFinite(value)
    ? `${value.toLocaleString(undefined, { maximumFractionDigits: digits })}${suffix}`
    : "—";
}

export function formatDate(value) {
  if (!value || /^(nan|null|undefined)$/i.test(String(value).trim())) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
}
