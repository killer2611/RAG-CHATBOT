"use client";

import { memo, useState } from "react";
import { Sliders, Moon, Sun, Monitor, Eye, ShieldCheck } from "lucide-react";
import { useTheme } from "@/components/providers/theme-provider";

export const SettingsWorkspace = memo(function SettingsWorkspace() {
  const { theme, setTheme } = useTheme();
  const [motionPreference, setMotionPreference] = useState<"standard" | "reduced">("standard");
  const [density, setDensity] = useState<"comfortable" | "compact">("comfortable");

  return (
    <div className="min-h-screen bg-surface-base px-4 py-8 sm:px-8 max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-2 border-b border-border-subtle pb-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-subtle text-accent shadow-xs">
            <Sliders size={20} />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary sm:text-2xl">
            Platform Preferences & Settings
          </h1>
        </div>
        <p className="text-xs text-text-secondary sm:text-sm">
          Customize workspace appearance, motion preferences, and client UI options.
        </p>
      </div>

      <div className="space-y-6">
        {/* Appearance / Theme */}
        <section className="rounded-2xl border border-border-subtle bg-surface-raised p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-text-primary border-b border-border-subtle pb-3">
            <Eye size={16} className="text-accent" />
            <span>Theme & Visual Appearance</span>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { id: "dark", label: "Dark Mode", desc: "Default graphite theme", icon: <Moon size={16} /> },
              { id: "light", label: "Light Mode", desc: "High contrast slate", icon: <Sun size={16} /> },
              { id: "system", label: "System Sync", desc: "Follow OS setting", icon: <Monitor size={16} /> },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTheme(t.id as "dark" | "light" | "system")}
                className={`flex flex-col items-start rounded-xl border p-4 text-left transition-all ${
                  theme === t.id
                    ? "border-accent bg-surface-base shadow-sm ring-1 ring-accent text-text-primary"
                    : "border-border-subtle bg-surface-base/50 text-text-secondary hover:border-border-default hover:bg-surface-base"
                }`}
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <span className="p-1.5 rounded-lg bg-surface-elevated text-accent">
                    {t.icon}
                  </span>
                  {theme === t.id && (
                    <span className="h-2 w-2 rounded-full bg-accent" />
                  )}
                </div>
                <div className="text-xs font-semibold text-text-primary">{t.label}</div>
                <div className="text-[11px] text-text-tertiary mt-0.5">{t.desc}</div>
              </button>
            ))}
          </div>
        </section>

        {/* UI Density & Motion */}
        <section className="rounded-2xl border border-border-subtle bg-surface-raised p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-text-primary border-b border-border-subtle pb-3">
            <Sliders size={16} className="text-accent" />
            <span>Accessibility & Motion Behavior</span>
          </div>

          <div className="space-y-4 text-xs">
            {/* Motion Preference */}
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-text-primary">Motion Preferences</div>
                <div className="text-text-tertiary">
                  Respects system <code className="font-mono">prefers-reduced-motion</code> media query.
                </div>
              </div>
              <select
                value={motionPreference}
                onChange={(e) => setMotionPreference(e.target.value as "standard" | "reduced")}
                aria-label="Motion preference"
                className="rounded-lg border border-border-subtle bg-surface-base px-3 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none"
              >
                <option value="standard">Standard Motion</option>
                <option value="reduced">Reduced Motion</option>
              </select>
            </div>

            {/* Layout Density */}
            <div className="flex items-center justify-between pt-3 border-t border-border-subtle/50">
              <div>
                <div className="font-semibold text-text-primary">Workspace Density</div>
                <div className="text-text-tertiary">
                  Adjust vertical padding and line spacing across conversation threads.
                </div>
              </div>
              <select
                value={density}
                onChange={(e) => setDensity(e.target.value as "comfortable" | "compact")}
                aria-label="Layout density"
                className="rounded-lg border border-border-subtle bg-surface-base px-3 py-1.5 text-xs text-text-primary focus:border-accent focus:outline-none"
              >
                <option value="comfortable">Comfortable (Default)</option>
                <option value="compact">Compact Density</option>
              </select>
            </div>
          </div>
        </section>

        {/* Technical Governance Notice */}
        <section className="rounded-2xl border border-border-subtle bg-surface-raised p-6 shadow-sm space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-text-primary">
            <ShieldCheck size={16} className="text-success" />
            <span>Security & Governance Policy</span>
          </div>
          <p className="text-xs leading-relaxed text-text-secondary">
            Runtime hyperparameters (model selection, chunk sizes, thresholds) are securely governed on the backend. No API keys, credentials, or internal filesystem paths are exposed or mutable from the client browser interface.
          </p>
        </section>
      </div>
    </div>
  );
});
