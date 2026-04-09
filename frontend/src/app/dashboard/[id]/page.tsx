import { Suspense } from "react";
import { SyllabusDetailPage } from "@/components/syllabus-detail-page";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <SyllabusDetailPage />
    </Suspense>
  );
}
