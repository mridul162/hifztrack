"use client";

import { useEffect, useId, useState } from "react";

type Ayah = { surah_number: number; ayah_number: number };
type Range = { start: Ayah; end: Ayah };
type PageList = { edition: { name: string }; pages: (Range & { page_number: number })[] };
type JuzList = { juzs: (Range & { juz_number: number })[] };
type Options = { caption?: string; ranges: (Range & { number: number })[] };
type CanonicalRange = {
  start_surah_number: number;
  start_ayah_number: number;
  end_surah_number: number;
  end_ayah_number: number;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type PickerProps = { onApply?: (range: CanonicalRange) => void };

export function MushafPagePicker(props: PickerProps) {
  return <ReferenceRangePicker kind="pages" {...props} />;
}

export function JuzPicker(props: PickerProps) {
  return <ReferenceRangePicker kind="juzs" {...props} />;
}

function ReferenceRangePicker({ kind, onApply }: PickerProps & { kind: "pages" | "juzs" }) {
  const id = useId();
  const [result, setResult] = useState<Options | "unavailable" | "error" | null>(null);
  const [selectedNumber, setSelectedNumber] = useState("");
  const isPage = kind === "pages";
  const label = isPage ? "Mushaf page" : "Juz";
  const plural = isPage ? "Mushaf pages" : "Juz ranges";
  const item = isPage ? "page" : "Juz";

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${apiUrl}/quran/${kind}`, { signal: controller.signal, cache: "no-store" })
      .then(async (response) => {
        if (response.status === 503) return "unavailable";
        if (!response.ok) throw new Error("Could not load reference ranges.");
        const data = (await response.json()) as PageList | JuzList;
        if ("pages" in data) {
          return {
            caption: data.edition.name,
            ranges: data.pages.map(({ page_number, ...range }) => ({ number: page_number, ...range })),
          };
        }
        return { ranges: data.juzs.map(({ juz_number, ...range }) => ({ number: juz_number, ...range })) };
      })
      .then((data) => {
        if (!controller.signal.aborted) setResult(data);
      })
      .catch(() => {
        if (!controller.signal.aborted) setResult("error");
      });
    return () => controller.abort();
  }, [kind]);

  if (result === null) return <p className="text-sm text-slate-600" role="status">Loading {plural}…</p>;
  if (result === "unavailable") {
    return <p className="text-sm text-slate-600" role="status">{label} mappings are unavailable. Use Surah and Ayah numbers.</p>;
  }
  if (result === "error") {
    return <p className="text-sm text-amber-900" role="alert">Could not load {plural}. Use Surah and Ayah numbers.</p>;
  }

  const range = result.ranges.find((option) => option.number === Number(selectedNumber));
  return (
    <div className="grid gap-2 text-sm">
      {result.caption && <p className="text-slate-600">{result.caption}</p>}
      <label htmlFor={id} className="font-medium">{label}</label>
      <select
        id={id}
        className="w-fit rounded-md border border-slate-300 bg-white px-3 py-2"
        value={selectedNumber}
        onChange={(event) => setSelectedNumber(event.target.value)}
      >
        <option value="">Choose a {item}</option>
        {result.ranges.map((option) => (
          <option key={option.number} value={option.number}>{option.number}</option>
        ))}
      </select>
      {range && (
        <p className="text-slate-700" role="status">
          Ayah range {range.start.surah_number}:{range.start.ayah_number}–{range.end.surah_number}:{range.end.ayah_number}
        </p>
      )}
      {range && onApply && (
        <button
          className="w-fit rounded-md border border-emerald-800 px-3 py-2 font-medium text-emerald-900 hover:bg-emerald-50"
          type="button"
          onClick={() => onApply({
            start_surah_number: range.start.surah_number,
            start_ayah_number: range.start.ayah_number,
            end_surah_number: range.end.surah_number,
            end_ayah_number: range.end.ayah_number,
          })}
        >
          Use {item} range
        </button>
      )}
    </div>
  );
}
