from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

# Main menus
def main_menu():
    return ReplyKeyboardMarkup([
        ['🛍 Browse Products', 'ℹ️ Information'],
        ['📞 Support']
    ], resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup([
        ['➕ Add Product', '📊 View Orders'],
        ['📦 Available Products', '🏠 Main Menu']
    ], resize_keyboard=True)

# Product management
def product_management_keyboard(product_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Delete Product", callback_data=f"delete_{product_id}")]
    ])

# Payment confirmation
def payment_confirmation_keyboard(order_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{order_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order_id}")
        ]
    ])

def confirmation_keyboard(order_id, action):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"{action}_yes_{order_id}"),
            InlineKeyboardButton("❌ No", callback_data=f"{action}_no_{order_id}")
        ]
    ])

# Blockchain selection
def blockchain_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Polygon", callback_data="chain_polygon"),
            InlineKeyboardButton("Solana", callback_data="chain_solana"),
        ],
        [InlineKeyboardButton("Binance Smart Chain", callback_data="chain_bsc")]
    ])

# Token selection
def token_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("USDT", callback_data="token_USDT"),
            InlineKeyboardButton("USDC", callback_data="token_USDC")
        ]
    ])
