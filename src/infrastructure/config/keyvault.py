import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class KeyVault:
    def __init__(self, keyvault_uri: str = None):
        if keyvault_uri is None:
            keyvault_uri = os.environ.get("KEYVAULTURI")
        
        if not keyvault_uri:
            raise ValueError("Key Vault URI is not provided. Please set the KEYVAULTURI environment variable.")
        
        self.credentials = DefaultAzureCredential()
        self.secret_client = SecretClient(
            keyvault_uri,
            self.credentials,
        )

    def get_secret(self, secret_name: str) -> str:
        """
        Get secret from Azure Key Vault

        Args:
            secret_name (str): Name of the secret

        Returns:
            str: Value of the secret
        """
        
        return self.secret_client.get_secret(secret_name).value

    def __del__(self):
        self.secret_client.close()
