import Link from "next/link";

import type { Case } from "../schemas";
import { CaseStatusChip } from "./CaseStatusChip";

export function CaseHeader({ data }: { data: Case }) {
  return (
    <div className="flex flex-col gap-1 px-6 pt-5 pb-4">
      <p className="text-xs text-muted">
        <Link href="/cases" className="hover:underline">
          Cases
        </Link>{" "}
        / {data.id}
      </p>
      <div className="flex items-center gap-3">
        <h1 className="flex items-center gap-3 text-ink">
          <span className="font-mono text-[22px] font-bold">{data.id}</span>
          <span className="text-[15px] font-normal text-muted">
            {data.title}
          </span>
        </h1>
        <CaseStatusChip status={data.status} />
      </div>
    </div>
  );
}
