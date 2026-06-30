import Link from "next/link";

export function MatchNotFound({ matchId }: { matchId: string }) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 rounded-xl border border-zinc-200 bg-white p-8 text-center shadow-sm">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 text-2xl">
        ?
      </div>
      <div className="flex flex-col gap-1">
        <p className="font-semibold text-zinc-800">Match not found</p>
        <p className="text-sm text-zinc-500">
          No match with ID &ldquo;{matchId}&rdquo; in the dataset.
        </p>
      </div>
      <Link
        href="/"
        className="rounded-md bg-court-green px-5 py-2 text-sm font-medium text-white hover:bg-court-green-light"
      >
        Back to dashboard
      </Link>
    </div>
  );
}
