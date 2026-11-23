"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { mutate, UserProfile } from "@/lib/auth";

function LoginForm() {
  const search = useSearchParams();
  const next = search.get("next");
  const destination = next?.startsWith("/") && !next.startsWith("//") ? next : "/profile";
  const [error, setError] = useState("");
  const [user, setUser] = useState<UserProfile | null>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    try { setUser(await mutate<UserProfile>("/auth/login", "POST", Object.fromEntries(new FormData(event.currentTarget)))); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Sign in failed."); }
  }
  return <main className="mx-auto max-w-lg px-6 py-16"><h1 className="text-3xl font-semibold">Sign in</h1>
    {user ? <p className="mt-6">Signed in. <Link className="underline" href={destination}>Continue</Link></p> :
      <form onSubmit={submit} className="mt-8 grid gap-4">
        <label>Email<input name="email" type="email" autoComplete="email" required className="mt-1 block w-full rounded border p-3" /></label>
        <label>Password<input name="password" type="password" autoComplete="current-password" required className="mt-1 block w-full rounded border p-3" /></label>
        <button className="rounded bg-emerald-800 p-3 text-white">Sign in</button>{error && <p role="alert">{error}</p>}
      </form>}
    <p className="mt-6">Need an account? <Link className="underline" href="/register">Register</Link></p></main>;
}

export default function LoginPage() { return <Suspense fallback={<main className="p-8">Loading…</main>}><LoginForm /></Suspense>; }
