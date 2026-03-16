import { EventList } from "./event-list";
import { ExportButtons } from "./export-buttons";

export function ResultsPage() {
  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <h1 className="text-3xl font-bold mb-8">Parsed Assignments</h1>
      <EventList />
      <ExportButtons />
    </main>
  );
}
