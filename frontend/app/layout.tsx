import { Noto_Sans, Public_Sans } from 'next/font/google';
import localFont from 'next/font/local';
import { headers } from 'next/headers';
import { ThemeProvider } from '@/components/app/theme-provider';
import { ThemeToggle } from '@/components/app/theme-toggle';
import { cn } from '@/lib/shadcn/utils';
import { getAppConfig, getStyles } from '@/lib/utils';
import '@/styles/globals.css';

const notoSans = Noto_Sans({
  variable: '--font-noto-sans',
  subsets: ['latin', 'devanagari'],
  weight: ['400', '500', '600', '700'],
});

const publicSans = Public_Sans({
  variable: '--font-public-sans',
  subsets: ['latin'],
});

const commitMono = localFont({
  display: 'swap',
  variable: '--font-commit-mono',
  src: [
    {
      path: '../fonts/CommitMono-400-Regular.otf',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../fonts/CommitMono-700-Regular.otf',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../fonts/CommitMono-400-Italic.otf',
      weight: '400',
      style: 'italic',
    },
    {
      path: '../fonts/CommitMono-700-Italic.otf',
      weight: '700',
      style: 'italic',
    },
  ],
});

interface RootLayoutProps {
  children: React.ReactNode;
}

export default async function RootLayout({ children }: RootLayoutProps) {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);
  const styles = getStyles(appConfig);

  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn(
        notoSans.variable,
        publicSans.variable,
        commitMono.variable,
        'scroll-smooth font-sans antialiased'
      )}
    >
      <head>
        {styles && <style>{styles}</style>}
        <title>Kisan Mitra — आपका कृषि सहायक</title>
        <meta
          name="description"
          content="AI voice assistant for Indian farmers. Crop advice, pest control & government scheme guidance. #VoiceForBharat"
        />
      </head>
      <body className="overflow-x-hidden">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {/* Kisan Mitra header */}
          <header className="fixed top-0 left-0 z-50 hidden w-full flex-row items-center justify-between px-6 py-4 md:flex">
            <div className="flex items-center gap-2">
              {/* Wheat icon */}
              <svg
                width="28"
                height="28"
                viewBox="0 0 32 32"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="text-primary"
              >
                <path
                  d="M16 28V10M16 10C16 10 12 8 10 4C14 4 17 7 16 10ZM16 10C16 10 20 8 22 4C18 4 15 7 16 10ZM16 14C16 14 11 12 9 8C13 7 17 11 16 14ZM16 14C16 14 21 12 23 8C19 7 15 11 16 14ZM16 19C16 19 11 17 9 13C13 12 17 16 16 19ZM16 19C16 19 21 17 23 13C19 12 15 16 16 19Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span className="text-primary text-base font-bold tracking-tight">
                Kisan Mitra
              </span>
              <span className="text-muted-foreground text-xs">| आपका कृषि सहायक</span>
            </div>
            <span className="text-muted-foreground font-mono text-xs font-semibold tracking-wider uppercase">
              Powered by{' '}
              <a
                target="_blank"
                rel="noopener noreferrer"
                href="https://murf.ai"
                className="text-primary underline underline-offset-4"
              >
                Murf Falcon
              </a>{' '}
              · #VoiceForBharat
            </span>
          </header>

          {children}

          <div className="group fixed bottom-0 left-1/2 z-50 mb-2 -translate-x-1/2">
            <ThemeToggle className="translate-y-20 transition-transform delay-150 duration-300 group-hover:translate-y-0" />
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
