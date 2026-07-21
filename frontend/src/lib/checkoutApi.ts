/*
Separate, minimal axios client for the Customer Checkout page. Deliberately does NOT reuse
api.ts: a customer visiting checkout has no JWT, and api.ts's 401 interceptor redirects to
/login, which would break the flow. This client is authenticated per-call with the merchant's
publishable (pk_) key instead, taken from the checkout link's query params — never a JWT,
never a secret (sk_) key.
*/

import axios from "axios";

export function createCheckoutClient(publishableKey: string) {
  return axios.create({
    baseURL: "http://localhost:8000",
    headers: {
      Authorization: `Bearer ${publishableKey}`,
    },
  });
}