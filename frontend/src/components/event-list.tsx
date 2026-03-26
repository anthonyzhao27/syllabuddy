"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  GraduationCap,
  HelpCircle,
  FolderKanban,
  FlaskConical,
  Presentation,
  Flag,
  Clock,
  MessageSquare,
  MoreHorizontal,
  Pencil,
  Trash2,
  AlertTriangle,
  Calendar,
} from "lucide-react";
import type { EventType, ParsedEvent } from "@/types";

type EventListProps = {
  events: ParsedEvent[];
  onUpdate: (id: string, updates: Partial<ParsedEvent>) => void;
  onDelete: (id: string) => void;
};

const EVENT_CONFIG: Record<
  EventType,
  { icon: React.ReactNode; borderColor: string; bgColor: string; label: string }
> = {
  assignment: {
    icon: <FileText className="w-4 h-4" />,
    borderColor: "border-l-event-assignment",
    bgColor: "bg-event-assignment-bg",
    label: "Assignment",
  },
  exam: {
    icon: <GraduationCap className="w-4 h-4" />,
    borderColor: "border-l-event-exam",
    bgColor: "bg-event-exam-bg",
    label: "Exam",
  },
  quiz: {
    icon: <HelpCircle className="w-4 h-4" />,
    borderColor: "border-l-event-quiz",
    bgColor: "bg-event-quiz-bg",
    label: "Quiz",
  },
  project: {
    icon: <FolderKanban className="w-4 h-4" />,
    borderColor: "border-l-event-project",
    bgColor: "bg-event-project-bg",
    label: "Project",
  },
  lab: {
    icon: <FlaskConical className="w-4 h-4" />,
    borderColor: "border-l-event-lab",
    bgColor: "bg-event-lab-bg",
    label: "Lab",
  },
  presentation: {
    icon: <Presentation className="w-4 h-4" />,
    borderColor: "border-l-event-presentation",
    bgColor: "bg-event-presentation-bg",
    label: "Presentation",
  },
  milestone: {
    icon: <Flag className="w-4 h-4" />,
    borderColor: "border-l-event-milestone",
    bgColor: "bg-event-milestone-bg",
    label: "Milestone",
  },
  deadline: {
    icon: <Clock className="w-4 h-4" />,
    borderColor: "border-l-event-deadline",
    bgColor: "bg-event-deadline-bg",
    label: "Deadline",
  },
  discussion: {
    icon: <MessageSquare className="w-4 h-4" />,
    borderColor: "border-l-event-discussion",
    bgColor: "bg-event-discussion-bg",
    label: "Discussion",
  },
  other: {
    icon: <MoreHorizontal className="w-4 h-4" />,
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
        className="w-full text-center py-12"
      >
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-warm-50 flex items-center justify-center">
          <Calendar className="w-8 h-8 text-warm-300" />
        </div>
        <p className="text-warm-500">No assignments found in your syllabus.</p>
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
        <motion.div key={event.id} variants={itemVariants}>
          <EventCard
            event={event}
            isEditing={editingId === event.id}
            onEdit={() => setEditingId(event.id)}
            onCancel={() => setEditingId(null)}
            onSave={(updates) => {
              onUpdate(event.id, updates);
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
  event: ParsedEvent;
  isEditing: boolean;
  onEdit: () => void;
  onCancel: () => void;
  onSave: (updates: Partial<ParsedEvent>) => void;
  onDelete: () => void;
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
  const [time, setTime] = useState(event.time || "");
  const [type, setType] = useState<EventType>(event.type);
  const [description, setDescription] = useState(event.description || "");

  const config = EVENT_CONFIG[event.type];

  if (isEditing) {
    return (
      <div className="bg-white rounded-xl p-5 shadow-sm border-2 border-mint-300 space-y-4">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full bg-transparent border-b-2 border-warm-200 text-lg font-semibold text-warm-700 focus:outline-none focus:border-mint-400 pb-1 font-[family-name:var(--font-quicksand)]"
        />
        <div className="flex flex-wrap gap-3">
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="bg-warm-50 border border-warm-200 rounded-lg px-3 py-2 text-sm text-warm-700 focus:outline-none focus:border-mint-400 focus:ring-2 focus:ring-mint-100"
          />
          <input
            type="time"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            placeholder="Time (optional)"
            className="bg-warm-50 border border-warm-200 rounded-lg px-3 py-2 text-sm text-warm-700 focus:outline-none focus:border-mint-400 focus:ring-2 focus:ring-mint-100"
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value as EventType)}
            className="bg-warm-50 border border-warm-200 rounded-lg px-3 py-2 text-sm text-warm-700 focus:outline-none focus:border-mint-400 focus:ring-2 focus:ring-mint-100"
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
          placeholder="Description (optional)"
          className="w-full bg-warm-50 border border-warm-200 rounded-lg p-3 text-sm text-warm-700 placeholder:text-warm-300 focus:outline-none focus:border-mint-400 focus:ring-2 focus:ring-mint-100 resize-none"
          rows={2}
        />
        <div className="flex gap-3 pt-1">
          <button
            onClick={() =>
              onSave({
                title,
                date,
                time: time || undefined,
                type,
                description: description || undefined,
              })
            }
            className="px-5 py-2 text-sm font-semibold text-white rounded-lg cursor-pointer transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
            style={{
              background: "linear-gradient(to bottom, #4ade80, #22c55e)",
            }}
          >
            Save
          </button>
          <button
            onClick={onCancel}
            className="px-5 py-2 text-sm font-medium text-warm-500 border border-warm-200 rounded-lg hover:border-warm-300 hover:text-warm-700 cursor-pointer transition-all duration-200"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`${config.bgColor} rounded-xl p-5 border-l-4 ${config.borderColor} shadow-sm hover:shadow-md transition-shadow duration-200`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full bg-white/80`}
            >
              {config.icon}
              {config.label}
            </span>
            {event.course && (
              <span className="text-xs text-warm-400 font-medium">
                {event.course}
              </span>
            )}
          </div>
          <h3 className="text-lg font-semibold text-warm-700 mb-1 font-[family-name:var(--font-quicksand)]">
            {event.title}
          </h3>
          <p className="text-sm text-warm-500 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            {event.date}
            {event.time && ` at ${event.time}`}
          </p>
          {event.description && (
            <p className="text-sm text-warm-400 mt-2">{event.description}</p>
          )}
          {event.isAmbiguous && (
            <div className="flex items-center gap-1.5 mt-3 text-sm text-warning font-medium">
              <AlertTriangle className="w-4 h-4" />
              Date was inferred — please verify
            </div>
          )}
        </div>
        <div className="flex gap-1 ml-4">
          <button
            onClick={onEdit}
            className="p-2 text-warm-400 hover:text-warm-600 hover:bg-white/50 rounded-lg cursor-pointer transition-all duration-200"
            title="Edit"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={onDelete}
            className="p-2 text-warm-400 hover:text-error hover:bg-error-light/50 rounded-lg cursor-pointer transition-all duration-200"
            title="Remove"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
