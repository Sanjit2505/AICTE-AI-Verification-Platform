import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration (MySQL 8.0)
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "sanjit25")
MYSQL_DB = os.getenv("MYSQL_DB", "aicte_trust_layer")

# Application Settings
SECRET_KEY = os.getenv("SECRET_KEY", "aicte-trust-layer-secret-key-2026-v1")
ALGORITHM = "HS256"
BLOCKCHAIN_CHAIN_NAME = "Polygon Amoy Testnet (Simulated Hash Anchor)"
BLOCKCHAIN_CONTRACT_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
