from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from sqlalchemy.orm import Session
import bot.database as db
from bot.keyboards import admin_menu, product_management_keyboard, payment_confirmation_keyboard, confirmation_keyboard

# Conversation states for adding products
PRODUCT_NAME, PRODUCT_DESCRIPTION, PRODUCT_PRICE, PRODUCT_IMAGES, PRODUCT_COORDINATES = range(5)

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in context.bot_data['config'].ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized as admin.")
        return
    
    await update.message.reply_text(
        "👨‍💼 Admin Panel",
        reply_markup=admin_menu()
    )

async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Enter product name:")
    return PRODUCT_NAME

async def product_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product'] = {'name': update.message.text}
    await update.message.reply_text("📄 Enter product description:")
    return PRODUCT_DESCRIPTION

async def product_description_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product']['description'] = update.message.text
    await update.message.reply_text("💰 Enter product price (in USDT/USDC):")
    return PRODUCT_PRICE

async def product_price_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text)
        context.user_data['new_product']['price'] = price
        await update.message.reply_text("🖼 Please send the first image for this product:")
        return PRODUCT_IMAGES
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number for the price:")
        return PRODUCT_PRICE

async def product_images_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        # Store the largest photo
        photo_file = await update.message.photo[-1].get_file()
        image_path = f"data/images/{update.effective_user.id}_{len(context.user_data.get('images', []))}.jpg"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        await photo_file.download_to_drive(image_path)
        
        if 'images' not in context.user_data:
            context.user_data['images'] = []
        context.user_data['images'].append(image_path)
        
        if len(context.user_data['images']) == 1:
            await update.message.reply_text("🖼 Now send the second image:")
            return PRODUCT_IMAGES
        else:
            await update.message.reply_text("📍 Now send the coordinates (format: latitude,longitude):")
            return PRODUCT_COORDINATES
    else:
        await update.message.reply_text("❌ Please send an image:")
        return PRODUCT_IMAGES

async def product_coordinates_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product']['coordinates'] = update.message.text
    context.user_data['new_product']['image1_path'] = context.user_data['images'][0]
    context.user_data['new_product']['image2_path'] = context.user_data['images'][1]
    
    # Save product to database
    with db.SessionLocal() as session:
        new_product = db.Product(**context.user_data['new_product'])
        session.add(new_product)
        session.commit()
    
    # Clear temporary data
    context.user_data.pop('new_product')
    context.user_data.pop('images')
    
    await update.message.reply_text("✅ Product added successfully!", reply_markup=admin_menu())
    return ConversationHandler.END

async def view_pending_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in context.bot_data['config'].ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized.")
        return
    
    with db.SessionLocal() as session:
        pending_orders = session.query(db.Order).filter(db.Order.status == 'pending').all()
        
        if not pending_orders:
            await update.message.reply_text("📭 No pending orders.")
            return
        
        for order in pending_orders:
            product = session.query(db.Product).filter(db.Product.id == order.product_id).first()
            message = (
                f"🔄 Pending Order #{order.id}\n"
                f"Product: {product.name}\n"
                f"Price: {product.price} {order.payment_token}\n"
                f"Blockchain: {order.blockchain}\n"
                f"Customer: @{order.customer_username}\n"
                f"Crypto Address: {order.customer_crypto_address}\n"
                f"Transaction Hash: {order.transaction_hash or 'Not provided'}"
            )
            await update.message.reply_text(
                message,
                reply_markup=payment_confirmation_keyboard(order.id)
            )

async def handle_payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    order_id = int(data.split('_')[1])
    
    if data.startswith('confirm_'):
        await query.edit_message_text(
            "Are you sure you want to CONFIRM this payment?",
            reply_markup=confirmation_keyboard(order_id, 'confirm')
        )
    elif data.startswith('reject_'):
        await query.edit_message_text(
            "Are you sure you want to REJECT this payment?",
            reply_markup=confirmation_keyboard(order_id, 'reject')
        )

async def handle_final_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    parts = data.split('_')
    action = parts[0]  # confirm or reject
    confirmation = parts[1]  # yes or no
    order_id = int(parts[2])
    
    if confirmation == 'no':
        await query.edit_message_text("❌ Action cancelled.")
        return
    
    with db.SessionLocal() as session:
        order = session.query(db.Order).filter(db.Order.id == order_id).first()
        product = session.query(db.Product).filter(db.Product.id == order.product_id).first()
        
        if action == 'confirm':
            order.status = 'confirmed'
            order.admin_id = query.from_user.id
            order.confirmed_at = db.datetime.now()
            
            # Mark product as sold
            product.is_available = False
            
            session.commit()
            
            # Send digital goods to customer
            try:
                await context.bot.send_message(
                    chat_id=order.customer_id,
                    text=f"✅ Your payment has been confirmed! Here are your purchased items:\n\nProduct: {product.name}"
                )
                # Send first image
                with open(product.image1_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=order.customer_id,
                        photo=photo,
                        caption="📸 Image 1 of your purchase"
                    )
                # Send second image
                with open(product.image2_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=order.customer_id,
                        photo=photo,
                        caption="📸 Image 2 of your purchase"
                    )
                # Send coordinates
                await context.bot.send_message(
                    chat_id=order.customer_id,
                    text=f"📍 Coordinates: {product.coordinates}"
                )
                
                order.status = 'completed'
                session.commit()
                
            except Exception as e:
                print(f"Error sending digital goods: {e}")
            
            await query.edit_message_text("✅ Payment confirmed and digital goods sent to customer!")
            
        elif action == 'reject':
            order.status = 'rejected'
            order.admin_id = query.from_user.id
            session.commit()
            
            # Notify customer
            try:
                await context.bot.send_message(
                    chat_id=order.customer_id,
                    text="❌ Your payment was rejected by admin. Please contact support."
                )
            except Exception as e:
                print(f"Error notifying customer: {e}")
            
            await query.edit_message_text("❌ Payment rejected and customer notified.")
