---
name: tw-payment-integration
description: >
  台灣金流整合指南，涵蓋綠界 ECPay 與藍新 NewebPay 的串接流程、付款方式
  （信用卡/ATM/超商）、背景通知（callback）處理、退款、訂單狀態管理，以及
  安全注意事項。適合需要在台灣市場收款的 Web 應用。
category: engineering
tags: [payment, taiwan, ecpay, newebpay, integration, fintech]
related: [api-design-rest, auth-patterns, mongodb-go, line-integration-tw]
---

# 台灣金流整合

> 金流是信任的基礎設施。付款流程的每一步都要驗證、記錄、可追溯。對金錢的操作，寧可多檢查也不要少。

## 適用情境

- 在台灣市場的 Web 應用需要收款
- 串接綠界 ECPay 或藍新 NewebPay
- 處理付款成功/失敗的回調（callback）
- 實作退款流程
- 管理訂單與付款狀態

---

## 金流商選擇

| 金流商 | 適合 | 手續費（信用卡） | 特色 |
|--------|------|------------------|------|
| **綠界 ECPay** | 中小型、個人 | 2.75% | 申請簡單、文件多、超商取貨付款 |
| **藍新 NewebPay** | 中大型、企業 | 2.6-2.8% | API 較現代、電子發票整合 |
| **TapPay** | 行動支付優先 | 議價 | Apple Pay/Google Pay/LINE Pay 整合好 |
| **LINE Pay** | LINE 生態系 | 3% | 直接串接或透過綠界/藍新 |

**建議：** 起步用綠界（申請門檻低、文件多）；規模成長後考慮藍新或 TapPay。

---

## 付款流程（通用）

```
1. 使用者在前端選擇付款 → 前端呼叫你的 API
2. 你的 API 建立訂單（狀態: pending）
3. 你的 API 組裝付款參數 + 簽章 → 回傳給前端
4. 前端 redirect / POST 到金流商付款頁
5. 使用者完成付款
6. 金流商背景通知你的 API（callback URL）
7. 你的 API 驗證簽章 → 更新訂單狀態（paid / failed）
8. 金流商 redirect 使用者回你的前端
```

**重點：** 以 **Step 6 的 callback** 為準，不是 Step 8 的 redirect。使用者可能在 redirect 前關掉視窗。

---

## 綠界 ECPay 串接

### 環境

| | 測試 | 正式 |
|-|------|------|
| API URL | `https://payment-stage.ecpay.com.tw` | `https://payment.ecpay.com.tw` |
| MerchantID | `3002607` (測試用) | 你申請的 |
| HashKey | `pwFHCqoQZGmho4w6` (測試用) | 你的 |
| HashIV | `EkRm7iFT261dpevs` (測試用) | 你的 |

### 建立訂單 + 產生付款表單

```go
type ECPayOrder struct {
    MerchantID        string
    MerchantTradeNo   string    // 你的訂單編號（唯一, max 20 chars）
    MerchantTradeDate string    // yyyy/MM/dd HH:mm:ss
    PaymentType       string    // "aio"
    TotalAmount       int       // 整數，不含小數
    TradeDesc         string
    ItemName          string
    ReturnURL         string    // 背景通知 URL（callback）
    ClientBackURL     string    // 付完款回前端的 URL
    ChoosePayment     string    // "ALL" 或 "Credit", "ATM", "CVS"
    EncryptType       int       // 1 (SHA256)
    CheckMacValue     string    // 簽章
}
```

### 簽章計算（CheckMacValue）

```
1. 將所有參數按 key 排序（A-Z）
2. 組成 key=value& 字串
3. 前面加 HashKey=xxx&，後面加 &HashIV=xxx
4. URL encode（小寫）
5. SHA256 → 轉大寫
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

### 處理 callback（ReturnURL）

```go
func handleECPayCallback(w http.ResponseWriter, r *http.Request) {
    r.ParseForm()

    // 1. 驗證 CheckMacValue
    receivedMac := r.FormValue("CheckMacValue")
    params := extractParams(r.Form) // 排除 CheckMacValue 本身
    expectedMac := CalculateCheckMac(params, hashKey, hashIV)
    if receivedMac != expectedMac {
        log.Error("invalid CheckMacValue")
        w.Write([]byte("0|ErrorMessage"))
        return
    }

    // 2. 檢查 RtnCode
    rtnCode := r.FormValue("RtnCode")
    tradeNo := r.FormValue("MerchantTradeNo")

    if rtnCode == "1" {
        // 付款成功 → 更新訂單狀態
        orderService.MarkPaid(ctx, tradeNo, r.FormValue("TradeNo"))
    } else {
        orderService.MarkFailed(ctx, tradeNo, rtnCode)
    }

    // 3. 回應 "1|OK" 表示收到
    w.Write([]byte("1|OK"))
}
```

1. **一定要驗證 CheckMacValue。** 否則任何人都能偽造 callback。
2. **回應 `1|OK`。** 綠界收到後才不會重複通知。沒回應會重送最多 3 次。
3. **以 callback 為準，不是 redirect。** 使用者可能在 redirect 前關瀏覽器。

---

## 藍新 NewebPay 串接

### 差異

- 使用 AES-256 加密（不是純簽章），參數先 AES 加密再 SHA256 簽章
- 付款參數包在 `TradeInfo`（AES 加密）和 `TradeSha`（SHA256）

流程類似綠界：組裝參數 → 加密 → 送出 → callback 回來 → 解密驗證。

---

## 訂單狀態管理

```go
type OrderStatus string
const (
    OrderPending   OrderStatus = "pending"    // 建立，未付款
    OrderPaid      OrderStatus = "paid"       // 付款成功
    OrderFailed    OrderStatus = "failed"     // 付款失敗
    OrderRefunded  OrderStatus = "refunded"   // 已退款
    OrderCancelled OrderStatus = "cancelled"  // 使用者取消
)
```

### 狀態機

```
pending → paid      (callback: RtnCode=1)
pending → failed    (callback: RtnCode≠1, 或逾時)
pending → cancelled (使用者主動取消)
paid → refunded     (商家發起退款)
```

4. **訂單編號（MerchantTradeNo）必須唯一。** 用 UUID 或 timestamp + random。
5. **記錄金流商的交易編號（TradeNo）。** 對帳和退款時需要。
6. **每次狀態變更都記錄 log。** 金錢相關操作必須可追溯。

---

## 退款

### 綠界退款 API

```
POST /CreditDetail/DoAction
Action: R (退款)
MerchantTradeNo: 原訂單編號
TradeNo: 綠界交易編號
TotalAmount: 退款金額
```

7. **退款前驗證訂單狀態。** 只有 `paid` 的訂單可以退款。
8. **部分退款要記錄已退金額。** 避免超退。
9. **退款是非同步的。** API 回應只是「已受理」，實際退款需等金流商處理。

---

## 安全注意事項

10. **HashKey / HashIV 絕不放在前端或 git。** 環境變數或 secret manager。
11. **Callback URL 必須是 HTTPS。** 金流商通常強制要求。
12. **驗證所有 callback 的簽章。** 防止偽造。
13. **記錄所有付款相關操作。** 包含：建立訂單、callback 收到、狀態變更、退款。
14. **金額用整數（分/元）。** 不要用浮點數。台灣金流通常以「元」為單位，無小數。
15. **測試環境和正式環境用不同的 key。** 切換時要確認所有設定都更新。

---

## 常見陷阱

| 陷阱 | 對策 |
|------|------|
| **依賴 redirect 判斷付款成功** | 以 callback 為準 |
| **沒驗證 CheckMacValue** | 一定驗簽章 |
| **callback 沒回 `1\|OK`** | 金流商會重複通知 3 次 |
| **訂單編號重複** | 用 UUID 或加 timestamp |
| **金額用 float** | 用 int（元） |
| **沒有在測試環境完整跑過** | 綠界提供測試商店，全流程測試 |
| **退款沒防重複** | 檢查訂單狀態 + 已退金額 |

---

## 檢查清單

串接完成前確認：

- [ ] 測試環境全流程跑過（建立 → 付款 → callback → 狀態更新）
- [ ] CheckMacValue 驗證邏輯正確
- [ ] Callback URL 是 HTTPS
- [ ] 訂單編號唯一且不超過長度限制
- [ ] 金額用整數
- [ ] HashKey/HashIV 不在程式碼或前端
- [ ] 每次狀態變更有 log
- [ ] 退款流程測試通過
- [ ] 正式環境切換 checklist（URL、MerchantID、Key/IV）

---

## 相關技能

- [`api-design-rest`](../api-design-rest/SKILL.md) — API 設計（付款 API 端點）
- [`auth-patterns`](../auth-patterns/SKILL.md) — 使用者認證（誰在付款）
- [`mongodb-go`](../mongodb-go/SKILL.md) — 訂單資料儲存
