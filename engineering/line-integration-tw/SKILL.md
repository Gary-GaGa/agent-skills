---
name: line-integration-tw
description: >
  LINE 平台整合指南（台灣市場）— LINE Login、LINE Notify、LIFF、Messaging API、
  Rich Menu，以及常見的揪團/預約場景應用。適合需要在台灣市場用 LINE 做社交登入、
  推播通知、或嵌入式應用的 Web 服務。
category: engineering
tags: [line, taiwan, login, notification, liff, messaging, integration]
related: [auth-patterns, nextjs-fundamentals, realtime-websocket, tw-payment-integration]
---

# LINE 整合（台灣市場）

> LINE 在台灣的滲透率 > 90%。如果你的目標使用者在台灣，LINE Login + LINE Notify 幾乎是必備。

## 適用情境

- 實作 LINE Login（社交登入）
- 用 LINE Notify 發送通知（免費、簡單）
- 用 Messaging API 透過官方帳號發訊息
- 用 LIFF 在 LINE 內嵌入網頁應用
- 用 Rich Menu 做互動選單

---

## LINE Developer 平台設定

### 建立 Channel

1. 到 [LINE Developers Console](https://developers.line.biz/)
2. 建立 Provider
3. 建立 Channel：
   - **LINE Login** — 社交登入用
   - **Messaging API** — 發訊息、Rich Menu 用
   - **LINE Notify** — 簡易推播通知用（獨立服務）

### 重要資訊

| 項目 | 在哪裡 |
|------|--------|
| Channel ID | Channel 基本設定 |
| Channel Secret | Channel 基本設定 |
| Channel Access Token | Messaging API → Issue |
| Callback URL | LINE Login → 設定 |
| Webhook URL | Messaging API → 設定 |
| LIFF ID | LINE Login → LIFF → 新增 |

---

## LINE Login

### 流程（OAuth 2.0 Authorization Code）

```
1. 前端 redirect 到 LINE 授權頁
2. 使用者同意授權
3. LINE redirect 回你的 callback URL（帶 code）
4. 後端用 code 換 access_token + id_token
5. 後端用 access_token 取得使用者資料
6. 後端建立/更新使用者 → 發 JWT
```

### Go 後端實作

```go
// Step 4: exchange code for token
func exchangeLineToken(code, redirectURI string) (*LineTokenResponse, error) {
    data := url.Values{
        "grant_type":    {"authorization_code"},
        "code":          {code},
        "redirect_uri":  {redirectURI},
        "client_id":     {lineChannelID},
        "client_secret": {lineChannelSecret},
    }
    resp, err := http.PostForm("https://api.line.me/oauth2/v2.1/token", data)
    // parse response → LineTokenResponse{AccessToken, IDToken, ...}
}

// Step 5: get user profile
func getLineProfile(accessToken string) (*LineProfile, error) {
    req, _ := http.NewRequest("GET", "https://api.line.me/v2/profile", nil)
    req.Header.Set("Authorization", "Bearer "+accessToken)
    // parse response → LineProfile{UserID, DisplayName, PictureURL}
}
```

### 前端 redirect

```tsx
const LINE_AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize";
const params = new URLSearchParams({
  response_type: "code",
  client_id: process.env.NEXT_PUBLIC_LINE_CHANNEL_ID!,
  redirect_uri: `${window.location.origin}/auth/line/callback`,
  state: generateRandomState(),   // CSRF protection
  scope: "profile openid email",
});
window.location.href = `${LINE_AUTH_URL}?${params}`;
```

### 重要規則

1. **一定要驗證 `state` 參數。** 防止 CSRF 攻擊。
2. **LINE User ID 是 per-provider 唯一。** 同一個使用者在不同 Channel 有不同 UserID。
3. **email 需要另外申請權限。** 在 LINE Login Channel 設定中申請 `email` scope。
4. **`id_token` 包含使用者資訊（JWT）。** 可以直接解碼取得 name、picture、email，不需要再打 profile API。

---

## LINE Notify（免費推播）

最簡單的通知方式：免費、不需要官方帳號、每小時最多 1000 則。

### 使用者授權流程

```
1. 使用者到你的網站，點「連結 LINE Notify」
2. Redirect 到 LINE Notify 授權頁
3. 使用者選擇接收通知的聊天室（自己 or 群組）
4. LINE 回傳 code → 你的後端換 access_token
5. 存 token，之後直接用它發通知
```

### 發送通知

```go
func sendLineNotify(token, message string) error {
    data := url.Values{"message": {message}}
    req, _ := http.NewRequest("POST",
        "https://notify-api.line.me/api/notify",
        strings.NewReader(data.Encode()))
    req.Header.Set("Authorization", "Bearer "+token)
    req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
    resp, err := http.DefaultClient.Do(req)
    // check resp.StatusCode == 200
    return err
}
```

### 適用場景

| 場景 | 通知內容 |
|------|----------|
| 有人加入揪團 | 「Alice 加入了你的籃球團！(5/10)」 |
| 揪團人數已滿 | 「你的羽球團已滿 6 人，準備開打！」 |
| 揪團被取消 | 「明天的排球團已取消，原因：場地維修」 |
| 活動提醒 | 「提醒：明天 19:00 籃球，地點：XX 體育館」 |

5. **LINE Notify 是 per-user token。** 每個使用者授權後有自己的 token。
6. **群組通知：** 使用者授權時可以選擇群組，通知會發到群組裡。適合揪團場景。
7. **免費但有限制：** 每個 token 每小時 1000 則。對小型應用足夠。

---

## Messaging API（官方帳號）

比 LINE Notify 更強大：可以發 Flex Message（豐富排版）、Quick Reply、Rich Menu。

### 發送訊息

```go
func sendPushMessage(userID, text string) error {
    body := map[string]any{
        "to": userID,
        "messages": []map[string]any{
            {"type": "text", "text": text},
        },
    }
    jsonBody, _ := json.Marshal(body)
    req, _ := http.NewRequest("POST",
        "https://api.line.me/v2/bot/message/push",
        bytes.NewReader(jsonBody))
    req.Header.Set("Authorization", "Bearer "+channelAccessToken)
    req.Header.Set("Content-Type", "application/json")
    resp, err := http.DefaultClient.Do(req)
    return err
}
```

### Flex Message（豐富排版）

```go
// 揪團卡片
flexMessage := map[string]any{
    "type": "flex",
    "altText": "新揪團：籃球 @ XX 體育館",
    "contents": map[string]any{
        "type": "bubble",
        "header": map[string]any{...},
        "body": map[string]any{
            "type": "box", "layout": "vertical",
            "contents": []map[string]any{
                {"type": "text", "text": "🏀 籃球", "weight": "bold", "size": "xl"},
                {"type": "text", "text": "📍 XX 體育館"},
                {"type": "text", "text": "📅 2025/01/20 19:00-21:00"},
                {"type": "text", "text": "👥 3/10 人"},
            },
        },
        "footer": map[string]any{
            "type": "box", "layout": "vertical",
            "contents": []map[string]any{
                {"type": "button", "action": map[string]any{
                    "type": "uri", "label": "立即加入",
                    "uri": "https://your-app.com/groups/abc123",
                }},
            },
        },
    },
}
```

8. **Push Message 有免費額度。** 免費方案每月 200 則；付費方案按量計價。
9. **Flex Message Simulator** 可以線上設計排版：[https://developers.line.biz/flex-simulator/](https://developers.line.biz/flex-simulator/)

---

## LIFF（LINE Frontend Framework）

在 LINE 內嵌入你的網頁應用。使用者在 LINE 對話中點連結 → 打開你的 Web App（但在 LINE 內）。

### 適用場景

- 揪團報名頁面（在 LINE 群組分享連結 → 直接在 LINE 內開啟報名）
- 個人資料設定
- 付款頁面

### 前端使用

```tsx
import liff from "@line/liff";

async function initLIFF() {
  await liff.init({ liffId: "your-liff-id" });
  if (!liff.isLoggedIn()) {
    liff.login();
    return;
  }
  const profile = await liff.getProfile();
  // profile.userId, profile.displayName, profile.pictureUrl
}
```

10. **LIFF 自動取得 LINE 使用者資訊。** 不需要再做 LINE Login 流程。
11. **LIFF 可以分享訊息到聊天室。** `liff.shareTargetPicker(messages)` — 讓使用者把揪團連結分享出去。
12. **LIFF 有三種 size：** Compact（底部彈出）、Tall（2/3 螢幕）、Full（全螢幕）。

---

## Rich Menu（底部選單）

官方帳號底部的圖片選單，使用者點擊觸發動作。

```json
{
  "size": {"width": 2500, "height": 843},
  "areas": [
    {
      "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
      "action": {"type": "uri", "uri": "https://your-app.com/groups"}
    },
    {
      "bounds": {"x": 833, "y": 0, "width": 834, "height": 843},
      "action": {"type": "uri", "uri": "https://your-app.com/groups/create"}
    },
    {
      "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
      "action": {"type": "uri", "uri": "https://your-app.com/profile"}
    }
  ]
}
```

適合做成：「找團」「開團」「我的」三個按鈕。

---

## 揪團服務的 LINE 整合建議

| 功能 | 用什麼 | 優先度 |
|------|--------|--------|
| 登入 | LINE Login | 🔴 必做 |
| 開團/滿團通知 | LINE Notify | 🔴 必做 |
| 揪團分享到 LINE | LIFF `shareTargetPicker` | 🟡 建議 |
| 豐富揪團卡片 | Messaging API Flex Message | 🟡 建議 |
| 底部選單 | Rich Menu | 🔵 加分 |
| 在 LINE 內報名 | LIFF | 🔵 加分 |

13. **先做 LINE Login + LINE Notify。** 這兩個覆蓋 80% 需求，實作成本低。
14. **LIFF 和 Flex Message 後做。** 提升體驗但不影響核心功能。

---

## 常見陷阱

| 陷阱 | 對策 |
|------|------|
| **LINE User ID 跨 Channel 不同** | 用你自己的 user ID 作為主鍵；LINE ID 是外部身份 |
| **忘記驗證 state** | CSRF 攻擊。一定要驗 |
| **LINE Notify token 外洩** | token 等同於發送權限。存在 DB，不放前端 |
| **LIFF init 失敗沒處理** | 檢查是否在 LINE 內開啟；外部瀏覽器 fallback |
| **Messaging API 免費額度用完** | 監控用量；重要通知用 LINE Notify（免費）|
| **Webhook 沒回 200** | LINE 會重送。回 200 再處理（async）|
| **Channel Access Token 沒更新** | Long-lived token 或設定自動 rotate |

---

## 檢查清單

- [ ] LINE Login Channel 設定完成（Callback URL、scope）
- [ ] LINE Login 授權流程 → 後端換 token → 建立使用者
- [ ] state 參數驗證（CSRF）
- [ ] LINE Notify 授權流程完成
- [ ] 通知場景定義（哪些事件觸發通知）
- [ ] LINE User ID 對應到你的系統 user ID
- [ ] Channel Secret / Access Token 不在前端或 git
- [ ] 測試環境用獨立的 LINE Channel
- [ ] LIFF（如使用）在 LINE 內和瀏覽器都測試

---

## 相關技能

- [`auth-patterns`](../auth-patterns/SKILL.md) — LINE Login 是 OAuth 的一種
- [`nextjs-fundamentals`](../nextjs-fundamentals/SKILL.md) — 前端整合 LIFF 和 LINE Login
- [`realtime-websocket`](../realtime-websocket/SKILL.md) — 即時通知搭配 LINE Notify
- [`tw-payment-integration`](../tw-payment-integration/SKILL.md) — 付款流程
