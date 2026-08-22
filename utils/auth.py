"""utils/auth.py – User Authentication Manager"""

import hashlib
import os


class AuthManager:
    def __init__(self):
        self._users = {}   # backed by DatabaseManager in production

    def _hash_password(self, password: str, salt: str = None) -> tuple:
        if not salt:
            salt = os.urandom(16).hex()
        hashed = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return hashed, salt

    def register_user(self, username: str, password: str,
                      email: str, role: str) -> dict:
        if username in self._users:
            return {'success': False, 'message': 'Username already exists'}
        hashed, salt = self._hash_password(password)
        self._users[username] = {
            'id':       len(self._users) + 1,
            'username': username,
            'email':    email,
            'role':     role,
            'password': hashed,
            'salt':     salt
        }
        return {'success': True, 'message': 'Registered successfully'}

    def verify_user(self, username: str, password: str) -> dict:
        user = self._users.get(username)
        if not user:
            return {'success': False, 'message': 'User not found'}
        hashed, _ = self._hash_password(password, user['salt'])
        if hashed == user['password']:
            return {'success': True, 'user': user}
        return {'success': False, 'message': 'Invalid password'}
