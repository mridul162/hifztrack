type AyahRange = {
  start_surah_number: number;
  start_ayah_number: number;
  end_surah_number: number;
  end_ayah_number: number;
};

type ProgressSummary = { total_memorized_ayahs: number; completion_percentage: number };
type SharedActivity<Log> = { membership_id: string; display_name: string; log: AyahRange & Log };

export type PersonalDashboard = {
  progress: ProgressSummary & {
    status_counts: { not_started: number; learning: number; memorized: number; strong: number };
  };
  recent_sabaq: (AyahRange & { id: string; activity_date: string; status: string })[];
  recent_revision: (AyahRange & {
    id: string; activity_date: string; revision_type: string; time_spent_minutes: number;
  })[];
  memberships: { group_id: string; group_name: string; role: string; lifecycle: string }[];
};

export type GroupDashboard = {
  active_member_count: number;
  average_completion_percentage: number | null;
  contributor_count: number;
  member_limit: number;
  member_offset: number;
  members: { membership_id: string; display_name: string; role: string; progress: ProgressSummary | null }[];
  recent_sabaq: SharedActivity<{ created_at: string; status: string }>[];
  recent_revision: SharedActivity<{
    activity_date: string; revision_type: string; time_spent_minutes: number; self_rating: number | null;
  }>[];
};

export function formatAyahRange(entry: AyahRange) {
  return `${entry.start_surah_number}:${entry.start_ayah_number}–${entry.end_surah_number}:${entry.end_ayah_number}`;
}
