import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/Providers";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "ResQ Web — Windows Process Monitoring & Automatic Recovery",
  description:
    "A professional-grade Operating Systems platform for Windows process supervision, unexpected termination detection, and policy-driven recovery.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="light">
      <body className="bg-slate-50 text-slate-900 flex min-h-screen antialiased">
        <Providers>
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0 min-h-screen">
            <Navbar />
            <main className="flex-1 p-6 sm:p-8 overflow-y-auto bg-slate-50">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
