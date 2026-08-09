'use client';

import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1 },
    hidden: { opacity: 0 },
  },
  initial: 'hidden' as const,
  animate: 'visible' as const,
  exit: 'hidden' as const,
  transition: { duration: 0.5, ease: 'linear' as const },
};

/** Connecting spinner shown between clicking Start and the session becoming live */
function ConnectingView() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-5 px-4 text-center">
      {/* Spinning wheat ring */}
      <div className="relative flex h-20 w-20 items-center justify-center" aria-hidden="true">
        <div className="absolute inset-0 animate-spin rounded-full border-4 border-primary/20 border-t-primary" />
        <span className="text-3xl">🌾</span>
      </div>
      <div>
        <p className="text-foreground text-lg font-semibold">Inaigirathu… / Connecting</p>
        <p className="text-muted-foreground text-sm">Connecting you to Kisan Mitra</p>
      </div>
    </div>
  );
}

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, isConnecting, start } = useSessionContext();
  const { resolvedTheme } = useTheme();

  return (
    <AnimatePresence mode="wait">
      {/* Ready — not yet started */}
      {!isConnected && !isConnecting && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={start}
        />
      )}

      {/* Connecting spinner */}
      {isConnecting && !isConnected && (
        <motion.div key="connecting" {...VIEW_MOTION_PROPS}>
          <ConnectingView />
        </motion.div>
      )}

      {/* Active session */}
      {isConnected && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}
