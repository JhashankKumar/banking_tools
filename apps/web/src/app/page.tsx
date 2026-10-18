export default function Page() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center gap-4 px-6 py-16">
      <h1 className="text-4xl font-semibold tracking-tight">
        OpenFraud Investigator
      </h1>
      <p className="text-lg text-zinc-600 dark:text-zinc-400">
        Trace the money. Connect the evidence. Investigate with AI.
      </p>
      <p className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100">
        Demo application. Synthetic data only. Not for real customer data.
      </p>
    </main>
  );
}
