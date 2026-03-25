"use client";

import { useState } from "react";
import type { EventType, ParsedEvent } from "@/types";

type EventListProps = {
  events: ParsedEvent[];
  onUpdate: (id: string, updates: Partial<ParsedEvent>) => void;
  onDelete: (id: string) => void;
};

const TYPE_STYLES: Record<EventType, string> = {
  assignment: "bg-blue-100 text-blue-700",
  exam: "bg-red-100 text-red-700",
  quiz: "bg-amber-100 text-amber-700",
  project: "bg-purple-100 text-purple-700",
  lab: "bg-emerald-100 text-emerald-700",
  presentation: "bg-pink-100 text-pink-700",
  milestone: "bg-indigo-100 text-indigo-700",
  deadline: "bg-orange-100 text-orange-700",
  discussion: "bg-cyan-100 text-cyan-700",
  other: "bg-gray-100 text-gray-600",
};

export function EventList({ events, onUpdate, onDelete }: EventListProps) {
  const [editingId, setEditingId] = useState<string | null>(null);

  if (events.length === 0) {
    return (
      <div className="w-full max-w-2xl">
        <p className="text-sm text-sage-600 text-center">
          No assignments parsed.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl space-y-4">
      {events.map((event) => (
        <EventCard
          key={event.id}
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
      ))}
    </div>
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

  if (isEditing) {
    return (
      <div className="bg-white rounded-lg p-5 shadow-sm border-2 border-sage-400 space-y-4">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full bg-transparent border-b-2 border-sage-300 text-lg font-semibold text-sage-800 focus:outline-none focus:border-sage-500 pb-1"
        />
        <div className="flex flex-wrap gap-3">
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="bg-sage-50 border border-sage-300 rounded-md px-3 py-1.5 text-sm text-sage-800 focus:outline-none focus:border-sage-500"
          />
          <input
            type="time"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            placeholder="Time (optional)"
            className="bg-sage-50 border border-sage-300 rounded-md px-3 py-1.5 text-sm text-sage-800 focus:outline-none focus:border-sage-500"
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value as EventType)}
            className="bg-sage-50 border border-sage-300 rounded-md px-3 py-1.5 text-sm text-sage-800 focus:outline-none focus:border-sage-500"
          >
            <option value="assignment">Assignment</option>
            <option value="exam">Exam</option>
            <option value="quiz">Quiz</option>
            <option value="project">Project</option>
            <option value="lab">Lab</option>
            <option value="presentation">Presentation</option>
            <option value="milestone">Milestone</option>
            <option value="deadline">Deadline</option>
            <option value="discussion">Discussion</option>
            <option value="other">Other</option>
          </select>
        </div>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (optional)"
          className="w-full bg-sage-50 border border-sage-300 rounded-md p-3 text-sm text-sage-800 placeholder:text-sage-400 focus:outline-none focus:border-sage-500"
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
            className="px-4 py-1.5 text-sm font-medium bg-teal-600 text-white rounded-md hover:bg-teal-700 cursor-pointer transition-colors"
          >
            Save
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-1.5 text-sm font-medium text-sage-600 hover:text-sage-800 cursor-pointer transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg p-5 shadow-sm border border-sage-200 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${TYPE_STYLES[event.type]}`}>
              {event.type}
            </span>
            {event.course && (
              <span className="text-xs text-sage-500 font-medium">{event.course}</span>
            )}
          </div>
          <h3 className="text-lg font-semibold text-sage-800">{event.title}</h3>
          <p className="text-sm text-sage-600">
            {event.date}
            {event.time && ` at ${event.time}`}
          </p>
          {event.description && (
            <p className="text-sm text-sage-500 mt-1">{event.description}</p>
          )}
          {event.isAmbiguous && (
            <p className="text-sm text-amber-600 mt-2 font-medium">
              ⚠ Date was inferred — please verify
            </p>
          )}
        </div>
        <div className="flex gap-1">
          <button
            onClick={onEdit}
            className="text-xs font-medium text-sage-500 hover:text-sage-700 px-2 py-1 cursor-pointer transition-colors"
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            className="text-xs font-medium text-red-400 hover:text-red-600 px-2 py-1 cursor-pointer transition-colors"
          >
            Remove
          </button>
        </div>
      </div>
    </div>
  );
}
