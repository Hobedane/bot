import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
    
    # Cryptocurrency addresses for different blockchains
    CRYPTO_ADDRESSES = {
        'polygon': os.getenv('POLYGON_ADDRESS'),
        'solana': os.getenv('SOLANA_ADDRESS'),
        'bsc': os.getenv('BSC_ADDRESS')
    }
    
    SUPPORTED_TOKENS = ['USDT', 'USDC']
    SUPPORTED_CHAINS = ['polygon', 'solana', 'bsc']

config = Config()
