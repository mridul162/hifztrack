"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { MushafPagePicker } from "@/components/mushaf-page-picker";
import { getJson, mutate } from "@/lib/auth";

type Surah = { surah_number: number; ayah_count: number };
type RevisionType = "RECENT" | "OLD" | "FULL_JUZ" | "FULL_QURAN";
type RevisionSession = {
  id: string;
  start_surah_number: number;
  start_ayah_number: number;
  end_surah_number: number;
  end_ayah_number: number;
  revision_type: RevisionType;
  activity_date: string;
  time_spent_minutes: number;
  self_rating: number | null;
  notes: string | null;
  created_at: string;
};
type RevisionForm = {
  start_surah_number: number;
  start_ayah_number: number;
  end_surah_number: number;
  end_ayah_number: number;
  revision_type: RevisionType;
  activity_date: string;
  time_spent_minutes: number;
  self_rating: number | null;
  notes: string;
};

const revisionTypes: { value: RevisionType; label: string }[] = [
  { value: "RECENT", label: "Recent" },
  { value: "OLD", label: "Older portion" },
  { value: "FULL_JUZ", label: "Full Juz" },
  { value: "FULL_QURAN", label: "Full Quran" },
];
const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const today = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
};
const initialForm = (): RevisionForm => ({
  start_surah_number: 1, start_ayah_number: 1, end_surah_number: 1, end_ayah_number: 1,
  revision_type: "RECENT", activity_date: today(), time_spent_minutes: 0,
  self_rating: null, notes: "",
});

export default function RevisionPage() {
  const [surahs, setSurahs] = useState<Surah[]>([]);
  const [sessions, setSessions] = useState<RevisionSession[]>([]);
  const [form, setForm] = useState<RevisionForm>(initialForm);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([
      fetch(`${apiUrl}/quran/surahs`, { credentials: "include", cache: "no-store" }).then(
        async (response) => {
          if (!response.ok) throw new Error("Quran reference data is not available yet.");
          return (await response.json()) as Surah[];
        },
      ),
      getJson<RevisionSession[]>("/revision/me?limit=50&offset=0"),
    ])
      .then(([surahList, history]) => {
        if (!active) return;
        setSurahs(surahList);
        setSessions(history);
        setHasMore(history.length === 50);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "Could not load revision history.");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  function setNumberField(field: keyof RevisionForm, value: string) {
    setForm((current) => ({ ...current, [field]: Number(value) }));
  }

  async function reloadHistory() {
    const history = await getJson<RevisionSession[]>("/revision/me?limit=50&offset=0");
    setSessions(history);
    setHasMore(history.length === 50);
  }

  async function saveSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setHistoryError(null);
    setNotice(null);
    const start = [form.start_surah_number, form.start_ayah_number];
    const end = [form.end_surah_number, form.end_ayah_number];
    if (start[0] > end[0] || (start[0] === end[0] && start[1] > end[1])) {
      setError("Start Ayah must not follow end Ayah.");
      setSaving(false);
      return;
    }
    try {
      await mutate("/revision", "POST", form);
      setNotice("Revision session recorded in your history.");
      setForm(initialForm());
      try {
        await reloadHistory();
      } catch (reason) {
        const detail = reason instanceof Error ? reason.message : "Could not refresh revision history.";
        setHistoryError(`The revision was recorded, but history could not be refreshed: ${detail}`);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not record revision session.");
    } finally { setSaving(false); }
  }

  async function loadOlderHistory() {
    setHistoryLoading(true);
    setError(null);
    try {
      const older = await getJson<RevisionSession[]>(`/revision/me?limit=50&offset=${sessions.length}`);
      setSessions((current) => [...current, ...older]);
      setHasMore(older.length === 50);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load older revision history.");
    } finally { setHistoryLoading(false); }
  }

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <nav className="mb-8 flex flex-wrap gap-5 text-sm">
          <Link className="underline" href="/">Home</Link>
          <Link className="underline" href="/quran">Quran references</Link>
          <Link className="underline" href="/memorization">My memorization</Link>
          <Link className="underline" href="/profile">Profile</Link>
        </nav>
        <header className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-800">HifzTrack</p>
          <h1 className="mt-2 text-3xl font-semibold">My revision</h1>
          <p className="mt-3 max-w-2xl leading-7 text-slate-600">
            Record Muraja’ah separately from memorization status. Sessions use numeric Surah/Ayah
            references and remain in your personal history after creation.
          </p>
        </header>

        {loading && <p role="status">Loading revision history...</p>}
        {error && (
          <div className="mb-5 rounded-lg bg-amber-50 p-4 text-amber-950" role="alert">
            <p>{error}</p>
            {error.includes("Sign in") && <Link className="mt-2 inline-block underline" href="/login">Sign in</Link>}
          </div>
        )}
        {historyError && (
          <p className="mb-5 rounded-lg bg-amber-50 p-4 text-amber-950" role="alert">
            {historyError}
          </p>
        )}
        {notice && <p className="mb-5 rounded-lg bg-emerald-50 p-4 text-emerald-950" role="status">{notice}</p>}
        {!loading && !error && surahs.length === 0 && (
          <p className="mb-5 rounded-lg bg-slate-50 p-4 text-slate-700" role="status">No Quran references are available yet.</p>
        )}

        {!loading && !error && surahs.length > 0 && (
          <div className="space-y-6">
            <section className="rounded-xl border border-emerald-950/10 bg-white p-5 shadow-sm" aria-labelledby="revision-form-heading">
              <h2 id="revision-form-heading" className="text-lg font-semibold">Record a revision session</h2>
              <p className="mt-1 text-sm text-slate-600">
                Enter the canonical range you reviewed. Revision does not change any Ayah’s status.
                Saved sessions cannot be edited or deleted.
              </p>
              <div className="mt-4">
                <MushafPagePicker onApply={(coordinates) => setForm((current) => ({ ...current, ...coordinates }))} />
              </div>
              <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={(event) => void saveSession(event)}>
                {([
                  ["start_surah_number", "Start Surah", 1, 114],
                  ["start_ayah_number", "Start Ayah", 1, 286],
                  ["end_surah_number", "End Surah", 1, 114],
                  ["end_ayah_number", "End Ayah", 1, 286],
                ] as const).map(([field, label, min, max]) => (
                  <label key={field} className="grid gap-1 text-sm font-medium">
                    {label}
                    <input className="rounded-md border border-slate-300 px-3 py-2" type="number"
                      min={min} max={max} required value={form[field] as number}
                      onChange={(event) => setNumberField(field, event.target.value)} />
                  </label>
                ))}
                <label className="grid gap-1 text-sm font-medium">
                  Revision type
                  <select className="rounded-md border border-slate-300 px-3 py-2" value={form.revision_type}
                    onChange={(event) => setForm((current) => ({
                      ...current, revision_type: event.target.value as RevisionType,
                    }))}>
                    {revisionTypes.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
                  </select>
                </label>
                <label className="grid gap-1 text-sm font-medium">
                  Activity date
                  <input className="rounded-md border border-slate-300 px-3 py-2" type="date" required
                    value={form.activity_date}
                    onChange={(event) => setForm((current) => ({ ...current, activity_date: event.target.value }))} />
                </label>
                <label className="grid gap-1 text-sm font-medium">
                  Time spent (minutes)
                  <input className="rounded-md border border-slate-300 px-3 py-2" type="number" min={0} max={32767}
                    required value={form.time_spent_minutes}
                    onChange={(event) => setNumberField("time_spent_minutes", event.target.value)} />
                </label>
                <label className="grid gap-1 text-sm font-medium">
                  Self-rating (optional)
                  <select className="rounded-md border border-slate-300 px-3 py-2" value={form.self_rating ?? ""}
                    onChange={(event) => setForm((current) => ({
                      ...current, self_rating: event.target.value === "" ? null : Number(event.target.value),
                    }))}>
                    <option value="">No rating</option>
                    {[1, 2, 3, 4, 5].map((rating) => <option key={rating} value={rating}>{rating}</option>)}
                  </select>
                </label>
                <label className="grid gap-1 text-sm font-medium sm:col-span-2">
                  Notes (optional)
                  <textarea className="min-h-24 rounded-md border border-slate-300 px-3 py-2"
                    value={form.notes}
                    onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} />
                </label>
                <div className="sm:col-span-2">
                  <button className="rounded-md bg-emerald-800 px-4 py-2 font-medium text-white disabled:opacity-60"
                    disabled={saving} type="submit">
                    {saving ? "Saving..." : "Save revision session"}
                  </button>
                </div>
              </form>
            </section>

            <section className="rounded-xl border border-emerald-950/10 bg-white p-5 shadow-sm" aria-labelledby="revision-history-heading">
              <h2 id="revision-history-heading" className="text-lg font-semibold">Revision history</h2>
              {sessions.length === 0 ? (
                <p className="mt-3 text-sm text-slate-600">No revision sessions recorded yet.</p>
              ) : (
                <ul className="mt-4 divide-y divide-slate-200">
                  {sessions.map((session) => (
                    <li key={session.id} className="py-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="font-medium">
                            {session.start_surah_number}:{session.start_ayah_number} – {session.end_surah_number}:{session.end_ayah_number}
                          </p>
                          <p className="mt-1 text-sm text-slate-600">
                            {session.activity_date} · {revisionTypes.find((type) => type.value === session.revision_type)?.label}
                            {` · ${session.time_spent_minutes} minutes`}
                            {session.self_rating !== null && ` · Rating ${session.self_rating}/5`}
                          </p>
                          {session.notes && <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{session.notes}</p>}
                        </div>
                        <span className="text-xs text-slate-500">Saved history</span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              {hasMore && (
                <button className="mt-4 rounded-md border border-slate-300 px-4 py-2 text-sm"
                  disabled={historyLoading} type="button" onClick={() => void loadOlderHistory()}>
                  {historyLoading ? "Loading..." : "Load older activity"}
                </button>
              )}
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
