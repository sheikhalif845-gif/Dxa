const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// ==========================================
// ⚙️ CONFIGURATION (SYNC WITH APP)
// ==========================================
const BOT_TOKEN = "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg";
const ADMIN_ID = 8197284774;
const OTP_API_URL = "http://147.135.212.197/crapi/st/viewstats";
const OTP_API_TOKEN = "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ==";

const bot = new TelegramBot(BOT_TOKEN, { polling: true });

// --- DATA SYSTEM ---
const DATA_DIR = path.join(__dirname, 'data');
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR);

function readDb(file) {
    const p = path.join(DATA_DIR, file);
    if (!fs.existsSync(p)) return [];
    try { return JSON.parse(fs.readFileSync(p, 'utf8')); }
    catch { return []; }
}

function writeDb(file, data) {
    const p = path.join(DATA_DIR, file);
    fs.writeFileSync(p, JSON.stringify(data, null, 2), 'utf8');
}

function getConfig() {
    let s = readDb('settings.json');
    if (!s || Array.isArray(s)) {
        s = {
            force_join: true,
            channels: [{ name: "DXA Universe", url: "https://t.me/dxa_universe", username: "@dxa_universe" }],
            admins: [],
            otp_groups: [],
            brand_name: "DXA UNIVERSE",
            mask_text: "DXA"
        };
        writeDb('settings.json', s);
    }
    return s;
}

const isAdmin = (uid) => uid == ADMIN_ID || getConfig().admins.includes(uid.toString());

// ==========================================
// 🎨 PREMIUM UI ASSETS
// ==========================================
const E = {
    FIRE: "5337267511261960341", HELLO: "5353027129250453493", DONE: "5352694861990501856",
    NUMBER: "5337132498965010628", ADMIN: "5353032893096567467", ROCKET: "5352597830089347330"
};

const icon = (emoji, eid) => `<tg-emoji emoji-id="${eid}">${emoji}</tg-emoji>`;

// --- STATE ---
let processedOtps = new Set();
let lastOtpContent = {};

// ==========================================
// 📊 OTP ENGINE (SYNC WITH APP)
// ==========================================
async function otpProcessor() {
    try {
        const res = await axios.get(`${OTP_API_URL}?token=${OTP_API_TOKEN}&records=50`);
        if (res.status === 200) {
            const data = res.data;
            const s = getConfig();
            const nums = readDb('numbers.json');

            data.forEach(rec => {
                const [srv, num_f, content, tstamp] = rec;
                const norm = num_f.replace(/\D/g, '');
                const mid = `${num_f}_${tstamp}`;

                if (processedOtps.has(mid)) return;

                const code = content.match(/\d{4,8}/)?.[0] || content;
                if (lastOtpContent[norm] === code) {
                    processedOtps.add(mid);
                    return;
                }

                lastOtpContent[norm] = code;
                processedOtps.add(mid);

                const mask = s.mask_text;
                const masked = norm.length > 7 ? `${norm.slice(0, 3)}${mask}${norm.slice(-4)}` : norm;

                const msg = `━━━━━━━━━━━\n` +
                    `《 ${icon('✅', E.DONE)} <b>𝗡𝗘𝗪 𝗠𝗘𝗦𝗦𝗔𝗚𝗘</b> 》\n` +
                    `━━━━━━━━━━━\n` +
                    `<blockquote>${icon('🔹', '5352638632278660622')} <b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲:</b> <b>${srv}</b></blockquote>\n` +
                    `<blockquote>${icon('📱', E.NUMBER)} <b>𝗡𝘂𝗺𝗯𝗲𝗿:</b> <code>${masked}</code></blockquote>\n` +
                    `━━━━━━━━━━━\n` +
                    `<blockquote>${icon('💬', E.FIRE)} <b>𝗖𝗼𝗻𝘁𝗲𝗻𝘁:</b> <code>${content}</code></blockquote>\n` +
                    `━━━━━━━━━━━\n` +
                    `<i>${s.brand_name}</i>`;

                const opts = { parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: `📋 ${code}`, callback_data: 'copy' }]] } };

                s.otp_groups.forEach(gid => bot.sendMessage(gid, msg, opts).catch(() => {}));
                const match = nums.find(n => n.used && n.number.replace(/\D/g, '') === norm);
                if (match) bot.sendMessage(match.assignedTo, msg, opts).catch(() => {});
            });
        }
    } catch (e) { console.error('OTP Check Failed'); }
}

setInterval(otpProcessor, 5000);

// ==========================================
// 🛠 COMMANDS & UI
// ==========================================
bot.onText(/\/start/, (msg) => {
    const kb = {
        reply_markup: {
            keyboard: [["📱 Get Number", "🛠 Support"]],
            resize_keyboard: true
        }
    };
    if (isAdmin(msg.from.id)) kb.reply_markup.keyboard.push(["👑 Admin Panel"]);
    bot.sendMessage(msg.chat.id, `Welcome to <b>${getConfig().brand_name}</b>`, { parse_mode: 'HTML', ...kb });
});

bot.on('message', (msg) => {
    if (msg.text === "👑 Admin Panel" && isAdmin(msg.from.id)) {
        const nums = readDb('numbers.json');
        const used = nums.filter(n => n.used).length;
        const avail = nums.length - used;
        const bar = "█".repeat(Math.floor((avail / nums.length) * 10 || 0)).padEnd(10, "░");

        const text = `═《 ${icon('👑', E.ADMIN)} <b>𝗗𝗔𝗦𝗛𝗕𝗢𝗔𝗥𝗗</b> 》═\n` +
            `━━━━━━━━━━━━━\n` +
            `${icon('🚀', E.ROCKET)} <b>Stock:</b> ${avail}/${nums.length}\n` +
            `<b>Health:</b> [${bar}]\n` +
            `━━━━━━━━━━━━━`;

        bot.sendMessage(msg.chat.id, text, {
            parse_mode: 'HTML',
            reply_markup: {
                inline_keyboard: [
                    [{ text: "📤 Upload", callback_data: "up" }, { text: "⚙️ Settings", callback_data: "sets" }],
                    [{ text: "🗑 Files", callback_data: "fs" }, { text: "🔙 Close", callback_data: "cls" }]
                ]
            }
        });
    }
});

console.log("Bot.js is running...");
