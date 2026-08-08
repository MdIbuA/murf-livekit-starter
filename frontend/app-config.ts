export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Kisan Mitra',
  pageTitle: 'Kisan Mitra — आपका कृषि सहायक',
  pageDescription:
    'AI voice assistant for Indian farmers. Crop advice, pest control, and government scheme guidance — powered by Murf Falcon TTS. #VoiceForBharat',

  // Chat input enabled so users can type questions in any language
  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: false,

  logo: '/murf-logo.svg',
  logoDark: '/murf-logo-dark.svg',
  accent: '#16a34a',
  accentDark: '#4ade80',
  startButtonText: 'Baat Karo / Start Call',

  // Aura visualizer in crop-green
  audioVisualizerType: 'aura',
  audioVisualizerColor: '#16a34a',
  audioVisualizerColorDark: '#4ade80',
  audioVisualizerColorShift: 0.25,

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
