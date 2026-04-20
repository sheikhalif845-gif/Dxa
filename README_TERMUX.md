# Termux Setup Guide for DXA Number Bot

Follow these steps to run the bot on your Termux (Android).

## 1. Install Required Packages
Open Termux and run:
```bash
pkg update && pkg upgrade -y
pkg install nodejs -y
```

## 2. Setup the Bot Folder
Move the bot files to your Termux directory and enter the folder:
```bash
cd /path/to/your/bot-folder
```

## 3. Install NPM Dependencies
```bash
npm install
```

## 4. Configure Environment Variables
Create a `.env` file and add your tokens:
```bash
nano .env
```
Paste these values (replace with your own if needed):
```env
BOT_TOKEN=8332473503:AAEvyS-iBhm6eVp1VdEMYpTLhX5KEUu0WxQ
ADMIN_ID=8197284774
OTP_API_URL=http://147.135.212.197/crapi/st/viewstats
OTP_API_TOKEN=R1dPQUFBUzSLhmRod3SLV0OYhHxKbWeEWHdqfYl_eVhTU5RzWGZogQ==
```
Press `CTRL+O` then `ENTER` to save, and `CTRL+X` to exit.

## 5. Run the Bot
To start the bot, run:
```bash
npm start
```

## Scalability Note
The bot uses a JSON database (`numbers.json`). This works perfectly for hundreds of users. For thousands of concurrent users, the bot is optimized to process OTPs efficiently by matching numbers assigned to specific user IDs.

## Keep Bot Running (Optional)
To keep the bot running even after closing Termux, use `pm2`:
```bash
npm install -g pm2
pm2 start npm --name "dxa-bot" -- start
```
