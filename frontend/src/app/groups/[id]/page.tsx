"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getJson, mutate } from "@/lib/auth";

type Group = { id: string; name: string; description: string | null; group_type: string; lifecycle: string; my_role: string; my_membership_id: string };
type Member = { id: string; display_name: string; role: string; state: string; joined_at: string | null };
type Page = { items: Member[]; total: number; limit: number; offset: number };
type Invitation = { id: string; expires_at: string; max_uses: number | null; used_count: number; revoked_at: string | null };

export default function GroupDetailPage() {
  const params = useParams<{ id: string }>(); const id = params.id;
  const [group, setGroup] = useState<Group | null>(null); const [members, setMembers] = useState<Member[]>([]);
  const [memberTotal, setMemberTotal] = useState(0); const [memberOffset, setMemberOffset] = useState(0);
  const [invitations, setInvitations] = useState<Invitation[]>([]); const [oneTimeToken, setOneTimeToken] = useState("");
  const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  async function load(offset = memberOffset) {
    try {
      const [g, m] = await Promise.all([getJson<Group>(`/groups/${id}`), getJson<Page>(`/groups/${id}/members?limit=50&offset=${offset}`) ]);
      setGroup(g); setMembers(m.items); setMemberTotal(m.total); setMemberOffset(offset);
      if (g.my_role === "ADMIN") setInvitations(await getJson<Invitation[]>(`/groups/${id}/invitations`));
    } catch (e) { setError((e as Error).message); } finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [id]);
  async function update(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    try { const form = new FormData(event.currentTarget); await mutate(`/groups/${id}`, "PATCH", { name: form.get("name"), description: form.get("description") || null }); await load(); }
    catch (e) { setError((e as Error).message); }
  }
  async function invite() {
    setError(""); setOneTimeToken("");
    try { const result = await mutate<{ token: string }>(`/groups/${id}/invitations`, "POST", {}); setOneTimeToken(result.token); await load(); }
    catch (e) { setError((e as Error).message); }
  }
  async function archive() { if (!window.confirm("Archive this group? It will become read-only.")) return; try { await mutate(`/groups/${id}/archive`, "POST"); await load(); } catch (e) { setError((e as Error).message); } }
  async function leave() { if (!window.confirm("Leave this group? Your access will end immediately.")) return; try { await mutate(`/groups/${id}/leave`, "POST"); await load(); } catch (e) { setError((e as Error).message); } }
  async function changeMember(member: Member, field: "role" | "state", value: string) {
    try { await mutate(`/groups/${id}/members/${member.id}`, "PATCH", { [field]: value }); await load(); }
    catch (e) { setError((e as Error).message); }
  }
  async function revoke(invitationId: string) { try { await mutate(`/groups/${id}/invitations/${invitationId}/revoke`, "POST"); await load(); } catch (e) { setError((e as Error).message); } }
  if (loading) return <main className="mx-auto max-w-3xl px-6 py-12" role="status">Loading group…</main>;
  if (!group) return <main className="mx-auto max-w-3xl px-6 py-12"><Link href="/groups" className="underline">Back to groups</Link><p role="alert" className="mt-4">{error || "Group unavailable."}</p></main>;
  const admin = group.my_role === "ADMIN" && group.lifecycle === "ACTIVE";
  return <main className="mx-auto max-w-3xl px-6 py-12">
    <nav className="mb-8 flex gap-5"><Link href="/groups" className="underline">Your groups</Link><Link href="/profile" className="underline">Profile</Link><Link href={`/groups/${id}/sharing`} className="underline">Sharing settings</Link></nav>
    <div className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-3xl font-semibold">{group.name}</h1><p className="mt-2 text-slate-600">{group.group_type} · {group.my_role} · {group.lifecycle}</p>{group.description && <p className="mt-3">{group.description}</p>}</div><button onClick={leave} className="rounded border px-4 py-2">Leave group</button></div>
    {admin && <section className="mt-8 rounded-xl border bg-white p-5"><h2 className="text-xl font-semibold">Manage group</h2><form onSubmit={update} className="mt-4 grid gap-3"><label>Name<input name="name" defaultValue={group.name} maxLength={200} required className="mt-1 block w-full rounded border p-3" /></label><label>Description<textarea name="description" defaultValue={group.description ?? ""} className="mt-1 block w-full rounded border p-3" /></label><button className="rounded bg-emerald-800 px-4 py-3 text-white">Save details</button></form><button onClick={archive} className="mt-4 rounded border border-red-300 px-4 py-2 text-red-700">Archive group</button></section>}
    {admin && group.lifecycle === "ACTIVE" && <section className="mt-6 rounded-xl border bg-white p-5"><h2 className="text-xl font-semibold">Invitations</h2><button onClick={invite} className="mt-3 rounded bg-emerald-800 px-4 py-3 text-white">Create invitation link</button>{oneTimeToken && <div className="mt-4 rounded bg-emerald-50 p-4"><p>Copy this link now. It is shown only once.</p><code className="mt-2 block break-all">{typeof window !== "undefined" ? `${window.location.origin}/invitations/accept?token=${oneTimeToken}` : oneTimeToken}</code><button className="mt-2 underline" onClick={() => setOneTimeToken("")}>Dismiss link</button></div>}<ul className="mt-4 grid gap-2">{invitations.map((inv) => <li key={inv.id} className="flex flex-wrap justify-between gap-2 border-t py-3"><span>{inv.used_count}/{inv.max_uses ?? "∞"} uses · expires {new Date(inv.expires_at).toLocaleDateString()} {inv.revoked_at ? "· revoked" : ""}</span>{!inv.revoked_at && <button onClick={() => revoke(inv.id)} className="underline">Revoke</button>}</li>)}</ul></section>}
    <section className="mt-8"><h2 className="text-xl font-semibold">Members ({memberTotal})</h2><ul className="mt-3 divide-y rounded-xl border bg-white">{members.map((member) => <li key={member.id} className="flex flex-wrap items-center justify-between gap-3 p-4"><div><p className="font-medium">{member.display_name}</p><p className="text-sm text-slate-500">{member.role} · {member.state}</p></div>{admin && member.id !== group.my_membership_id && member.state !== "LEFT" && <div className="flex gap-2"><select aria-label={`Role for ${member.display_name}`} value={member.role} onChange={(e) => changeMember(member, "role", e.target.value)} className="rounded border p-2"><option>MEMBER</option><option>MENTOR</option><option>ADMIN</option></select><select aria-label={`State for ${member.display_name}`} value={member.state} onChange={(e) => changeMember(member, "state", e.target.value)} className="rounded border p-2"><option>ACTIVE</option><option>SUSPENDED</option><option>LEFT</option></select></div>}</li>)}</ul><div className="mt-3 flex justify-between"><button disabled={memberOffset === 0} onClick={() => load(Math.max(0, memberOffset - 50))} className="rounded border px-4 py-2 disabled:opacity-50">Previous</button><span className="self-center text-sm text-slate-600">{memberTotal ? memberOffset + 1 : 0}–{Math.min(memberOffset + members.length, memberTotal)} of {memberTotal}</span><button disabled={memberOffset + members.length >= memberTotal} onClick={() => load(memberOffset + 50)} className="rounded border px-4 py-2 disabled:opacity-50">Next</button></div></section>
    <section className="mt-6 rounded-xl border bg-white p-5"><h2 className="text-xl font-semibold">Shared information</h2><ul className="mt-3 grid gap-2">{members.filter((member) => member.state === "ACTIVE").map((member) => <li key={member.id}><Link className="underline" href={`/groups/${id}/members/${member.id}/shared`}>View {member.display_name}'s shared information</Link></li>)}</ul></section>
    {error && <p role="alert" className="mt-5 text-red-700">{error}</p>}
  </main>;
}
