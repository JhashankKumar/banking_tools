"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { StatePanel } from "@/components/ui/StatePanel";
import { useMe } from "@/features/auth/queries";
import { landingFor } from "@/lib/permissions";

export default function Home() {
  const router = useRouter();
  const me = useMe();
  useEffect(() => {
    if (me.data) router.replace(landingFor(me.data.role));
  }, [me.data, router]);
  return <StatePanel kind="loading" title="Opening your workspace" />;
}
