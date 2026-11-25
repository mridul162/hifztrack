"use client";

import { useEffect, useId, useState } from "react";

type Ayah = { surah_number: number; ayah_number: number };
type Page = { page_number: number; start: Ayah; end: Ayah };
type PageList = { edition: { id: string; name: string }; pages: Page[] };
type CanonicalRange = {
  start_surah_number: number;
  start_ayah_number: number;
  end_surah_number: number;
  end_ayah_number: number;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function MushafPagePicker({ onApply }: { onApply?: (range: CanonicalRange) => void }) {
  const id = useId();
  const [result, setResult] = useState<PageList | "unavailable" | "error" | null>(null);
  const [selectedNumber, setSelectedNumber] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${apiUrl}/quran/pages`, { signal: controller.signal, cache: "no-store" })
      .then(async (response) => {
        if (response.status === 503) return "unavailable";
        if (!response.ok) throw new Error("Could not load Mushaf pages.");
        return (await response.json()) as PageList;
      })
      .then((data) => {
        if (!controller.signal.aborted) setResult(data);
      })
      .catch(() => {
        if (!controller.signal.aborted) setResult("error");
      });
    return () => controller.abort();
  }, []);

  if (result === null) return <p className="text-sm text-slate-600" role="status">Loading Mushaf pages…</p>;
  if (result === "unavailable") {
    return <p className="text-sm text-slate-600" role="status">Mushaf page mappings are unavailable. Use Surah and Ayah numbers.</p>;
  }
  if (result === "error") {
    return <p className="text-sm text-amber-900" role="alert">Could not load Mushaf pages. Use Surah and Ayah numbers.</p>;
  }

  const page = result.pages.find((item) => item.page_number === Number(selectedNumber));
  return (
    <div className="grid gap-2 text-sm">
      <p className="text-slate-600">{result.edition.name}</p>
      <label htmlFor={id} className="font-medium">Mushaf page</label>
      <select
        id={id}
        className="w-fit rounded-md border border-slate-300 bg-white px-3 py-2"
        value={selectedNumber}
        onChange={(event) => setSelectedNumber(event.target.value)}
      >
        <option value="">Choose a page</option>
        {result.pages.map((item) => (
          <option key={item.page_number} value={item.page_number}>{item.page_number}</option>
        ))}
      </select>
      {page && (
        <p className="text-slate-700" role="status">
          Ayah range {page.start.surah_number}:{page.start.ayah_number}–{page.end.surah_number}:{page.end.ayah_number}
        </p>
      )}
      {page && onApply && (
        <button
          className="w-fit rounded-md border border-emerald-800 px-3 py-2 font-medium text-emerald-900 hover:bg-emerald-50"
          type="button"
          onClick={() => onApply({
            start_surah_number: page.start.surah_number,
            start_ayah_number: page.start.ayah_number,
            end_surah_number: page.end.surah_number,
            end_ayah_number: page.end.ayah_number,
          })}
        >
          Use page range
        </button>
      )}
    </div>
  );
}
