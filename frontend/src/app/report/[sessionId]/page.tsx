"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, CircleAlert } from "lucide-react";
import { PageError, PageLoading } from "@/components/page-state";
import { SiteHeader } from "@/components/site-header";
import { api } from "@/lib/api";
import { useLoad } from "@/lib/use-load";
import { RoundVerdictCard, turnLabel } from "@/components/report/round-verdict";
import type { Report, VoiceSectionId } from "@/lib/types";

const SECTION_TITLES: Record<string, string> = {
  dsa: "Coding round",
  project: "Project round",
  fundamentals: "Fundamentals round",
  general: "Opening questions",
};

const OBSERVATION_LABELS: Record<string, string> = {
  tab_hidden: "Left the interview tab",
  fullscreen_exit: "Tried to leave full-screen",
  face_missing: "Face not visible",
  multiple_people: "More than one person",
  low_light: "Lighting",
  suspicious_gaze: "Eyes off the screen",
  suspicious_lip_movement: "Mouth movement",
  suspicious_phone: "Phone in view",
  camera_unavailable: "Camera unavailable",
  mouth_motion: "Mouth movement (for review)",
};

const COMMUNICATION_LABELS: Record<string, string> = {
  clarity: "Clarity",
  answer_structure: "Structure",
  evidence: "Evidence",
};

function Heading({ children }: { children: React.ReactNode }) {
  return <h2 className="font-display text-xl font-semibold text-ink">{children}</h2>;
}

export default function ReportPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data: report, error, reload } = useLoad(() => api.report(sessionId), sessionId);

  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-5 pb-24 pt-10 sm:px-8">
        <Link href={`/session/${sessionId}`} className="inline-flex items-center gap-1.5 text-[13px] font-medium text-ink-2 hover:text-ink">
          <ArrowLeft className="size-4" /> Interview map
        </Link>
        {error && !report && <PageError message={error} onRetry={reload} />}
        {!report && !error && <PageLoading label="Building your report" />}
        {report && <ReportBody report={report} />}
      </main>
    </>
  );
}

function ReportBody({ report }: { report: Report }) {
  const scores = Object.entries(report.round_scores);
  const communication = Object.entries(report.communication_assessment).filter(([, text]) => text);
  const observations = report.integrity_observations.filter((o) => o.type !== "vision_check");
  const dsa = report.dsa_result?.evaluation ? report.dsa_result : null;

  return (
    <>
      <header className="mt-8 grid items-end gap-8 border-b border-line pb-10 sm:grid-cols-[auto_1fr]">
        <div>
          <p className="text-sm text-ink-3">Overall</p>
          <p className="font-display text-[88px] font-semibold leading-none text-ink">{report.overall_score}</p>
        </div>
        <div className="sm:pb-2">
          <h1 className="font-display text-2xl font-semibold text-ink">Interview report</h1>
          <p className="mt-2 text-[15px] leading-relaxed text-ink-2">{report.summary}</p>
          <p className="mt-1 text-xs text-ink-3">The overall score averages the rounds you completed. The interview agent wrote this report from your answers and code.</p>
        </div>
      </header>

      {report.disqualified && (
        <div className="mt-8 flex gap-3 rounded-xl bg-danger-soft p-4 text-sm text-danger">
          <CircleAlert className="mt-0.5 size-4 shrink-0" />
          The session was locked after {report.warnings} monitoring warnings. The observations below explain why.
        </div>
      )}

      {communication.length > 0 && (
        <section className="mt-10">
          <Heading>How you communicated</Heading>
          <dl className="mt-4 space-y-3">
            {communication.map(([key, text]) => (
              <div key={key} className="grid gap-1 sm:grid-cols-[10rem_1fr] sm:gap-6">
                <dt className="text-[13px] font-medium text-ink-3">{COMMUNICATION_LABELS[key] ?? key}</dt>
                <dd className="text-[15px] leading-relaxed text-ink-2">{text}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {scores.length > 0 && (
        <section className="mt-10">
          <Heading>Round scores</Heading>
          <dl className="mt-4 grid gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-3">
            {scores.map(([section, score]) => (
              <div key={section} className="bg-surface p-5">
                <dt className="text-[13px] text-ink-3">{SECTION_TITLES[section] ?? section}</dt>
                <dd className="mt-1 font-display text-3xl font-semibold text-ink">{score}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {dsa?.evaluation && (
        <section className="mt-12">
          <Heading>Coding round: {dsa.title}</Heading>
          <div className="mt-4 rounded-xl border border-line bg-surface p-5">
            <p className="text-[15px] text-ink">
              {dsa.evaluation.tests_passed} of {dsa.evaluation.tests_total} tests passed in {dsa.language}.
              {dsa.late ? " Submitted after the time limit." : ""}
            </p>
            <p className="mt-2 text-[14px] leading-relaxed text-ink-2">{dsa.evaluation.complexity_feedback}</p>
            <p className="mt-1 text-[14px] leading-relaxed text-ink-2">{dsa.evaluation.code_quality_feedback}</p>
          </div>
        </section>
      )}

      {Object.entries(report.section_summaries).map(([section, summary]) => {
        const verdict = report.round_verdicts?.[section as VoiceSectionId];
        return (
        <section key={section} className="mt-12">
          <div className="flex items-baseline justify-between gap-4">
            <Heading>{SECTION_TITLES[section] ?? section}</Heading>
            <span className="text-[13px] text-ink-3">
              {verdict ? `Round score ${report.round_scores[section as VoiceSectionId] ?? summary.average_score}` : `Average ${summary.average_score}`}
            </span>
          </div>
          {verdict && <RoundVerdictCard verdict={verdict} />}
          {verdict && <h3 className="mt-8 text-[13px] font-medium text-ink-3">The conversation</h3>}
          <ol className="mt-4 space-y-4">
            {summary.answers.map((item, i) => (
              <li key={i} className="rounded-xl border border-line bg-surface p-5">
                {turnLabel(item.kind) && (
                  <p className="mb-2 text-[12px] font-medium uppercase tracking-wide text-ink-3">
                    {turnLabel(item.kind)}
                    {item.topic ? ` · ${item.topic}` : ""}
                  </p>
                )}
                <div className="flex items-start justify-between gap-4">
                  <p className="font-medium leading-relaxed text-ink">{item.question}</p>
                  <span className="shrink-0 rounded-md bg-surface-2 px-2 py-0.5 font-mono text-[13px] text-ink">
                    {item.skipped || item.feedback.score == null ? "Skipped" : item.feedback.score}
                  </span>
                </div>
                <p className="mt-3 border-l-2 border-line pl-3 text-[14px] leading-relaxed text-ink-2">
                  {item.skipped ? "Skipped" : item.answer}
                </p>
                {item.skipped ? (
                  <p className="mt-4 text-[13px] leading-relaxed text-ink-2">{item.feedback.improvement}</p>
                ) : (
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <p className="text-[13px] leading-relaxed text-ink-2">
                      <span className="block font-medium text-accent">What worked</span>
                      {item.feedback.strength}
                    </p>
                    <p className="text-[13px] leading-relaxed text-ink-2">
                      <span className="block font-medium text-amber">What to improve</span>
                      {item.feedback.improvement}
                    </p>
                  </div>
                )}
              </li>
            ))}
          </ol>
        </section>
        );
      })}

      <section className="mt-12">
        <Heading>Next steps</Heading>
        <ul className="mt-4 space-y-2">
          {report.next_steps.map((step) => (
            <li key={step} className="flex gap-3 text-[15px] text-ink-2">
              <span className="mt-2.5 size-1.5 shrink-0 rounded-full bg-accent" />
              {step}
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-12">
        <Heading>Monitoring observations</Heading>
        <p className="mt-1.5 text-[13px] text-ink-3">Recorded for a person to review. None of these is proof of misconduct.</p>
        {observations.length === 0 ? (
          <p className="mt-4 text-[15px] text-ink-2">Nothing was observed.</p>
        ) : (
          <ul className="mt-4 divide-y divide-line rounded-xl border border-line bg-surface">
            {observations.map((o, i) => (
              <li key={i} className="flex flex-wrap items-baseline gap-x-4 gap-y-1 px-5 py-3">
                <span className="text-sm font-medium text-ink">{OBSERVATION_LABELS[o.type] ?? o.type}</span>
                <span className="flex-1 text-[13px] text-ink-2">{o.details}</span>
                {o.observed_at && o.observed_at.includes("T") && (
                  <span className="font-mono text-xs text-ink-3">{new Date(o.observed_at).toLocaleTimeString()}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
