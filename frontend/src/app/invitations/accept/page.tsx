"use client";

import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { mutate } from "@/lib/auth";

function Acceptance() {
  const params = useSearchParams(); const router = useRouter();
  const [error, setError] = useState(""); const [working, setWorking] = useState(false); const token = params.get("token") ?? "";
  useEffect(() => { if (token) window.history.replaceState(null, "", "/invitations/accept"); }, [token]);
  async function accept() { setWorking(true); setError(""); try { const membership = await mutate<{ group_id: string }>("/invitations/accept", "POST", { token }); router.replace(`/groups/${membership.group_id}`); } catch (e) { setError((e as Error).message); } finally { setWorking(false); } }
  return <main className="mx-auto max-w-lg px-6 py-16"><Link href="/groups" className="underline">Your groups</Link><h1 className="mt-8 text-3xl font-semibold">Join a group</h1><p className="mt-3 text-slate-600">Accept this invitation to join as a member.</p>{token ? <button disabled={working} onClick={accept} className="mt-6 rounded bg-emerald-800 px-5 py-3 text-white">{working ? "Joining…" : "Accept invitation"}</button> : <p className="mt-6">Invitation token is missing.</p>}{error && <p role="alert" className="mt-4 text-red-700">{error} <Link href={`/login?next=${encodeURIComponent(`/invitations/accept?token=${token}`)}`} className="underline">Sign in</Link></p>}</main>;
}

export default function AcceptInvitationPage() { return <Suspense fallback={<main className="p-8">Loading invitation…</main>}><Acceptance /></Suspense>; }
