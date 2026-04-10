"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { motion } from "framer-motion";
import {
  Calendar,
  CheckCircle2,
  Clock,
  FileText,
  FlaskConical,
  FolderKanban,
  GraduationCap,
  HelpCircle,
  MessageSquare,
  MoreHorizontal,
  Pencil,
  Presentation,
  Trash2,
  Flag,
} from "lucide-react";
import type { EventType, SavedEvent, SavedEventUpdateInput } from "@/types";
import { ConfirmDialog } from "./confirm-dialog";

type EventListProps = {
  events: SavedEvent[];
  onUpdate: (id: string, updates: SavedEventUpdateInput) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
};

type EventConfig = {
  icon: ReactNode;
  borderColor: string;
  bgColor: string;
  label: string;
};

function formatTime12Hour(time: string): string {
  const [hours, minutes] = time.split(":").map(Number);
  const period = hours >= 12 ? "PM" : "AM";
  const hours12 = hours % 12 || 12;
  return `${hours12}:${minutes.toString().padStart(2, "0")} ${period}`;
}

const EVENT_CONFIG: Record<EventType, EventConfig> = {
  assignment: {
    icon: <FileText className="h-4 w-4" />,
    borderColor: "border-l-event-assignment",
    bgColor: "bg-event-assignment-bg",
    label: "Assignment",
  },
  exam: {
    icon: <GraduationCap className="h-4 w-4" />,
    borderColor: "border-l-event-exam",
    bgColor: "bg-event-exam-bg",
    label: "Exam",
  },
  quiz: {
    icon: <HelpCircle className="h-4 w-4" />,
    borderColor: "border-l-event-quiz",
    bgColor: "bg-event-quiz-bg",
    label: "Quiz",
  },
  project: {
    icon: <FolderKanban className="h-4 w-4" />,
    borderColor: "border-l-event-project",
    bgColor: "bg-event-project-bg",
    label: "Project",
  },
  lab: {
    icon: <FlaskConical className="h-4 w-4" />,
    borderColor: "border-l-event-lab",
    bgColor: "bg-event-lab-bg",
    label: "Lab",
  },
  presentation: {
    icon: <Presentation className="h-4 w-4" />,
    borderColor: "border-l-event-presentation",
    bgColor: "bg-event-presentation-bg",
    label: "Presentation",
  },
  milestone: {
    icon: <Flag className="h-4 w-4" />,
    borderColor: "border-l-event-milestone",
    bgColor: "bg-event-milestone-bg",
    label: "Milestone",
  },
  deadline: {
    icon: <Clock className="h-4 w-4" />,
    borderColor: "border-l-event-deadline",
    bgColor: "bg-event-deadline-bg",
    label: "Deadline",
  },
  discussion: {
    icon: <MessageSquare className="h-4 w-4" />,
    borderColor: "border-l-event-discussion",
    bgColor: "bg-event-discussion-bg",
    label: "Discussion",
  },
  other: {
    icon: <MoreHorizontal className="h-4 w-4" />,
    borderColor: "border-l-event-other",
    bgColor: "bg-event-other-bg",
    label: "Other",
  },
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.25, 0.1, 0.25, 1] as const,
    },
  },
};

export function EventList({ events, onUpdate, onDelete }: EventListProps) {
  const [editingId, setEditingId] = useState<string | null>(null);

  if (events.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="w-full py-12 text-center"
      >
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-warm-50">
          <Calendar className="h-8 w-8 text-warm-300" />
        </div>
        <p className="text-warm-500">No events saved for this syllabus.</p>
      </motion.div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="w-full space-y-3"
    >
      {events.map((event) => (
        <motion.div
          key={`${event.id}-${event.title}-${event.date}-${event.time ?? ""}-${event.course}-${event.type}-${event.description}-${event.isEdited}`}
          variants={itemVariants}
        >
          <EventCard
            event={event}
            isEditing={editingId === event.id}
            onEdit={() => setEditingId(event.id)}
            onCancel={() => setEditingId(null)}
            onSave={async (updates) => {
              await onUpdate(event.id, updates);
              setEditingId(null);
            }}
            onDelete={() => onDelete(event.id)}
          />
        </motion.div>
      ))}
    </motion.div>
  );
}

type EventCardProps = {
  event: SavedEvent;
  isEditing: boolean;
  onEdit: () => void;
  onCancel: () => void;
  onSave: (updates: SavedEventUpdateInput) => Promise<void>;
  onDelete: () => Promise<void>;
};

function EventCard({
  event,
  isEditing,
  onEdit,
  onCancel,
  onSave,
  onDelete,
}: EventCardProps) {
  const [title, setTitle] = useState(event.title);
  const [date, setDate] = useState(event.date);
  const [time, setTime] = useState(event.time ?? "");
  const [course, setCourse] = useState(event.course);
  const [type, setType] = useState<EventType>(event.type);
  const [description, setDescription] = useState(event.description);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const config = EVENT_CONFIG[event.type];

  async function handleSave() {
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }

    if (!date) {
      setError("Date is required.");
      return;
    }

    const updates: SavedEventUpdateInput = {};

    if (title !== event.title) {
      updates.title = title;
    }

    if (date !== event.date) {
      updates.date = date;
    }

    if (time !== (event.time ?? "")) {
      updates.time = time ? time : null;
    }

    if (course !== event.course) {
      updates.course = course;
    }

    if (type !== event.type) {
      updates.type = type;
    }

    if (description !== event.description) {
      updates.description = description;
    }

    if (Object.keys(updates).length === 0) {
      onCancel();
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await onSave(updates);
    } catch (nextError) {
      setError(
        nextError instanceof Error ? nextError.message : "Failed to save event"
      );
      setSaving(false);
      return;
    }

    setSaving(false);
  }

  async function handleDelete() {
    setDeleting(true);
    setError(null);

    try {
      await onDelete();
    } catch (nextError) {
      setError(
        nextError instanceof Error
          ? nextError.message
          : "Failed to delete event"
      );
      setDeleting(false);
      return;
    }

    setDeleting(false);
  }

  if (isEditing) {
    return (
      <div className="space-y-4 rounded-2xl border-2 border-mint-300 bg-white p-5 shadow-sm">
        <div className="grid gap-4">
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            className="w-full border-b-2 border-warm-200 bg-transparent pb-1 text-lg font-semibold text-warm-700 focus:border-mint-400 focus:outline-none font-[family-name:var(--font-quicksand)]"
          />

          <div className="grid gap-3 md:grid-cols-2">
            <input
              type="date"
              value={date}
              onChange={(event) => setDate(event.target.value)}
              className="rounded-xl border border-warm-200 bg-warm-50 px-3 py-2 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
            />
            <input
              type="time"
              value={time}
              onChange={(event) => setTime(event.target.value)}
              className="rounded-xl border border-warm-200 bg-warm-50 px-3 py-2 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
            />
            <input
              type="text"
              value={course}
              onChange={(event) => setCourse(event.target.value)}
              placeholder="Course"
              className="rounded-xl border border-warm-200 bg-warm-50 px-3 py-2 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
            />
            <select
              value={type}
              onChange={(event) => setType(event.target.value as EventType)}
              className="rounded-xl border border-warm-200 bg-warm-50 px-3 py-2 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
            >
              {Object.entries(EVENT_CONFIG).map(([key, value]) => (
                <option key={key} value={key}>
                  {value.label}
                </option>
              ))}
            </select>
          </div>

          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Description"
            rows={3}
            className="w-full resize-none rounded-xl border border-warm-200 bg-warm-50 p-3 text-sm text-warm-700 placeholder:text-warm-300 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
          />
        </div>

        {error ? <p className="text-sm text-error">{error}</p> : null}

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving}
            className="rounded-xl px-5 py-2 text-sm font-semibold text-white shadow-sm transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-60"
            style={{
              background: "linear-gradient(to bottom, #4ade80, #22c55e)",
            }}
          >
            {saving ? "Saving..." : "Save"}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={saving}
            className="rounded-xl border border-warm-200 px-5 py-2 text-sm font-medium text-warm-500 transition-colors hover:border-warm-300 hover:text-warm-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`${config.bgColor} rounded-2xl border-l-4 ${config.borderColor} p-5 shadow-sm transition-shadow duration-200 hover:shadow-md`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/80 px-2.5 py-1 text-xs font-medium">
              {config.icon}
              {config.label}
            </span>
            {event.isEdited ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-white/80 px-2.5 py-1 text-xs font-medium text-mint-700">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Edited
              </span>
            ) : null}
            {event.course ? (
              <span className="text-xs font-medium text-warm-400">
                {event.course}
              </span>
            ) : null}
          </div>

          <h3 className="mb-1 text-lg font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
            {event.title}
          </h3>
          <p className="flex items-center gap-1.5 text-sm text-warm-500">
            <Calendar className="h-3.5 w-3.5" />
            {event.date}
            {event.time ? ` at ${formatTime12Hour(event.time)}` : ""}
          </p>
          {event.description ? (
            <p className="mt-2 text-sm text-warm-400">{event.description}</p>
          ) : null}
          {error ? <p className="mt-3 text-sm text-error">{error}</p> : null}
        </div>

        <div className="ml-2 flex gap-1">
          <button
            type="button"
            onClick={onEdit}
            className="rounded-lg p-2 text-warm-400 transition-all duration-200 hover:bg-white/50 hover:text-warm-600"
            title="Edit"
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => setShowDeleteDialog(true)}
            disabled={deleting}
            className="rounded-lg p-2 text-warm-400 transition-all duration-200 hover:bg-error-light/50 hover:text-error disabled:cursor-not-allowed disabled:opacity-60"
            title="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      <ConfirmDialog
        isOpen={showDeleteDialog}
        onCancel={() => setShowDeleteDialog(false)}
        onConfirm={() => {
          setShowDeleteDialog(false);
          void handleDelete();
        }}
        title="Delete Event"
        message={`Delete "${event.title}"?`}
      />
    </div>
  );
}
