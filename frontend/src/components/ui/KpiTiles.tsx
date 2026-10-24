import { Skeleton } from "./Skeleton";
import { cx } from "./cx";

export interface Kpi {
  label: string;
  value: string | number;
  tone?: "review" | "error" | "default";
}

export function KpiTiles({ tiles }: { tiles: Kpi[] | null }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      {(tiles ?? Array.from({ length: 4 }, () => null)).map((t, i) => (
        <div
          key={t?.label ?? i}
          className="rounded-xl border border-line bg-surface px-5 py-3.5 shadow-sm"
        >
          {t ? (
            <>
              <p className="text-xs text-muted">{t.label}</p>
              <p
                className={cx(
                  "font-mono text-[22px] font-bold",
                  t.tone === "review"
                    ? "text-review"
                    : t.tone === "error"
                      ? "text-error"
                      : "text-ink",
                )}
              >
                {t.value}
              </p>
            </>
          ) : (
            <Skeleton className="h-11" />
          )}
        </div>
      ))}
    </div>
  );
}
