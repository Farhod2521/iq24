import { Suspense } from "react";
import { TopicDetailView } from "./topic-detail";

export default function TopicPage() {
  return (
    <Suspense>
      <TopicDetailView />
    </Suspense>
  );
}
