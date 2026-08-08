'use client';

import { Button } from '@/components/ui/button';

interface MicPermissionErrorProps {
  onRetry?: () => void;
}

/**
 * Full-screen microphone permission error view — bilingual (Hindi + English)
 * Shown when the browser microphone access is denied.
 */
export function MicPermissionError({ onRetry }: MicPermissionErrorProps) {
  function handleRetry() {
    if (onRetry) {
      onRetry();
    } else {
      window.location.reload();
    }
  }

  return (
    <div
      className="bg-background flex min-h-svh flex-col items-center justify-center px-6 py-16 text-center"
      role="alert"
      aria-live="assertive"
      id="mic-permission-error"
    >
      {/* Icon */}
      <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-destructive/10 text-4xl shadow-inner">
        🎙️
      </div>

      {/* Hindi heading */}
      <h1 className="text-foreground text-2xl font-bold">Microphone ki permission chahiye</h1>
      {/* English sub-heading */}
      <p className="text-muted-foreground mt-1 text-base font-medium">
        Microphone access is required
      </p>

      <p className="text-muted-foreground mt-4 max-w-sm text-sm leading-relaxed">
        Kisan Mitra ko aapki awaaz sunne ke liye microphone ki zarurat hai.
        <br />
        <span className="text-foreground font-medium">
          Kisan Mitra needs your microphone to hear you.
        </span>
      </p>

      {/* Browser instructions */}
      <div className="mt-6 w-full max-w-sm rounded-xl border border-border bg-card px-5 py-4 text-left text-sm shadow-sm">
        <p className="text-foreground mb-3 font-semibold">Browser me allow karo:</p>
        <ol className="text-muted-foreground space-y-2">
          <li className="flex items-start gap-2">
            <span className="text-primary mt-0.5 font-bold">1.</span>
            <span>
              <strong>Chrome:</strong> Click the 🔒 lock icon in the address bar → Site settings →
              Microphone → Allow
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary mt-0.5 font-bold">2.</span>
            <span>
              <strong>Firefox:</strong> Click the 🔒 icon → Connection secure → More information →
              Permissions → Microphone → Allow
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary mt-0.5 font-bold">3.</span>
            <span>
              <strong>Safari:</strong> Safari menu → Settings for this website → Microphone → Allow
            </span>
          </li>
        </ol>
      </div>

      {/* Retry */}
      <Button
        id="mic-retry-button"
        onClick={handleRetry}
        className="mt-8 w-56 rounded-full bg-primary font-semibold text-primary-foreground shadow-md hover:scale-105 transition-transform"
        aria-label="Reload page to try microphone again"
      >
        🔄 Dobara try karo / Try Again
      </Button>

      {/* KVK notice */}
      <p className="text-muted-foreground mt-8 text-xs">
        Expert advice? KVK Helpline:{' '}
        <span className="font-semibold text-primary">1800-180-1551</span>
      </p>
    </div>
  );
}
