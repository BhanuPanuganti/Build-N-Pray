"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { DocumentInput } from "@/components/setup/document-input";
import { SiteHeader } from "@/components/site-header";
import { PageError, PageLoading } from "@/components/page-state";
import { Button, LinkButton } from "@/components/ui/button";
import { Field, Textarea } from "@/components/ui/field";
import { DifficultyBadge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { useUser } from "@/lib/auth";
import { useLoad } from "@/lib/use-load";

export default function InterviewLinkPage() {
  const { token } = useParams<{ token: string }>();
  const router = useRouter();
  const user = useUser();
  const { data, error, reload } = useLoad(() => api.publicInterview(token), token);
  const [ready, setReady] = useState(false);
  const [resume, setResume] = useState("");
  const [goal, setGoal] = useState("");
  const [busy, setBusy] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => setReady(true), []);

  const canStart = resume.trim().length >= 10 && goal.trim().length >= 5;
  const next = `/i/${token}`;

  async function start(event: React.FormEvent) {
    event.preventDefault();
    if (!canStart) return;
    setBusy(true);
    setSubmitError(null);
    try {
      const { session_id } = await api.joinInterview(token, resume.trim(), goal.trim());
      router.push(`/session/${session_id}`);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : "Could not start the interview.");
      setBusy(false);
    }
  }

  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl flex-1 px-5 pb-24 pt-14 sm:px-8">
        {error && !data && <PageError message={error} onRetry={reload} />}
        {!data && !error && <PageLoading label="Loading the interview" />}
        {data && (
          <>
            <p className="text-sm text-ink-3">Interview</p>
            <h1 className="mt-1 font-display text-4xl font-semibold text-ink">{data.role}</h1>
            <div className="mt-4">
              <DifficultyBadge difficulty={data.difficulty} />
            </div>
            <p className="mt-6 text-[15px] leading-relaxed text-ink-2">{data.summary}</p>
            <div className="mt-8 whitespace-pre-wrap rounded-2xl border border-line bg-surface p-6 text-[15px] leading-relaxed text-ink-2">{data.job_description}</div>
            <ul className="mt-6 space-y-1 text-sm text-ink-2">
              {data.dsa_enabled && <li>Coding round, {data.dsa_duration_minutes} minutes, written for this job</li>}
              <li>{data.project_question_count} project questions from your résumé</li>
              <li>{data.fundamentals_question_count} fundamentals questions from this job</li>
            </ul>
            {!ready ? null : !user ? (
              <div className="mt-10 rounded-2xl border border-line bg-surface p-6">
                <p className="font-display text-lg font-semibold text-ink">Sign in to begin</p>
                <p className="mt-1 text-sm text-ink-2">The interview is tied to your name and email so the interviewer can see your scores.</p>
                <LinkButton href={`/sign-in?next=${encodeURIComponent(next)}`} className="mt-5">
                  Sign in
                </LinkButton>
              </div>
            ) : (
              <form onSubmit={start} className="mt-10 space-y-6">
                <p className="text-sm text-ink-2">Continuing as {user.name}.</p>
                <Field label="Résumé">
                  {(id) => <DocumentInput id={id} value={resume} onChange={setResume} minLength={10} placeholder="Projects, what you built, the technologies you used…" />}
                </Field>
                <Field label="What do you want to get better at?">
                  {(id) => <Textarea id={id} value={goal} onChange={(e) => setGoal(e.target.value)} className="min-h-20" />}
                </Field>
                {submitError && <p className="text-[13px] text-danger">{submitError}</p>}
                <Button type="submit" size="lg" disabled={!canStart} loading={busy}>
                  Start interview
                </Button>
              </form>
            )}
          </>
        )}
      </main>
    </>
  );
}
