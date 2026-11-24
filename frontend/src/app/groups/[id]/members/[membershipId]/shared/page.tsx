"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getJson } from "@/lib/auth";

type SharedData = {
  overall_progress_visibility: "PRIVATE" | "SUMMARY" | "DETAILED";
  progress_summary?: { total_memorized_ayahs: number; completion_percentage: number };
  detailed_progress?: { surah_number: number; ayah_number: number; memorization_status: string }[];
  memorization_logs?: { start_surah_number: number; start_ayah_number: number; end_surah_number: number; end_ayah_number: number; created_at: string; status: string }[];
  revision_logs?: { start_surah_number: number; start_ayah_number: number; end_surah_number: number; end_ayah_number: number; revision_type: string; activity_date: string; time_spent_minutes: number; self_rating?: number | null }[];
};

function range(item: { start_surah_number: number; start_ayah_number: number; end_surah_number: number; end_ayah_number: number }) {
  return `${item.start_surah_number}:${item.start_ayah_number}-${item.end_surah_number}:${item.end_ayah_number}`;
}

export default function SharedMemberPage() {
  const params = useParams<{ id: string; membershipId: string }>();
  const [data, setData] = useState<SharedData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    void getJson<SharedData>(`/groups/${params.id}/members/${params.membershipId}/shared`)
      .then((result) => { if (mounted) setData(result); })
      .catch((reason) => { if (mounted) setError((reason as Error).message); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [params.id, params.membershipId]);

  if (loading) return <main className="mx-auto max-w-3xl px-6 py-12" role="status">Loading shared information...</main>;
  return <main className="mx-auto max-w-3xl px-6 py-12">
    <nav className="mb-8 flex gap-5"><Link className="underline" href={`/groups/${params.id}`}>Back to group</Link><Link className="underline" href="/groups">Your groups</Link></nav>
    <h1 className="text-3xl font-semibold">Shared information</h1>
    {error && <p role="alert" className="mt-4 rounded bg-red-50 p-4 text-red-800">{error}</p>}
    {data && <>
      <section className="mt-6 rounded-xl border bg-white p-5"><h2 className="text-xl font-semibold">Overall progress · {data.overall_progress_visibility.toLowerCase()}</h2>
        {data.progress_summary && <p className="mt-3">{data.progress_summary.total_memorized_ayahs.toLocaleString()} Ayahs memorized · {data.progress_summary.completion_percentage}% of the Quran</p>}
        {data.detailed_progress && <><p className="mt-2 text-sm text-slate-600">Current status for {data.detailed_progress.length.toLocaleString()} Ayahs</p><ul className="mt-3 grid max-h-96 grid-cols-2 gap-2 overflow-auto sm:grid-cols-3">{data.detailed_progress.map((ayah) => <li key={`${ayah.surah_number}:${ayah.ayah_number}`} className="rounded bg-slate-50 px-3 py-2 text-sm">{ayah.surah_number}:{ayah.ayah_number} · {ayah.memorization_status.replaceAll("_", " ")}</li>)}</ul></>}
        {!data.progress_summary && !data.detailed_progress && <p className="mt-3 text-slate-600">No overall progress is shared.</p>}
      </section>
      {data.memorization_logs && <section className="mt-6 rounded-xl border bg-white p-5"><h2 className="text-xl font-semibold">Memorization logs</h2>{data.memorization_logs.length === 0 ? <p className="mt-3 text-slate-600">No memorization logs yet.</p> : <ul className="mt-3 divide-y">{data.memorization_logs.map((item, index) => <li key={`${item.created_at}-${index}`} className="py-3">{range(item)} · {item.status.toLowerCase()} · {new Date(item.created_at).toLocaleString()}</li>)}</ul>}</section>}
      {data.revision_logs && <section className="mt-6 rounded-xl border bg-white p-5"><h2 className="text-xl font-semibold">Revision logs</h2>{data.revision_logs.length === 0 ? <p className="mt-3 text-slate-600">No revision logs yet.</p> : <ul className="mt-3 divide-y">{data.revision_logs.map((item, index) => <li key={`${item.activity_date}-${index}`} className="py-3">{range(item)} · {item.revision_type.replaceAll("_", " ")} · {item.activity_date} · {item.time_spent_minutes} min{item.self_rating == null ? "" : ` · rating ${item.self_rating}/5`}</li>)}</ul>}</section>}
    </>}
  </main>;
}
