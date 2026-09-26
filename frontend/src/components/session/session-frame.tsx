"use client";

import { createContext, useContext, useEffect } from "react";
import { ProctorMonitor } from "@/components/proctor/ProctorMonitor";
import { DisqualifiedPage } from "@/components/session/disqualified-page";
import { api } from "@/lib/api";
import { useProctor } from "@/lib/proctor/use-proctor";
import { useLoad } from "@/lib/use-load";

const SessionProctorContext = createContext<ReturnType<typeof useProctor> | null>(null);

export function useSessionProctor() {
  const proctor = useContext(SessionProctorContext);
  if (!proctor) throw new Error("Camera monitoring is only available inside a session.");
  return proctor;
}

export function SessionFrame({ sessionId, children }: { sessionId: string; children: React.ReactNode }) {
  const proctor = useProctor(sessionId);
  const { data: summary, reload } = useLoad(() => api.session(sessionId), sessionId);
  const ended = proctor.locked || Boolean(summary?.disqualified);

  useEffect(() => {
    if (!proctor.locked) return;
    void document.exitFullscreen?.().catch(() => undefined);
    reload();
  }, [proctor.locked, reload]);

  if (ended) {
    const events = summary?.warnings_log?.length
      ? summary.warnings_log
      : proctor.toasts.map((toast) => ({ type: toast.type, details: toast.details }));
    return (
      <DisqualifiedPage
        sessionId={sessionId}
        warnings={summary?.warnings || proctor.warnings}
        limit={summary?.warning_limit || proctor.limit}
        events={events}
      />
    );
  }

  return (
    <SessionProctorContext.Provider value={proctor}>
      <div className="flex min-h-full flex-col-reverse lg:grid lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="min-w-0">{children}</div>
        <ProctorMonitor proctor={proctor} serverWarnings={summary?.warnings ?? 0} />
      </div>
    </SessionProctorContext.Provider>
  );
}
