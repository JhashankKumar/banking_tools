import { Suspense } from "react";

import { LoginBrandPanel } from "@/features/auth/components/LoginBrandPanel";
import { LoginForm } from "@/features/auth/components/LoginForm";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen bg-page">
      <LoginBrandPanel />
      <div className="flex flex-1 items-center justify-center p-8">
        <Suspense>
          <LoginForm />
        </Suspense>
      </div>
    </main>
  );
}
