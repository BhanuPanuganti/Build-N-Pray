"use client";

import { useParams } from "next/navigation";
import { PageError, PageLoading } from "@/components/page-state";
import { CodingWorkspace } from "@/components/workspace/coding-workspace";
import { api } from "@/lib/api";
import { useLoad } from "@/lib/use-load";

export default function PracticeProblemPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data, error, reload } = useLoad(() => Promise.all([api.problem(slug), api.languages()]), slug);

  if (error && !data) {
    return (
      <div className="flex min-h-dvh">
        <PageError message={error} onRetry={reload} />
      </div>
    );
  }
  if (!data) {
    return (
      <div className="flex min-h-dvh">
        <PageLoading label="Opening the editor" />
      </div>
    );
  }

  const [problem, languages] = data;
  return (
    <CodingWorkspace
      problem={problem}
      languages={languages}
      scope="practice"
      backHref="/practice"
      backLabel="All problems"
      onSubmit={(language, code) => api.submitProblem(slug, language, code)}
    />
  );
}
