# DOPE2000 WATCH — iPhone Web App starter

This is an installable iPhone web app project for:
- attempting to detect when the public TikTok LIVE for `dope2000` starts;
- sending an iPhone Web Push notification;
- opening the public LIVE page from the notification.

## Important limits (read before deploying)
1. TikTok does not provide a general public API that guarantees third-party LIVE-start and account-privacy status monitoring. This project uses the unofficial `TikTokLive` Python package for LIVE detection. TikTok changes may break it, delay it, or restrict access.
2. It **cannot reliably determine whether an account has become private**. If TikTok blocks or hides profile data, the app must show “状態を確認できません” rather than claim the account is private.
3. It cannot view a private account's LIVE without the account owner's approval. It does not bypass privacy controls.
4. A notification does not mean the recipient can watch the LIVE. Viewing may require login, follow approval, or other TikTok permissions. Anonymous viewing is not guaranteed.
5. This is a source project, not a deployed/working hosted service. Push notifications will not arrive until you deploy the backend on a continuously running HTTPS host and configure VAPID keys.

## iPhone requirements
- iOS/iPadOS 16.4 or later
- Open the deployed HTTPS site in Safari
- Share → Add to Home Screen
- Launch it from the Home Screen icon
- Tap “通知を有効にする” and allow notifications

Web Push on iPhone is supported for web apps added to the Home Screen; a normal Safari tab is not enough.

## Deploy
Use a host that runs a persistent Python process (not a serverless function that sleeps between requests) and supports HTTPS and persistent storage.

1. Install Python 3.11+.
2. Install dependencies: `pip install -r requirements.txt`
3. Generate VAPID keys using the pywebpush documentation/tooling. Set:
   - `VAPID_PUBLIC_KEY`
   - `VAPID_PRIVATE_KEY`
   - `VAPID_CLAIMS_SUB` (for example `mailto:admin@example.com`)
4. Set `TIKTOK_USERNAME=dope2000`.
5. Start: `uvicorn server:app --host 0.0.0.0 --port 8000`
6. Put the app behind HTTPS.
7. Open the HTTPS URL on the iPhone and follow the iPhone requirements above.

Keep the private VAPID key secret. Do not commit `.env` or subscription data. For real use, add authentication/admin controls and encrypted persistent storage before sharing the service with others.

## Status meanings
- `LIVE検知`: the unofficial client currently appears connected to the LIVE room.
- `待機中`: no current LIVE connection is detected.
- `状態を確認できません`: the monitor has an error or TikTok is not allowing a reliable check.
- Privacy state is deliberately not inferred from connection errors.
