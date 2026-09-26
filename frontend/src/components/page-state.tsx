import { CircleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

export function PageLoading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex flex-1 items-center justify-center gap-2.5 py-24 text-sm text-ink-2">
      <Spinner className="size-4 text-accent" />
      {label}
    </div>
  );
}

export function PageError({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-1 items-center justify-center px-6 py-24">
      <div className="max-w-md text-center">
        <CircleAlert className="mx-auto size-6 text-danger" />
        <p className="mt-3 text-[15px] text-ink">{message}</p>
        {onRetry && (
          <Button variant="secondary" size="sm" className="mt-5" onClick={onRetry}>
            Try again
          </Button>
        )}
      </div>
    </div>
  );
}
