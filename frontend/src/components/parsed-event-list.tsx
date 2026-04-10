"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { motion } from "framer-motion";
import {
  Calendar,
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
import type { EventType, ParsedEvent } from "@/types";

type ParsedEventListProps = {
  events: ParsedEvent[];
  onUpdate: (index: number, event: ParsedEvent) => void;
  onDelete: (index: number) => void;
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

export function ParsedEventList({
  events,
  onUpdate,
  onDelete,
}: ParsedEventListProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="w-full space-y-3"
    >
      {events.map((event, index) => (
        <motion.div
          key={`${index}-${event.title}-${event.date}`}
          variants={itemVariants}
        >
          <ParsedEventCard
            event={event}
            isEditing={editingIndex === index}
            onEdit={() => setEditingIndex(index)}
            onCancel={() => setEditingIndex(null)}
            onSave={(updated) => {
              onUpdate(index, updated);
              setEditingIndex(null);
            }}
            onDelete={() => {
              if (window.confirm(`Delete "${event.title}"?`)) {
                onDelete(index);
              }
            }}
          />
        </motion.div>
      ))}
    </motion.div>
  );
}

type ParsedEventCardProps = {
  event: ParsedEvent;
  isEditing: boolean;
  onEdit: () => void;
  onCancel: () => void;
  onSave: (updated: ParsedEvent) => void;
  onDelete: () => void;
};

function ParsedEventCard({
  event,
  isEditing,
  onEdit,
  onCancel,
  onSave,
  onDelete,
}: ParsedEventCardProps) {
  const [title, setTitle] = useState(event.title);
  const [date, setDate] = useState(event.date);
  const [time, setTime] = useState(event.time ?? "");
  const [course, setCourse] = useState(event.course);
  const [type, setType] = useState<EventType>(event.type);
  const [description, setDescription] = useState(event.description);
  const [error, setError] = useState<string | null>(null);

  const config = EVENT_CONFIG[event.type];

  function handleSave() {
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }

    if (!date) {
      setError("Date is required.");
      return;
    }

    onSave({
      title: title.trim(),
      date,
      time: time || null,
      course,
      type,
      description,
      durationMinutes: event.durationMinutes,
    });
  }

  if (isEditing) {
    return (
      <div className="space-y-4 rounded-2xl border-2 border-mint-300 bg-white p-5 shadow-sm">
        <div className="grid gap-4">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full border-b-2 border-warm-200 bg-transparent pb-1 text-lg font-semibold text-warm-700 focus:border-mint-400 focus:outline-none font-[family-name:var(--font-quicksand)]"
          />

          <div className="grid gap-3 md:grid-cols-2">
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="rounded-xl border border-warm-200 bg-warm-50 px-3 py-2 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
            />
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="rounded-xl border border-warm-200 bg-warm-50 px-3 py-2 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
            />
            <input
              type="text"
              value={course}
              onChange={(e) => setCourse(e.target.value)}
              placeholder="Course"
              className="rounded-xl border border-warm-200 bg-warm-50 px-3 py-2 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
            />
            <select
              value={type}
              onChange={(e) => setType(e.target.value as EventType)}
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
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description"
            rows={3}
            className="w-full resize-none rounded-xl border border-warm-200 bg-warm-50 p-3 text-sm text-warm-700 placeholder:text-warm-300 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
          />
        </div>

        {error ? <p className="text-sm text-error">{error}</p> : null}

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleSave}
            className="rounded-xl px-5 py-2 text-sm font-semibold text-white shadow-sm transition-all duration-200"
            style={{
              background: "linear-gradient(to bottom, #4ade80, #22c55e)",
            }}
          >
            Save
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl border border-warm-200 px-5 py-2 text-sm font-medium text-warm-500 transition-colors hover:border-warm-300 hover:text-warm-700"
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
            onClick={onDelete}
            className="rounded-lg p-2 text-warm-400 transition-all duration-200 hover:bg-error-light/50 hover:text-error"
            title="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
