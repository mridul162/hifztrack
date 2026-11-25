"use client";

import Link from "next/link";
import { type ReactNode, useEffect, useState } from "react";
import { getJson } from "@/lib/auth";
import { formatAyahRange, type GroupDashboard } from "@/lib/dashboard";

export default function GroupDashboardPanel({ groupId, fallback }: { groupId: string; fallback: ReactNode }) {
  const [offset, setOffset] = useState(0);
  const [dashboard, setDashboard] = useState<GroupDashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    void getJson<GroupDashboard>(`/groups/${groupId}/dashboard?offset=${offset}`)
      .then((data) => { if (mounted) setDashboard(data); })
      .catch((reason: Error) => { if (mounted) setError(reason.message); });
    return () => { mounted = false; };
  }, [groupId, offset]);

  function showMembers(nextOffset: number) {
    setDashboard(null);
    setError("");
    setOffset(nextOffset);
  }

  const memberPath = (membershipId: string) => `/groups/${groupId}/members/${membershipId}/shared`;

  return <section className="mt-8" aria-labelledby="group-dashboard-heading">
    <h2 id="group-dashboard-heading" className="text-2xl font-semibold">Group dashboard</h2>
    {!dashboard && !error && <p className="mt-4" role="status">Loading group dashboard…</p>}
    {error && <p className="mt-4 rounded-xl bg-red-50 p-4 text-red-800" role="alert">
      {error} {error === "Sign in to continue." && <Link href={`/login?next=/groups/${groupId}`} className="underline">Sign in</Link>}
    </p>}
    {error && error !== "Group not found" && error !== "Sign in to continue." && fallback}
    {dashboard && <>
      <dl className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border bg-white p-5">
          <dt className="text-sm text-slate-600">Active members</dt>
          <dd className="mt-1 text-2xl font-semibold">{dashboard.active_member_count.toLocaleString()}</dd>
        </div>
        <div className="rounded-xl border bg-white p-5">
          <dt className="text-sm text-slate-600">Average Quran completion</dt>
          <dd className="mt-1 text-2xl font-semibold">{dashboard.average_completion_percentage === null ? "Unavailable" : `${dashboard.average_completion_percentage}%`}</dd>
          <dd className="mt-1 text-sm text-slate-600">{dashboard.contributor_count.toLocaleString()} {dashboard.contributor_count === 1 ? "member shares" : "members share"} progress</dd>
        </div>
      </dl>

      <section className="mt-4 rounded-xl border bg-white p-5">
        <h3 className="text-xl font-semibold">Active members and progress</h3>
        {dashboard.members.length ? <ul className="mt-3 divide-y">{dashboard.members.map((member) => <li key={member.membership_id} className="flex flex-wrap justify-between gap-3 py-3">
          <div><Link href={memberPath(member.membership_id)} className="break-words font-medium underline">{member.display_name}</Link><p className="text-sm text-slate-600">{member.role}</p></div>
          <p className="text-sm text-slate-700">{member.progress ? `${member.progress.total_memorized_ayahs.toLocaleString()} Ayahs · ${member.progress.completion_percentage}%` : "Progress unavailable"}</p>
        </li>)}</ul> : <p className="mt-3 text-sm text-slate-600">No active members on this page.</p>}
        {(dashboard.member_offset > 0 || dashboard.active_member_count > dashboard.member_limit) && <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <button className="rounded border px-4 py-2 disabled:opacity-50" disabled={dashboard.member_offset === 0} onClick={() => showMembers(Math.max(0, dashboard.member_offset - dashboard.member_limit))}>Previous active members</button>
          <button className="rounded border px-4 py-2 disabled:opacity-50" disabled={dashboard.member_offset + dashboard.member_limit >= dashboard.active_member_count} onClick={() => showMembers(dashboard.member_offset + dashboard.member_limit)}>Next active members</button>
        </div>}
      </section>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <section className="rounded-xl border bg-white p-5">
          <h3 className="text-xl font-semibold">Recent shared Sabaq</h3>
          {dashboard.recent_sabaq.length ? <ol className="mt-3 divide-y">{dashboard.recent_sabaq.map(({ membership_id, display_name, log }, index) => <li key={`${membership_id}-${index}`} className="py-2">
            <Link href={memberPath(membership_id)} className="break-words font-medium underline">{display_name}</Link>
            <p className="text-sm text-slate-600">{formatAyahRange(log)} · {log.status.toLowerCase()} · {new Date(log.created_at).toLocaleString()}</p>
          </li>)}</ol> : <p className="mt-3 text-sm text-slate-600">No shared Sabaq activity.</p>}
        </section>
        <section className="rounded-xl border bg-white p-5">
          <h3 className="text-xl font-semibold">Recent shared revision</h3>
          {dashboard.recent_revision.length ? <ol className="mt-3 divide-y">{dashboard.recent_revision.map(({ membership_id, display_name, log }, index) => <li key={`${membership_id}-${index}`} className="py-2">
            <Link href={memberPath(membership_id)} className="break-words font-medium underline">{display_name}</Link>
            <p className="text-sm text-slate-600">{formatAyahRange(log)} · {log.revision_type.toLowerCase().replaceAll("_", " ")} · {log.activity_date} · {log.time_spent_minutes} min{log.self_rating === null ? "" : ` · Rating ${log.self_rating}/5`}</p>
          </li>)}</ol> : <p className="mt-3 text-sm text-slate-600">No shared revision activity.</p>}
        </section>
      </div>
    </>}
  </section>;
}
