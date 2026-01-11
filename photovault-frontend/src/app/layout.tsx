import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/auth-provider";
import { Toaster } from "sonner";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";

export const metadata: Metadata = {
  title: "PhotoVault",
  description: "Secure photo management system",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundary>
          <AuthProvider>
            {children}
            <Toaster richColors />
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
