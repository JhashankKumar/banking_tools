/** Mirrors the `##` headings of docs/project/SECURITY_LIMITATIONS.md; keep the two in step. */
export const LIMITATION_HEADINGS = [
  "Customer-information filter",
  "Scripted model, not a real one",
  "Demo authentication",
  "Role-based access only",
  "No per-IP rate limiting",
  "Run time bounds",
  "Data sent to OpenRouter",
  "Not a compliance claim",
] as const;

export const LIMITATIONS_PATH = "docs/project/SECURITY_LIMITATIONS.md";

export function KnownLimitations() {
  return (
    <section
      aria-labelledby="known-limitations"
      className="flex flex-col gap-2 rounded-xl border border-line bg-surface px-5 py-4 shadow-sm"
    >
      <h2 id="known-limitations" className="text-sm font-semibold text-ink">
        Known limitations
      </h2>
      <p className="text-xs text-muted">
        What these checks do not cover. Details in{" "}
        <code className="font-mono">{LIMITATIONS_PATH}</code>.
      </p>
      <ul className="list-disc pl-5 text-xs text-ink">
        {LIMITATION_HEADINGS.map((h) => (
          <li key={h}>{h}</li>
        ))}
      </ul>
    </section>
  );
}
