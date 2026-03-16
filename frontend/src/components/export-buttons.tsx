export function ExportButtons() {
  return (
    <div className="flex gap-4 mt-8">
      {/* TODO: Google Calendar export */}
      {/* TODO: Apple Calendar (.ics) export */}
      {/* TODO: Outlook export */}
      <button className="px-4 py-2 rounded bg-zinc-200 dark:bg-zinc-800 text-sm" disabled>
        Google Calendar
      </button>
      <button className="px-4 py-2 rounded bg-zinc-200 dark:bg-zinc-800 text-sm" disabled>
        Apple Calendar
      </button>
      <button className="px-4 py-2 rounded bg-zinc-200 dark:bg-zinc-800 text-sm" disabled>
        Outlook
      </button>
    </div>
  );
}
