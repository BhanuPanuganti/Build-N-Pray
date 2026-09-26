"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CodingPreview } from "@/components/admin/coding-preview";
import { Scoreboard } from "@/components/admin/scoreboard";
import { PageError, PageLoading } from "@/components/page-state";
import { SiteHeader } from "@/components/site-header";
import { DifficultyBadge } from "@/components/ui/badge";
import { Button, LinkButton } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useUser } from "@/lib/auth";
import { useLoad } from "@/lib/use-load";

function Board({ id }: { id: string }) {
  const interview = useLoad(() => api.interview(id), id);
  const attempts = useLoad(() => api.attempts(id), `${id}:attempts`);
  const [copied, setCopied] = useState(false);
  const [link, setLink] = useState("");
  const path = interview.data?.path ?? "";

  useEffect(() => {
    if (path) setLink(`${window.location.origin}${path}`);
  }, [path]);

  if (interview.error && !interview.data) return <PageError message={interview.error} onRetry={interview.reload} />;
  if (!interview.data) return <PageLoading label="Loading the scoreboard" />;
  const scored = (attempts.data ?? []).map((row) => row.overall_score).filter((score): score is number => score !== null);
  const average = scored.length ? Math.round(scored.reduce((sum, score) => sum + score, 0) / scored.length) : null;

  async function copy() {
    await navigator.clipboard.writeText(link);
    setCopied(true);
  }

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="text-sm text-ink-3">Scoreboard</p>
          <h1 className="mt-1 font-display text-4xl font-semibold text-ink">{interview.data.role}</h1>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <DifficultyBadge difficulty={interview.data.difficulty} />
            <span className="text-sm text-ink-2">{interview.data.attempt_count} started</span>
            {average !== null && <span className="text-sm text-ink-2">Average {average}</span>}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={copy}>{copied ? "Copied" : "Copy link"}</Button>
          <Button variant="ghost" onClick={() => { interview.reload(); attempts.reload(); }}>Refresh</Button>
        </div>
      </div>
      <p className="mt-6 max-w-2xl text-[15px] leading-relaxed text-ink-2">{interview.data.summary}</p>
      <p className="mt-2 break-all font-mono text-[13px] text-ink-3">{link}</p>

      <div className="mt-10">
        {attempts.error && !attempts.data && <PageError message={attempts.error} onRetry={attempts.reload} />}
        {!attempts.data && !attempts.error && <PageLoading label="Loading attempts" />}
        {attempts.data && <Scoreboard attempts={attempts.data} />}
      </div>

      {interview.data.coding_problem && <CodingPreview problem={interview.data.coding_problem} />}
    </>
  );
}

export default function InterviewBoardPage() {
  const { id } = useParams<{ id: string }>();
  const user = useUser();
  const [ready, setReady] = useState(false);
  useEffect(() => setReady(true), []);

  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-5xl flex-1 px-5 pb-24 pt-14 sm:px-8">
        {!ready && <PageLoading label="Loading the scoreboard" />}
        {ready && user?.role !== "admin" && (
          <div>
            <p className="font-display text-2xl font-semibold text-ink">Interviewer account needed</p>
            <LinkButton href={`/sign-in?next=/admin/interviews/${id}`} className="mt-6">
              Sign in
            </LinkButton>
          </div>
        )}
        {ready && user?.role === "admin" && <Board id={id} />}
      </main>
    </>
  );
}
