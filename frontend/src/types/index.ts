export type ApiEvent = {
  title: string;
  due_date: string;
  course: string;
  event_type: string;
  description: string;
};

export type ApiParseResponse = {
  events: ApiEvent[];
};

export type ParsedEvent = {
  id: string;
  title: string;
  date: string;
  time?: string;
  description?: string;
  course: string;
  type: "assignment" | "exam" | "quiz" | "project" | "other";
  isAmbiguous: boolean;
};

export type ParseResponse = {
  events: ParsedEvent[];
};

export type UploadMode = "file" | "url" | "paste";
