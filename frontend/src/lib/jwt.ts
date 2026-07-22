/*
Minimal, dependency-free JWT payload decoder — used only to read the `role` claim client-side
for route gating (AdminRoute). This is NOT a security boundary by itself: the backend's
require_admin dependency is the real enforcement point on every admin route. This only
prevents a non-admin from seeing the admin UI shell at all.
*/

export function decodeJwtPayload(token: string): { sub?: string; role?: string; merchant_id?: string | null } | null {
  try {
    const payloadPart = token.split(".")[1];
    const decoded = atob(payloadPart.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

export function getCurrentRole(): string | null {
  const token = localStorage.getItem("access_token");
  if (!token) return null;
  const payload = decodeJwtPayload(token);
  return payload?.role ?? null;
}