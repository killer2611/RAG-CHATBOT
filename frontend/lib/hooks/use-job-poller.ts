"use client";

import { useCallback, useEffect, useState } from "react";
import { getEvaluateResults, getEvaluateStatus } from "@/lib/api/client";
import type { EvaluationResultsResponse, JobStatus } from "@/types/api";

const BACKOFF_SCHEDULE_MS = [1000, 2000, 3000, 5000];
const MAX_BACKOFF_MS = 5000;

interface UseJobPollerReturn {
  jobStatus: JobStatus | null;
  results: EvaluationResultsResponse | null;
  isPolling: boolean;
  error: string | null;
  startPolling: (jobId: string) => void;
  stopPolling: () => void;
}

/**
 * Custom hook providing bounded backoff polling for background evaluation jobs.
 *
 * Rules:
 * - Bounded backoff: 1s -> 2s -> 3s -> 5s (capped at 5s).
 * - Automatic termination on completed / failed states.
 * - Auto-fetch structured results on completion (no raw file paths exposed).
 * - Guaranteed unmount and dependency cleanup with zero duplicate polling loops.
 */
export function useJobPoller(initialJobId?: string | null): UseJobPollerReturn {
  const [jobId, setJobId] = useState<string | null>(initialJobId ?? null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [results, setResults] = useState<EvaluationResultsResponse | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(Boolean(initialJobId));
  const [error, setError] = useState<string | null>(null);

  const startPolling = useCallback((newJobId: string) => {
    setJobId(newJobId);
    setJobStatus(null);
    setResults(null);
    setError(null);
    setIsPolling(true);
  }, []);

  const stopPolling = useCallback(() => {
    setJobId(null);
    setIsPolling(false);
  }, []);

  useEffect(() => {
    if (!jobId) return;

    let isMounted = true;
    let timerId: NodeJS.Timeout | null = null;
    let attempt = 0;

    async function poll() {
      if (!isMounted || !jobId) return;

      try {
        const status = await getEvaluateStatus(jobId);
        if (!isMounted) return;

        setJobStatus(status);

        if (status.status === "completed") {
          setIsPolling(false);
          try {
            const res = await getEvaluateResults(jobId);
            if (isMounted) {
              setResults(res);
            }
          } catch (resErr) {
            if (isMounted) {
              setError(
                resErr instanceof Error
                  ? resErr.message
                  : "Failed to fetch evaluation results"
              );
            }
          }
          return;
        }

        if (status.status === "failed") {
          setIsPolling(false);
          setError(status.error ?? status.message ?? "Evaluation failed");
          return;
        }

        const delay =
          attempt < BACKOFF_SCHEDULE_MS.length
            ? BACKOFF_SCHEDULE_MS[attempt]
            : MAX_BACKOFF_MS;
        attempt += 1;

        timerId = setTimeout(poll, delay);
      } catch (err) {
        if (!isMounted) return;
        setIsPolling(false);
        setError(err instanceof Error ? err.message : "Polling request failed");
      }
    }

    poll();

    return () => {
      isMounted = false;
      if (timerId) clearTimeout(timerId);
    };
  }, [jobId]);

  return {
    jobStatus,
    results,
    isPolling,
    error,
    startPolling,
    stopPolling,
  };
}
