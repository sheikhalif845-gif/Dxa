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
const BOT_TOKEN = process.env.BOT_TOKEN || "8332473503:AAEvyS-iBhm6eVp1VdEMYpTLhX5KEUu0WxQ";
const ADMIN_ID = parseInt(process.env.ADMIN_ID || "8197284774");
const bot = new TelegramBot(BOT_TOKEN, { polling: true });

const FORCE_JOIN_CHANNELS = [
    { name: "DXA Universe", url: "https://t.me/dxa_universe", username: "@dxa_universe" },
    { name: "Developer X Asik", url: "https://t.me/developer_x_asik", username: "@developer_x_asik" }
];

const PREMIUM_EMOJIS = {
    "FIRE": "5337267511261960341", "HELLO": "5353027129250453493", "DXA": "5334763399299506604",
    "DONE": "5352694861990501856", "NUMBER": "5337132498965010628", "SUPPORT": "5337302974806922068",
    "ADMIN": "5353032893096567467", "USER": "5352861489541714456", "FILE": "5352721946054268944",
    "NUMBERS": "5352862640592949843", "ROCKET": "5352597830089347330", "GRAPH": "5352877703043258544",
    "UPLOAD": "5353001161878182134", "BROADCAST": "5352980533150259581", "PIN": "5352922460897452503",
    "DOT": "5352638632278660622", "N1": "5352651766288652742", "N2": "5355186458418257716",
    "N3": "5352867219028091093", "WAIT": "5336983442125001376", "CLOSE": "5336997731481193790"
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

// --- Helper Functions ---
async function checkForceJoin(userId: number) {
    for (const channel of FORCE_JOIN_CHANNELS) {
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
    if (userId === ADMIN_ID) {
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

    const isJoined = await checkForceJoin(userId);
    if (!isJoined) {
        const inline_keyboard: TelegramBot.InlineKeyboardButton[][] = FORCE_JOIN_CHANNELS.map(c => [
            { text: `Join ${c.name}`, url: c.url }
        ]);
        inline_keyboard.push([{ text: "Joined ✅", callback_data: "check_join" }]);
        
        await bot.sendMessage(msg.chat.id, "You must join our channels to use this bot:", {
            reply_markup: { inline_keyboard }
        });
        return;
    }

    const welcomeText = 
        `${e("🔥", PREMIUM_EMOJIS.FIRE)} DXA NUMBER BOT ${e("🔥", PREMIUM_EMOJIS.FIRE)}\n` +
        `━━━━━━━━━━━\n` +
        `${e("👋", PREMIUM_EMOJIS.HELLO)} Hello, <b>${msg.from?.first_name}</b>! Welcome To DXA UNIVERSE.\n\n` +
        `${e("📌", PREMIUM_EMOJIS.PIN)} Tap Get Number to start!\n` +
        `━━━━━━━━━━━\n` +
        `${e("😒", PREMIUM_EMOJIS.DXA)} POWERED BY DXA UNIVERSE`;

    await bot.sendMessage(msg.chat.id, welcomeText, {
        parse_mode: 'HTML',
        reply_markup: getMainButtons(userId)
    });
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

bot.on('message', async (msg) => {
    if (!msg.text || !msg.from) return;
    const userId = msg.from.id;
    const chatId = msg.chat.id;

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
            `${e("🔥", PREMIUM_EMOJIS.FIRE)} DXA SUPPORT CENTER ${e("🔥", PREMIUM_EMOJIS.FIRE)}\n` +
            `━━━━━━━━━━━\n` +
            `${e("👋", PREMIUM_EMOJIS.HELLO)} Hello, <b>${msg.from.first_name}</b>! Tell Me How Can I Help You.\n\n` +
            `${e("📌", PREMIUM_EMOJIS.PIN)} Tap Support Button to Contact The Admin!\n` +
            `━━━━━━━━━━━\n` +
            `${e("😒", PREMIUM_EMOJIS.DXA)} POWERED BY DXA UNIVERSE`;

        const reply_markup = {
            inline_keyboard: [
                [{ text: "💬 Support Center", url: "https://t.me/asik_x_bd_bot" }],
                [{ text: "🔙 Back", callback_data: "close_menu" }]
            ]
        };
        const sent = await bot.sendMessage(chatId, supportText, { parse_mode: 'HTML', reply_markup });
        lastMenus.set(userId, sent.message_id);
    } else if (msg.text === "👑 Admin Panel" && userId === ADMIN_ID) {
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
        [{ text: "📤 Upload Numbers", callback_data: "admin_upload" }],
        [{ text: "🗑 Delete Files", callback_data: "admin_delete_files" }],
        [{ text: "📢 Broadcast", callback_data: "admin_broadcast" }],
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

        const text = 
            `${e("✅", PREMIUM_EMOJIS.DONE)} <b>NUMBERS ALLOCATED</b>\n` +
            `━━━━━━━━━━━━━━\n` +
            ` ${e("🔹", PREMIUM_EMOJIS.DOT)} Service: <b>${service}</b>\n` +
            ` ${e("📍", PREMIUM_EMOJIS.PIN)} Country: <b>${country}</b>\n` +
            `━━━━━━━━━━━━━━\n` +
            formatted.join("\n") + "\n" +
            `━━━━━━━━━━━━━━\n` +
            `${e("😒", PREMIUM_EMOJIS.DXA)} POWERED BY DXA UNIVERSE`;

        const inline_keyboard = [
            [{ text: "🔄 Change Number", callback_data: `sel_country:${service}:${country}` }],
            [{ text: "💬 OTP Group", url: "https://t.me/dxaotpzone" }],
            [{ text: "🔙 Back", callback_data: "back_to_services" }]
        ];

        await bot.editMessageText(text, {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard }
        });
    } else if (data === "admin_upload") {
        await bot.editMessageText(`${e("📤", PREMIUM_EMOJIS.UPLOAD)} <b>UPLOAD NUMBERS</b>\n━━━━━━━━━━━━━\nPlease send the .txt file containing numbers.`, {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'HTML',
            reply_markup: {
                inline_keyboard: [[{ text: "🔙 Back", callback_data: "admin_panel_back" }]]
            }
        });
        bot.once('document', async (docMsg) => {
            if (!docMsg.document || !docMsg.document.file_name?.endsWith(".txt")) {
                await bot.sendMessage(chatId, "❌ Please send a valid .txt file.");
                return;
            }
            const fileMsg = await bot.sendMessage(chatId, `${e("🔹", PREMIUM_EMOJIS.DOT)} Enter Service Name:`, { parse_mode: 'HTML' });
            bot.once('text', async (serviceMsg) => {
                const service = serviceMsg.text;
                const countryMsg = await bot.sendMessage(chatId, `${e("📍", PREMIUM_EMOJIS.PIN)} Enter Country Name:`, { parse_mode: 'HTML' });
                bot.once('text', async (countryMsgResp) => {
                    const country = countryMsgResp.text!;
                    const statusMsg = await bot.sendMessage(chatId, `${e("⏳", PREMIUM_EMOJIS.WAIT)} Processing file...`, { parse_mode: 'HTML' });
                    
                    try {
                        const fileLink = await bot.getFileLink(docMsg.document!.file_id);
                        const response = await fetch(fileLink);
                        const text = await response.text();
                        const lines = text.split(/\r?\n/).filter(l => l.trim() !== "");
                        
                        const numbers = readJson("numbers.json");
                        const files = readJson("files.json");
                        const fileId = Date.now().toString();
                        
                        files.push({ id: fileId, fileName: docMsg.document!.file_name, service, country, count: lines.length });
                        lines.forEach(line => {
                            numbers.push({
                                id: Math.random().toString(36).substr(2, 9),
                                number: line.trim(),
                                service,
                                country,
                                used: false,
                                fileId
                            });
                        });
                        
                        writeJson("numbers.json", numbers);
                        writeJson("files.json", files);
                        
                        await bot.deleteMessage(chatId, statusMsg.message_id);
                        await bot.sendMessage(chatId, `${e("✅", PREMIUM_EMOJIS.DONE)} Success! ${lines.length} numbers added.`, { parse_mode: 'HTML' });
                    } catch (err: any) {
                        await bot.sendMessage(chatId, `❌ Error: ${err.message}`);
                    }
                });
            });
        });
    } else if (data === "admin_broadcast") {
        await bot.editMessageText(`${e("📢", PREMIUM_EMOJIS.BROADCAST)} <b>BROADCAST MESSAGE</b>\n━━━━━━━━━━━━━\nSend the message to broadcast:`, {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'HTML',
            reply_markup: {
                inline_keyboard: [[{ text: "🔙 Back", callback_data: "admin_panel_back" }]]
            }
        });
        bot.once('message', async (bcMsg) => {
            const users = readJson("users.json");
            let count = 0;
            const statusMsg = await bot.sendMessage(chatId, `${e("📢", PREMIUM_EMOJIS.BROADCAST)} Broadcasting...`, { parse_mode: 'HTML' });
            
            for (const u of users) {
                try {
                    await bot.copyMessage(u.uid, chatId, bcMsg.message_id);
                    count++;
                } catch {}
            }
            await bot.editMessageText(`${e("✅", PREMIUM_EMOJIS.DONE)} Broadcast complete! Sent to ${count} users.`, {
                chat_id: chatId,
                message_id: statusMsg.message_id,
                parse_mode: 'HTML'
            });
        });
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
        const now = Date.now();
        
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
            
            const match = numbersData.find((n: any) => {
                if (!n.used || !n.assignedTo) return false;
                const normalizedDbNum = normalizeNumber(n.number);
                
                return normalizedDbNum === normalizedApiNum || 
                       normalizedDbNum.endsWith(normalizedApiNum) || 
                       normalizedApiNum.endsWith(normalizedDbNum);
            });

            if (match) {
                const isoTimestamp = timestamp.includes(' ') ? timestamp.replace(' ', 'T') : timestamp;
                const messageTime = new Date(isoTimestamp).getTime();
                
                // Debug log for every potential match
                console.log(`[OTP] Found Match! Num: ${normalizedApiNum}, User: ${match.assignedTo}, Msg: ${content}`);

                // Relaxed timestamp check to 24 hours to handle potential timezone differences between API and server.
                if (!isNaN(messageTime) && messageTime < (match.assignedAt - 86400000)) {
                    console.log(`[OTP] Rejected: Too old. MsgTime: ${messageTime}, AssignedAt: ${match.assignedAt}`);
                    processedMessages.add(msgId);
                    continue;
                }

                // IMPROVED OTP EXTRACTION:
                // 1. Try 3-3 format (123-456 or 123 456)
                // 2. Try 4-8 consecutive digits (ignoring \b to handle cases like 1234n)
                const otpMatch = content.match(/\d{3}[- ]\d{3}/) || content.match(/\d{4,8}/);
                let code = otpMatch ? otpMatch[0] : "";

                if (!code) {
                   console.log(`[OTP] Rejected: No code found in content: "${content}"`);
                   processedMessages.add(msgId);
                   continue;
                }

                const flagKey = (match.country || "").toString().toLowerCase();
                const flag = COUNTRY_FLAGS[flagKey] || "📱";

                // Get service specific premium emoji
                const serviceKey = service.toString().toUpperCase().replace(/\s+/g, '');
                const premium = APP_EMOJIS[serviceKey] || (serviceKey === 'ROCKET' ? APP_EMOJIS['ROCKET_APP'] : null);
                
                let serviceIcon;
                if (premium) {
                    serviceIcon = e(premium[0], premium[1]);
                } else {
                    // Default premium emoji for unknown services as requested
                    serviceIcon = e("💬", "5337302974806922068");
                }

                // Format: Icon Service Number
                const msgBody = `${serviceIcon} <b>${service}</b>  <code>${normalizedApiNum}</code>`;

                const reply_markup = {
                    inline_keyboard: [
                        [{ 
                            text: `📋 ${code}`, 
                            copy_text: { text: code } 
                        } as any]
                    ]
                };

                try {
                    await bot.sendMessage(match.assignedTo, msgBody, { 
                        parse_mode: 'HTML', 
                        reply_markup 
                    });
                    processedMessages.add(msgId);
                    console.log(`[OTP] SUCCESS: Sent ${code} to ${match.assignedTo}`);
                } catch (sendErr) {
                    console.error(`[OTP] Send failed to ${match.assignedTo}:`, sendErr);
                }
            }
        }
    } catch (err) {
        console.error("[OTP] Global fetch error:", err);
    }
}

// --- Server Setup ---

async function startServer() {
    const app = express();
    const PORT = 3000;

    app.use(express.json());

    // API Routes for Dashboard
    app.get('/api/stats', (req, res) => {
        const users = readJson("users.json");
        const numbers = readJson("numbers.json");
        const files = readJson("files.json");
        res.json({
            users: users.length,
            totalNumbers: numbers.length,
            availableNumbers: numbers.filter((n: any) => !n.used).length,
            assignedNumbers: numbers.filter((n: any) => n.used).length,
            files: files.length
        });
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
