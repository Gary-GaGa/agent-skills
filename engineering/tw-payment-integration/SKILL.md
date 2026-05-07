---
name: tw-payment-integration
description: >
  Payment integration for the Taiwan market — ECPay and NewebPay flows,
  payment methods (credit card / ATM / convenience store), background
  callback handling, refunds, order state management, and security
  considerations. For web apps that need to collect payments in Taiwan.
category: engineering
tags: [payment, taiwan, ecpay, newebpay, integration, fintech]
keywords: [ECPay, NewebPay, TapPay, LINE Pay, CheckMacValue, MerchantTradeNo]
related: [api-design-rest, auth-patterns, mongodb-go, line-integration-tw]
---

# Taiwan Payment Integration

> Payments are infrastructure for trust. Every step has to be verified, logged, and traceable. When money is involved, err on the side of more checks, not fewer.

## When to Use This Skill

- A web app serving the Taiwan market needs to collect payments
- Integrating with ECPay or NewebPay
- Handling success/failure payment callbacks
- Implementing the refund flow
- Managing order and payment state

---

## Choosing a Provider

| Provider | Fits | Credit-card fee | Notable |
|----------|------|-----------------|---------|
| **ECPay** | SMB, individuals | 2.75% | Easy onboarding, abundant docs, supports COD via convenience stores |
| **NewebPay** | Mid/large, enterprise | 2.6–2.8% | More modern API, e-invoice integration |
| **TapPay** | Mobile-first | Negotiated | Best Apple Pay / Google Pay / LINE Pay integration |
| **LINE Pay** | LINE ecosystem | 3% | Direct integration or via ECPay / NewebPay |

**Recommendation:** start with ECPay (lowest barrier, most documentation); consider NewebPay or TapPay as you scale.

---

## Generic Payment Flow

```
1. User picks payment in the frontend → frontend calls your API
2. Your API creates the order (state: pending)
3. Your API builds payment params + signature → returns to frontend
4. Frontend redirects / POSTs to the provider's payment page
5. User completes the payment
6. Provider sends a background callback to your API (callback URL)
7. Your API verifies the signature → updates order state (paid / failed)
8. Provider redirects the user back to your frontend
```

**Key:** the source of truth is **Step 6 (callback)**, not Step 8 (redirect). The user may close the browser before the redirect.

---

## ECPay Integration

### Environments

| | Stage | Production |
|-|-------|------------|
| API URL | `https://payment-stage.ecpay.com.tw` | `https://payment.ecpay.com.tw` |
| MerchantID | `3002607` (stage) | yours |
| HashKey | `pwFHCqoQZGmho4w6` (stage) | yours |
| HashIV | `EkRm7iFT261dpevs` (stage) | yours |

### Order parameters

```go
type ECPayOrder struct {
    MerchantID        string
    MerchantTradeNo   string    // your order ID (unique, max 20 chars)
    MerchantTradeDate string    // yyyy/MM/dd HH:mm:ss
    PaymentType       string    // "aio"
    TotalAmount       int       // integer, no decimals
    TradeDesc         string
    ItemName          string
    ReturnURL         string    // background callback URL
    ClientBackURL     string    // post-payment redirect URL
    ChoosePayment     string    // "ALL" or "Credit", "ATM", "CVS"
    EncryptType       int       // 1 (SHA256)
    CheckMacValue     string    // signature
}
```

### Computing the signature (CheckMacValue)

```
1. Sort all params by key (A-Z)
2. Build "key=value&" string
3. Prepend "HashKey=xxx&", append "&HashIV=xxx"
4. URL-encode (lowercase)
5. SHA256 → uppercase
```

```go
func CalculateCheckMac(params map[string]string, hashKey, hashIV string) string {
    keys := make([]string, 0, len(params))
    for k := range params { keys = append(keys, k) }
    sort.Strings(keys)

    var buf strings.Builder
    buf.WriteString("HashKey=" + hashKey + "&")
    for _, k := range keys {
        buf.WriteString(k + "=" + params[k] + "&")
    }
    buf.WriteString("HashIV=" + hashIV)

    encoded := url.QueryEscape(buf.String())
    encoded = strings.ToLower(encoded)

    hash := sha256.Sum256([]byte(encoded))
    return strings.ToUpper(hex.EncodeToString(hash[:]))
}
```

### Handling the callback (ReturnURL)

```go
func handleECPayCallback(w http.ResponseWriter, r *http.Request) {
    r.ParseForm()

    // 1. Verify CheckMacValue
    receivedMac := r.FormValue("CheckMacValue")
    params := extractParams(r.Form) // exclude CheckMacValue itself
    expectedMac := CalculateCheckMac(params, hashKey, hashIV)
    if receivedMac != expectedMac {
        log.Error("invalid CheckMacValue")
        w.Write([]byte("0|ErrorMessage"))
        return
    }

    // 2. Check RtnCode
    rtnCode := r.FormValue("RtnCode")
    tradeNo := r.FormValue("MerchantTradeNo")

    if rtnCode == "1" {
        // Payment success → update order state
        orderService.MarkPaid(ctx, tradeNo, r.FormValue("TradeNo"))
    } else {
        orderService.MarkFailed(ctx, tradeNo, rtnCode)
    }

    // 3. Reply "1|OK" to acknowledge
    w.Write([]byte("1|OK"))
}
```

1. **Always verify `CheckMacValue`.** Without it, anyone can forge the callback.
2. **Reply `1|OK`.** ECPay only stops retrying once it sees this. No reply triggers up to 3 retries.
3. **Trust the callback, not the redirect.** Users may close the browser before the redirect runs.

---

## NewebPay Integration

### Differences vs ECPay

- Uses AES-256 encryption (not just signing): params are AES-encrypted, then SHA256-signed
- Payment payload is split into `TradeInfo` (AES) and `TradeSha` (SHA256)

The shape of the flow is the same as ECPay: assemble params → encrypt → submit → receive callback → decrypt and verify.

---

## Order State Management

```go
type OrderStatus string
const (
    OrderPending   OrderStatus = "pending"    // created, unpaid
    OrderPaid      OrderStatus = "paid"
    OrderFailed    OrderStatus = "failed"
    OrderRefunded  OrderStatus = "refunded"
    OrderCancelled OrderStatus = "cancelled"
)
```

### State machine

```
pending → paid       (callback: RtnCode=1)
pending → failed     (callback: RtnCode != 1, or timeout)
pending → cancelled  (user actively cancels)
paid → refunded      (merchant initiates refund)
```

4. **`MerchantTradeNo` must be unique.** Use UUID or timestamp + random.
5. **Record the provider's `TradeNo` too.** You'll need it for reconciliation and refunds.
6. **Log every state change.** Anything money-related must be traceable.

---

## Refunds

### ECPay refund API

```
POST /CreditDetail/DoAction
Action:           R (refund)
MerchantTradeNo:  original order ID
TradeNo:          ECPay transaction ID
TotalAmount:      refund amount
```

7. **Verify order state before refunding.** Only `paid` orders can be refunded.
8. **Track refunded amount for partial refunds.** Prevent over-refunding.
9. **Refund is async.** The API response means "accepted"; the actual movement happens on the provider's side.

---

## Security Notes

10. **Never put HashKey / HashIV in the frontend or in git.** Use env vars or a secret manager.
11. **The callback URL must be HTTPS.** Providers usually mandate this.
12. **Verify the signature on every callback.** Forgery prevention.
13. **Log every payment-related operation.** Order creation, callback receipt, state change, refund.
14. **Use integer amounts.** No floats. TWD is denominated in whole units; treat it as `int`.
15. **Stage and production must use different keys.** Audit all settings during the cutover.

---

## Common Traps

| Trap | Counter |
|------|---------|
| **Treating redirect as success** | Trust callback, not redirect |
| **Skipping `CheckMacValue` verification** | Always verify the signature |
| **Forgetting `1\|OK` reply** | Provider retries up to 3 times |
| **Duplicate `MerchantTradeNo`** | UUID or timestamp + random |
| **Floats for amount** | Use `int` (TWD) |
| **Skipping end-to-end stage testing** | ECPay's stage merchant lets you exercise the full flow |
| **No refund de-duplication** | Check order state + already-refunded amount |

---

## Pre-Flight Checklist

Before going live:

- [ ] End-to-end stage flow exercised (create → pay → callback → state update)
- [ ] `CheckMacValue` verification correct
- [ ] Callback URL is HTTPS
- [ ] Order ID unique and within length limits
- [ ] Amounts as integers
- [ ] `HashKey` / `HashIV` never in code or frontend
- [ ] Every state change logged
- [ ] Refund flow tested
- [ ] Production cutover checklist (URL, MerchantID, Key/IV)

---

## Related Skills

- [`api-design-rest`](../api-design-rest/SKILL.md) — API design (payment endpoints)
- [`auth-patterns`](../auth-patterns/SKILL.md) — user authentication (who's paying)
- [`mongodb-go`](../mongodb-go/SKILL.md) — order persistence
