"use client";

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";
import type { ParsedEvent } from "@/types";

type ParsedData = {
  files: File[];
  events: ParsedEvent[];
  courseCode: string | null;
  syllabusName: string;
};

type ParsedDataContextValue = {
  data: ParsedData | null;
  setData: (data: ParsedData | null) => void;
  clear: () => void;
};

const ParsedDataContext = createContext<ParsedDataContextValue | null>(null);

export function ParsedDataProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<ParsedData | null>(null);

  function clear() {
    setData(null);
  }

  return (
    <ParsedDataContext.Provider value={{ data, setData, clear }}>
      {children}
    </ParsedDataContext.Provider>
  );
}

export function useParsedData(): ParsedDataContextValue {
  const context = useContext(ParsedDataContext);

  if (!context) {
    throw new Error("useParsedData must be used within a ParsedDataProvider.");
  }

  return context;
}
