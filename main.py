import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from bot import config
from bot.handlers import admin_handlers, user_handlers
from bot.keyboards import main_menu
import bot.database as db

def main():
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Store config in bot data for access in handlers
    application.bot_data['config'] = config
    
    # Admin command handlers
    application.add_handler(CommandHandler("admin", admin_handlers.admin_start))
    
    # Admin conversation handler for adding products
    admin_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^➕ Add Product$'), admin_handlers.add_product_start)],
        states={
            admin_handlers.PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.product_name_received)],
            admin_handlers.PRODUCT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.product_description_received)],
            admin_handlers.PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.product_price_received)],
            admin_handlers.PRODUCT_IMAGES: [MessageHandler(filters.PHOTO, admin_handlers.product_images_received)],
            admin_handlers.PRODUCT_COORDINATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.product_coordinates_received)],
        },
        fallbacks=[]
    )
    application.add_handler(admin_conv_handler)
    
    # Admin order management
    application.add_handler(MessageHandler(filters.Regex('^📊 View Orders$'), admin_handlers.view_pending_orders))
    application.add_handler(CallbackQueryHandler(admin_handlers.handle_payment_confirmation, pattern='^(confirm|reject)_'))
    application.add_handler(CallbackQueryHandler(admin_handlers.handle_final_confirmation, pattern='^(confirm|reject)_(yes|no)_'))
    
    # User command handlers
    application.add_handler(CommandHandler("start", user_handlers.start))
    application.add_handler(MessageHandler(filters.Regex('^🛍 Browse Products$'), user_handlers.show_products))
    application.add_handler(MessageHandler(filters.Regex('^ℹ️ Information$'), user_handlers.show_info))
    application.add_handler(MessageHandler(filters.Regex('^📞 Support$'), lambda u, c: u.message.reply_text("Contact support for help.")))
    application.add_handler(MessageHandler(filters.Regex('^🏠 Main Menu$'), user_handlers.start))
    
    # User product browsing and buying
    application.add_handler(CallbackQueryHandler(user_handlers.handle_buy_product, pattern='^buy_'))
    application.add_handler(CallbackQueryHandler(user_handlers.handle_blockchain_selection, pattern='^chain_'))
    application.add_handler(CallbackQueryHandler(user_handlers.handle_token_selection, pattern='^token_'))
    
    # User order conversation handler
    user_order_conv_handler = ConversationHandler(
        entry_points=[],
        states={
            user_handlers.CUSTOMER_CRYPTO_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.receive_customer_address)],
            user_handlers.TRANSACTION_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.receive_transaction_hash)],
        },
        fallbacks=[],
        map_to_parent={}
    )
    application.add_handler(user_order_conv_handler)
    
    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
