import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function PrivacyPolicyPage() {
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
            Privacy Policy
          </h1>
          <p className="mb-8 text-sm text-warm-400">
            Last updated: {new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
          </p>

          <div className="space-y-8 text-warm-600">
            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Introduction
              </h2>
              <p>
                Syllabuddy (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) is committed to protecting your privacy.
                This Privacy Policy explains how we collect, use, and safeguard your information when you use our
                syllabus parsing and calendar export service.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Information We Collect
              </h2>

              <h3 className="mb-2 mt-4 font-semibold text-warm-600">Account Information</h3>
              <ul className="ml-4 list-disc space-y-1 text-warm-500">
                <li>Email address (used for authentication)</li>
                <li>Password (securely hashed, never stored in plain text)</li>
              </ul>

              <h3 className="mb-2 mt-4 font-semibold text-warm-600">Uploaded Content</h3>
              <ul className="ml-4 list-disc space-y-1 text-warm-500">
                <li>Syllabus documents (PDF, DOCX files)</li>
                <li>Screenshot images of syllabi (PNG, JPG, WEBP)</li>
                <li>These files are stored securely and associated with your account</li>
              </ul>

              <h3 className="mb-2 mt-4 font-semibold text-warm-600">Extracted Data</h3>
              <ul className="ml-4 list-disc space-y-1 text-warm-500">
                <li>Assignment titles and descriptions</li>
                <li>Due dates and times</li>
                <li>Course codes and names</li>
                <li>Event types (exams, quizzes, projects, etc.)</li>
                <li>Your timezone preference</li>
              </ul>

              <h3 className="mb-2 mt-4 font-semibold text-warm-600">Session Data</h3>
              <ul className="ml-4 list-disc space-y-1 text-warm-500">
                <li>Authentication tokens stored in your browser</li>
                <li>We do not use third-party analytics or tracking cookies</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                How We Use Your Information
              </h2>
              <ul className="ml-4 list-disc space-y-2 text-warm-500">
                <li>
                  <strong className="text-warm-600">Syllabus Parsing:</strong> Your uploaded documents are processed
                  to extract assignment and event information using AI technology.
                </li>
                <li>
                  <strong className="text-warm-600">Calendar Export:</strong> Extracted events can be downloaded
                  as a calendar (.ics) file and imported into Google Calendar, Apple Calendar, or Outlook.
                </li>
                <li>
                  <strong className="text-warm-600">Account Management:</strong> Your email is used to authenticate
                  you and manage your account.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Third-Party Services
              </h2>
              <p className="mb-3">We use the following third-party services to provide our functionality:</p>

              <h3 className="mb-2 mt-4 font-semibold text-warm-600">OpenAI</h3>
              <p className="text-warm-500">
                We use OpenAI&apos;s API to parse your syllabus content and extract assignment information.
                The text from your documents is sent to OpenAI for processing but is not stored by our
                application after extraction is complete.
              </p>

              <h3 className="mb-2 mt-4 font-semibold text-warm-600">Supabase</h3>
              <p className="text-warm-500">
                We use Supabase for authentication and data storage. Your data is stored securely with
                row-level security policies ensuring you can only access your own information. Data is
                hosted in Supabase&apos;s US East (us-east-1) region.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Data Storage & Security
              </h2>
              <ul className="ml-4 list-disc space-y-2 text-warm-500">
                <li>All data is stored in secure, encrypted databases</li>
                <li>Row-level security ensures users can only access their own data</li>
                <li>Passwords are hashed using industry-standard algorithms</li>
                <li>All communications use HTTPS encryption</li>
                <li>
                  Uploaded files are stored in Supabase Storage under a per-user
                  directory protected by row-level security
                </li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Data Retention
              </h2>
              <p className="text-warm-500">
                Syllabus files and extracted events persist until you delete them from the dashboard or delete
                your account. OpenAI processes document text transiently and we do not retain it after
                extraction is complete. Account deletion is immediate and irreversible.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Your Rights
              </h2>
              <p className="mb-3">You have the right to:</p>
              <ul className="ml-4 list-disc space-y-1 text-warm-500">
                <li>Access your personal data</li>
                <li>Delete your syllabi and extracted events</li>
                <li>
                  Delete your account and all associated data instantly from the{" "}
                  <Link
                    href="/settings"
                    className="text-mint-600 transition-colors hover:text-mint-700"
                  >
                    Settings page
                  </Link>
                </li>
                <li>Export your data</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Changes to This Policy
              </h2>
              <p className="text-warm-500">
                We may update this Privacy Policy from time to time. We will notify you of any significant
                changes by posting the new policy on this page with an updated revision date.
              </p>
            </section>

            <section>
              <h2 className="mb-3 font-quicksand text-xl font-semibold text-warm-700">
                Contact Us
              </h2>
              <p className="text-warm-500">
                If you have any questions about this Privacy Policy or our data practices, please contact us
                at{" "}
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
