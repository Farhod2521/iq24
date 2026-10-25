import { Suspense } from "react";
import { UsersView } from "./users-view";

export default function UsersPage() {
  return (
    <Suspense>
      <UsersView />
    </Suspense>
  );
}
