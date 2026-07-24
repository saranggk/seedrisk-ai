"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "theme";

export function ThemeToggle() {
  // Mirrors the class the pre-hydration bootstrap script in layout.tsx
  // already applied to <html> — read it on mount rather than re-deciding,
  // so this component and the bootstrap script never disagree.
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    setIsDark(document.documentElement.classList.contains("dark"));
  }, []);

  const handleToggle = () => {
    const next = !isDark;
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem(STORAGE_KEY, next ? "dark" : "light");
    setIsDark(next);
  };

  return (
    <button
      onClick={handleToggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="fixed right-4 top-4 z-50 flex h-9 w-9 items-center justify-center rounded-full border border-border bg-surface text-base shadow-sm transition-colors hover:border-court-green"
    >
      {isDark ? "☀️" : "🌙"}
    </button>
  );
}
