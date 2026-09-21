import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen px-6 py-12 md:px-8">
      <div className="mx-auto max-w-3xl">
        <Link
          href="/"
          className="mb-8 inline-flex items-center gap-2 text-sm text-warm-500 transition-colors hover:text-warm-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>

        <div className="rounded-2xl border border-white/70 bg-white/85 p-8 shadow-lg md:p-12">
          <h1 className="mb-2 font-quicksand text-3xl font-bold text-warm-700 md:text-4xl">
            Terms of Service
          </h1>
          <p className="mb-8 text-sm text-warm-400">
            Last updated:{" "}
            {new Date().toLocaleDateString("en-US", {
              month: "long",
              day: "numeric",
              year: "numeric",
            })}
          </p>

          <div className="space-y-8 text-warm-600">
            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Acceptance of Terms
              </h2>
              <p>
                By accessing or using Syllabuddy (&quot;the Service&quot;), you agree to be bound by these
                Terms of Service (&quot;Terms&quot;). If you do not agree to these Terms, do not use the
                Service.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Eligibility
              </h2>
              <p className="text-warm-500">
                You must be at least 13 years old to use the Service. The Service is intended for use in
                the United States; if you access it from elsewhere, you do so at your own risk and remain
                responsible for compliance with local laws.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Account & Authentication
              </h2>
              <p className="text-warm-500">
                You are responsible for safeguarding access to your account and for any activity that occurs
                under it. You agree to use accurate information and to notify us promptly of any unauthorized
                access.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                License to Use the Service
              </h2>
              <p className="text-warm-500">
                Subject to these Terms, we grant you a limited, non-exclusive, non-transferable, revocable
                license to access and use the Service for your personal, non-commercial academic use.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                User Content
              </h2>
              <p className="text-warm-500">
                You retain ownership of any syllabi, documents, or other content you upload (&quot;User
                Content&quot;). By uploading User Content, you grant Syllabuddy a worldwide, non-exclusive
                license to host, process, and display that content solely to provide the Service to you,
                including transmitting text to third-party AI providers for extraction.
              </p>
              <p className="mt-3 text-warm-500">
                You represent that you have the right to upload the User Content and that doing so does not
                violate any third party&apos;s rights or applicable law.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Prohibited Use
              </h2>
              <ul className="ml-4 list-disc space-y-1 text-warm-500">
                <li>Uploading content you do not have the right to upload</li>
                <li>Attempting to disrupt, probe, or reverse-engineer the Service</li>
                <li>Using the Service to harass, defraud, or harm others</li>
                <li>Automated scraping or excessive request volume</li>
                <li>Using the Service to violate any law or regulation</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                AI Extraction Disclaimer
              </h2>
              <p className="text-warm-500">
                Syllabuddy uses AI to extract assignments and due dates from your uploaded materials. AI
                output may be inaccurate, incomplete, or out of date. You are responsible for verifying
                every extracted item against the original syllabus before relying on it. Syllabuddy is not
                liable for missed deadlines, incorrect dates, or any consequences resulting from reliance
                on extracted data.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Third-Party Services
              </h2>
              <p className="text-warm-500">
                The Service relies on third-party providers (OpenAI for extraction, Supabase for storage and
                authentication). See our{" "}
                <Link
                  href="/privacy"
                  className="text-mint-600 transition-colors hover:text-mint-700"
                >
                  Privacy Policy
                </Link>{" "}
                for details. Your use of those providers is subject to their respective terms.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Termination
              </h2>
              <p className="text-warm-500">
                You may delete your account at any time from the{" "}
                <Link
                  href="/settings"
                  className="text-mint-600 transition-colors hover:text-mint-700"
                >
                  Settings page
                </Link>
                . We may suspend or terminate your access to the Service if you violate these Terms or if
                continued provision becomes impractical.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Disclaimers
              </h2>
              <p className="text-warm-500">
                THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES OF
                ANY KIND, WHETHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION WARRANTIES OF
                MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. WE DO NOT WARRANT
                THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR-FREE, OR THAT EXTRACTED DATA WILL BE ACCURATE.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Limitation of Liability
              </h2>
              <p className="text-warm-500">
                TO THE MAXIMUM EXTENT PERMITTED BY LAW, SYLLABUDDY AND ITS OPERATORS WILL NOT BE LIABLE FOR
                ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING OUT OF YOUR
                USE OF THE SERVICE. OUR TOTAL LIABILITY FOR ANY CLAIM ARISING OUT OF THE SERVICE SHALL NOT
                EXCEED ONE HUNDRED U.S. DOLLARS (USD $100).
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Governing Law
              </h2>
              <p className="text-warm-500">
                These Terms are governed by the laws of the State of California, United States, without
                regard to conflict-of-laws principles. Any disputes will be resolved exclusively in the
                state or federal courts located in California.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Changes to These Terms
              </h2>
              <p className="text-warm-500">
                We may update these Terms from time to time. Significant changes will be reflected by an
                updated revision date at the top of this page. Continued use of the Service after changes
                take effect constitutes acceptance.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Contact
              </h2>
              <p className="text-warm-500">
                Questions about these Terms? Email{" "}
                <a
                  href="mailto:privacy@syllabuddy.com"
                  className="text-mint-600 transition-colors hover:text-mint-700"
                >
                  privacy@syllabuddy.com
                </a>
                .
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
