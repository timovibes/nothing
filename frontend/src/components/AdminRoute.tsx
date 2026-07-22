/*
Gate for Admin Portal routes — requires both a valid session AND role === "admin". Real
enforcement still lives in the backend's require_admin dependency on every /api/v1/admin/*
route; this only stops a non-admin merchant_owner from loading the admin UI shell itself.
*/

import { Navigate } from "react-router-dom";
import { getCurrentRole } from "../lib/jwt";

export function AdminRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("access_token");
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  const role = getCurrentRole();
  if (role !== "admin") {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}