"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { PageError, PageLoading } from "@/components/page-state";
import { SiteHeader } from "@/components/site-header";
import { DifficultyBadge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { useLoad } from "@/lib/use-load";

export default function PracticePage() {
  const { data, error, loading, reload } = useLoad(() => Promise.all([api.problems(), api.languages()]), "practice");
  const [problems, languages] = data ?? [[], []];
  const runnable = languages.filter((l) => l.runnable).map((l) => l.label);

  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-4xl flex-1 px-5 pb-24 pt-14 sm:px-8">
        <h1 className="font-display text-4xl font-semibold text-ink">Coding practice</h1>
        <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-ink-2">
          Solve a problem in the same editor the interview uses. Nothing is timed or scored here, so try different approaches and languages.
        </p>

        {loading && !data && <PageLoading label="Loading problems" />}
        {error && !data && <PageError message={error} onRetry={reload} />}

        {data && (
          <>
            <ul className="mt-10 divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface">
              {problems.map((problem) => (
                <li key={problem.slug}>
                  <Link href={`/practice/${problem.slug}`} className="group flex items-center gap-5 px-6 py-5 transition-colors hover:bg-surface-2/60">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-ink">{problem.title}</p>
                      <p className="mt-1 text-[13px] text-ink-3">
                        {problem.tags.join(", ")}. {problem.total_tests} tests.
                      </p>
                    </div>
                    <DifficultyBadge difficulty={problem.difficulty} />
                    <ArrowUpRight className="size-4 text-ink-3 transition-colors group-hover:text-accent" />
                  </Link>
                </li>
              ))}
            </ul>
            <p className="mt-5 text-[13px] leading-relaxed text-ink-3">
              Code runs in the Judge0 sandbox. {runnable.length} of {languages.length} editor languages can run
              {runnable.length < languages.length ? `: ${runnable.join(", ")}` : ""}.
            </p>
          </>
        )}
      </main>
    </>
  );
}
