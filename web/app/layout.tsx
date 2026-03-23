import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import UserNav from "@/components/UserNav";
import { GlobalProvider } from "@/context/GlobalContext";
import ThemeScript from "@/components/ThemeScript";
import LayoutWrapper from "@/components/LayoutWrapper";
import { I18nClientBridge } from "@/i18n/I18nClientBridge";

// Use Inter font with swap display for better loading
const font = Inter({
  subsets: ["latin"],
  display: "swap",
  fallback: ["system-ui", "sans-serif"],
});

export const metadata: Metadata = {
  title: "EducAgent – An Agentic Causality Tutor",
  description: "An Agentic Causality Tutor Embedded in Modern Copilots",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <ThemeScript />
      </head>
      <body className={font.className}>
        <GlobalProvider>
          <I18nClientBridge>
            <LayoutWrapper>
              <div className="flex h-screen bg-slate-50 dark:bg-slate-900 overflow-hidden transition-colors duration-200">
                <Sidebar />
                <div className="flex-1 flex flex-col overflow-hidden">
                  <header className="flex-shrink-0 flex items-center justify-end px-4 h-12 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
                    <UserNav />
                  </header>
                  <main className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-900">
                    {children}
                  </main>
                </div>
              </div>
            </LayoutWrapper>
          </I18nClientBridge>
        </GlobalProvider>
      </body>
    </html>
  );
}
