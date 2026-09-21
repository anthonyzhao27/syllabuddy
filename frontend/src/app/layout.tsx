import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import { Footer } from "@/components/footer";
import "./globals.css";

const SITE_URL = "https://syllabuddy-pi.vercel.app";
const SITE_DESCRIPTION =
  "Extract assignments and due dates from your course syllabi";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: "Syllabuddy", template: "%s | Syllabuddy" },
  description: SITE_DESCRIPTION,
  applicationName: "Syllabuddy",
  openGraph: {
    type: "website",
    url: SITE_URL,
    siteName: "Syllabuddy",
    title: "Syllabuddy",
    description: SITE_DESCRIPTION,
    images: [{ url: "/opengraph-image", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Syllabuddy",
    description: SITE_DESCRIPTION,
    images: ["/opengraph-image"],
  },
  icons: { icon: "/icon.png" },
  manifest: "/manifest.webmanifest",
  verification: {
    google: "yFuhT_4lbxBNRSGIZMglaXW6tPPn_s5-eMwkUnD0N7k",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased flex min-h-screen flex-col">
        <Providers>
          <div className="flex-1">{children}</div>
        </Providers>
        <Footer />
      </body>
    </html>
  );
}
