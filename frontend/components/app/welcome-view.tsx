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
