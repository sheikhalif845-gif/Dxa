import express from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import fs from 'fs';
import TelegramBot from 'node-telegram-bot-api';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// --- Configuration ---
const BOT_TOKEN = process.env.BOT_TOKEN || "8332473503:AAFvgTSIEdiCWiPwAJq7uKm2Dg_hMmgydRg";
const ADMIN_ID = parseInt(process.env.ADMIN_ID || "8197284774");

if (BOT_TOKEN === "YOUR_BOT_TOKEN") {
    console.error("❌ [TELEGRAM] BOT_TOKEN is missing or invalid in .env file.");
}

const bot = new TelegramBot(BOT_TOKEN, { polling: true });

bot.on('polling_error', (error) => {
    if (error.message.includes('401')) {
        console.error("❌ [TELEGRAM] ERROR 401: Unauthorized. Your BOT_TOKEN is invalid. Please check your .env file.");
        bot.stopPolling();
    } else {
        console.error("[TELEGRAM] Polling Error:", error.message);
    }
});

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

const APP_EMOJIS: { [key: string]: [string, string] } = {
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

function e(emoji: string, emojiId: string) {
    return `<tg-emoji emoji-id="${emojiId}">${emoji}</tg-emoji>`;
}

// --- Database Helpers ---
const DATA_DIR = path.join(__dirname, 'data');
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR);

const OTP_API_URL = process.env.OTP_API_URL || "http://147.135.212.197/crapi/st/viewstats";
const OTP_API_TOKEN = process.env.OTP_API_TOKEN || "R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ==";

const cooldowns = new Map<number, number>();
const processedMessages = new Set<string>();

function readJson(filename: string) {
    const filePath = path.join(DATA_DIR, filename);
    if (!fs.existsSync(filePath)) return [];
    try {
        const content = fs.readFileSync(filePath, 'utf-8');
        return JSON.parse(content);
    } catch {
        return [];
    }
}

function writeJson(filename: string, data: any) {
    const filePath = path.join(DATA_DIR, filename);
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
}

// --- Settings Management ---
function getSettings() {
    const settings = readJson("settings.json");
    if (!settings || Array.isArray(settings)) {
        const defaultSettings = {
            force_join: true,
            channels: [
                { name: "DXA Universe", url: "https://t.me/dxa_universe", username: "@dxa_universe" }
            ],
            admins: [],
            otp_groups: [],
            otp_link: "https://t.me/dxaotpzone",
            brand_name: "DXA UNIVERSE",
            mask_text: "DXA",
            group_buttons: {}
        };
        writeJson("settings.json", defaultSettings);
        return defaultSettings;
    }
    
    // Migration
    let updated = false;
    if (!settings.brand_name) { settings.brand_name = "DXA UNIVERSE"; updated = true; }
    if (!settings.mask_text) { settings.mask_text = "DXA"; updated = true; }
    if (!settings.group_buttons) { settings.group_buttons = {}; updated = true; }
    if (updated) writeJson("settings.json", settings);

    return settings;
}

function getBrand() { return getSettings().brand_name || "DXA UNIVERSE"; }
function getMask() { return getSettings().mask_text || "DXA"; }

function isAdmin(userId: number) {
    if (userId === ADMIN_ID) return true;
    const settings = getSettings();
    return (settings.admins || []).map(String).includes(userId.toString());
}

async function checkForceJoin(userId: number) {
    const settings = getSettings();
    if (!settings.force_join) return true;
    if (isAdmin(userId)) return true;
    
    for (const channel of settings.channels || []) {
        try {
            const member = await bot.getChatMember(channel.username, userId);
            if (['left', 'kicked', 'restricted'].includes(member.status)) return false;
        } catch {
            return false;
        }
    }
    return true;
}

function getMainButtons(userId: number) {
    const buttons = [
        [{ text: "📱 Get Number" }, { text: "🛠 Support" }]
    ];
    if (isAdmin(userId)) {
        buttons.push([{ text: "👑 Admin Panel" }]);
    }
    return {
        keyboard: buttons,
        resize_keyboard: true
    };
}

// --- Bot Logic ---

bot.onText(/\/start/, async (msg) => {
    const userId = msg.from?.id;
    if (!userId) return;

    const users = readJson("users.json");
    if (!users.some((u: any) => u.uid === userId.toString())) {
        users.push({
            uid: userId.toString(),
            username: msg.from?.username,
            joinedAt: new Date().toString()
        });
        writeJson("users.json", users);
    }

async function showForceJoinMsg(chatId: number) {
    const settings = getSettings();
    const text = 
        `${e('🚫', PREMIUM_EMOJIS.CLOSE)} <b>ACCESS RESTRICTED</b> ${e('🚫', PREMIUM_EMOJIS.CLOSE)}\n` +
        `━━━━━━━━━━━━\n` +
        `${e('📢', PREMIUM_EMOJIS.BROADCAST)} <b>Join Our Official Channel</b>\n\n` +
        `${e('🔐', PREMIUM_EMOJIS.OTP_ID)} To unlock full access to <b>This Bot</b>, You Must Join Our Channel First.\n` +
        `━━━━━━━━━━━━\n` +
        `${e('✅', PREMIUM_EMOJIS.DONE)} After Joining, Tap The Button Below To Continue`;
    
    const inline_keyboard = (settings.channels || []).map((c: any) => [
        { text: `Join ${c.name}`, url: c.url }
    ]);
    inline_keyboard.push([{ text: `Joined ✅`, callback_data: "check_join" }]);
    await bot.sendMessage(chatId, text, { parse_mode: 'HTML', reply_markup: { inline_keyboard } });
}

// ... in start logic ...
    const isJoined = await checkForceJoin(userId);
    if (!isJoined) {
        await showForceJoinMsg(msg.chat.id);
        return;
    }

    const brand = getBrand();
    await deleteLastMenu(msg.chat.id, userId);

    const welcomeText = 
        `═《 ${e("🔥", PREMIUM_EMOJIS.FIRE)} 𝗗𝗫𝗔 𝗡𝗨𝗠𝗕𝗘𝗥 𝗕𝗢𝗧 ${e("🔥", PREMIUM_EMOJIS.FIRE)} 》═\n` +
        `━━━━━━━━━━━\n` +
        `${e("👋", PREMIUM_EMOJIS.HELLO)} 𝗛𝗲𝗹𝗹𝗼, <b>${msg.from?.first_name}</b>! 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗗𝗫𝗔 𝗨𝗡𝗜𝗩𝗘𝗥𝗦𝗘\n` +
        `${e("💬", PREMIUM_EMOJIS.CHAT)} 𝗦𝘆𝘀𝘁𝗲𝗺 𝗥𝗲𝗮𝗱𝘆 𝘁𝗼 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲 𝗡𝘂𝗺𝗯𝗲𝗿𝘀\n` +
        `━━━━━━━━━━━\n` +
        `${e("📌", PREMIUM_EMOJIS.PIN)} 𝗧𝗮𝗽 ➤ 𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥\n` +
        `➤ 𝗧𝗼 𝗦𝘁𝗮𝗿𝘁 𝗦𝗲𝗿𝘃𝗶𝗰𝗲\n` +
        `━━━━━━━━━━━\n` +
        `${e("😒", PREMIUM_EMOJIS.DXA)} 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 <b>𝗗𝗫𝗔 𝗨𝗡𝗜𝗩𝗘𝗥𝗦𝗘</b>\n` +
        `━━━━━━━━━━━`;

    const sent = await bot.sendMessage(msg.chat.id, welcomeText, {
        parse_mode: 'HTML',
        reply_markup: getMainButtons(userId)
    });
    lastMenus.set(userId, sent.message_id);
});

const lastMenus = new Map<number, number>();

async function deleteLastMenu(chatId: number, userId: number) {
    const lastId = lastMenus.get(userId);
    if (lastId) {
        try {
            await bot.deleteMessage(chatId, lastId);
        } catch (e) {}
        lastMenus.delete(userId);
    }
}

// Helper for safe message editing
async function safeEdit(chatId: number, messageId: number, text: string, options: any) {
    try {
        await bot.editMessageText(text, { chat_id: chatId, message_id: messageId, ...options });
    } catch (err: any) {
        if (err.message && err.message.includes('message to edit not found')) {
            // Already deleted or moved on, ignore
            return;
        }
        console.error(`[TELEGRAM] SafeEdit Error:`, err.message || err);
    }
}

// Global Exception Handler for Promises
process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});
process.on('uncaughtException', (err) => {
    console.error('Uncaught Exception thrown:', err);
});

bot.on('polling_error', (err) => {
    console.error(`[TELEGRAM] Polling Error: ${err.message}`);
});

const waitingForInput = new Map<number, string>();

bot.on('document', async (msg) => {
    if (!msg.from || !msg.document) return;
    const userId = msg.from.id;
    const chatId = msg.chat.id;

    if (!isAdmin(userId)) return;

    if (waitingForInput.get(userId) === "admin_upload") {
        if (!msg.document.file_name?.endsWith(".txt")) {
            await bot.sendMessage(chatId, "❌ Please send a valid .txt file.");
            return;
        }

        waitingForInput.delete(userId);
        await bot.sendMessage(chatId, `${e("🔹", PREMIUM_EMOJIS.DOT)} Enter Service Name:`, { parse_mode: 'HTML' });
        waitingForInput.set(userId, `svc_name:${msg.document.file_id}:${msg.document.file_name}`);
    }
});

bot.on('message', async (msg) => {
    if (!msg.text || !msg.from) return;
    const userId = msg.from.id;
    const chatId = msg.chat.id;

    // Handle administrative input states
    const state = waitingForInput.get(userId);
    if (state) {
        try {
            const settings = getSettings();
            const input = msg.text.trim();
            
            if (state === "add_admin") {
            if (!settings.admins.includes(input)) {
                settings.admins.push(input);
                writeJson("settings.json", settings);
                await bot.sendMessage(chatId, `✅ Admin ${input} added!`);
            }
            waitingForInput.delete(userId);
            showManageAdmins(chatId, lastMenus.get(userId)!);
            return;
        } else if (state === "add_otp_group") {
            if (!settings.otp_groups.includes(input)) {
                settings.otp_groups.push(input);
                writeJson("settings.json", settings);
                await bot.sendMessage(chatId, `✅ Group ${input} added!`);
            }
            waitingForInput.delete(userId);
            showManageOtpGroups(chatId, lastMenus.get(userId)!);
            return;
        } else if (state === "set_otp_link") {
            if (input.startsWith("http")) {
                settings.otp_link = input;
                writeJson("settings.json", settings);
                await bot.sendMessage(chatId, `✅ OTP Link updated!`);
            }
            waitingForInput.delete(userId);
            showSettingsPanel(chatId, lastMenus.get(userId)!);
            return;
        } else if (state === "add_channel") {
            if (input.includes("|")) {
                const parts = input.split("|").map(p => p.trim());
                if (parts.length === 3) {
                    settings.channels.push({ name: parts[0], url: parts[1], username: parts[2] });
                    writeJson("settings.json", settings);
                    await bot.sendMessage(chatId, `✅ Channel ${parts[0]} added!`);
                }
            }
            waitingForInput.delete(userId);
            showManageForceJoin(chatId, lastMenus.get(userId)!);
            return;
        } else if (state === "set_brand_name") {
            settings.brand_name = input;
            writeJson("settings.json", settings);
            await bot.sendMessage(chatId, `✅ Brand Name updated to: <b>${input}</b>`, { parse_mode: 'HTML' });
            waitingForInput.delete(userId);
            showSettingsPanel(chatId, lastMenus.get(userId)!);
            return;
        } else if (state === "set_mask_text") {
            settings.mask_text = input;
            writeJson("settings.json", settings);
            await bot.sendMessage(chatId, `✅ Mask Text updated to: <b>${input}</b>`, { parse_mode: 'HTML' });
            waitingForInput.delete(userId);
            showSettingsPanel(chatId, lastMenus.get(userId)!);
            return;
        } else if (state.startsWith("add_grp_spec_btn:")) {
            const gid = state.split(":")[1];
            if (input.includes("|")) {
                const parts = input.split("|").map(p => p.trim());
                if (parts.length === 2) {
                    if (!settings.group_buttons) settings.group_buttons = {};
                    if (!settings.group_buttons[gid]) settings.group_buttons[gid] = [];
                    settings.group_buttons[gid].push({ text: parts[0], url: parts[1] });
                    writeJson("settings.json", settings);
                    await bot.sendMessage(chatId, `✅ Button Added for Group ${gid}!`);
                }
            }
            waitingForInput.delete(userId);
            showGroupButtonsSettings(chatId, lastMenus.get(userId)!, gid);
            return;
        } else if (state === "add_otp_msg_btn") {
            if (input.includes("|")) {
                const parts = input.split("|").map(p => p.trim());
                if (parts.length === 2) {
                    if (!settings.otp_message_buttons) settings.otp_message_buttons = [];
                    settings.otp_message_buttons.push({ text: parts[0], url: parts[1] });
                    writeJson("settings.json", settings);
                    await bot.sendMessage(chatId, `✅ OTP Button Added!`);
                }
            }
            waitingForInput.delete(userId);
            showManageOtpGroups(chatId, lastMenus.get(userId)!);
            return;
        } else if (state.startsWith("svc_name:")) {
            const [_, fileId, fileName] = state.split(":");
            waitingForInput.set(userId, `country_name:${fileId}:${fileName}:${input}`);
            await bot.sendMessage(chatId, `${e("📍", PREMIUM_EMOJIS.PIN)} Enter Country Name:`, { parse_mode: 'HTML' });
            return;
        } else if (state.startsWith("country_name:")) {
            const [_, fileId, fileName, service] = state.split(":");
            const country = input;
            waitingForInput.delete(userId);
            const statusMsg = await bot.sendMessage(chatId, `${e("⏳", PREMIUM_EMOJIS.WAIT)} Processing file...`, { parse_mode: 'HTML' });
            
            try {
                const fileLink = await bot.getFileLink(fileId);
                const response = await fetch(fileLink);
                const text = await response.text();
                const lines = text.split(/\r?\n/).filter(l => l.trim() !== "");
                
                const numbers = readJson("numbers.json");
                const files = readJson("files.json");
                const fid = Date.now().toString();
                
                files.push({ id: fid, fileName, service, country, count: lines.length });
                lines.forEach(line => {
                    numbers.push({
                        id: Math.random().toString(36).substr(2, 9),
                        number: line.trim(),
                        service,
                        country,
                        used: false,
                        fileId: fid
                    });
                });
                
                writeJson("numbers.json", numbers);
                writeJson("files.json", files);
                
                await bot.deleteMessage(chatId, statusMsg.message_id);
                await bot.sendMessage(chatId, `${e("✅", PREMIUM_EMOJIS.DONE)} Success! ${lines.length} numbers added.`, { parse_mode: 'HTML' });
            } catch (err: any) {
                await bot.sendMessage(chatId, `❌ Error: ${err.message}`);
            }
            showAdminPanel(chatId, undefined, userId);
            return;
        } else if (state === "admin_broadcast") {
            const users = readJson("users.json");
            let count = 0;
            const statusMsg = await bot.sendMessage(chatId, `${e("⏳", PREMIUM_EMOJIS.WAIT)} <b>Broadcasting...</b>\nProgress: 0/${users.length}`, { parse_mode: 'HTML' });
            
            for (let i = 0; i < users.length; i++) {
                const u = users[i];
                try {
                    await bot.copyMessage(u.uid, chatId, msg.message_id);
                    count++;
                } catch (e) {}
                
                // Update progress every 10 users to avoid rate limiting
                if ((i + 1) % 10 === 0 || i === users.length - 1) {
                    await bot.editMessageText(`${e("⏳", PREMIUM_EMOJIS.WAIT)} <b>Broadcasting...</b>\nProgress: ${i + 1}/${users.length}\nSuccessful: ${count}`, {
                        chat_id: chatId,
                        message_id: statusMsg.message_id,
                        parse_mode: 'HTML'
                    }).catch(() => {});
                }
            }
            
            await bot.editMessageText(`${e("✅", PREMIUM_EMOJIS.DONE)} <b>Broadcast complete!</b>\n━━━━━━━━━━━━━\nSent to: ${count} users.\nFailed: ${users.length - count}`, {
                chat_id: chatId,
                message_id: statusMsg.message_id,
                parse_mode: 'HTML'
            });
            waitingForInput.delete(userId);
            return;
        }
    } catch (adminInputErr: any) {
        console.error(`[ADMIN] Input handler error:`, adminInputErr.message || adminInputErr);
        waitingForInput.delete(userId);
    }
}

    if (msg.text.startsWith('/')) return;

    const isJoined = await checkForceJoin(userId);
    if (!isJoined && msg.text !== "Joined ✅") return;

    if (msg.text === "📱 Get Number") {
        // Attempt to delete the user's "Get Number" message to keep chat clean
        try { await bot.deleteMessage(chatId, msg.message_id); } catch (e) {}
        // Delete previous bot menu if exists
        await deleteLastMenu(chatId, userId);
        showServices(chatId, undefined, userId);
    } else if (msg.text === "🛠 Support") {
        try { await bot.deleteMessage(chatId, msg.message_id); } catch (e) {}
        await deleteLastMenu(chatId, userId);

        const supportText =
            `═《 ${e("🔥", PREMIUM_EMOJIS.FIRE)} 𝗗𝗫𝗔 𝗦𝗨𝗣𝗣𝗢𝗥𝗧 ${e("🔥", PREMIUM_EMOJIS.FIRE)} 》═\n` +
            `━━━━━━━━━━━\n` +
            `${e("👋", PREMIUM_EMOJIS.HELLO)} 𝗛𝗲𝗹𝗹𝗼, <b>${msg.from.first_name}</b>!\n` +
            `${e("💬", PREMIUM_EMOJIS.CHAT)} 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗗𝗫𝗔 𝗦𝘂ｐｐ𝗼𝗿𝘁 𝗣𝗮𝗻𝗲𝗹\n` +
            `➤ 𝗧𝗲𝗹𝗹 𝗠𝗲 𝗛𝗼𝘄 𝗖𝗮𝗻 𝗜 𝗛𝗲𝗹𝗽 𝗬𝗼𝘂.\n` +
            `${e("📌", PREMIUM_EMOJIS.PIN)} 𝗧𝗮ｐ 𝗦𝘂ｐｐ𝗼𝗿𝘁 𝗕𝘂𝘁𝘁𝗼𝗻\n` +
            `➤ 𝗧𝗼 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗧𝗵𝗲 𝗔𝗱𝗺𝗶𝗻!\n` +
            `━━━━━━━━━━━\n` +
            `${e("😒", PREMIUM_EMOJIS.DXA)} 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 <b>𝗗𝗫𝗔 𝗨𝗡𝗜𝗩𝗘𝗥𝗦𝗘</b>`;

        const reply_markup = {
            inline_keyboard: [
                [{ text: "💬 Support Center", url: "https://t.me/asik_x_bd_bot" }],
                [{ text: "🔙 Back", callback_data: "close_menu" }]
            ]
        };
        const sent = await bot.sendMessage(chatId, supportText, { parse_mode: 'HTML', reply_markup });
        lastMenus.set(userId, sent.message_id);
    } else if (msg.text === "👑 Admin Panel" && isAdmin(userId)) {
        try { await bot.deleteMessage(chatId, msg.message_id); } catch (e) {}
        await deleteLastMenu(chatId, userId);
        showAdminPanel(chatId, undefined, userId);
    }
});

async function showServices(chatId: number, messageId?: number, userId?: number) {
    const numbers = readJson("numbers.json");
    const available = numbers.filter((n: any) => !n.used);
    const services = Array.from(new Set(available.map((n: any) => n.service))).sort();

    const inline_keyboard: any[] = [];
    let text = "";

    if (services.length === 0) {
        text = `${e("❌", PREMIUM_EMOJIS.CLOSE)} No numbers available at the moment.`;
        inline_keyboard.push([{ text: "🔙 Back", callback_data: "close_menu" }]);
    } else {
        text = `${e("📱", PREMIUM_EMOJIS.NUMBER)} <b>Select a Service:</b>`;
        services.forEach((s: any) => {
            inline_keyboard.push([{ text: `🔹 ${s}`, callback_data: `sel_service:${s}` }]);
        });
        inline_keyboard.push([{ text: "🔙 Back", callback_data: "close_menu" }]);
    }

    if (messageId) {
        await bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard } });
    } else {
        const sent = await bot.sendMessage(chatId, text, { parse_mode: 'HTML', reply_markup: { inline_keyboard } });
        if (userId) lastMenus.set(userId, sent.message_id);
    }
}

function showSettingsPanel(chatId: number, messageId: number) {
    const text = `${e("⚙️", PREMIUM_EMOJIS.NOTE)} <b>BOT SETTINGS CENTER</b> ${e("⚙️", PREMIUM_EMOJIS.NOTE)}\n` +
                 `━━━━━━━━━━━━━\n\n` +
                 `Welcome to the bot configuration hub. Select a category below to manage your bot instance.`;
    
    const inline_keyboard = [
        [{ text: "📢 Force Join System", callback_data: "manage_force_join" }],
        [{ text: "👥 Admin Management", callback_data: "manage_admins" }],
        [{ text: "💬 OTP Group System", callback_data: "manage_otp_groups" }],
        [{ text: "🔗 Bot OTP Button Link", callback_data: "manage_bot_otp_link" }],
        [{ text: "✨ Branding & Masking", callback_data: "manage_branding" }],
        [{ text: "🔙 Back to Admin", callback_data: "admin_panel_back" }]
    ];
    
    bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard } });
}

async function showManageForceJoin(chatId: number, messageId: number) {
    const settings = getSettings();
    const status = settings.force_join ? "Active ✅" : "Disabled ❌";
    
    let text = `${e("📢", PREMIUM_EMOJIS.BROADCAST)} <b>FORCE JOIN SYSTEM</b>\n` +
               `━━━━━━━━━━━━━\n\n` +
               `Current Status: <b>${status}</b>\n\n` +
               `<b>Active Channels:</b>\n`;
    
    const channels = settings.channels || [];
    const inline_keyboard: any[] = [];
    
    if (channels.length === 0) {
        text += "  • No channels configured.\n";
    } else {
        channels.forEach((c: any, i: number) => {
            text += `  ${i+1}. ${c.name} (<code>${c.username}</code>)\n`;
            inline_keyboard.push([{ text: `🗑 Delete ${c.name}`, callback_data: `del_chan:${i}` }]);
        });
    }
    
    text += `\n━━━━━━━━━━━━━`;
    
    const toggleBtn = settings.force_join ? "OFF ❌" : "ON ✅";
    inline_keyboard.push([{ text: `Toggle Force Join: ${toggleBtn}`, callback_data: "toggle_force_join" }]);
    inline_keyboard.push([{ text: "➕ Add Channel", callback_data: "add_channel" }]);
    if (channels.length > 0) inline_keyboard.push([{ text: "🗑 Delete All Channels", callback_data: "reset_channels" }]);
    inline_keyboard.push([{ text: "🔙 Back", callback_data: "admin_settings" }]);
    
    await bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard } });
}

async function showManageAdmins(chatId: number, messageId: number) {
    const settings = getSettings();
    let text = `${e("👤", PREMIUM_EMOJIS.USER)} <b>ADMIN MANAGEMENT</b>\n` +
               `━━━━━━━━━━━━━\n\n` +
               `Master Admin: <code>${ADMIN_ID}</code> (Immortal)\n\n` +
               `<b>Co-Admins:</b>\n`;
    
    const admins = settings.admins || [];
    const inline_keyboard: any[] = [];
    
    if (admins.length === 0) {
        text += "  • No co-admins added.\n";
    } else {
        admins.forEach((a: any) => {
            text += `  • <code>${a}</code>\n`;
            inline_keyboard.push([{ text: `🗑 Remove Admin ${a}`, callback_data: `del_admin:${a}` }]);
        });
    }
            
    text += `\n━━━━━━━━━━━━━`;
    inline_keyboard.push([{ text: "➕ Add Admin", callback_data: "add_admin" }]);
    if (admins.length > 0) inline_keyboard.push([{ text: "🗑 Remove All Co-Admins", callback_data: "reset_admins" }]);
    inline_keyboard.push([{ text: "🔙 Back", callback_data: "admin_settings" }]);
    
    await bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard } });
}

async function showManageOtpGroups(chatId: number, messageId: number) {
    const settings = getSettings();
    let text = `${e("💬", PREMIUM_EMOJIS.CHAT)} <b>OTP GROUP SYSTEM</b>\n` +
               `━━━━━━━━━━━━━\n\n` +
               `<b>Forwarding Groups:</b>\n`;
    
    const groups = settings.otp_groups || [];
    const group_buttons = settings.group_buttons || {};
    const inline_keyboard: any[] = [];
    
    if (groups.length === 0) {
        text += `  ${e("❌", PREMIUM_EMOJIS.CLOSE)} No groups added.\n`;
    } else {
        groups.forEach((g: any) => {
            const btn_count = (group_buttons[g.toString()] || []).length;
            text += `  ${e("🔹", PREMIUM_EMOJIS.DOT)} <code>${g}</code> (${btn_count} Buttons)\n`;
            inline_keyboard.push([
                { text: `⚙️ Buttons for ${g}`, callback_data: `setup_grp_btns:${g}` },
                { text: `🗑 Remove`, callback_data: `del_otp_grp:${g}` }
            ]);
        });
    }
            
    text += `\n<b>Global OTP Buttons:</b>\n`;
    const buttons = settings.otp_message_buttons || [];
    if (buttons.length === 0) {
        text += `  ${e("❌", PREMIUM_EMOJIS.CLOSE)} No global buttons.\n`;
    } else {
        buttons.forEach((b: any, i: number) => {
            text += `  ${i+1}. ${b.text} (${e("🔗", PREMIUM_EMOJIS.PIN)})\n`;
            inline_keyboard.push([{ text: `🗑 Delete Global: ${b.text}`, callback_data: `del_otp_btn:${i}` }]);
        });
    }

    text += `\n━━━━━━━━━━━━━`;
    inline_keyboard.push([{ text: "➕ Add Forwarding Group", callback_data: "add_otp_group" }]);
    inline_keyboard.push([{ text: "➕ Add Global Button", callback_data: "add_otp_msg_btn" }]);
    if (groups.length > 0 || buttons.length > 0) inline_keyboard.push([{ text: "🗑 Reset OTP System", callback_data: "reset_otp_groups" }]);
    inline_keyboard.push([{ text: "🔙 Back", callback_data: "admin_settings" }]);
    
    await bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard } });
}

async function showGroupButtonsSettings(chatId: number, messageId: number, groupId: string) {
    const settings = getSettings();
    const group_buttons = (settings.group_buttons || {})[groupId] || [];
    
    let text = `${e("💬", PREMIUM_EMOJIS.CHAT)} <b>BUTTONS FOR GROUP:</b> <code>${groupId}</code>\n` +
               `━━━━━━━━━━━━━\n\n` +
               `These buttons only appear when OTP is forwarded to this specific group.\n\n`;
    
    const inline_keyboard: any[] = [];
    if (group_buttons.length === 0) {
        text += `  ${e("❌", PREMIUM_EMOJIS.CLOSE)} No group-specific buttons.\n`;
    } else {
        group_buttons.forEach((btn: any, i: number) => {
            text += `  ${i+1}. ${btn.text} (${e("🔗", PREMIUM_EMOJIS.PIN)})\n`;
            inline_keyboard.push([{ text: `🗑 Delete: ${btn.text}`, callback_data: `del_grp_spec_btn:${groupId}:${i}` }]);
        });
    }
            
    inline_keyboard.push([{ text: "➕ Add Button", callback_data: `add_grp_spec_btn:${groupId}` }]);
    inline_keyboard.push([{ text: "🔙 Back", callback_data: "manage_otp_groups" }]);
    
    await bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard } });
}

async function showBotKeypadSettings(chatId: number, messageId: number) {
    const settings = getSettings();
    const link = settings.otp_link || "https://t.me/dxaotpzone";
    const text = `${e("🔗", PREMIUM_EMOJIS.PIN)} <b>BOT OTP BUTTON LINK</b>\n` +
                 `━━━━━━━━━━━━━\n\n` +
                 `This link is used for the '💬 OTP Group' button displayed after a user allocates numbers.\n\n` +
                 `Current Link: <b>${link}</b>\n\n` +
                 `━━━━━━━━━━━━━`;
    
    const inline_keyboard = [
        [{ text: "✏️ Edit Link", callback_data: "set_otp_link" }],
        [{ text: "🔙 Back", callback_data: "admin_settings" }]
    ];
    
    await bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard } });
}

async function showAdminPanel(chatId: number, messageId?: number, userId?: number) {
    const users = readJson("users.json");
    const numbers = readJson("numbers.json");
    const files = readJson("files.json");
    const assigned = numbers.filter((n: any) => n.used).length;
    const available = numbers.filter((n: any) => !n.used).length;
    const total = numbers.length;
    
    const percent = total > 0 ? Math.floor((available / total) * 10) : 0;
    const bar = "█".repeat(percent) + "░".repeat(10 - percent);

    const text = 
        `${e("👑", PREMIUM_EMOJIS.ADMIN)} <b>ADMIN CONTROL PANEL</b> ${e("👑", PREMIUM_EMOJIS.ADMIN)}\n` +
        `━━━━━━━━━━━━━\n\n` +
        `${e("📊", PREMIUM_EMOJIS.GRAPH)} <b>DATABASE OVERVIEW</b>\n` +
        `─ ─ ─ ─ ─ ─ ─\n` +
        `  ${e("👤", PREMIUM_EMOJIS.USER)}  Users       »  ${users.length}\n` +
        `  ${e("📁", PREMIUM_EMOJIS.FILE)}  Files       »  ${files.length}\n` +
        `  ${e("🔢", PREMIUM_EMOJIS.NUMBERS)}  Numbers     »  ${total}\n` +
        `  ${e("✅", PREMIUM_EMOJIS.DONE)}  Assigned    »  ${assigned}\n` +
        `  ${e("🚀", PREMIUM_EMOJIS.ROCKET)}  Available   »  ${available}\n\n` +
        `${e("📈", PREMIUM_EMOJIS.GRAPH)} <b>STOCK LEVEL</b>\n` +
        `─ ─ ─ ─ ─ ─ ─\n` +
        `  [${bar}]  ${available} free\n\n` +
        `━━━━━━━━━━━━━`;

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

// Callback query handler
bot.on('callback_query', async (query) => {
    const chatId = query.message?.chat.id;
    const messageId = query.message?.message_id;
    const data = query.data;
    const userId = query.from.id;

    if (!chatId || !messageId || !data) return;

    // Admin Panel Guards
    const ADMIN_ACTIONS = [
        "manage_force_join", "manage_admins", "manage_otp_groups", "manage_bot_otp_link", 
        "admin_settings", "add_admin", "reset_admins", "add_otp_group", "reset_otp_groups",
        "set_otp_link", "toggle_force_join", "reset_channels", "add_channel", "admin_upload",
        "admin_broadcast", "admin_delete_files", "admin_panel_back", "view_used", "view_unused",
        "add_otp_msg_btn", "reset_otp_groups"
    ];
    
    const isAdminAction = ADMIN_ACTIONS.some(act => data.startsWith(act)) || 
                          ["del_chan:", "del_admin:", "del_otp_grp:", "del_otp_btn:", "del_file:"].some(pref => data.startsWith(pref));
    
    if (isAdminAction && !isAdmin(userId)) {
        await bot.answerCallbackQuery(query.id, { text: "❌ Limited to Admins only!", show_alert: true });
        return;
    }

    if (data === "check_join") {
        const isJoined = await checkForceJoin(userId);
        if (isJoined) {
            await bot.deleteMessage(chatId, messageId);
            // Re-send start message
            const welcomeText = 
                `${e("🔥", PREMIUM_EMOJIS.FIRE)} DXA NUMBER BOT ${e("🔥", PREMIUM_EMOJIS.FIRE)}\n` +
                `━━━━━━━━━━━\n` +
                `${e("👋", PREMIUM_EMOJIS.HELLO)} Hello, <b>${query.from.first_name}</b>! Welcome To DXA UNIVERSE.\n\n` +
                `${e("📌", PREMIUM_EMOJIS.PIN)} Tap Get Number to start!\n` +
                `━━━━━━━━━━━\n` +
                `${e("😒", PREMIUM_EMOJIS.DXA)} POWERED BY DXA UNIVERSE`;

            await bot.sendMessage(chatId, welcomeText, {
                parse_mode: 'HTML',
                reply_markup: getMainButtons(userId)
            });
        } else {
            await bot.answerCallbackQuery(query.id, { text: "❌ Join all channels first!", show_alert: true });
        }
    } else if (data === "close_menu") {
        await bot.deleteMessage(chatId, messageId);
    } else if (data === "back_to_services") {
        showServices(chatId, messageId);
    } else if (data.startsWith("sel_service:")) {
        const service = data.split(":")[1];
        const numbers = readJson("numbers.json").filter((n: any) => !n.used && n.service === service);
        const countries = Array.from(new Set(numbers.map((n: any) => n.country))).sort();
        
        const inline_keyboard = (countries as string[]).map(c => [
            { text: `📍 ${c}`, callback_data: `sel_country:${service}:${c}` }
        ]);
        inline_keyboard.push([{ text: "🔙 Back", callback_data: "back_to_services" }]);
        
        await bot.editMessageText(`${e("📍", PREMIUM_EMOJIS.PIN)} <b>Select Country for ${service}:</b>`, {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard }
        });
    } else if (data.startsWith("sel_country:")) {
        const now = Date.now();
        const lastTime = cooldowns.get(userId) || 0;
        const diff = (now - lastTime) / 1000;
        
        if (diff < 10) {
            const waitTime = Math.ceil(10 - diff);
            await bot.answerCallbackQuery(query.id, { 
                text: `❌ Please wait ${waitTime} seconds before getting numbers again!`, 
                show_alert: true 
            });
            return;
        }

        const parts = data.split(":");
        const service = parts[1];
        const country = parts[2];
        
        const allNums = readJson("numbers.json");
        const available = allNums.filter((n: any) => !n.used && n.service === service && n.country === country);
        
        if (available.length < 3) {
            await bot.answerCallbackQuery(query.id, { text: "❌ Not enough numbers available in this category.", show_alert: true });
            return;
        }

        // Randomly select 3
        const shuffled = available.sort(() => 0.5 - Math.random());
        const selected = shuffled.slice(0, 3);
        const selectedIds = selected.map((n: any) => n.id);

        allNums.forEach((n: any) => {
            if (selectedIds.includes(n.id)) {
                n.used = true;
                n.assignedTo = userId.toString();
                n.assignedAt = now;
            }
        });
        writeJson("numbers.json", allNums);
        
        // Update cooldown
        cooldowns.set(userId, now);

        const icons = [e("1️⃣", PREMIUM_EMOJIS.N1), e("2️⃣", PREMIUM_EMOJIS.N2), e("3️⃣", PREMIUM_EMOJIS.N3)];
        const formatted = selected.map((n: any, i: number) => {
            let num = n.number.toString().trim();
            if (!num.startsWith("+")) num = "+" + num;
            return `${icons[i]} <code>${num}</code>`;
        });

        const serviceKey = service.toString().toUpperCase().replace(/\s+/g, '');
        const premium = APP_EMOJIS[serviceKey];
        const serviceIcon = premium ? e(premium[0], premium[1]) : e("🖥", PREMIUM_EMOJIS.SUPPORT);

        const text = 
            `━━━━━━━━━━━\n` +
            `《 ${e("✅", PREMIUM_EMOJIS.DONE)} 𝗡𝗨𝗠𝗕𝗘𝗥𝗦 𝗔𝗟𝗟𝗢𝗖𝗔𝗧𝗘𝗗 》\n` +
            `━━━━━━━━━━━\n` +
            `<blockquote>${e("🔹", PREMIUM_EMOJIS.DOT)} <b>𝗦𝗲𝗿𝘃𝗶𝗰𝗲</b> ${serviceIcon} <b>${service}</b></blockquote>\n` +
            `<blockquote>${e("📍", PREMIUM_EMOJIS.PIN)} <b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆</b> 🌐 <b>${country}</b></blockquote>\n` +
            `━━━━━━━━━━━\n` +
            formatted.join("\n") + "\n" +
            `━━━━━━━━━━━\n` +
            `${e("😒", PREMIUM_EMOJIS.DXA)} 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 <b>𝗗𝗫𝗔 𝗨𝗡𝗜𝗩𝗘𝗥𝗦𝗘</b>\n` +
            `━━━━━━━━━━━`;

        const inline_keyboard = [
            [{ text: "🔄 Change Number", callback_data: `sel_country:${service}:${country}` }],
            [{ text: "💬 OTP Group", url: getSettings().otp_link || "https://t.me/dxaotpzone" }],
            [{ text: "🔙 Back", callback_data: "back_to_services" }]
        ];

        await bot.editMessageText(text, {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard }
        });
    } else if (data === "manage_force_join") {
        showManageForceJoin(chatId, messageId);
    } else if (data === "manage_admins") {
        showManageAdmins(chatId, messageId);
    } else if (data === "manage_otp_groups") {
        showManageOtpGroups(chatId, messageId);
    } else if (data === "manage_bot_otp_link") {
        showBotKeypadSettings(chatId, messageId);
    } else if (data === "manage_branding") {
        const brand = getBrand();
        const mask = getMask();
        const text = `${e("✨", PREMIUM_EMOJIS.FIRE)} <b>BRANDING & MASKING</b>\n` +
                     `━━━━━━━━━━━━━\n\n` +
                     `Current Brand: <b>${brand}</b>\n` +
                     `Current Mask: <b>${mask}</b>\n\n` +
                     `━━━━━━━━━━━━━`;
        const inline_keyboard = [
            [{ text: "✏️ Edit Brand Name", callback_data: "set_brand_name" }],
            [{ text: "✏️ Edit Mask Text", callback_data: "set_mask_text" }],
            [{ text: "🔙 Back", callback_data: "admin_settings" }]
        ];
        await bot.editMessageText(text, { chat_id: chatId, message_id: messageId, parse_mode: 'HTML', reply_markup: { inline_keyboard } });
    } else if (data === "set_brand_name") {
        await safeEdit(chatId, messageId, "✏️ <b>EDIT BRAND NAME</b>\n━━━━━━━━━━━━━\nPlease send the new Brand Name:", {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard: [[{ text: "🔙 Back", callback_data: "manage_branding" }]] }
        });
        waitingForInput.set(userId, "set_brand_name");
    } else if (data === "set_mask_text") {
        await safeEdit(chatId, messageId, "✏️ <b>EDIT MASK TEXT</b>\n━━━━━━━━━━━━━\nPlease send the new Mask string (e.g., DXA):", {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard: [[{ text: "🔙 Back", callback_data: "manage_branding" }]] }
        });
        waitingForInput.set(userId, "set_mask_text");
    } else if (data.startsWith("del_chan:")) {
        const idx = parseInt(data.split(":")[1]);
        const settings = getSettings();
        if (settings.channels && settings.channels[idx]) {
            settings.channels.splice(idx, 1);
            writeJson("settings.json", settings);
            await bot.answerCallbackQuery(query.id, { text: "Channel Deleted" });
        }
        showManageForceJoin(chatId, messageId);
    } else if (data.startsWith("del_admin:")) {
        const uid = data.split(":")[1];
        const settings = getSettings();
        settings.admins = (settings.admins || []).filter((a: any) => a !== uid);
        writeJson("settings.json", settings);
        await bot.answerCallbackQuery(query.id, { text: "Admin Removed" });
        showManageAdmins(chatId, messageId);
    } else if (data.startsWith("del_otp_grp:")) {
        const gid = data.split(":")[1];
        const settings = getSettings();
        settings.otp_groups = (settings.otp_groups || []).filter((g: any) => g !== gid);
        writeJson("settings.json", settings);
        await bot.answerCallbackQuery(query.id, { text: "Group Removed" });
        showManageOtpGroups(chatId, messageId);
    } else if (data.startsWith("del_otp_btn:")) {
        const idx = parseInt(data.split(":")[1]);
        const settings = getSettings();
        if (settings.otp_message_buttons && settings.otp_message_buttons[idx]) {
            settings.otp_message_buttons.splice(idx, 1);
            writeJson("settings.json", settings);
            await bot.answerCallbackQuery(query.id, { text: "Button Deleted" });
        }
        showManageOtpGroups(chatId, messageId);
    } else if (data === "add_otp_msg_btn") {
        await safeEdit(chatId, messageId, "➕ <b>ADD OTP BUTTON</b>\n━━━━━━━━━━━━━\nSend button details as:\n<code>Button Name | https://link.com</code>", {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard: [[{ text: "🔙 Back", callback_data: "manage_otp_groups" }]] }
        });
        waitingForInput.set(userId, "add_otp_msg_btn");
    } else if (data.startsWith("setup_grp_btns:")) {
        const gid = data.split(":")[1];
        showGroupButtonsSettings(chatId, messageId, gid);
    } else if (data.startsWith("add_grp_spec_btn:")) {
        const gid = data.split(":")[1];
        await safeEdit(chatId, messageId, `➕ <b>ADD BUTTON FOR ${gid}</b>\n━━━━━━━━━━━━━\nFormat: <code>Button Name | https://link.com</code>`, {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard: [[{ text: "🔙 Back", callback_data: `setup_grp_btns:${gid}` }]] }
        });
        waitingForInput.set(userId, `add_grp_spec_btn:${gid}`);
    } else if (data.startsWith("del_grp_spec_btn:")) {
        const parts = data.split(":");
        const gid = parts[1];
        const idx = parseInt(parts[2]);
        const settings = getSettings();
        if (settings.group_buttons && settings.group_buttons[gid] && settings.group_buttons[gid][idx]) {
            settings.group_buttons[gid].splice(idx, 1);
            writeJson("settings.json", settings);
            await bot.answerCallbackQuery(query.id, { text: "Button Removed" });
        }
        showGroupButtonsSettings(chatId, messageId, gid);
    } else if (data === "admin_settings") {
        waitingForInput.delete(userId);
        showSettingsPanel(chatId, messageId);
    } else if (data === "toggle_force_join") {
        const settings = getSettings();
        settings.force_join = !settings.force_join;
        writeJson("settings.json", settings);
        await bot.answerCallbackQuery(query.id, { text: "Settings Updated!" });
        showManageForceJoin(chatId, messageId);
    } else if (data === "reset_admins") {
        const settings = getSettings();
        settings.admins = [];
        writeJson("settings.json", settings);
        await bot.answerCallbackQuery(query.id, { text: "Admins list cleared!" });
        showManageAdmins(chatId, messageId);
    } else if (data === "reset_channels") {
        const settings = getSettings();
        settings.channels = [];
        writeJson("settings.json", settings);
        await bot.answerCallbackQuery(query.id, { text: "Channels list cleared!" });
        showManageForceJoin(chatId, messageId);
    } else if (data === "reset_otp_groups") {
        const settings = getSettings();
        settings.otp_groups = [];
        settings.otp_message_buttons = [];
        writeJson("settings.json", settings);
        await bot.answerCallbackQuery(query.id, { text: "OTP System Reset!" });
        showManageOtpGroups(chatId, messageId);
    } else if (data === "add_admin") {
        await safeEdit(chatId, messageId, "➕ <b>ADD NEW ADMIN</b>\n━━━━━━━━━━━━━\nPlease send the Telegram User ID of the new admin:", {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard: [[{ text: "🔙 Back", callback_data: "admin_settings" }]] }
        });
        waitingForInput.set(userId, "add_admin");
    } else if (data === "add_otp_group") {
        await safeEdit(chatId, messageId, "➕ <b>ADD OTP GROUP</b>\n━━━━━━━━━━━━━\nPlease send the Group ID (with -100 prefix):", {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard: [[{ text: "🔙 Back", callback_data: "admin_settings" }]] }
        });
        waitingForInput.set(userId, "add_otp_group");
    } else if (data === "set_otp_link") {
        await safeEdit(chatId, messageId, "🔗 <b>SET OTP LINK</b>\n━━━━━━━━━━━━━\nPlease send the new invitation link:", {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard: [[{ text: "🔙 Back", callback_data: "admin_settings" }]] }
        });
        waitingForInput.set(userId, "set_otp_link");
    } else if (data === "add_channel") {
        await safeEdit(chatId, messageId, "➕ <b>ADD NEW CHANNEL</b>\n━━━━━━━━━━━━━\nPlease send channel details in following format:\n\n<code>Channel Name | Public URL | @Username</code>", {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard: [[{ text: "🔙 Back", callback_data: "admin_settings" }]] }
        });
        waitingForInput.set(userId, "add_channel");
    } else if (data === "admin_upload") {
        await safeEdit(chatId, messageId, `${e("📤", PREMIUM_EMOJIS.UPLOAD)} <b>UPLOAD NUMBERS</b>\n━━━━━━━━━━━━━\nPlease send the .txt file containing numbers.`, {
            parse_mode: 'HTML',
            reply_markup: {
                inline_keyboard: [[{ text: "🔙 Back", callback_data: "admin_panel_back" }]]
            }
        });
        waitingForInput.set(userId, "admin_upload");
    } else if (data === "admin_broadcast") {
        await safeEdit(chatId, messageId, `${e("📢", PREMIUM_EMOJIS.BROADCAST)} <b>BROADCAST MESSAGE</b>\n━━━━━━━━━━━━━\nSend the message to broadcast:`, {
            parse_mode: 'HTML',
            reply_markup: {
                inline_keyboard: [[{ text: "🔙 Back", callback_data: "admin_panel_back" }]]
            }
        });
        waitingForInput.set(userId, "admin_broadcast");
    } else if (data === "admin_delete_files") {
        const files = readJson("files.json");
        if (files.length === 0) {
            await bot.answerCallbackQuery(query.id, { text: "No files found." });
            return;
        }
        const inline_keyboard = files.map((f: any) => [
            { text: `❌ ${f.fileName} (${f.service})`, callback_data: `del_file:${f.id}` }
        ]);
        inline_keyboard.push([{ text: "🔙 Back", callback_data: "admin_panel_back" }]);
        
        await bot.editMessageText(`${e("🗑", PREMIUM_EMOJIS.FILE)} <b>DELETE FILES</b>\n━━━━━━━━━━━━━\nSelect a file to delete:`, {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard }
        });
    } else if (data.startsWith("del_file:")) {
        const fileId = data.split(":")[1];
        let files = readJson("files.json");
        let numbers = readJson("numbers.json");
        
        files = files.filter((f: any) => f.id !== fileId);
        numbers = numbers.filter((n: any) => n.fileId !== fileId);
        
        writeJson("files.json", files);
        writeJson("numbers.json", numbers);
        
        await bot.answerCallbackQuery(query.id, { text: "✅ File and numbers deleted!" });
        showAdminPanel(chatId, messageId);
    } else if (data === "admin_panel_back") {
        waitingForInput.delete(userId);
        showAdminPanel(chatId, messageId);
    } else if (data === "view_used" || data === "view_unused") {
        const isUsed = data === "view_used";
        const numbers = readJson("numbers.json").filter((n: any) => n.used === isUsed);
        
        const text = 
            `${isUsed ? e("✅", PREMIUM_EMOJIS.DONE) : e("🚀", PREMIUM_EMOJIS.ROCKET)} <b>${isUsed ? "USED" : "UNUSED"} NUMBERS</b>\n` +
            `━━━━━━━━━━━━━\n` +
            `Total: <b>${numbers.length}</b>\n\n` +
            `You can download the full list as a .txt file below.\n` +
            `━━━━━━━━━━━━━`;
            
        const inline_keyboard = [
            [{ text: `📥 Download ${isUsed ? "Used" : "Unused"} (.txt)`, callback_data: `download_${isUsed ? "used" : "unused"}` }],
            [{ text: "🔙 Back", callback_data: "admin_panel_back" }]
        ];
        
        await bot.editMessageText(text, {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard }
        });
    } else if (data === "download_used" || data === "download_unused") {
        const isUsed = data === "download_used";
        const numbers = readJson("numbers.json").filter((n: any) => n.used === isUsed);
        
        if (numbers.length === 0) {
            await bot.answerCallbackQuery(query.id, { text: "❌ No numbers found!", show_alert: true });
            return;
        }
        
        const fileContent = numbers.map((n: any) => n.number).join("\n");
        const fileName = `${isUsed ? "used" : "unused"}_numbers_${Date.now()}.txt`;
        
        await bot.sendDocument(chatId, Buffer.from(fileContent), {
            caption: `${isUsed ? "✅ Used" : "🚀 Unused"} numbers list.`
        }, {
            filename: fileName,
            contentType: 'text/plain'
        });
        
        await bot.answerCallbackQuery(query.id, { text: "✅ File sent!" });
    } else if (data.startsWith("copy_otp:")) {
        const code = data.split(":")[1];
        await bot.answerCallbackQuery(query.id, { text: `Code ${code} selected.` });
    }
});

/**
 * Normalizes a phone number by removing all non-digit characters (+, -, spaces, etc.)
 * This ensures matching works whether the number has a + sign or not.
 */
function normalizeNumber(num: string | number): string {
    return num.toString().replace(/\D/g, "");
}

const COUNTRY_FLAGS: { [key: string]: string } = {
    "ghana": "🇬🇭",
    "nigeria": "🇳🇬",
    "usa": "🇺🇸",
    "uk": "🇬🇧",
    "india": "🇮🇳",
    "bangladesh": "🇧🇩",
    "spain": "🇪🇸",
    "venezuela": "🇻🇪"
};

function getServiceInfo(originalService: string, content: string) {
    const text = content.toUpperCase();
    let service = originalService;
    
    // Better detection for generic service names
    const keywords = [
        { key: 'INSTAGRAM', name: 'Instagram' },
        { key: 'WHATSAPP', name: 'WhatsApp' },
        { key: 'TELEGRAM', name: 'Telegram' },
        { key: 'FACEBOOK', name: 'Facebook' },
        { key: 'GOOGLE', name: 'Google' },
        { key: 'TIKTOK', name: 'TikTok' },
        { key: 'IMO', name: 'Imo' },
        { key: 'BKASH', name: 'bKash' },
        { key: 'NAGAD', name: 'Nagad' }
    ];

    for (const k of keywords) {
        if (text.includes(k.key)) {
            service = k.name;
            break;
        }
    }

    const serviceKey = service.toUpperCase().replace(/\s+/g, '');
    let serviceIcon;
    const premium = APP_EMOJIS[serviceKey];
    if (premium) {
        serviceIcon = e(premium[0], premium[1]);
    } else {
        serviceIcon = e("🖥", PREMIUM_EMOJIS.SUPPORT);
    }
    
    return { service, serviceIcon };
}

async function fetchOtps() {
    try {
        const response = await fetch(`${OTP_API_URL}?token=${OTP_API_TOKEN}&records=50`);
        if (!response.ok) {
            console.error(`[OTP] API Error: ${response.status} ${response.statusText}`);
            return;
        }
        const data = await response.json() as any[];
        if (!Array.isArray(data)) {
            console.error("[OTP] API returned non-array data type:", typeof data);
            return;
        }

        const numbersData = readJson("numbers.json");
        const settings = getSettings();
        
        for (const record of data) {
            if (!Array.isArray(record) || record.length < 4) continue;
            
            const [service, fullNumber, content, timestamp] = record;
            const msgId = `${fullNumber}_${timestamp}`;
            
            if (processedMessages.has(msgId)) continue;
            
            // Limit processedMessages set size to 10,000 to prevent memory leaks
            if (processedMessages.size > 10000) {
                const firstElement = processedMessages.values().next().value;
                processedMessages.delete(firstElement);
            }
            
            const normalizedApiNum = normalizeNumber(fullNumber);

            // IMPROVED OTP EXTRACTION:
            const otpMatch = content.match(/\d{3}[- ]\d{3}/) || content.match(/\d{4,8}/);
            const code = otpMatch ? otpMatch[0] : content; // Use full content if no code found

            if (content) {
                const { service: detectedService, serviceIcon } = getServiceInfo(service, content);

                const brand = getBrand();
                const mask = getMask();
                const maskedNum = normalizedApiNum.length >= 7 
                    ? `${normalizedApiNum.slice(0, 3)}${mask}${normalizedApiNum.slice(-4)}`
                    : normalizedApiNum;
                
                const groupMsgBody = `${serviceIcon} ${detectedService} <code>${maskedNum}</code>`;

                const getOtpMarkup = (specificButtons: any[] | null = null, otpCode: string) => {
                    const m_obj: any = {
                        inline_keyboard: [
                            [{ 
                                text: `📋 ${otpCode}`, 
                                copy_text: { text: otpCode } 
                            } as any]
                        ]
                    };
                    const btns = specificButtons !== null ? specificButtons : (settings.otp_message_buttons || []);
                    btns.forEach((btn: any) => {
                        m_obj.inline_keyboard.push([{ text: btn.text, url: btn.url }]);
                    });
                    return m_obj;
                };

                // 1. Forward to ALL OTP Groups (Global)
                const groupButtons = settings.group_buttons || {};
                for (const gId of (settings.otp_groups || [])) {
                    try {
                        const targetId = /^-?\d+$/.test(gId.toString()) ? parseInt(gId.toString()) : gId;
                        const specBtns = groupButtons[gId.toString()];
                        await bot.sendMessage(targetId, groupMsgBody, { 
                            parse_mode: 'HTML', 
                            reply_markup: getOtpMarkup(specBtns || null, code) 
                        });
                    } catch (forwardErr: any) {
                        console.error(`[OTP] Forward to group ${gId} failed:`, forwardErr.message || "Unknown Error");
                    }
                }

                // 2. Check if number belongs to a user and send to them
                const match = numbersData.find((n: any) => 
                    n.used && normalizeNumber(n.number) === normalizedApiNum
                ) as any;

                if (match && match.assignedTo) {
                    try {
                        const msgBody = `${serviceIcon} ${detectedService} <code>${normalizedApiNum}</code>`;
                        await bot.sendMessage(match.assignedTo, msgBody, { 
                            parse_mode: 'HTML', 
                            reply_markup: getOtpMarkup(null, code)
                        });
                        console.log(`[OTP] SUCCESS: Sent ${code} to user ${match.assignedTo}`);
                    } catch (sendErr: any) {
                        console.error(`[OTP] Send failed to user ${match.assignedTo}:`, sendErr.message || "Unknown Error");
                    }
                }

                processedMessages.add(msgId);
            }
        }
    } catch (err: any) {
        console.error("[OTP] Global fetch error:", err.message || "Network Error");
    }
}

// --- Server Setup ---

async function startServer() {
    const app = express();
    const PORT = 3000;

    app.use(express.json());

    // API Routes for Dashboard
    app.get('/api/stats', (req, res) => {
        try {
            const users = readJson("users.json");
            // Ensure at least one entry if empty for demo
            if (users.length === 0) {
                users.push({ uid: "8197284774", username: "asikisback16", joinedAt: new Date().toString() });
                writeJson("users.json", users);
            }
            const numbers = readJson("numbers.json");
            const files = readJson("files.json");
            const settings = getSettings();
            res.json({
                users: users.length,
                totalNumbers: numbers.length,
                availableNumbers: numbers.filter((n: any) => !n.used).length,
                assignedNumbers: numbers.filter((n: any) => n.used).length,
                files: files.length,
                settings: settings
            });
        } catch (err: any) {
            console.error("[API] Stats Error:", err.message);
            res.status(500).json({ error: "Internal Server Error", message: err.message });
        }
    });

    if (process.env.NODE_ENV !== "production") {
        const vite = await createViteServer({
            server: { middlewareMode: true },
            appType: "spa",
        });
        app.use(vite.middlewares);
    } else {
        const distPath = path.join(process.cwd(), 'dist');
        app.use(express.static(distPath));
        app.get('*', (req, res) => {
            res.sendFile(path.join(distPath, 'index.html'));
        });
    }

    app.listen(PORT, "0.0.0.0", () => {
        console.log(`Server running on http://localhost:${PORT}`);
        console.log(`Bot is running...`);
        
        // Start OTP Monitor
        setInterval(fetchOtps, 5000);
    });
}

startServer();
