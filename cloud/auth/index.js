const functions = require("firebase-functions");
const admin = require("firebase-admin");
const crypto = require("crypto");

if (!admin.apps.length) {
  admin.initializeApp();
}

/**
 * Validates Telegram WebApp initData HMAC-SHA256 signature
 */
function verifyInitData(initData, botToken) {
  if (!initData || typeof initData !== "string" || initData.length > 4096 || !botToken) {
    return null;
  }
  const params = new URLSearchParams(initData);
  const hash = params.get("hash");
  if (!hash) return null;

  params.delete("hash");

  // Check timestamp (24 hour max age, max 60s future clock skew)
  const authDate = parseInt(params.get("auth_date") || "0", 10);
  const now = Math.floor(Date.now() / 1000);
  if (!authDate || isNaN(authDate) || authDate <= 0 || now - authDate > 86400 || authDate > now + 60) {
    return null;
  }

  const entries = Array.from(params.entries());
  entries.sort(([a], [b]) => a.localeCompare(b));
  const dataCheckString = entries.map(([k, v]) => `${k}=${v}`).join("\n");

  const secretKey = crypto.createHmac("sha256", "WebAppData").update(botToken).digest();
  const calculatedHash = crypto.createHmac("sha256", secretKey).update(dataCheckString).digest("hex");

  const calcBuf = Buffer.from(calculatedHash, "utf8");
  const recvBuf = Buffer.from(String(hash), "utf8");
  if (calcBuf.length === recvBuf.length && crypto.timingSafeEqual(calcBuf, recvBuf)) {
    try {
      return JSON.parse(params.get("user") || "{}");
    } catch {
      return null;
    }
  }
  return null;
}

exports.authTelegram = functions.https.onRequest(async (req, res) => {
  // CORS support
  res.set("Access-Control-Allow-Origin", "*");
  res.set("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") {
    res.status(204).send("");
    return;
  }

  const { initData } = req.body || {};
  const botToken = process.env.TELEGRAM_BOT_TOKEN;

  if (!initData || !botToken) {
    res.status(400).json({ error: "Missing initData or BOT_TOKEN configuration" });
    return;
  }

  const user = verifyInitData(initData, botToken);
  if (!user || !user.id) {
    res.status(401).json({ error: "Invalid Telegram signature" });
    return;
  }

  try {
    const customToken = await admin.auth().createCustomToken(String(user.id), {
      username: user.username || ""
    });
    res.status(200).json({ token: customToken, user });
  } catch (err) {
    res.status(500).json({ error: "Internal authentication error" });
  }
});
