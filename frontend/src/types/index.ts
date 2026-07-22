// TypeScript types mirroring the exact shapes our backend actually returns — kept in sync with
// the Pydantic response schemas from Modules 2–7.

export interface Merchant {
  id: string;
  business_name: string;
  business_email: string;
  country: string;
  default_currency: string;
  kyc_status: "pending" | "under_review" | "approved" | "rejected";
  is_live_mode_enabled: boolean;
}

export interface WalletBalance {
  currency: string;
  available_balance_minor: number;
  total_settled_minor: number;
  updated_at: string;
}

export interface PaymentIntent {
  id: string;
  customer_id: string | null;
  amount_minor: number;
  currency: string;
  status:
    | "requires_payment_method"
    | "requires_confirmation"
    | "processing"
    | "succeeded"
    | "declined"
    | "canceled";
  description: string | null;
  failure_reason: string | null;
  is_live_mode: string;
  created_at: string;
  updated_at: string;
}

export interface ApiKey {
  id: string;
  key_type: "pk_test" | "sk_test" | "pk_live" | "sk_live";
  display_prefix: string;
  is_active: boolean;
  created_at: string;
  revoked_at: string | null;
}

export interface ApiKeyCreated {
  id: string;
  key_type: "pk_test" | "sk_test" | "pk_live" | "sk_live";
  display_prefix: string;
  raw_key: string;
  created_at: string;
}

// The deliberately narrow shape the checkout-scoped backend route returns —
// no merchant_id, no customer_id, no internal fields. See PaymentIntentCheckoutResponse.
export interface CheckoutIntent {
  id: string;
  amount_minor: number;
  currency: string;
  description: string | null;
  status: PaymentIntent["status"];
}

export interface CheckoutPaymentMethodCreated {
  id: string;
  card_brand: string;
  card_last4: string;
  card_exp_month: number;
  card_exp_year: number;
  created_at: string;
}

export interface Refund {
  id: string;
  payment_intent_id: string;
  amount_minor: number;
  currency: string;
  status: "succeeded" | "failed";
  reason: string | null;
  created_at: string;
}

export interface MerchantProfile {
  id: string;
  business_name: string;
  business_email: string;
  country: string;
  default_currency: string;
  kyc_status: "pending" | "under_review" | "approved" | "rejected";
  kyc_rejection_reason: string | null;
  settlement_bank_name: string | null;
  settlement_account_number: string | null;
  settlement_account_name: string | null;
  is_live_mode_enabled: boolean;
  created_at: string;
}

export interface LiveApiKeyCreated {
  id: string;
  key_type: "pk_live" | "sk_live";
  display_prefix: string;
  raw_key: string;
  created_at: string;
}

export interface FraudCase {
  id: string;
  payment_intent_id: string;
  merchant_id: string;
  risk_score: number;
  status: "pending" | "approved" | "rejected";
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface SystemSetting {
  id: string;
  key: string;
  value: Record<string, unknown>;
  description: string | null;
  updated_at: string;
}

export interface FeatureFlag {
  id: string;
  key: string;
  merchant_id: string | null;
  enabled: boolean;
  description: string | null;
  created_at: string;
}

export interface MaintenanceWindow {
  id: string;
  title: string;
  description: string | null;
  starts_at: string;
  ends_at: string;
  created_at: string;
}

export interface ReportExport {
  id: string;
  report_type: string;
  status: "pending" | "completed" | "failed" | string;
  file_path: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}