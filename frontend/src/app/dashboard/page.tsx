import { Suspense } from "react";
import { DashboardPage } from "@/components/dashboard-page";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <DashboardPage />
    </Suspense>
  );
}
