"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getJson, mutate } from "@/lib/auth";

type Visibility = "PRIVATE" | "SUMMARY" | "DETAILED";
type SharingSettings = {
  membership_id: string;
  overall_progress_visibility: Visibility;
  share_memorization_logs: boolean;
  share_revision_logs: boolean;
  share_goals: boolean;
  share_assessments: boolean;
};

const labels: Record<Visibility, string> = {
  PRIVATE: "Private",
  SUMMARY: "Summary",
  DETAILED: "Detailed",
};

export default function SharingSettingsPage() {
  const { id } = useParams<{ id: string }>();
  const [settings, setSettings] = useState<SharingSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let mounted = true;
    void getJson<SharingSettings>(`/groups/${id}/sharing/me`)
      .then((result) => { if (mounted) setSettings(result); })
      .catch((reason) => { if (mounted) setError((reason as Error).message); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [id]);

  function change<K extends keyof SharingSettings>(key: K, value: SharingSettings[K]) {
    if (!settings) return;
    setSettings({ ...settings, [key]: value });
    setNotice("");
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!settings) return;
    setSaving(true); setError(""); setNotice("");
    try {
      const saved = await mutate<SharingSettings>(`/groups/${id}/sharing/me`, "PATCH", {
        overall_progress_visibility: settings.overall_progress_visibility,
        share_memorization_logs: settings.share_memorization_logs,
        share_revision_logs: settings.share_revision_logs,
        share_goals: settings.share_goals,
        share_assessments: settings.share_assessments,
      });
      setSettings(saved);
      setNotice("Your sharing settings have been saved.");
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <main className="mx-auto max-w-3xl px-6 py-12" role="status">Loading sharing settings...</main>;
  if (!settings) return <main className="mx-auto max-w-3xl px-6 py-12"><Link className="underline" href={`/groups/${id}`}>Back to group</Link><p role="alert" className="mt-4">{error || "Sharing settings are unavailable."}</p></main>;

  return <main className="mx-auto max-w-3xl px-6 py-12">
    <nav className="mb-8 flex gap-5"><Link className="underline" href={`/groups/${id}`}>Back to group</Link><Link className="underline" href="/groups">Your groups</Link></nav>
    <h1 className="text-3xl font-semibold">Your sharing settings</h1>
    <p className="mt-2 text-slate-600">These choices apply only to your membership in this group. New memberships start with summary progress shared and all other categories off.</p>
    <form onSubmit={save} className="mt-6 grid gap-5 rounded-xl border bg-white p-6">
      <label className="grid gap-2 font-medium">Overall progress
        <select value={settings.overall_progress_visibility} onChange={(event) => change("overall_progress_visibility", event.target.value as Visibility)} className="rounded border p-3">
          {(Object.keys(labels) as Visibility[]).map((value) => <option key={value} value={value}>{labels[value]}</option>)}
        </select>
        <span className="text-sm font-normal text-slate-600">Private shares nothing. Summary shares total memorized Ayahs and completion percentage. Detailed shares each Ayah reference and its current status, without activity history.</span>
      </label>
      {([
        ["share_memorization_logs", "Memorization logs", "Surah/Ayah ranges, submission time, and current record status. Private notes and correction details stay private."],
        ["share_revision_logs", "Revision logs", "Surah/Ayah ranges, revision type, activity date, duration, and self-rating. Private notes stay private; sharing does not allow edits or deletion."],
        ["share_goals", "Goals", "Goal details can be shared when goal features are available. Goal management is not part of this release."],
        ["share_assessments", "Assessments", "Assessment results and recorded feedback can be shared when assessment features are available. Assessment workflows are not part of this release."],
      ] as const).map(([key, title, description]) => <label key={key} className="flex gap-3 rounded-lg border p-4">
        <input type="checkbox" checked={settings[key]} onChange={(event) => change(key, event.target.checked)} className="mt-1 h-4 w-4 accent-emerald-800" />
        <span><span className="font-medium">{title}</span><span className="mt-1 block text-sm text-slate-600">{description}</span></span>
      </label>)}
      <button disabled={saving} className="rounded bg-emerald-800 px-4 py-3 text-white disabled:opacity-50">{saving ? "Saving..." : "Save settings"}</button>
    </form>
    {error && <p role="alert" className="mt-4 rounded bg-red-50 p-4 text-red-800">{error}</p>}
    {notice && <p role="status" className="mt-4 rounded bg-emerald-50 p-4 text-emerald-900">{notice}</p>}
  </main>;
}
