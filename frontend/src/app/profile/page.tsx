"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { getProfile, mutate, UserProfile } from "@/lib/auth";

export default function ProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { getProfile().then(setUser).catch((reason: Error) => setError(reason.message)); }, []);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    try { setUser(await mutate<UserProfile>("/users/me", "PATCH", Object.fromEntries(new FormData(event.currentTarget)))); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Update failed."); }
  }
  async function logout() { try { await mutate<void>("/auth/logout", "POST"); setUser(null); setError("You have signed out."); } catch (reason) { setError(reason instanceof Error ? reason.message : "Sign out failed."); } }
  return <main className="mx-auto max-w-lg px-6 py-16"><nav className="mb-8 flex flex-wrap gap-5"><Link className="underline" href="/">Home</Link><Link className="underline" href="/login">Sign in</Link><Link className="underline" href="/register">Register</Link>{user && <Link className="underline" href="/dashboard">Dashboard</Link>}</nav>
    <h1 className="text-3xl font-semibold">Your profile</h1>
    {user && <><p className="mt-4">{user.email}</p><form onSubmit={save} className="mt-6 grid gap-4"><label>Name<input name="full_name" defaultValue={user.full_name} required maxLength={150} className="mt-1 block w-full rounded border p-3" /></label><button className="rounded bg-emerald-800 p-3 text-white">Save profile</button></form><button onClick={logout} className="mt-4 rounded border px-4 py-2">Sign out</button></>}
    {error && <p className="mt-4" role="status">{error} {!user && !error.startsWith("You have") && <Link className="underline" href="/login">Sign in</Link>}</p>}
  </main>;
}
