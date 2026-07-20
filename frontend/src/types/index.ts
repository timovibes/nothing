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