import { Suspense } from "react";
import { SubjectsView } from "./subjects-view";

export default function SubjectsPage() {
  return (
    <Suspense>
      <SubjectsView />
    </Suspense>
  );
}
