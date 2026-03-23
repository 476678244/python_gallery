"""Encryption utilities for SafeClaw"""

import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Encryption manager for sensitive data"""
    
    def __init__(self, password: str = None, salt: bytes = None):
        self.password = password or os.environ.get('SAFECLAW_ENCRYPTION_KEY', 'default_key')
        self.salt = salt or os.environ.get('SAFECLAW_SALT', b'default_salt')
        
        # Derive encryption key
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key(self) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        try:
            encrypted_data = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt dictionary data"""
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt dictionary data"""
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)
    
    def encrypt_file(self, file_path: str, output_path: str) -> bool:
        """Encrypt file contents"""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            encrypted_data = self.cipher.encrypt(file_data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            return True
        except Exception as e:
            logger.error(f"Error encrypting file {file_path}: {e}")
            return False
    
    def decrypt_file(self, encrypted_path: str, output_path: str) -> bool:
        """Decrypt file contents"""
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            return True
        except Exception as e:
            logger.error(f"Error decrypting file {encrypted_path}: {e}")
            return False

class HashManager:
    """Hash management for data integrity"""
    
    @staticmethod
    def hash_string(data: str, algorithm: str = "sha256") -> str:
        """Hash string data"""
        try:
            hash_func = getattr(hashlib, algorithm)()
            hash_func.update(data.encode())
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing data: {e}")
            raise
    
    @staticmethod
    def hash_file(file_path: str, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
        """Hash file contents"""
        try:
            hash_func = getattr(hashlib, algorithm)()
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            raise
    
    @staticmethod
    def verify_hash(data: str, expected_hash: str, algorithm: str = "sha256") -> bool:
        """Verify data hash"""
        try:
            actual_hash = HashManager.hash_string(data, algorithm)
            return actual_hash == expected_hash
        except Exception as e:
            logger.error(f"Error verifying hash: {e}")
            return False
    
    @staticmethod
    def verify_file_hash(file_path: str, expected_hash: str, algorithm: str = "sha256") -> bool:
        """Verify file hash"""
        try:
            actual_hash = HashManager.hash_file(file_path, algorithm)
            return actual_hash == expected_hash
        except Exception as e:
            logger.error(f"Error verifying file hash: {e}")
            return False

class SecureStorage:
    """Secure storage for sensitive configuration"""
    
    def __init__(self, storage_path: str, encryption_manager: EncryptionManager):
        self.storage_path = storage_path
        self.encryption_manager = encryption_manager
    
    def store(self, key: str, value: Any) -> bool:
        """Store encrypted value"""
        try:
            # Convert value to JSON
            if not isinstance(value, str):
                value = json.dumps(value)
            
            # Encrypt and store
            encrypted_value = self.encryption_manager.encrypt(value)
            
            # Store in memory (for now, could be extended to file storage)
            if not hasattr(self, '_storage'):
                self._storage = {}
            
            self._storage[key] = encrypted_value
            return True
        except Exception as e:
            logger.error(f"Error storing secure value for key {key}: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve and decrypt value"""
        try:
            if not hasattr(self, '_storage') or key not in self._storage:
                return None
            
            encrypted_value = self._storage[key]
            decrypted_value = self.encryption_manager.decrypt(encrypted_value)
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted_value)
            except json.JSONDecodeError:
                return decrypted_value
        except Exception as e:
            logger.error(f"Error retrieving secure value for key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete stored value"""
        try:
            if hasattr(self, '_storage') and key in self._storage:
                del self._storage[key]
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting secure value for key {key}: {e}")
            return False
    
    def list_keys(self) -> list:
        """List all stored keys"""
        if hasattr(self, '_storage'):
            return list(self._storage.keys())
        return []

class PasswordManager:
    """Password generation and validation utilities"""
    
    @staticmethod
    def generate_password(length: int = 12, use_symbols: bool = True, 
                         use_numbers: bool = True, use_uppercase: bool = True) -> str:
        """Generate secure password"""
        import random
        import string
        
        chars = string.ascii_lowercase
        if use_uppercase:
            chars += string.ascii_uppercase
        if use_numbers:
            chars += string.digits
        if use_symbols:
            chars += string.punctuation
        
        password = ''.join(random.choice(chars) for _ in range(length))
        return password
    
    @staticmethod
    def check_password_strength(password: str) -> Dict[str, Any]:
        """Check password strength"""
        import re
        
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters")
        
        if len(password) >= 12:
            score += 1
        else:
            feedback.append("Consider using 12+ characters for better security")
        
        # Character variety checks
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Include lowercase letters")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Include uppercase letters")
        
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("Include numbers")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("Include special characters")
        
        # Common patterns check
        if re.search(r'(.)\1{2,}', password):  # Repeated characters
            score -= 1
            feedback.append("Avoid repeated characters")
        
        if re.search(r'123|abc|qwe', password.lower()):  # Common sequences
            score -= 1
            feedback.append("Avoid common sequences")
        
        # Determine strength
        if score >= 5:
            strength = "Strong"
        elif score >= 3:
            strength = "Medium"
        else:
            strength = "Weak"
        
        return {
            "score": max(0, min(6, score)),
            "strength": strength,
            "feedback": feedback
        }

# Global instances
_default_encryption_manager = None
_default_hash_manager = HashManager()

def get_encryption_manager(password: str = None) -> EncryptionManager:
    """Get default encryption manager"""
    global _default_encryption_manager
    
    if _default_encryption_manager is None or password:
        _default_encryption_manager = EncryptionManager(password)
    
    return _default_encryption_manager

def get_hash_manager() -> HashManager:
    """Get default hash manager"""
    return _default_hash_manager

def quick_encrypt(data: str, password: str = None) -> str:
    """Quick encryption utility"""
    manager = get_encryption_manager(password)
    return manager.encrypt(data)

def quick_decrypt(encrypted_data: str, password: str = None) -> str:
    """Quick decryption utility"""
    manager = get_encryption_manager(password)
    return manager.decrypt(encrypted_data)

def quick_hash(data: str, algorithm: str = "sha256") -> str:
    """Quick hash utility"""
    return HashManager.hash_string(data, algorithm)
