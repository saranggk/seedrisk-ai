import Link from "next/link";
import { ApiError } from "@/lib/api";

export function ErrorState({
  error,
  onRetry,
  backHref,
}: {
  error: ApiError;
  onRetry: () => void;
  backHref?: string;
}) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 rounded-xl border border-red-200 bg-red-50 p-6 text-center">
      <div className="flex flex-col gap-1">
        <p className="font-semibold text-red-800">Couldn&apos;t load match data</p>
        <p className="text-sm text-red-700">{error.message}</p>
      </div>

      {error.isNetworkError && (
        <p className="text-sm text-red-700">
          Start the backend in another terminal, then retry:
          <br />
          <code className="mt-1 inline-block rounded bg-red-100 px-2 py-1 font-mono text-xs">
            cd backend &amp;&amp; uvicorn app.main:app --reload
          </code>
        </p>
      )}

      <div className="flex items-center gap-3">
        <button
          onClick={onRetry}
          className="rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800"
        >
          Retry
        </button>
        {backHref && (
          <Link href={backHref} className="text-sm font-medium text-red-700 hover:underline">
            Back to dashboard
          </Link>
        )}
      </div>
    </div>
  );
}
