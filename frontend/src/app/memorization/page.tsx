"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { JuzPicker, MushafPagePicker } from "@/components/mushaf-page-picker";
import { SurahSelect, type Surah } from "@/components/surah-select";
import { getJson, mutate } from "@/lib/auth";

type Status = "NOT_STARTED" | "LEARNING" | "MEMORIZED" | "STRONG";
type Progress = { surah_number: number; ayah_number: number; memorization_status: Status; updated_at: string };
type Submission = {
  id: string; start_surah_number: number; start_ayah_number: number;
  end_surah_number: number; end_ayah_number: number; activity_date: string;
  notes: string | null; time_spent_minutes: number | null;
  status: "SUBMITTED" | "CANCELLED"; created_at: string;
};
type RangeForm = {
  start_surah_number: number; start_ayah_number: number;
  end_surah_number: number; end_ayah_number: number; activity_date: string;
};

const statuses: Status[] = ["NOT_STARTED", "LEARNING", "MEMORIZED", "STRONG"];
const statusLabels: Record<Status, string> = {
  NOT_STARTED: "Not started", LEARNING: "Learning", MEMORIZED: "Memorized", STRONG: "Strong",
};
const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const today = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
};

export default function MemorizationPage() {
  const [surahs, setSurahs] = useState<Surah[]>([]);
  const [selectedSurah, setSelectedSurah] = useState(1);
  const [progress, setProgress] = useState<Progress[]>([]);
  const [history, setHistory] = useState<Submission[]>([]);
  const [historyHasMore, setHistoryHasMore] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [range, setRange] = useState<RangeForm>({
    start_surah_number: 1, start_ayah_number: 1, end_surah_number: 1, end_ayah_number: 1, activity_date: today(),
  });
  const [correctingId, setCorrectingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const progressByAyah = useMemo(
    () => new Map(progress.map((item) => [`${item.surah_number}:${item.ayah_number}`, item.memorization_status])),
    [progress],
  );
  const selectedAyahCount = surahs.find((surah) => surah.surah_number === selectedSurah)?.ayah_count ?? 0;

  async function reloadPersonalData() {
    const [currentProgress, entries] = await Promise.all([
      getJson<Progress[]>("/memorization/progress"), getJson<Submission[]>("/memorization/submissions?limit=50&offset=0"),
    ]);
    setProgress(currentProgress);
    setHistory(entries);
    setHistoryHasMore(entries.length === 50);
  }

  useEffect(() => {
    let active = true;
    Promise.all([
      fetch(`${apiUrl}/quran/surahs`).then(async (response) => {
        if (!response.ok) throw new Error("Quran reference data is not available in this environment.");
        return (await response.json()) as Surah[];
      }),
      getJson<Progress[]>("/memorization/progress"),
      getJson<Submission[]>("/memorization/submissions?limit=50&offset=0"),
    ]).then(([surahList, currentProgress, entries]) => {
      if (!active) return;
      setSurahs(surahList);
      setProgress(currentProgress);
      setHistory(entries);
      setHistoryHasMore(entries.length === 50);
    }).catch((reason: unknown) => {
      if (active) setError(reason instanceof Error ? reason.message : "Could not load memorization data.");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  async function updateStatus(ayahNumber: number, status: Status) {
    if (status === "STRONG" && !window.confirm("Confirm that this Ayah is strong?")) return;
    setError(null); setNotice(null);
    try {
      await mutate(`/memorization/progress/${selectedSurah}/${ayahNumber}`, "PUT", {
        memorization_status: status, confirm_strong: status === "STRONG",
      });
      await reloadPersonalData();
      setNotice(`Surah ${selectedSurah}:${ayahNumber} status saved.`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save Ayah status.");
    }
  }

  function setRangeField(field: keyof RangeForm, value: string) {
    setRange((current) => ({ ...current, [field]: field === "activity_date" ? value : Number(value) }));
  }

  async function saveSubmission(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError(null); setNotice(null);
    const start = [range.start_surah_number, range.start_ayah_number];
    const end = [range.end_surah_number, range.end_ayah_number];
    if (start[0] > end[0] || (start[0] === end[0] && start[1] > end[1])) {
      setError("Start Ayah must not follow end Ayah."); setSaving(false); return;
    }
    try {
      const path = correctingId ? `/memorization/submissions/${correctingId}/correct` : "/memorization/submissions";
      await mutate(path, "POST", range);
      await reloadPersonalData();
      setCorrectingId(null);
      setNotice(correctingId ? "Sabaq entry corrected; the original remains in history." : "Sabaq activity submitted.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save Sabaq activity.");
    } finally { setSaving(false); }
  }

  function beginCorrection(entry: Submission) {
    setCorrectingId(entry.id);
    setRange({
      start_surah_number: entry.start_surah_number, start_ayah_number: entry.start_ayah_number,
      end_surah_number: entry.end_surah_number, end_ayah_number: entry.end_ayah_number,
      activity_date: entry.activity_date,
    });
    setNotice("Edit the replacement range and submit the correction.");
  }

  async function cancelSubmission(entry: Submission) {
    setError(null); setNotice(null);
    try {
      await mutate(`/memorization/submissions/${entry.id}/cancel`, "POST");
      await reloadPersonalData();
      setNotice("Sabaq entry cancelled. Its history is preserved.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not cancel Sabaq activity.");
    }
  }

  async function loadOlderHistory() {
    setHistoryLoading(true);
    setError(null);
    try {
      const older = await getJson<Submission[]>(`/memorization/submissions?limit=50&offset=${history.length}`);
      setHistory((current) => [...current, ...older]);
      setHistoryHasMore(older.length === 50);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load older Sabaq activity.");
    } finally {
      setHistoryLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <nav className="mb-8 flex flex-wrap gap-5 text-sm">
          <Link className="underline" href="/">Home</Link><Link className="underline" href="/quran">Quran references</Link><Link className="underline" href="/revision">My revision</Link><Link className="underline" href="/profile">Profile</Link>
        </nav>
        <header className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-800">HifzTrack</p>
          <h1 className="mt-2 text-3xl font-semibold">My memorization</h1>
          <p className="mt-3 max-w-2xl leading-7 text-slate-600">Track your own Ayah status and Sabaq history using canonical numeric references. Sabaq activity does not change memorization status.</p>
        </header>

        {loading && <p role="status">Loading memorization data…</p>}
        {error && <div className="mb-5 rounded-lg bg-amber-50 p-4 text-amber-950" role="alert">
          <p>{error}</p>{error.includes("Sign in") && <Link className="mt-2 inline-block underline" href="/login">Sign in</Link>}
        </div>}
        {notice && <p className="mb-5 rounded-lg bg-emerald-50 p-4 text-emerald-950" role="status">{notice}</p>}

        {!loading && surahs.length > 0 && (
          <div className="space-y-6">
            <section className="rounded-xl border border-emerald-950/10 bg-white p-5 shadow-sm" aria-labelledby="progress-heading">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div><h2 id="progress-heading" className="text-lg font-semibold">Current Ayah status</h2><p className="mt-1 text-sm text-slate-600">Ayahs without a saved status are Not started.</p></div>
                <label className="text-sm font-medium" htmlFor="browse-surah">Browse Surah</label>
                <SurahSelect id="browse-surah" surahs={surahs} value={selectedSurah}
                  onChange={(value) => setSelectedSurah(Number(value))} />
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {Array.from({ length: selectedAyahCount }, (_, index) => index + 1).map((ayahNumber) => {
                  const key = `${selectedSurah}:${ayahNumber}`;
                  const status = progressByAyah.get(key) ?? "NOT_STARTED";
                  return <div key={key} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 p-3">
                    <span className="font-medium">{selectedSurah}:{ayahNumber}</span>
                    <select aria-label={`Status for ${key}`} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" value={status} onChange={(event) => void updateStatus(ayahNumber, event.target.value as Status)}>
                      {statuses.map((item) => <option key={item} value={item}>{statusLabels[item]}</option>)}
                    </select>
                  </div>;
                })}
              </div>
            </section>

            <section className="rounded-xl border border-emerald-950/10 bg-white p-5 shadow-sm" aria-labelledby="sabaq-heading">
              <h2 id="sabaq-heading" className="text-lg font-semibold">{correctingId ? "Correct Sabaq entry" : "Submit Sabaq activity"}</h2>
              <p className="mt-1 text-sm text-slate-600">Use a numeric start and end reference. Repeated ranges remain separate history entries.</p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <JuzPicker onApply={(coordinates) => setRange((current) => ({ ...current, ...coordinates }))} />
                <MushafPagePicker onApply={(coordinates) => setRange((current) => ({ ...current, ...coordinates }))} />
              </div>
              <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={(event) => void saveSubmission(event)}>
                {([
                  ["start_surah_number", "Start Surah", 1, 114], ["start_ayah_number", "Start Ayah", 1, 286],
                  ["end_surah_number", "End Surah", 1, 114], ["end_ayah_number", "End Ayah", 1, 286],
                ] as const).map(([field, label, min, max]) => <div key={field} className="grid gap-1 text-sm font-medium">
                  <label htmlFor={`sabaq-${field}`}>{label}</label>
                  {field.endsWith("surah_number") ? (
                    <SurahSelect id={`sabaq-${field}`} surahs={surahs} value={range[field]}
                      onChange={(value) => setRangeField(field, value)} />
                  ) : (
                    <input id={`sabaq-${field}`} className="rounded-md border border-slate-300 px-3 py-2" type="number"
                      min={min} max={max} required value={range[field]}
                      onChange={(event) => setRangeField(field, event.target.value)} />
                  )}
                </div>)}
                <label className="grid gap-1 text-sm font-medium">Activity date<input className="rounded-md border border-slate-300 px-3 py-2" type="date" required value={range.activity_date} onChange={(event) => setRangeField("activity_date", event.target.value)} /></label>
                <div className="flex items-end gap-3">
                  <button className="rounded-md bg-emerald-800 px-4 py-2 font-medium text-white disabled:opacity-60" disabled={saving} type="submit">{saving ? "Saving…" : correctingId ? "Save correction" : "Submit Sabaq"}</button>
                  {correctingId && <button className="rounded-md border border-slate-300 px-4 py-2" type="button" onClick={() => setCorrectingId(null)}>Cancel edit</button>}
                </div>
              </form>
            </section>

            <section className="rounded-xl border border-emerald-950/10 bg-white p-5 shadow-sm" aria-labelledby="history-heading">
              <h2 id="history-heading" className="text-lg font-semibold">Sabaq history</h2>
              {history.length === 0 ? <p className="mt-3 text-sm text-slate-600">No Sabaq activity submitted yet.</p> : <ul className="mt-4 divide-y divide-slate-200">
                {history.map((entry) => <li key={entry.id} className="flex flex-wrap items-center justify-between gap-4 py-4">
                  <div><p className="font-medium">{entry.start_surah_number}:{entry.start_ayah_number} – {entry.end_surah_number}:{entry.end_ayah_number}</p><p className="text-sm text-slate-600">{entry.activity_date} · {entry.status}</p></div>
                  {entry.status === "SUBMITTED" && <div className="flex gap-2">
                    <button className="rounded-md border border-slate-300 px-3 py-1.5 text-sm" type="button" onClick={() => beginCorrection(entry)}>Correct</button>
                    <button className="rounded-md border border-rose-300 px-3 py-1.5 text-sm text-rose-800" type="button" onClick={() => void cancelSubmission(entry)}>Cancel</button>
                  </div>}
                </li>)}
              </ul>}
              {historyHasMore && <button className="mt-4 rounded-md border border-slate-300 px-4 py-2 text-sm" disabled={historyLoading} type="button" onClick={() => void loadOlderHistory()}>{historyLoading ? "Loading…" : "Load older activity"}</button>}
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
