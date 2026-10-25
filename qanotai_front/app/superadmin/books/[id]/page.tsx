import { Suspense } from "react";
import { BookDetailView } from "./book-detail";

export default function BookPage() {
  return (
    <Suspense>
      <BookDetailView />
    </Suspense>
  );
}
