import { BrowserRouter, Routes, Route } from "react-router-dom";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";
import { OverviewPage } from "./pages/OverviewPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { ApiKeysPage } from "./pages/ApiKeysPage";
import { StubPage } from "./pages/StubPage";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { DashboardLayout } from "./components/DashboardLayout";
import { CheckoutPage } from "./pages/CheckoutPage";
import { PaymentsPage } from "./pages/PaymentsPage";
import { RefundsPage } from "./pages/RefundsPage";
import { CustomersPage } from "./pages/CustomersPage";
import { WebhooksPage } from "./pages/WebhooksPage";
import { PayoutsPage } from "./pages/PayoutsPage";
import { SettingsPage } from "./pages/SettingsPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/checkout/:intentId" element={<CheckoutPage />} />
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
                <StubPage title="Team" />
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
      </Routes>
    </BrowserRouter>
  );
}

export default App;