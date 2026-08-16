"use client";

import { useCallback, useEffect, useState } from "react";
import { Terminal } from "lucide-react";
import { SystemHealthBanner } from "@/components/system/system-health-banner";
import { RuntimeConfigCards } from "@/components/system/runtime-config-cards";
import { PipelineArchitectureMap } from "@/components/system/pipeline-architecture-map";
import { getHealth, getSystemInfo, ApiError } from "@/lib/api/client";
import type { HealthResponse, SystemInfoResponse } from "@/types/api";

export function SystemWorkspace() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfoResponse | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState<boolean>(true);
  const [isLoadingInfo, setIsLoadingInfo] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const fetchHealthData = useCallback(async () => {
    setIsLoadingHealth(true);
    setHealthError(null);
    try {
      const h = await getHealth();
      setHealth(h);
      setLastChecked(new Date());
    } catch (err) {
      setHealthError(
        err instanceof ApiError
          ? err.detail
          : err instanceof Error
          ? err.message
          : "Backend is unreachable"
      );
      setHealth(null);
    } finally {
      setIsLoadingHealth(false);
    }
  }, []);

  const fetchSystemInfoData = useCallback(async () => {
    setIsLoadingInfo(true);
    try {
      const info = await getSystemInfo();
      setSystemInfo(info);
    } catch {
      // System info endpoint failed
    } finally {
      setIsLoadingInfo(false);
    }
  }, []);

  const handleRefresh = useCallback(async () => {
    await Promise.all([fetchHealthData(), fetchSystemInfoData()]);
  }, [fetchHealthData, fetchSystemInfoData]);

  useEffect(() => {
    let isMounted = true;

    getHealth()
      .then((h) => {
        if (isMounted) {
          setHealth(h);
          setLastChecked(new Date());
          setIsLoadingHealth(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setHealthError(
            err instanceof ApiError ? err.detail : "Backend unreachable"
          );
          setIsLoadingHealth(false);
        }
      });

    getSystemInfo()
      .then((info) => {
        if (isMounted) {
          setSystemInfo(info);
          setIsLoadingInfo(false);
        }
      })
      .catch(() => {
        if (isMounted) setIsLoadingInfo(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-surface-base px-4 py-8 sm:px-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-2 border-b border-border-subtle pb-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-subtle text-accent shadow-xs">
            <Terminal size={20} />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary sm:text-2xl">
            System Observability & Architecture
          </h1>
        </div>
        <p className="text-xs text-text-secondary sm:text-sm">
          Live service health monitoring, runtime configuration hyperparameters, and pipeline architecture topology.
        </p>
      </div>

      {/* Live Health Status Banner */}
      <section aria-label="Live Service Health">
        <SystemHealthBanner
          health={health}
          isLoading={isLoadingHealth}
          error={healthError}
          lastChecked={lastChecked}
          onRefresh={handleRefresh}
        />
      </section>

      {/* Runtime Configuration Cards */}
      <section aria-label="Runtime Hyperparameters">
        <RuntimeConfigCards
          systemInfo={systemInfo}
          isLoading={isLoadingInfo}
        />
      </section>

      {/* Pipeline Architecture Map */}
      <section aria-label="Pipeline Architecture Map">
        <PipelineArchitectureMap />
      </section>
    </div>
  );
}
