"use client";

import { Button } from "@/components/ui/button";
import type { useProctor } from "@/lib/proctor/use-proctor";

export function ProctorMonitor({ proctor }: { proctor: ReturnType<typeof useProctor> }) {
  const { videoRef, status, warnings, limit, toasts, signals, running, starting, locked, start } = proctor;

  return (
    <aside className="flex flex-col gap-4 border-line bg-surface p-4 lg:border-l">
      <div className="pointer-events-none fixed inset-x-0 top-4 z-[80] flex flex-col items-center gap-2 px-4">
        {toasts.map((toast) => (
          <div key={toast.id} role="alert" className="pointer-events-auto w-full max-w-sm rounded-xl bg-danger px-4 py-3 text-white shadow-float">
            <p className="text-sm font-semibold">{toast.title}</p>
            <p className="mt-1 text-sm leading-5 text-white/90">{toast.detail}</p>
            <p className="mt-2 text-xs font-medium tracking-wide text-white/80">
              Warning {toast.count} of {toast.limit}
              {toast.locked ? " · Session locked" : ""}
            </p>
          </div>
        ))}
      </div>
      <div>
        <h2 className="font-display text-base font-semibold">Camera monitoring</h2>
        <p className="mt-1 text-sm leading-5 text-ink-3">Eye direction is an observation for review. It is not a cheating verdict.</p>
      </div>
      <video ref={videoRef} className="aspect-video w-full rounded-lg bg-black object-cover -scale-x-100" autoPlay muted playsInline />
      <p className="min-h-10 text-sm leading-5 text-ink-2" aria-live="polite">{status}</p>
      {signals && running ? (
        <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-xs">
          <div>
            <dt className="text-ink-3">Face</dt>
            <dd className="font-medium">{signals.faceVisible ? "Visible" : "Not visible"}</dd>
          </div>
          <div>
            <dt className="text-ink-3">People</dt>
            <dd className="font-medium">{signals.people}</dd>
          </div>
          <div>
            <dt className="text-ink-3">Gaze</dt>
            <dd className="font-medium">{signals.gazeAwaySeconds > 0 ? `Away ${signals.gazeAwaySeconds.toFixed(1)}s` : "On screen"}</dd>
          </div>
          <div>
            <dt className="text-ink-3">Mouth</dt>
            <dd className="font-medium">{signals.mouthSeconds > 0 ? `Moving ${signals.mouthSeconds.toFixed(1)}s` : "Still"}</dd>
          </div>
        </dl>
      ) : null}
      <p className="text-sm font-medium">Warnings: {warnings} / {limit}</p>
      <Button className="w-full" onClick={() => void start()} disabled={starting || running || locked}>
        {locked ? "Monitoring locked" : starting ? "Starting camera…" : running ? "Monitoring active" : "Enable camera"}
      </Button>
    </aside>
  );
}
