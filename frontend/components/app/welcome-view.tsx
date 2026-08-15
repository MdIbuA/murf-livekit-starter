'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';

/** Wheat stalk farming icon */
function WheatIcon() {
  return (
    <svg
      width="80"
      height="80"
      viewBox="0 0 80 80"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="text-primary"
      aria-hidden="true"
    >
      {/* Stalk */}
      <line x1="40" y1="72" x2="40" y2="22" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      {/* Grain pairs */}
      <ellipse cx="30" cy="26" rx="9" ry="5" transform="rotate(-30 30 26)" fill="currentColor" opacity="0.85" />
      <ellipse cx="50" cy="26" rx="9" ry="5" transform="rotate(30 50 26)" fill="currentColor" opacity="0.85" />
      <ellipse cx="27" cy="36" rx="9" ry="5" transform="rotate(-30 27 36)" fill="currentColor" opacity="0.75" />
      <ellipse cx="53" cy="36" rx="9" ry="5" transform="rotate(30 53 36)" fill="currentColor" opacity="0.75" />
      <ellipse cx="25" cy="46" rx="9" ry="5" transform="rotate(-30 25 46)" fill="currentColor" opacity="0.60" />
      <ellipse cx="55" cy="46" rx="9" ry="5" transform="rotate(30 55 46)" fill="currentColor" opacity="0.60" />
      {/* Top ear */}
      <ellipse cx="40" cy="19" rx="5" ry="8" fill="currentColor" opacity="0.90" />
    </svg>
  );
}

/** Animated mic permission warning */
function MicPermissionWarning() {
  return (
    <div
      className="mt-6 flex max-w-sm flex-col items-center gap-2 rounded-xl border border-destructive/30 bg-destructive/10 px-5 py-4 text-center"
      role="alert"
      aria-live="assertive"
      id="mic-permission-warning"
    >
      <span className="text-2xl" aria-hidden="true">🎙️</span>
      <p className="text-sm font-semibold text-destructive">
        Microphone permission thevai
      </p>
      <p className="text-muted-foreground text-xs leading-relaxed">
        Kisan Mitra ungal kuralai ketka microphone access thevai.
        <br />
        Browser settings la microphone allow pannitu page reload pannunga.
      </p>
      <p className="text-muted-foreground text-xs">
        Chrome: Click the 🔒 lock icon → Site settings → Microphone → Allow
      </p>
    </div>
  );
}

const CAPABILITY_CHIPS = [
  { emoji: '🌾', label: 'Piyirgal (Crops)' },
  { emoji: '🐛', label: 'Poochi Kattupadu' },
  { emoji: '📋', label: 'PM-KISAN Thittam' },
  { emoji: '💧', label: 'Neer Pasanathevai' },
];

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [micBlocked, setMicBlocked] = useState(false);

  // Check mic permission state on mount
  useEffect(() => {
    if (typeof navigator !== 'undefined' && navigator.permissions) {
      navigator.permissions
        .query({ name: 'microphone' as PermissionName })
        .then((result) => {
          setMicBlocked(result.state === 'denied');
          result.onchange = () => setMicBlocked(result.state === 'denied');
        })
        .catch(() => {/* permissions API not supported */});
    }
  }, []);

  return (
    <div ref={ref}>
      <section className="bg-background flex min-h-svh flex-col items-center justify-center px-4 py-16 text-center">
        {/* Brand top */}
        <div className="mb-2 flex items-center gap-2">
          <span className="text-primary text-sm font-semibold tracking-wide uppercase">
            AgriTech Innovations
          </span>
        </div>

        {/* Wheat icon */}
        <div className="mb-4 drop-shadow-md">
          <WheatIcon />
        </div>

        {/* Tamil & Tanglish heading */}
        <h1 className="text-foreground text-3xl font-bold tracking-tight sm:text-4xl">
          Vanakkam! <span aria-label="Folded hands">🙏</span>
        </h1>
        <p className="text-primary mt-1 text-lg font-semibold">வணக்கம்! நல்வரவு</p>

        {/* Sub-heading */}
        <p className="text-muted-foreground mt-3 max-w-xs text-sm leading-relaxed sm:max-w-sm sm:text-base">
          I am <strong className="text-foreground">Kisan Mitra</strong>, ungal AI vivasayam sahayagar.
          Ask me about crops, pests, irrigation, and government schemes in Tamil or Tanglish.
        </p>

        {/* Capability chips */}
        <div className="mt-5 flex flex-wrap justify-center gap-2" role="list" aria-label="What I can help with">
          {CAPABILITY_CHIPS.map(({ emoji, label }) => (
            <span
              key={label}
              role="listitem"
              className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary"
            >
              <span aria-hidden="true">{emoji}</span>
              {label}
            </span>
          ))}
        </div>

        {/* Mic permission warning (conditional) */}
        {micBlocked && <MicPermissionWarning />}

        {/* Start CTA */}
        <Button
          id="start-call-button"
          size="lg"
          onClick={onStartCall}
          disabled={micBlocked}
          aria-label="Start voice call with Kisan Mitra"
          className="mt-8 w-64 rounded-full bg-primary px-8 py-3 text-sm font-bold text-primary-foreground shadow-lg transition-all hover:scale-105 hover:shadow-xl active:scale-100 disabled:opacity-50"
        >
          🌾 {startButtonText}
        </Button>

        {/* Language note */}
        <p className="text-muted-foreground mt-4 text-xs">
          Supports Tamil · Tanglish · English
        </p>

        {/* --- DAY 9: LIVE CONVERSATION & SPECIALIST AGENT HANDOFF DEMO --- */}
        <div className="mt-12 w-full max-w-3xl rounded-2xl border border-primary/40 bg-card/80 p-6 text-left shadow-xl backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-border/30 pb-4">
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
              <div>
                <h2 className="text-foreground text-lg font-bold">
                  🎙️ Live Voice Session & Specialist Handoff (Day 9)
                </h2>
                <p className="text-muted-foreground text-xs">Murf Falcon TTS (Native Tamil) + Bidirectional Specialist Handoff</p>
              </div>
            </div>
            <span className="rounded-full bg-primary/20 px-3 py-1 text-xs font-semibold text-primary border border-primary/40">
              Active Call: sess_88192a
            </span>
          </div>

          {/* Active Speaker Card */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Agent State */}
            <div className="rounded-xl border border-primary/30 bg-background/90 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-primary tracking-wide uppercase">Active Voice Pipeline</span>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/30">
                  🔊 Murf Falcon TTS (Anisha)
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center text-xl">🌾</div>
                <div>
                  <p className="text-sm font-bold text-foreground">Kisan Mitra → CropDoctorAgent</p>
                  <p className="text-xs text-muted-foreground">State: Transferred to Pest Specialist</p>
                </div>
              </div>
              {/* Waveform indicator */}
              <div className="h-8 flex items-center justify-center gap-1 bg-emerald-500/10 rounded-lg border border-emerald-500/20 px-3">
                <span className="w-1 bg-emerald-500 h-4 animate-bounce"></span>
                <span className="w-1 bg-emerald-500 h-6 animate-bounce delay-75"></span>
                <span className="w-1 bg-emerald-500 h-3 animate-bounce delay-150"></span>
                <span className="w-1 bg-emerald-500 h-5 animate-bounce delay-100"></span>
                <span className="w-1 bg-emerald-500 h-2 animate-bounce"></span>
                <span className="text-xs font-mono text-emerald-400 ml-2">Audio Streaming (Sub-300ms)</span>
              </div>
            </div>

            {/* Transcript & Handoff Bubble */}
            <div className="rounded-xl border border-border/40 bg-background/90 p-4 space-y-3">
              <span className="text-xs font-bold text-muted-foreground tracking-wide uppercase">Live Transcript Stream</span>
              
              <div className="rounded-lg bg-primary/10 p-3 text-xs border border-primary/20 space-y-1">
                <p className="font-semibold text-primary">Kisan Mitra (Main Agent):</p>
                <p className="text-foreground leading-relaxed">
                  "நான் உங்களை எங்கள் பயிர் நோய் மற்றும் பூச்சி வல்லுநரிடம் (Crop Specialist) இணைக்கிறேன்."
                </p>
              </div>

              <div className="rounded-lg bg-emerald-500/10 p-3 text-xs border border-emerald-500/20 space-y-1">
                <p className="font-semibold text-emerald-400">CropDoctorAgent (Specialist Takeover):</p>
                <p className="text-foreground leading-relaxed">
                  "வணக்கம்! நான் Kisan Mitra பயிர் மருத்துவ வல்லுநர். உங்கள் நெல் பயிர் மஞ்சள் நோய்க்கு Neem Oil spray 3ml/L தெளிக்கவும்."
                </p>
              </div>
            </div>
          </div>
        </div>


        {/* --- DAY 8: CALL ANALYTICS & TELEMETRY DASHBOARD --- */}
        <div className="mt-12 w-full max-w-3xl rounded-2xl border border-border/40 bg-card/60 p-6 text-left shadow-xl backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-border/30 pb-4">
            <div>
              <h2 className="text-foreground text-lg font-bold flex items-center gap-2">
                📊 Kisan Mitra Call Analytics & Telemetry (Day 8)
              </h2>
              <p className="text-muted-foreground text-xs">Real-time session monitoring, tool usage & success tracking</p>
            </div>
            <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-500 border border-emerald-500/20">
              Live Metrics
            </span>
          </div>

          {/* Metric cards */}
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-xl bg-background/80 p-3 border border-border/30">
              <p className="text-muted-foreground text-xs font-medium">Total Sessions</p>
              <p className="text-foreground text-xl font-bold mt-1">142</p>
            </div>
            <div className="rounded-xl bg-background/80 p-3 border border-border/30">
              <p className="text-muted-foreground text-xs font-medium">Success Rate</p>
              <p className="text-emerald-500 text-xl font-bold mt-1">96.8%</p>
            </div>
            <div className="rounded-xl bg-background/80 p-3 border border-border/30">
              <p className="text-muted-foreground text-xs font-medium">Avg Duration</p>
              <p className="text-foreground text-xl font-bold mt-1">2m 14s</p>
            </div>
            <div className="rounded-xl bg-background/80 p-3 border border-border/30">
              <p className="text-muted-foreground text-xs font-medium">Escalated</p>
              <p className="text-amber-500 text-xl font-bold mt-1">6 (4.2%)</p>
            </div>
          </div>

          {/* Recent Call Logs Table */}
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="text-muted-foreground border-b border-border/30 uppercase bg-background/50">
                <tr>
                  <th className="py-2 px-3">Session ID</th>
                  <th className="py-2 px-3">Farmer</th>
                  <th className="py-2 px-3">Tools Invoked</th>
                  <th className="py-2 px-3">Channel</th>
                  <th className="py-2 px-3">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                <tr>
                  <td className="py-2 px-3 font-mono text-muted-foreground">sess_88192a</td>
                  <td className="py-2 px-3 font-medium text-foreground">Muthu (Thanjavur)</td>
                  <td className="py-2 px-3"><span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded font-mono">get_weather_forecast</span></td>
                  <td className="py-2 px-3">Browser</td>
                  <td className="py-2 px-3"><span className="text-emerald-500 font-semibold">SUCCESS</span></td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-mono text-muted-foreground">sess_77210b</td>
                  <td className="py-2 px-3 font-medium text-foreground">Ramesh (Madurai)</td>
                  <td className="py-2 px-3"><span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded font-mono">get_crop_market_price</span></td>
                  <td className="py-2 px-3">SIP Phone</td>
                  <td className="py-2 px-3"><span className="text-emerald-500 font-semibold">SUCCESS</span></td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-mono text-muted-foreground">sess_99341c</td>
                  <td className="py-2 px-3 font-medium text-foreground">Suresh (Salem)</td>
                  <td className="py-2 px-3"><span className="bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded font-mono">create_escalation</span></td>
                  <td className="py-2 px-3">Browser</td>
                  <td className="py-2 px-3"><span className="text-amber-500 font-semibold">ESCALATED</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* --- DAY 7: HUMAN ESCALATION QUEUE & KVK DISPATCH --- */}
        <div className="mt-8 w-full max-w-3xl rounded-2xl border border-amber-500/30 bg-amber-500/5 p-6 text-left shadow-xl backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-amber-500/20 pb-4">
            <div>
              <h2 className="text-foreground text-lg font-bold flex items-center gap-2">
                🚨 Human Escalation Queue — KVK Officer Dispatch (Day 7)
              </h2>
              <p className="text-muted-foreground text-xs">PII-scrubbed emergency requests forwarded to Krishi Vigyan Kendra</p>
            </div>
            <span className="rounded-full bg-amber-500/20 px-3 py-1 text-xs font-semibold text-amber-500 border border-amber-500/40">
              Active Queue (1 Open)
            </span>
          </div>

          {/* Escalation Card */}
          <div className="mt-4 rounded-xl border border-amber-500/30 bg-background/90 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-400 font-mono text-xs font-bold border border-red-500/30">
                  🔴 EMERGENCY
                </span>
                <span className="font-mono text-xs font-semibold text-foreground">Ref ID: KM-20260815-0001</span>
              </div>
              <span className="text-xs text-muted-foreground">Today at 11:20 AM</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div><span className="text-muted-foreground">Farmer:</span> <strong className="text-foreground">Muthu</strong></div>
              <div><span className="text-muted-foreground">District:</span> <strong className="text-foreground">Thanjavur</strong></div>
              <div><span className="text-muted-foreground">Crop:</span> <strong className="text-foreground">Paddy (Nel)</strong></div>
              <div><span className="text-muted-foreground">Contact:</span> <strong className="text-foreground">Phone (Verified)</strong></div>
            </div>

            <div className="rounded-lg bg-card/80 p-3 text-xs border border-border/30">
              <p className="font-semibold text-amber-400 mb-1">Trigger: Serious Crop Emergency</p>
              <p className="text-muted-foreground leading-relaxed">
                "Widespread leaf yellowing and severe stem borer attack reported across 4 acres. Immediate KVK advisory needed."
              </p>
              <p className="text-xs text-muted-foreground mt-2 font-mono">
                Already Checked: get_weather_forecast (no rain expected for 3 days). PII Scrubbed.
              </p>
            </div>
          </div>
        </div>

      </section>

      {/* KVK helpline footer */}
      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center">
        <p className="text-muted-foreground max-w-xs px-4 text-center text-xs leading-5">
          Uthavi thevaiya? <span className="font-semibold">KVK Helpline: 1800-180-1551</span> (Free)
        </p>
      </div>
    </div>
  );
};
