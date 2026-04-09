"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

const MESSAGES = [
  "Reading your syllabus...",
  "Finding those due dates...",
  "Spotting assignments...",
  "Almost there...",
];

const CALENDAR_CELLS = [
  { row: 0, col: 0, delay: 0.2 },
  { row: 0, col: 2, delay: 0.5 },
  { row: 1, col: 1, delay: 0.8 },
  { row: 1, col: 3, delay: 1.1 },
  { row: 2, col: 0, delay: 1.4 },
  { row: 2, col: 2, delay: 1.7 },
  { row: 3, col: 1, delay: 2.0 },
  { row: 3, col: 4, delay: 2.3 },
];

type LoadingScreenProps = {
  isVisible: boolean;
};

export function LoadingScreen({ isVisible }: LoadingScreenProps) {
  const [messageIndex, setMessageIndex] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const prevVisibleRef = useRef(isVisible);

  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (isVisible) {
      if (!prevVisibleRef.current) {
        queueMicrotask(() => setMessageIndex(0));
      }
      intervalRef.current = setInterval(() => {
        setMessageIndex((prev) => (prev + 1) % MESSAGES.length);
      }, 2000);
    }

    prevVisibleRef.current = isVisible;

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isVisible]);

  return (
    <AnimatePresence>
      {isVisible && (
        <div className="fixed inset-0 z-50 bg-cream">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="flex h-full flex-col items-center justify-center"
          >
            <div className="flex flex-col items-center gap-8">
              <CalendarAnimation isVisible={isVisible} />
              <motion.p
                key={messageIndex}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                className="text-lg text-warm-500 font-medium font-[family-name:var(--font-nunito)]"
              >
                {MESSAGES[messageIndex]}
              </motion.p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

function CalendarAnimation({ isVisible }: { isVisible: boolean }) {
  const [visibleCells, setVisibleCells] = useState<number[]>([]);
  const timersRef = useRef<NodeJS.Timeout[]>([]);
  const loopIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const clearAllTimers = () => {
      timersRef.current.forEach(clearTimeout);
      timersRef.current = [];
      if (loopIntervalRef.current) {
        clearInterval(loopIntervalRef.current);
        loopIntervalRef.current = null;
      }
    };

    const runAnimationCycle = () => {
      timersRef.current.forEach(clearTimeout);
      timersRef.current = [];
      queueMicrotask(() => setVisibleCells([]));

      CALENDAR_CELLS.forEach((cell, index) => {
        const timer = setTimeout(() => {
          setVisibleCells((prev) => [...prev, index]);
        }, cell.delay * 1000);
        timersRef.current.push(timer);
      });
    };

    if (!isVisible) {
      clearAllTimers();
      return;
    }

    runAnimationCycle();

    loopIntervalRef.current = setInterval(runAnimationCycle, 3500);

    return clearAllTimers;
  }, [isVisible]);

  return (
    <div className="relative">
      <div className="w-48 h-48 bg-white rounded-2xl shadow-lg border border-warm-100 p-4 flex flex-col">
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-warm-100">
          <div className="w-16 h-3 bg-mint-200 rounded-full" />
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-peach-200 rounded-full" />
            <div className="w-2 h-2 bg-mint-200 rounded-full" />
          </div>
        </div>

        <div className="grid grid-cols-5 gap-1.5 flex-1">
          {Array.from({ length: 20 }).map((_, index) => {
            const row = Math.floor(index / 5);
            const col = index % 5;
            const cellIndex = CALENDAR_CELLS.findIndex(
              (c) => c.row === row && c.col === col
            );
            const isEventCell = cellIndex !== -1;
            const isCellVisible = visibleCells.includes(cellIndex);

            return (
              <div
                key={index}
                className="relative aspect-square rounded bg-warm-50 flex items-center justify-center"
              >
                <AnimatePresence>
                  {isEventCell && isCellVisible && (
                    <motion.div
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0, opacity: 0 }}
                      transition={{
                        type: "spring",
                        stiffness: 500,
                        damping: 25,
                      }}
                      className={`absolute inset-1 rounded ${
                        cellIndex % 3 === 0
                          ? "bg-mint-300"
                          : cellIndex % 3 === 1
                          ? "bg-peach-300"
                          : "bg-mint-400"
                      }`}
                    />
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
