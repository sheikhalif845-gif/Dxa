const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

dotenv.config();

// --- Configuration ---
const BOT_TOKEN = process.env.BOT_TOKEN || "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg";
const ADMIN_ID = parseInt(process.env.ADMIN_ID || "8197284774");

const bot = new TelegramBot(BOT_TOKEN, { polling: true });

const PREMIUM_EMOJIS = {
    "FIRE": "5337267511261960341", "HELLO": "5353027129250453493", "DXA": "5334763399299506604",
    "DONE": "5352694861990501856", "NUMBER": "5337132498965010628", "SUPPORT": "5337302974806922068",
    "ADMIN": "5353032893096567467", "USER": "5352861489541714456", "FILE": "5352721946054268944",
    "NUMBERS": "5352862640592949843", "ROCKET": "5352597830089347330", "GRAPH": "5352877703043258544",
    "UPLOAD": "5353001161878182134", "BROADCAST": "5352980533150259581", "PIN": "5420517437885943844",
    "DOT": "5352638632278660622", "N1": "5352651766288652742", "N2": "5355186458418257716",
    "N3": "5352867219028091093", "WAIT": "5336983442125001376", "CLOSE": "5420130255174145507",
    "OTP_ID": "5353022963132174959", "OFF": "5352974971167611327", "NOTE": "5395444784611480792",
    "DATE": "5352585194295564660", "WARN": "5336944168944047463", "SETTINGS": "5420155432272438703",
    "CHAT": "5337302974806922068", "MEMBER": "5420145051336485498", "ADD": "5420323438508155202",
    "DELETE": "5422557736330106570"
};

const APP_EMOJIS = {
    'FACEBOOK': ['🚫', '5334807341109908955'], 'WHATSAPP': ['🚫', '5334759662677957452'],
    'TELEGRAM': ['🚫', '5337010556253543833'], 'WHATSAPPBUSINESSES': ['🚫', '5336814486701514414'],
    'IMO': ['🚫', '5337155807752524558'], 'INSTAGRAM': ['🚫', '5334868205091459431'],
    'APPLE': ['🚫', '5334637951894722661'], 'FROZENICE': ['🚫', '5334530732331143967'],
    'NORDVPN': ['🚫', '5334944492300573096'], 'SNAPCHAT': ['🚫', '5334584041465222978'],
    'YOUTUBE': ['🚫', '5334769042886533147'], 'GOOGLE': ['🚫', '5335010201005231986'],
    'MICROSOFT': ['🖥', '5334880948259427772'], 'TEAMS': ['🌐', '5334590977837403844'],
    'MELBET': ['🌟', '5337102391244263212'], 'TIKTOK': ['🚫', '5339213256001102461'],
    'BKASH': ['💸', '5348469219761626211'], 'ROCKET_APP': ['💸', '5346042941196507141'],
    'BYBIT': ['💸', '5348372939479751825'], 'BINANCE': ['💸', '5348212415077064131'],
    'PROTONVPN': ['🥚', '5348390922507817684'], 'EXPRESSVPN': ['👨‍⚖️', '5346335574498251610'],
    'GMAIL': ['🐁', '5348494358205207761'], 'MESSENGER': ['🧻', '5348486915026884464'],
    'CHROME': ['⚗️', '5346311574221000149'], 'GOOGLEONE': ['🛴', '5348075478634766440'],
    'NAGAD': ['💴', '5352985330628730418'],
};

function e(emoji, emojiId) {
    return `<tg-emoji emoji-id="${emojiId}">${emoji}</tg-emoji>`;
}

// --- Database Helpers ---
const DATA_DIR = path.join(__dirname, 'data');
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR);

function readJson(filename) {
    const filePath = path.join(DATA_DIR, filename);
    if (!fs.existsSync(filePath)) return [];
    try { return JSON.parse(fs.readFileSync(filePath, 'utf-8')); } catch { return []; }
}

function writeJson(filename, data) {
    const filePath = path.join(DATA_DIR, filename);
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
}

// --- Settings Management ---
function getSettings() {
    const settings = readJson("settings.json");
    if (!settings || Array.isArray(settings)) {
        const defaultSettings = {
            force_join: true,
            channels: [{ name: "DXA Universe", url: "https://t.me/dxa_universe", username: "@dxa_universe" }],
            admins: [],
            otp_groups: [],
            otp_link: "https://t.me/dxaotpzone",
            brand_name: "DXA UNIVERSE",
            mask_text: "DXA",
            group_buttons: {},
            otp_message_buttons: []
        };
        writeJson("settings.json", defaultSettings);
        return defaultSettings;
    }
    return settings;
}

const isAdmin = (userId) => userId === ADMIN_ID || getSettings().admins.map(String).includes(userId.toString());

async function checkForceJoin(userId) {
    const s = getSettings();
    if (!s.force_join || isAdmin(userId)) return true;
    for (const c of (s.channels || [])) {
        try {
            const m = await bot.getChatMember(c.username, userId);
            if (['left', 'kicked', 'restricted'].includes(m.status)) return false;
        } catch { return false; }
    }
    return true;
}

function getMainButtons(userId) {
    const buttons = [[{ text: "📱 Get Number" }, { text: "🛠 Support" }]];
    if (isAdmin(userId)) buttons.push([{ text: "👑 Admin Panel" }]);
    return { keyboard: buttons, resize_keyboard: true };
}

const lastMenus = new Map();
const waitingForInput = new Map();
const cooldowns = new Map();

// --- UI Rendering Functions ---

async function showAdminPanel(chatId, messageId, userId) {
    const users = readJson("users.json");
    const numbers = readJson("numbers.json");
    const files = readJson("files.json");
    const available = numbers.filter(n => !n.used).length;
    const total = numbers.length || 1;
    const bar = "█".repeat(Math.min(10, Math.floor((available / total) * 10))).padEnd(10, "░");

    const text = `${e("👑", PREMIUM_EMOJIS.ADMIN)} <b>ADMIN CONTROL PANEL</b>\n━━━━━━━━━━━━━\n\n` +
                 `${e("📊", PREMIUM_EMOJIS.GRAPH)} <b>DATABASE OVERVIEW</b>\n` +
                 `  ${e("👤", PREMIUM_EMOJIS.USER)} Users: ${users.length}\n` +
                 `  ${e("🔢", PREMIUM_EMOJIS.NUMBERS)} Numbers: ${numbers.length}\n` +
                 `  ${e("🚀", PREMIUM_EMOJIS.ROCKET)} Available: ${available}\n\n` +
                 `Stock: [${bar}] ${available} free\n━━━━━━━━━━━━━`;

    const inline_keyboard = [
        [{ text: "📤 Upload Numbers", callback_data: "admin_upload" }, { text: "🗑 Delete Files", callback_data: "admin_delete_files" }],
        [{ text: "📢 Broadcast", callback_data: "admin_broadcast" }, { text: "⚙️ Settings", callback_data: "admin_settings" }],
        [{ text: "✅ Used Numbers", callback_data: "view_used" }, { text: "🚀 Unused Numbers", callback_data: "view_unused" }],
        [{ text: "🔙 Back", callback_data: "close_menu" }]
    ];

    if (messageId) {
        await bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard } });
    } else {
        const sent = await bot.sendMessage(chatId, text, { parse_mode: 'HTML', reply_markup: { inline_keyboard } });
        if (userId) lastMenus.set(userId, sent.message_id);
    }
}

function showSettingsPanel(chatId, messageId) {
    const text = `${e("⚙️", PREMIUM_EMOJIS.NOTE)} <b>BOT SETTINGS CENTER</b>\n━━━━━━━━━━━━━\nSelect a category to manage:`;
    const inline_keyboard = [
        [{ text: "📢 Force Join System", callback_data: "manage_force_join" }],
        [{ text: "👥 Admin Management", callback_data: "manage_admins" }],
        [{ text: "💬 OTP Group System", callback_data: "manage_otp_groups" }],
        [{ text: "🔍 Branding & Link", callback_data: "manage_branding" }],
        [{ text: "🔙 Back", callback_data: "admin_panel_back" }]
    ];
    bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard } });
}

async function showManageForceJoin(chatId, messageId) {
    const s = getSettings();
    const status = s.force_join ? "Active ✅" : "Disabled ❌";
    let text = `${e("📢", PREMIUM_EMOJIS.BROADCAST)} <b>FORCE JOIN SYSTEM</b>\nStatus: ${status}\n\n<b>Channels:</b>\n`;
    const ik = [];
    (s.channels || []).forEach((c, i) => {
        text += `${i+1}. ${c.name} (${c.username})\n`;
        ik.push([{ text: `🗑 Delete ${c.name}`, callback_data: `del_chan:${i}` }]);
    });
    ik.push([{ text: `Toggle: ${s.force_join ? "OFF" : "ON"}`, callback_data: "toggle_force_join" }]);
    ik.push([{ text: "➕ Add Channel", callback_data: "add_channel" }]);
    ik.push([{ text: "🔙 Back", callback_data: "admin_settings" }]);
    bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard: ik } });
}

async function showManageOtpGroups(chatId, messageId) {
    const s = getSettings();
    let text = `${e("💬", PREMIUM_EMOJIS.CHAT)} <b>OTP GROUP SYSTEM</b>\n\n<b>Groups:</b>\n`;
    const ik = [];
    (s.otp_groups || []).forEach(g => {
        text += `• <code>${g}</code>\n`;
        ik.push([{ text: `⚙️ Opts for ${g}`, callback_data: `setup_grp_btns:${g}` }, { text: `🗑`, callback_data: `del_otp_grp:${g}` }]);
    });
    ik.push([{ text: "➕ Add Group", callback_data: "add_otp_group" }, { text: "➕ Add Global Button", callback_data: "add_otp_msg_btn" }]);
    ik.push([{ text: "🔙 Back", callback_data: "admin_settings" }]);
    bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard: ik } });
}

// --- Main Event Handlers ---

bot.on('message', async (msg) => {
    if (!msg.from) return;
    const uid = msg.from.id;
    const cid = msg.chat.id;
    const txt = msg.text;

    // Register User
    const users = readJson("users.json");
    if (!users.some(u => u.uid == uid)) {
        users.push({ uid: uid.toString(), username: msg.from.username, joinedAt: new Date().toString() });
        writeJson("users.json", users);
    }

    if (txt === "/start") {
        const ok = await checkForceJoin(uid);
        if (!ok) {
            const s = getSettings();
            const ik = s.channels.map(c => [{ text: `Join ${c.name}`, url: c.url }]);
            ik.push([{ text: "Joined ✅", callback_data: "check_join" }]);
            return bot.sendMessage(cid, "🚫 Join our channels first!", { reply_markup: { inline_keyboard: ik } });
        }
        const sent = await bot.sendMessage(cid, `═《 ${e("🔥", PREMIUM_EMOJIS.FIRE)} DXA BOT 》═\nWelcome <b>${msg.from.first_name}</b>!`, { parse_mode: 'HTML', reply_markup: getMainButtons(uid) });
        lastMenus.set(uid, sent.message_id);
    }

    if (txt === "👑 Admin Panel" && isAdmin(uid)) {
        showAdminPanel(cid, null, uid);
    }

    if (txt === "📱 Get Number") {
        const nums = readJson("numbers.json");
        const svcs = [...new Set(nums.filter(n => !n.used).map(n => n.service))].sort();
        const ik = svcs.map(s => [{ text: `🔹 ${s}`, callback_data: `sel_service:${s}` }]);
        bot.sendMessage(cid, "📱 Select Service:", { reply_markup: { inline_keyboard: ik } });
    }

    // Input State Handler
    const state = waitingForInput.get(uid);
    if (state && txt) {
        const s = getSettings();
        if (state === "add_admin") {
            s.admins.push(txt); writeJson("settings.json", s);
            bot.sendMessage(cid, "✅ Admin Added!");
        } else if (state === "add_otp_group") {
            s.otp_groups.push(txt); writeJson("settings.json", s);
            bot.sendMessage(cid, "✅ Group Added!");
        } else if (state === "admin_broadcast") {
            const usrs = readJson("users.json");
            bot.sendMessage(cid, "📢 Broadcasting...");
            for (let u of usrs) { bot.copyMessage(u.uid, cid, msg.message_id).catch(() => {}); }
            bot.sendMessage(cid, "✅ Broadcast Complete!");
        }
        waitingForInput.delete(uid);
    }
});

bot.on('callback_query', async (q) => {
    const cid = q.message.chat.id;
    const mid = q.message.message_id;
    const uid = q.from.id;
    const data = q.data;

    if (data === "admin_settings") showSettingsPanel(cid, mid);
    if (data === "manage_force_join") showManageForceJoin(cid, mid);
    if (data === "manage_otp_groups") showManageOtpGroups(cid, mid);
    if (data === "toggle_force_join") {
        const s = getSettings(); s.force_join = !s.force_join; writeJson("settings.json", s);
        showManageForceJoin(cid, mid);
    }
    if (data === "add_admin") {
        bot.sendMessage(cid, "➕ Send User ID to add as Admin:");
        waitingForInput.set(uid, "add_admin");
    }
    if (data === "admin_broadcast") {
        bot.sendMessage(cid, "📢 Send the message to broadcast:");
        waitingForInput.set(uid, "admin_broadcast");
    }
    if (data === "close_menu") bot.deleteMessage(cid, mid);
    if (data === "admin_panel_back") showAdminPanel(cid, mid, uid);

    if (data.startsWith("sel_service:")) {
        const svc = data.split(":")[1];
        const nums = readJson("numbers.json").filter(n => !n.used && n.service == svc);
        const countries = [...new Set(nums.map(n => n.country))];
        const ik = countries.map(c => [{ text: `📍 ${c}`, callback_data: `sel_country:${svc}:${c}` }]);
        bot.editMessageText(`📍 Select Country for ${svc}:`, { chat_id: cid, message_id: mid, reply_markup: { inline_keyboard: ik } });
    }

    if (data.startsWith("sel_country:")) {
        const [_, svc, cnt] = data.split(":");
        const all = readJson("numbers.json");
        const av = all.filter(n => !n.used && n.service == svc && n.country == cnt);
        if (av.length < 3) return bot.answerCallbackQuery(q.id, { text: "❌ Not enough numbers!", show_alert: true });
        
        const sel = av.sort(() => 0.5 - Math.random()).slice(0, 3);
        sel.forEach(n => { n.used = true; n.assignedTo = uid.toString(); });
        writeJson("numbers.json", all);

        const text = `✅ <b>NUMBERS ALLOCATED</b>\nService: ${svc}\nCountry: ${cnt}\n\n` +
                     sel.map((n, i) => `${i+1}️⃣ <code>${n.number}</code>`).join("\n");
        bot.editMessageText(text, { chat_id: cid, message_id: mid, parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: "💬 OTP Group", url: getSettings().otp_link }]] } });
    }
});

// --- OTP Fetcher ---
const OTP_API_URL = "http://147.135.212.197/crapi/st/viewstats";
const OTP_API_TOKEN = "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ==";
const seen = new Set();

async function monitor() {
    try {
        const res = await axios.get(`${OTP_API_URL}?token=${OTP_API_TOKEN}&records=50`);
        const data = res.data;
        const nums = readJson("numbers.json");
        for (let rec of data) {
            const [srv, fNum, content, ts] = rec;
            const key = `${fNum}_${ts}`;
            if (seen.has(key)) continue;
            seen.add(key);

            const match = nums.find(n => n.used && fNum.includes(n.number.toString().replace(/\D/g, '')));
            if (match) {
                bot.sendMessage(match.assignedTo, `📩 <b>NEW OTP</b>\n\nService: ${srv}\nNumber: ${fNum}\nCode: <code>${content}</code>`, { parse_mode: 'HTML' });
            }
        }
    } catch {}
}
setInterval(monitor, 5000);

console.log("Bot system fully loaded.");
