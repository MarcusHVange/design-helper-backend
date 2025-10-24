import sys
from dotenv import load_dotenv
import os
from src.infrastructure.config.keyvault import KeyVault
sys.path.append("./")

load_dotenv(override=True)

key_vault = None
if os.environ.get("KEYVAULTURI"):
    try:
        key_vault = KeyVault()
        print("Key Vault client created successfully")
    except Exception as e:
        print(f"Warning: Could not create Key Vault client")
        print("Falling back to environment variables...")
        key_vault = None

def get_setting(setting_name: str) -> str:
    """
    Get setting from Key Vault or environment variable as fallback.
    """
    # Try Key Vault first if available
    if key_vault:
        try:
            return key_vault.get_secret(setting_name)
        except Exception:
            print(f"Warning: Could not get {setting_name} from Key Vault")
    
    # Fallback to environment variable with the same name
    env_value = os.environ.get(setting_name)
    if env_value:
        return env_value
    
    print(f"Warning: Could not find {setting_name} in Key Vault or environment")
    return ""

class AppConfig():
    AZURE_FOUNDRY_API_KEY: str = get_setting("AZURE-FOUNDRY-API-KEY")
    AI_SEARCH_ENDPOINT: str = get_setting("AI-SEARCH-ENDPOINT")
    AI_SEARCH_KEY: str = get_setting("AI-SEARCH-KEY")
    AZURE_BLOB_STORAGE_CONNECTION_STRING: str = get_setting("AZURE-BLOB-STORAGE-CONNECTION-STRING")