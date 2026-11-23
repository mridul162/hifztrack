"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { getJson, mutate } from "@/lib/auth";

type Group = { id: string; name: string; description: string | null; group_type: string; lifecycle: string; my_role: string };

export default function GroupsPage() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [groupType, setGroupType] = useState("COMMUNITY");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  async function load() { try { setGroups(await getJson<Group[]>("/groups")); } catch (e) { setError((e as Error).message); } finally { setLoading(false); } }
  useEffect(() => { void load(); }, []);
  async function create(event: FormEvent) {
    event.preventDefault(); setError("");
    try {
      await mutate<Group>("/groups", "POST", { name, description: description || null, group_type: groupType });
      setName(""); setDescription(""); await load();
    } catch (e) { setError((e as Error).message); }
  }
  return <main className="mx-auto max-w-3xl px-6 py-12">
    <nav className="mb-8 flex gap-5"><Link className="underline" href="/">Home</Link><Link className="underline" href="/profile">Profile</Link></nav>
    <h1 className="text-3xl font-semibold">Your groups</h1>
    <section className="mt-6 grid gap-3">{loading ? <p role="status">Loading groups…</p> : groups.length === 0 ? <p className="text-slate-600">You have not joined a group yet.</p> : groups.map((group) => <Link key={group.id} href={`/groups/${group.id}`} className="rounded-xl border bg-white p-5 hover:border-emerald-700"><span className="font-semibold">{group.name}</span><span className="ml-3 text-sm text-slate-500">{group.group_type} · {group.my_role}</span>{group.description && <p className="mt-2 text-sm text-slate-600">{group.description}</p>}</Link>)}</section>
    <form onSubmit={create} className="mt-10 grid gap-4 rounded-xl border bg-white p-6"><h2 className="text-xl font-semibold">Create a group</h2>
      <label>Group name<input required maxLength={200} value={name} onChange={(e) => setName(e.target.value)} className="mt-1 block w-full rounded border p-3" /></label>
      <label>Type<select value={groupType} onChange={(e) => setGroupType(e.target.value)} className="mt-1 block w-full rounded border p-3"><option value="COMMUNITY">Community</option><option value="CLASS">Class</option><option value="COHORT">Cohort</option></select></label>
      <label>Description<textarea maxLength={4000} value={description} onChange={(e) => setDescription(e.target.value)} className="mt-1 block w-full rounded border p-3" rows={3} /></label>
      <button className="rounded bg-emerald-800 px-4 py-3 text-white">Create group</button>
    </form>
    {error && <p role="alert" className="mt-4 text-red-700">{error}</p>}
  </main>;
}
