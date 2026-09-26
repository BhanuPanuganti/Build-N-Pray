import { Check } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { LinkButton } from "@/components/ui/button";

const rounds = [
  {
    title: "Coding round",
    body: "One timed problem in a full editor. Write in Python, JavaScript, TypeScript, Java, Go and more, run the samples as often as you like, then submit against hidden tests.",
  },
  {
    title: "Project questions",
    body: "The interviewer asks about the projects on your résumé: architecture, the choices you made, how you debugged and tested. You answer out loud.",
  },
  {
    title: "Fundamentals",
    body: "Core concepts the role depends on, from processes and threads to how a request reaches an API. Short, spoken answers.",
  },
];

const feedback = [
  "A score for every answer, with one strength and one thing to improve",
  "Test results, runtime and the likely complexity of your solution",
  "Every camera and browser observation, listed for review rather than judged",
];

function WorkspacePreview() {
  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-surface shadow-float">
      <div className="flex h-10 items-center gap-3 border-b border-line px-4">
        <span className="font-display text-[13px] font-semibold text-ink">Two Sum</span>
        <span className="rounded-full bg-accent-soft px-2 py-0.5 text-[11px] font-medium text-accent">Easy</span>
        <span className="ml-auto rounded-md bg-amber-soft px-2 py-0.5 font-mono text-[11px] font-medium text-amber">17:42</span>
      </div>
      <div className="grid grid-cols-[0.8fr_1.2fr] text-left">
        <div className="border-r border-line p-4">
          <p className="text-[12px] leading-relaxed text-ink-2">
            Given an array of integers <code className="rounded bg-surface-2 px-1 font-mono text-[11px] text-ink">nums</code> and a{" "}
            <code className="rounded bg-surface-2 px-1 font-mono text-[11px] text-ink">target</code>, return the indices of the two numbers that add up to the target.
          </p>
          <div className="mt-4 rounded-lg bg-surface-2 p-3 font-mono text-[11px] leading-relaxed text-ink-2">
            <p>
              <span className="text-ink-3">in </span> 2 7 11 15
            </p>
            <p className="pl-[22px]">9</p>
            <p>
              <span className="text-ink-3">out</span> 0 1
            </p>
          </div>
        </div>
        <pre className="overflow-hidden p-4 font-mono text-[11.5px] leading-[1.75] text-ink">
          <span className="font-semibold text-accent">def</span> two_sum(nums, target):{"\n"}
          {"    "}seen = {"{}"}
          {"\n"}
          {"    "}
          <span className="font-semibold text-accent">for</span> i, n <span className="font-semibold text-accent">in</span> enumerate(nums):{"\n"}
          {"        "}
          <span className="font-semibold text-accent">if</span> target - n <span className="font-semibold text-accent">in</span> seen:{"\n"}
          {"            "}
          <span className="font-semibold text-accent">return</span> [seen[target - n], i]{"\n"}
          {"        "}seen[n] = i
        </pre>
      </div>
      <div className="flex items-center gap-3 border-t border-line bg-surface-2/50 px-4 py-2.5">
        <span className="font-display text-sm font-semibold text-accent">Accepted</span>
        <span className="text-[12px] text-ink-3">7 of 7 tests passed, slowest 41 ms</span>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="mx-auto grid max-w-6xl items-center gap-14 px-5 pb-24 pt-16 sm:px-8 lg:grid-cols-[1fr_1.05fr] lg:pt-24">
          <div>
            <h1 className="font-display text-[44px] font-semibold leading-[1.04] text-ink sm:text-[58px]">Rehearse the technical interview before the real one.</h1>
            <p className="mt-6 max-w-lg text-[17px] leading-relaxed text-ink-2">
              A timed coding round in a real editor, spoken questions drawn from your own résumé, and written feedback on every answer.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <LinkButton href="/setup" size="lg">
                Set up a mock interview
              </LinkButton>
              <LinkButton href="/admin" variant="secondary" size="lg">
                Interview a group
              </LinkButton>
              <LinkButton href="/practice" variant="ghost" size="lg">
                Practice coding problems
              </LinkButton>
            </div>
          </div>
          <WorkspacePreview />
        </section>

        <section className="border-t border-line bg-surface">
          <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
            <h2 className="font-display text-3xl font-semibold text-ink">How a session runs</h2>
            <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-ink-2">
              Paste the job description and your résumé once. The questions are written for that role and those projects.
            </p>
            <ol className="mt-12 grid gap-10 md:grid-cols-3">
              {rounds.map((round, i) => (
                <li key={round.title} className="border-t-2 border-ink pt-5">
                  <p className="font-display text-sm font-semibold text-ink-3">Round {i + 1}</p>
                  <h3 className="mt-1 font-display text-xl font-semibold text-ink">{round.title}</h3>
                  <p className="mt-3 text-[15px] leading-relaxed text-ink-2">{round.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="mx-auto grid max-w-6xl gap-10 px-5 py-20 sm:px-8 md:grid-cols-2">
          <div>
            <h2 className="font-display text-3xl font-semibold text-ink">What you get back</h2>
            <p className="mt-3 max-w-md text-[15px] leading-relaxed text-ink-2">
              A report you can act on the same evening. It explains the score instead of just giving one.
            </p>
          </div>
          <ul className="space-y-4">
            {feedback.map((item) => (
              <li key={item} className="flex gap-3 text-[15px] leading-relaxed text-ink">
                <span className="mt-1 grid size-5 shrink-0 place-items-center rounded-full bg-accent-soft">
                  <Check className="size-3 text-accent" strokeWidth={3} />
                </span>
                {item}
              </li>
            ))}
          </ul>
        </section>
      </main>
      <footer className="border-t border-line">
        <div className="mx-auto max-w-6xl px-5 py-8 text-[13px] text-ink-3 sm:px-8">
          BNB is for practice. Camera and browser monitoring record observations for a person to review; they never decide that someone cheated.
        </div>
      </footer>
    </>
  );
}
