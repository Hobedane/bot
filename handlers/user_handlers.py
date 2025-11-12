from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from sqlalchemy.orm import Session
import bot.database as db
from bot.keyboards import main_menu, blockchain_keyboard, token_keyboard
from bot.config import config

# Conversation states for ordering
CUSTOMER_CRYPTO_ADDRESS, TRANSACTION_HASH = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛍 Welcome to Crypto Shop Bot!\n\n"
        "Browse available products and pay with USDT/USDC on Polygon, Solana, or BSC networks.",
        reply_markup=main_menu()
    )

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with db.SessionLocal() as session:
        products = session.query(db.Product).filter(db.Product.is_available == True).all()
        
        if not products:
            await update.message.reply_text("📭 No products available at the moment.")
            return
        
        for product in products:
            message = (
                f"🏷 {product.name}\n"
                f"📄 {product.description}\n"
                f"💰 Price: {product.price} USDT/USDC\n"
            )
            
            keyboard = [[{"text": "🛒 Buy This Product", "callback_data": f"buy_{product.id}"}]]
            await update.message.reply_text(message, reply_markup={"inline_keyboard": keyboard})

async def show_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_text = (
        "ℹ️ Important Information\n\n"
        "💳 Payment Methods:\n"
        "• USDT or USDC tokens only\n"
        "• Supported blockchains: Polygon, Solana, BSC\n\n"
        "🔄 Payment Process:\n"
        "1. Select product and payment method\n"
        "2. Provide your crypto address\n"
        "3. Make payment to our address\n"
        "4. Admin manually verifies transaction\n"
        "5. Receive digital goods after confirmation\n\n"
        "⏱ Processing Time: Manual verification may take some time\n"
        "📞 Contact support if you have issues"
    )
    await update.message.reply_text(info_text)

async def handle_buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[1])
    context.user_data['order_product_id'] = product_id
    
    await query.edit_message_text(
        "Select blockchain network:",
        reply_markup=blockchain_keyboard()
    )

async def handle_blockchain_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    blockchain = query.data.split('_')[1]
    context.user_data['order_blockchain'] = blockchain
    
    await query.edit_message_text(
        "Select payment token:",
        reply_markup=token_keyboard()
    )

async def handle_token_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    token = query.data.split('_')[1]
    context.user_data['order_token'] = token
    
    # Show payment address and request customer's address
    blockchain = context.user_data['order_blockchain']
    payment_address = config.CRYPTO_ADDRESSES[blockchain]
    
    with db.SessionLocal() as session:
        product = session.query(db.Product).filter(db.Product.id == context.user_data['order_product_id']).first()
    
    payment_instructions = (
        f"💳 Payment Instructions\n\n"
        f"Product: {product.name}\n"
        f"Amount: {product.price} {token}\n"
        f"Blockchain: {blockchain.upper()}\n"
        f"Send to: `{payment_address}`\n\n"
        f"⚠️ Important:\n"
        f"• Send exact amount\n"
        f"• Use only {blockchain.upper()} network\n"
        f"• Keep transaction hash\n\n"
        f"Now please provide YOUR crypto address (where we can verify the payment came from):"
    )
    
    await query.edit_message_text(
        payment_instructions,
        parse_mode='Markdown'
    )
    
    return CUSTOMER_CRYPTO_ADDRESS

async def receive_customer_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['customer_crypto_address'] = update.message.text
    
    await update.message.reply_text(
        "📝 Now please provide the transaction hash (if you've already made payment), or type 'skip' to provide it later:"
    )
    
    return TRANSACTION_HASH

async def receive_transaction_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    transaction_hash = update.message.text if update.message.text.lower() != 'skip' else None
    
    # Create order in database
    with db.SessionLocal() as session:
        new_order = db.Order(
            product_id=context.user_data['order_product_id'],
            customer_id=update.effective_user.id,
            customer_username=update.effective_user.username,
            customer_crypto_address=context.user_data['customer_crypto_address'],
            payment_token=context.user_data['order_token'],
            blockchain=context.user_data['order_blockchain'],
            transaction_hash=transaction_hash
        )
        session.add(new_order)
        session.commit()
        order_id = new_order.id
    
    # Notify admins
    product = session.query(db.Product).filter(db.Product.id == context.user_data['order_product_id']).first()
    
    admin_message = (
        f"🔄 New Pending Order #{order_id}\n"
        f"Product: {product.name}\n"
        f"Customer: @{update.effective_user.username}\n"
        f"Amount: {product.price} {context.user_data['order_token']}\n"
        f"Blockchain: {context.user_data['order_blockchain']}\n"
        f"Customer Address: {context.user_data['customer_crypto_address']}\n"
        f"Transaction Hash: {transaction_hash or 'Not provided'}"
    )
    
    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                reply_markup=payment_confirmation_keyboard(order_id)
            )
        except Exception as e:
            print(f"Could not notify admin {admin_id}: {e}")
    
    await update.message.reply_text(
        "✅ Order created! Admin has been notified and will verify your payment. "
        "You'll receive your digital goods once payment is confirmed.",
        reply_markup=main_menu()
    )
    
    # Clear conversation data
    context.user_data.pop('order_product_id')
    context.user_data.pop('order_blockchain')
    context.user_data.pop('order_token')
    context.user_data.pop('customer_crypto_address')
    
    return ConversationHandler.END
