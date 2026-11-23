const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type CsrfResponse = { csrf_token: string };
export type UserProfile = { id: string; email: string; full_name: string; created_at: string };

async function csrfToken(): Promise<string> {
  const response = await fetch(`${apiUrl}/auth/csrf`, { credentials: "include" });
  if (!response.ok) throw new Error("Could not prepare a secure request.");
  return ((await response.json()) as CsrfResponse).csrf_token;
}

export async function mutate<T>(path: string, method: string, body?: unknown): Promise<T> {
  const token = await csrfToken();
  const response = await fetch(`${apiUrl}${path}`, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!response.ok) {
    const data = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(data.detail ?? "Request failed.");
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function getProfile(): Promise<UserProfile> {
  const response = await fetch(`${apiUrl}/users/me`, { credentials: "include", cache: "no-store" });
  if (!response.ok) throw new Error("Sign in to view your profile.");
  return (await response.json()) as UserProfile;
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, { credentials: "include", cache: "no-store" });
  if (!response.ok) {
    if (response.status === 401) throw new Error("Sign in to continue.");
    const data = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(data.detail ?? "Request failed.");
  }
  return (await response.json()) as T;
}
