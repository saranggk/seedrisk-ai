export function LoadingState({ message = "Loading match data…" }: { message?: string }) {
  return (
    <div className="flex flex-col items-center gap-4 py-24 text-center">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-200 border-t-court-green" />
      <p className="text-sm text-zinc-500">{message}</p>
    </div>
  );
}
