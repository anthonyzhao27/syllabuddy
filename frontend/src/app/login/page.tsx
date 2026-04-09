import { Suspense } from "react";
import { LoginPage } from "@/components/login-page";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <LoginPage />
    </Suspense>
  );
}
