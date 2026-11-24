"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Surah = { surah_number: number; ayah_count: number };
type ReferenceSource = {
  category: string;
  source_name: string;
  source_version: string;
  source_url: string;
  usage_conditions: string;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function QuranReferencePage() {
  const [surahs, setSurahs] = useState<Surah[]>([]);
  const [source, setSource] = useState<ReferenceSource | null>(null);
  const [selectedSurah, setSelectedSurah] = useState<Surah | null>(null);
  const [ayahNumbers, setAyahNumbers] = useState<number[]>([]);
  const [selectedAyah, setSelectedAyah] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch(`${apiUrl}/quran/surahs`),
      fetch(`${apiUrl}/quran/reference-source`),
    ])
      .then(async ([surahResponse, sourceResponse]) => {
        if (!surahResponse.ok || !sourceResponse.ok) {
          throw new Error("Quran reference data is not loaded in this environment yet.");
        }
        const [surahData, sourceData] = (await Promise.all([
          surahResponse.json(),
          sourceResponse.json(),
        ])) as [Surah[], ReferenceSource[]];
        setSurahs(surahData);
        setSource(
          sourceData.find((item) => item.category === "SURAH_AYAH_ORDER") ?? null,
        );
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Could not load Quran references.");
      })
      .finally(() => setLoading(false));
  }, []);

  async function chooseSurah(surah: Surah) {
    setSelectedSurah(surah);
    setSelectedAyah(null);
    setAyahNumbers([]);
    setError(null);
    try {
      const response = await fetch(`${apiUrl}/quran/surahs/${surah.surah_number}/ayahs`);
      if (!response.ok) throw new Error("Could not load this Surah's Ayah references.");
      const result = (await response.json()) as { ayah_numbers: number[] };
      setAyahNumbers(result.ayah_numbers);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load Ayah references.");
    }
  }

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <nav className="mb-8 flex gap-5 text-sm">
          <Link className="underline" href="/">Home</Link>
          <Link className="underline" href="/profile">Profile</Link>
          <Link className="underline" href="/groups">Groups</Link>
        </nav>
        <header className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-800">
            HifzTrack
          </p>
          <h1 className="mt-2 text-3xl font-semibold">Quran references</h1>
          <p className="mt-3 max-w-2xl leading-7 text-slate-600">
            Browse canonical Surah and Ayah numbers. This reference view does not display Quran
            text, translations, or unverified page and Juz mappings.
          </p>
        </header>

        {loading && <p role="status">Loading references...</p>}
        {error && (
          <p className="mb-5 rounded-lg bg-amber-50 p-4 text-amber-950" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(20rem,0.8fr)]">
            <section
              className="rounded-xl border border-emerald-950/10 bg-white p-5 shadow-sm"
              aria-labelledby="surah-heading"
            >
              <h2 id="surah-heading" className="mb-4 text-lg font-semibold">
                Surahs
              </h2>
              <div className="grid max-h-[36rem] grid-cols-2 gap-2 overflow-y-auto sm:grid-cols-3">
                {surahs.map((surah) => (
                  <button
                    key={surah.surah_number}
                    type="button"
                    onClick={() => chooseSurah(surah)}
                    aria-pressed={selectedSurah?.surah_number === surah.surah_number}
                    className={[
                      "rounded-lg border border-slate-200 px-3 py-2 text-left text-sm",
                      "hover:border-emerald-700 aria-pressed:border-emerald-800",
                      "aria-pressed:bg-emerald-50",
                    ].join(" ")}
                  >
                    <span className="block font-medium">Surah {surah.surah_number}</span>
                    <span className="text-slate-600">{surah.ayah_count} Ayahs</span>
                  </button>
                ))}
              </div>
            </section>

            <section
              className="rounded-xl border border-emerald-950/10 bg-white p-5 shadow-sm"
              aria-labelledby="ayah-heading"
            >
              <h2 id="ayah-heading" className="mb-1 text-lg font-semibold">
                {selectedSurah ? `Ayahs in Surah ${selectedSurah.surah_number}` : "Ayah references"}
              </h2>
              <p className="mb-4 text-sm text-slate-600">
                {selectedAyah && selectedSurah
                  ? `Selected reference: ${selectedSurah.surah_number}:${selectedAyah}`
                  : "Choose a Surah, then select an Ayah number."}
              </p>
              {selectedSurah && (
                <div
                  className="grid max-h-[32rem] grid-cols-6 gap-2 overflow-y-auto sm:grid-cols-8"
                >
                  {ayahNumbers.map((ayahNumber) => (
                    <button
                      key={ayahNumber}
                      type="button"
                      onClick={() => setSelectedAyah(ayahNumber)}
                      aria-pressed={selectedAyah === ayahNumber}
                      aria-label={`Surah ${selectedSurah.surah_number}, Ayah ${ayahNumber}`}
                      className={[
                        "rounded-md border border-slate-200 py-2 text-sm",
                        "hover:border-emerald-700 aria-pressed:border-emerald-800",
                        "aria-pressed:bg-emerald-50",
                      ].join(" ")}
                    >
                      {ayahNumber}
                    </button>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}

        {source && (
          <aside
            className="mt-6 rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600"
          >
            Reference numbering source: {source.source_name}, Uthmani {source.source_version}.{" "}
            <a
              className="underline"
              href={source.source_url}
              target="_blank"
              rel="noreferrer"
            >
              Tanzil Project
            </a>.
            <p className="mt-2">{source.usage_conditions}</p>
          </aside>
        )}
      </div>
    </main>
  );
}
