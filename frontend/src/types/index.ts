export type ParsedEvent = {
  title: string;
  date: string; // ISO date string (YYYY-MM-DD)
  description?: string;
  type: "assignment" | "exam" | "quiz" | "project" | "other";
  isAmbiguous: boolean; // true if the date was inferred by the LLM
};

export type ParseResponse = {
  events: ParsedEvent[];
  semesterStart?: string;
  semesterEnd?: string;
};
