"use client";

import Link from "next/link";
import { BookOpen, ChevronDown, History, Users, type LucideIcon } from "lucide-react";
import { useEffect, useId, useState, type ReactNode } from "react";
import { getJson } from "@/lib/auth";
import { formatAyahRange, type PersonalDashboard } from "@/lib/dashboard";

const statuses = [
  { key: "not_started", label: "Not started", color: "bg-slate-400" },
  { key: "learning", label: "Learning", color: "bg-amber-400" },
  { key: "memorized", label: "Memorized", color: "bg-[#65ad7a]" },
  { key: "strong", label: "Strong", color: "bg-[#178449]" },
] as const;

const progressOrder = [...statuses].reverse();

function DashboardSection({ Icon, title, href, linkText, children }: {
  Icon: LucideIcon;
  title: string;
  href: string;
  linkText: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const contentId = useId();

  return <section>
    <div className="flex min-h-11 items-center justify-between gap-3">
      <h2 className="min-w-0">
        <button type="button" aria-expanded={open} aria-controls={contentId} onClick={() => setOpen(!open)} className="flex cursor-pointer items-center gap-2 rounded py-2 text-left text-sm font-semibold hover:text-emerald-200 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-emerald-300">
          <Icon aria-hidden="true" size={16} className="shrink-0" />
          {title}
          <ChevronDown aria-hidden="true" size={14} className={`shrink-0 text-neutral-400 ${open ? "rotate-180" : ""}`} />
        </button>
      </h2>
      <Link href={href} aria-label={linkText === "View history" ? `View ${title.toLowerCase()} history` : undefined} className="shrink-0 rounded py-2 text-sm text-neutral-300 hover:text-white hover:underline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-emerald-300">{linkText}</Link>
    </div>
    <div id={contentId} hidden={!open} className="mb-2 rounded-lg bg-neutral-900/60 px-3 text-sm">
      {children}
    </div>
  </section>;
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<PersonalDashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    void getJson<PersonalDashboard>("/dashboard/me")
      .then((data) => { if (mounted) setDashboard(data); })
      .catch((reason: Error) => { if (mounted) setError(reason.message); });
    return () => { mounted = false; };
  }, []);

  const progress = dashboard?.progress;

  return <main className="min-h-screen bg-neutral-950 px-4 py-8 text-neutral-100 sm:px-6 sm:py-12">
    <div className="mx-auto max-w-3xl">
      <nav aria-label="Dashboard navigation" className="mb-4 flex flex-wrap gap-x-5 gap-y-2 px-1 text-sm text-neutral-300">
        <Link href="/" className="underline decoration-neutral-500 underline-offset-4 hover:text-white">Home</Link>
        <Link href="/profile" className="underline decoration-neutral-500 underline-offset-4 hover:text-white">Profile</Link>
      </nav>

      <div className="rounded-2xl border border-neutral-700 bg-[#202020] p-4 sm:p-5">
        <h1 className="text-lg font-semibold">Your memorization progress</h1>
        {!dashboard && !error && <p className="mt-4 text-sm text-neutral-300" role="status">Loading your dashboard…</p>}
        {error && <p className="mt-4 rounded-lg bg-red-950 px-3 py-2 text-sm text-red-100" role="alert">
          {error} {error === "Sign in to continue." && <Link href="/login?next=/dashboard" className="underline">Sign in</Link>}
        </p>}
        {dashboard && progress && <>
          <p className="mt-4 text-sm text-neutral-300">Total memorized</p>
          <div className="mt-1 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 tabular-nums">
            <p className="text-2xl font-semibold">{progress.total_memorized_ayahs.toLocaleString()} <span className="text-sm font-medium text-neutral-300">/ 6,236</span></p>
            <p className="text-2xl font-semibold text-emerald-400">
              {progress.completion_percentage.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%<span className="sr-only"> complete</span>
            </p>
          </div>
          <div aria-hidden="true" className="mt-3 flex h-1 overflow-hidden rounded-full bg-slate-400">
            {progressOrder.map(({ key, color }) => <div key={key} className={`basis-0 ${color}`} style={{ flexGrow: progress.status_counts[key] }} />)}
          </div>
          <dl className="mt-5 grid grid-cols-2 gap-x-3 gap-y-3 text-sm sm:gap-x-5">
            {statuses.map(({ key, label, color }) => <div key={key} className="flex min-w-0 flex-wrap items-center justify-between gap-x-2 gap-y-0.5">
              <dt className="flex items-center gap-2 text-neutral-300"><span aria-hidden="true" className={`size-2.5 shrink-0 rounded-full ${color}`} />{label}</dt>
              <dd className="font-semibold tabular-nums">{progress.status_counts[key].toLocaleString()}</dd>
            </div>)}
          </dl>

          <div className="mt-6 border-t border-neutral-700 pt-3">
            <DashboardSection Icon={BookOpen} title="Recent Sabaq" href="/memorization" linkText="View history">
              {dashboard.recent_sabaq.length ? <ul className="divide-y divide-neutral-700">{dashboard.recent_sabaq.map((entry) => <li key={entry.id} className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 py-2.5">
                <span className="font-medium">{formatAyahRange(entry)}</span>
                <span className="text-neutral-300">{entry.activity_date} · {entry.status.toLowerCase()}</span>
              </li>)}</ul> : <p className="py-2.5 text-neutral-300">No Sabaq activity yet.</p>}
            </DashboardSection>
            <DashboardSection Icon={History} title="Recent revision" href="/revision" linkText="View history">
              {dashboard.recent_revision.length ? <ul className="divide-y divide-neutral-700">{dashboard.recent_revision.map((entry) => <li key={entry.id} className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 py-2.5">
                <span className="font-medium">{formatAyahRange(entry)}</span>
                <span className="text-neutral-300">{entry.activity_date} · {entry.revision_type.toLowerCase().replaceAll("_", " ")} · {entry.time_spent_minutes} min</span>
              </li>)}</ul> : <p className="py-2.5 text-neutral-300">No revision activity yet.</p>}
            </DashboardSection>
            <DashboardSection Icon={Users} title="Your groups" href="/groups" linkText="View groups">
              {dashboard.memberships.length ? <ul className="divide-y divide-neutral-700">{dashboard.memberships.map((group) => <li key={group.group_id} className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 py-2.5">
                <Link href={`/groups/${group.group_id}`} className="min-w-0 break-words font-medium underline underline-offset-4">{group.group_name}</Link>
                <span className="text-neutral-300">{group.role}{group.lifecycle === "ARCHIVED" && " · Archived"}</span>
              </li>)}</ul> : <p className="py-2.5 text-neutral-300">You have no active group memberships.</p>}
            </DashboardSection>
          </div>
        </>}
      </div>
    </div>
  </main>;
}
