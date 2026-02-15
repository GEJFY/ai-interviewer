import type { Metadata } from 'next';
import { Inter, Noto_Sans_JP } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { ThemeProvider } from '@/components/theme-provider';
import { Toaster } from '@/components/ui/toast';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

const notoSansJP = Noto_Sans_JP({
  subsets: ['latin'],
  variable: '--font-noto-sans-jp',
});

export const metadata: Metadata = {
  title: 'AI Interview Tool - GRC Advisory',
  description: 'AI-powered interview system for GRC advisory services',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja" suppressHydrationWarning>
      <body className={`${inter.variable} ${notoSansJP.variable} font-sans`}>
        <ThemeProvider>
          <Providers>
            {children}
            <Toaster />
          </Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}
