"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function Home() {
  const [apiStatus, setApiStatus] = useState("Checking API…");

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    fetch(`${apiUrl}/health/live`)
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        return response.json();
      })
      .then(() => setApiStatus("API connection is available"))
      .catch(() => setApiStatus("API connection is unavailable"));
  }, []);

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-16">
      <section className="w-full max-w-xl rounded-2xl border border-emerald-950/10 bg-white p-8 shadow-sm sm:p-12">
        <nav className="mb-8 flex flex-wrap gap-5"><Link className="underline" href="/login">Sign in</Link><Link className="underline" href="/register">Register</Link><Link className="underline" href="/profile">Profile</Link><Link className="underline" href="/groups">Groups</Link><Link className="underline" href="/quran">Quran references</Link></nav>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-800">
          HifzTrack
        </p>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
          Application foundation is running.
        </h1>
        <p className="mt-4 leading-7 text-slate-600">
          The development environment is ready for the next approved implementation task.
        </p>
        <p className="mt-6 border-t border-slate-100 pt-4 text-sm text-slate-600" role="status">
          {apiStatus}
        </p>
      </section>
    </main>
  );
}
