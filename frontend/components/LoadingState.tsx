export function LoadingState() {
  return (
    <div className="flex flex-col items-center gap-3 py-24 text-center">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-300 border-t-court-green" />
      <p className="text-sm text-zinc-500">Loading matches and predictions…</p>
    </div>
  );
}
