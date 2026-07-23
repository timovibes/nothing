import { BrowserRouter, Routes, Route } from "react-router-dom";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";
import { OverviewPage } from "./pages/OverviewPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { ApiKeysPage } from "./pages/ApiKeysPage";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { DashboardLayout } from "./components/DashboardLayout";
import { CheckoutPage } from "./pages/CheckoutPage";
import { PaymentsPage } from "./pages/PaymentsPage";
import { RefundsPage } from "./pages/RefundsPage";
import { CustomersPage } from "./pages/CustomersPage";
import { WebhooksPage } from "./pages/WebhooksPage";
import { PayoutsPage } from "./pages/PayoutsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { AdminRoute } from "./components/AdminRoute";
import { AdminLayout } from "./components/AdminLayout";
import { AdminMerchantsPage } from "./pages/admin/AdminMerchantsPage";
import { AdminFraudPage } from "./pages/admin/AdminFraudPage";
import { AdminSettingsPage } from "./pages/admin/AdminSettingsPage";
import { AdminFeatureFlagsPage } from "./pages/admin/AdminFeatureFlagsPage";
import { AdminMaintenancePage } from "./pages/admin/AdminMaintenancePage";
import { AdminReportsPage } from "./pages/admin/AdminReportsPage";
import { TeamPage } from "./pages/TeamPage";
import { AcceptInvitePage } from "./pages/AcceptInvitePage";
import { AdminChangePasswordPage } from "./pages/admin/AdminChangePasswordPage";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/checkout/:intentId" element={<CheckoutPage />} />
        <Route path="/accept-invite" element={<AcceptInvitePage />} />
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <OnboardingPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <OverviewPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/api-keys"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ApiKeysPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/payments"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PaymentsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/refunds"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RefundsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/payouts"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PayoutsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/customers"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <CustomersPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/webhooks"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <WebhooksPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/team"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <TeamPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <SettingsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/merchants"
          element={<AdminRoute><AdminLayout><AdminMerchantsPage /></AdminLayout></AdminRoute>}
        />
        <Route
          path="/admin/fraud"
          element={<AdminRoute><AdminLayout><AdminFraudPage /></AdminLayout></AdminRoute>}
        />
        <Route
          path="/admin/settings"
          element={<AdminRoute><AdminLayout><AdminSettingsPage /></AdminLayout></AdminRoute>}
        />
        <Route
          path="/admin/feature-flags"
          element={<AdminRoute><AdminLayout><AdminFeatureFlagsPage /></AdminLayout></AdminRoute>}
        />
        <Route
          path="/admin/maintenance"
          element={<AdminRoute><AdminLayout><AdminMaintenancePage /></AdminLayout></AdminRoute>}
        />
        <Route
          path="/admin/reports"
          element={<AdminRoute><AdminLayout><AdminReportsPage /></AdminLayout></AdminRoute>}
        />
        <Route
          path="/admin/change-password"
          element={<AdminRoute><AdminLayout><AdminChangePasswordPage /></AdminLayout></AdminRoute>}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;