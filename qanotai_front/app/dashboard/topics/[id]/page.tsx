import { Suspense } from "react";
import { TestView } from "./test-view";

export default function StudentTestPage() {
  return (
    <Suspense>
      <TestView />
    </Suspense>
  );
}
