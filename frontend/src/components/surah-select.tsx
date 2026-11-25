export type Surah = {
  surah_number: number;
  ayah_count: number;
  name_ar?: string;
  name_latin?: string;
};

type Props = {
  id?: string;
  surahs: Surah[];
  value: number;
  onChange: (value: string) => void;
};

export function SurahSelect({ id, surahs, value, onChange }: Props) {
  return (
    <select id={id} className="rounded-md border border-slate-300 px-3 py-2"
      required value={value} onChange={(event) => onChange(event.target.value)}>
      {surahs.map((surah) => {
        const label = [`Surah ${surah.surah_number}`, surah.name_latin, surah.name_ar]
          .filter(Boolean).join(" · ");
        return <option key={surah.surah_number} value={surah.surah_number}>{label}</option>;
      })}
    </select>
  );
}
