#!/bin/bash

# Script untuk membersihkan token Telegram dari Git history
# Gunakan sebelum membuat commit baru

echo "🔐 Membersihkan token Telegram dari konfigurasi..."
echo "⚠️  PERINGATAN: Ini hanya membersihkan dari file saat ini, bukan dari history git!"
echo ""

# Cek apakah ada token di .env
if [ -f ".env" ]; then
    echo "🔍 Memeriksa file .env..."
    if grep -q "TELEGRAM_BOT_TOKEN=" .env && ! grep -q "TELEGRAM_BOT_TOKEN=your_bot_token_here\|TELEGRAM_BOT_TOKEN=\$TELEGRAM_BOT_TOKEN\|TELEGRAM_BOT_TOKEN=REDACTED" .env; then
        echo "⚠️  Token ditemukan di .env, membersihkan..."
        sed -i 's/^TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=REDACTED/' .env
        echo "✅ Token di .env telah dibersihkan"
    else
        echo "✅ Tidak ada token sensitif di .env"
    fi
else
    echo "⚠️  File .env tidak ditemukan"
fi

# Buat file .env.secure jika belum ada
if [ ! -f ".env.secure" ]; then
    echo "🔐 Membuat .env.secure template..."
    cat > .env.secure << 'EOF'
# Environment variables for LibraryDown
# ⚠️ JANGAN COMMIT FILE INI KE GIT!
# Gunakan .env untuk lokal development
# Gunakan sistem environment variable untuk production

# Telegram Bot Configuration (LOCAL ONLY)
# Hapus dari sini sebelum deploy ke production
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
TELEGRAM_USER_ID=your_user_id_here

# Production environment variables should be set via system environment
# atau secrets management system
EOF
    echo "✅ File .env.secure template telah dibuat"
fi

# Pastikan .env.secure di .gitignore
if ! grep -q ".env.secure" .gitignore; then
    echo ".env.secure" >> .gitignore
    echo "✅ .env.secure ditambahkan ke .gitignore"
fi

echo ""
echo "📋 LANGKAH-LANGKAH SELANJUTNYA:"
echo "1. SEGERA RESET bot token Anda di @BotFather dengan perintah /revoke"
echo "2. Buat bot baru dan dapatkan token baru"
echo "3. JANGAN SIMPAN token di file yang akan di-commit"
echo "4. Gunakan environment variable untuk production"
echo ""
echo "🔐 Untuk development lokal, gunakan cara berikut:"
echo "   export TELEGRAM_BOT_TOKEN='token_anda_disini'"
echo "   export TELEGRAM_USER_ID='user_id_anda_disini'"
echo "   ./start_bot.sh"
echo ""