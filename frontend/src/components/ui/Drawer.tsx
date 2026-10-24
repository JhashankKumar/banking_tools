"use client";

import { X } from "lucide-react";
import { useEffect, useRef, type ReactNode } from "react";

/** Right-side modal drawer. Escape closes it; focus moves into it on open. */
export function Drawer({
  title,
  open,
  onClose,
  children,
  footer,
}: {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}) {
  const panel = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    panel.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div
        aria-hidden
        className="absolute inset-0 bg-black/20 dark:bg-black/50"
        onClick={onClose}
      />
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className="relative flex h-full w-[440px] flex-col gap-5 border-l border-line bg-surface p-7 shadow-2xl outline-none"
      >
        <header className="flex items-center">
          <h2 className="text-xl font-bold text-ink">{title}</h2>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="ml-auto rounded p-1 text-muted hover:bg-raised"
          >
            <X size={18} />
          </button>
        </header>
        <div className="flex flex-1 flex-col gap-5 overflow-y-auto">
          {children}
        </div>
        {footer && (
          <footer className="flex justify-end gap-2.5">{footer}</footer>
        )}
      </div>
    </div>
  );
}
