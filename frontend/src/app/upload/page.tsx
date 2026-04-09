import { Suspense } from "react";
import { UploadPage } from "@/components/upload-page";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <UploadPage />
    </Suspense>
  );
}
