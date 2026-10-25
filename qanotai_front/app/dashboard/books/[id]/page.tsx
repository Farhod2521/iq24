import { Suspense } from "react";
import { BookView } from "./book-view";

export default function StudentBookPage() {
  return (
    <Suspense>
      <BookView />
    </Suspense>
  );
}
