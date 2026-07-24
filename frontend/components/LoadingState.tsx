import { Spinner } from "./Spinner";

export function LoadingState({ message = "Loading match data…" }: { message?: string }) {
  return (
    <div className="flex flex-col items-center gap-4 py-24 text-center">
      <Spinner size="lg" accentColor="court-green" />
      <p className="text-sm text-text-muted">{message}</p>
    </div>
  );
}
