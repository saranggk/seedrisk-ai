import Link from "next/link";

export function MatchNotFound({ matchId }: { matchId: string }) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-3 rounded-xl border border-zinc-200 bg-zinc-50 p-6 text-center">
      <p className="font-semibold text-zinc-800">Match not found</p>
      <p className="text-sm text-zinc-600">
        There&apos;s no match with ID &quot;{matchId}&quot; in the dataset.
      </p>
      <Link
        href="/"
        className="mt-1 rounded-md bg-court-green px-4 py-2 text-sm font-medium text-white hover:bg-court-green-light"
      >
        Back to dashboard
      </Link>
    </div>
  );
}
