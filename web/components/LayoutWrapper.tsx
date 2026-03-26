"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import UserNav from "@/components/UserNav";

interface LayoutWrapperProps {
  children: React.ReactNode;
}

export default function LayoutWrapper({ children }: LayoutWrapperProps) {
  const pathname = usePathname();
  const isAuthPage = pathname === "/login" || pathname === "/signup";

  if (isAuthPage) {
    return (
      <div className="min-h-screen bg-slate-50 transition-colors duration-200 dark:bg-slate-900">
        {children}
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 transition-colors duration-200 dark:bg-slate-900">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-12 flex-shrink-0 items-center justify-end border-b border-slate-200 bg-white px-4 dark:border-slate-700 dark:bg-slate-800">
          <UserNav />
        </header>
        <main className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-900">
          {children}
        </main>
      </div>
    </div>
  );
}
