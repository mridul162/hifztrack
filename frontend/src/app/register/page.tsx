"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { mutate, UserProfile } from "@/lib/auth";

export default function RegisterPage() {
  const [error, setError] = useState("");
  const [user, setUser] = useState<UserProfile | null>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const form = new FormData(event.currentTarget);
    try { setUser(await mutate<UserProfile>("/auth/register", "POST", Object.fromEntries(form))); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Registration failed."); }
  }
  return <main className="mx-auto max-w-lg px-6 py-16"><h1 className="text-3xl font-semibold">Create your account</h1>
    {user ? <p className="mt-6">Account created. <Link className="underline" href="/profile">Continue to your profile</Link></p> :
      <form onSubmit={submit} className="mt-8 grid gap-4">
        <label>Name<input name="full_name" autoComplete="name" required maxLength={150} className="mt-1 block w-full rounded border p-3" /></label>
        <label>Email<input name="email" type="email" autoComplete="email" required className="mt-1 block w-full rounded border p-3" /></label>
        <label>Password<input name="password" type="password" autoComplete="new-password" minLength={12} maxLength={256} required className="mt-1 block w-full rounded border p-3" /></label>
        <button className="rounded bg-emerald-800 p-3 text-white">Create account</button>{error && <p role="alert">{error}</p>}
      </form>}
    <p className="mt-6">Already registered? <Link className="underline" href="/login">Sign in</Link></p></main>;
}
