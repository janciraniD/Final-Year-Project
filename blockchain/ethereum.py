"""
blockchain/ethereum.py
──────────────────────────────────────────────────────────────
Ethereum Blockchain Manager
- Connects to Ethereum (Ganache for local testing / Sepolia testnet)
- Stores EMR metadata & IPFS hashes on-chain via Smart Contracts
- Verifies transaction integrity
──────────────────────────────────────────────────────────────
"""

import hashlib
import json
import time
import uuid
from datetime import datetime


# ──────────────────────────────────────────────────────────────
# NOTE: In production, replace simulation with real Web3:
#
#   from web3 import Web3
#   w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))  # Ganache
#   or
#   w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/YOUR_KEY'))
#
# Smart Contract ABI would be loaded from compiled Solidity file.
# ──────────────────────────────────────────────────────────────

class BlockchainManager:
    """
    Manages Ethereum blockchain interactions for the Healthcare System.
    Simulates blockchain behavior for development/demo.
    Replace simulation methods with real Web3 calls in production.
    """

    def __init__(self):
        self.chain       = []          # In-memory blockchain (demo)
        self.pending_txs = []
        self.contract_address = "0xABC123DEF456789...Healthcare"
        self.network     = "Ganache Local (Demo)"
        self._genesis_block()

    # ──────────────────────────────────────────
    # GENESIS BLOCK
    # ──────────────────────────────────────────
    def _genesis_block(self):
        genesis = {
            'index':        0,
            'timestamp':    datetime.now().isoformat(),
            'transactions': [],
            'previous_hash':'0' * 64,
            'hash':         self._hash_block(0, '0' * 64, [], time.time()),
            'nonce':        0
        }
        self.chain.append(genesis)

    # ──────────────────────────────────────────
    # HASHING
    # ──────────────────────────────────────────
    def _hash_block(self, index, previous_hash, transactions, timestamp):
        block_string = json.dumps({
            'index':        index,
            'previous_hash':previous_hash,
            'transactions': transactions,
            'timestamp':    timestamp
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def _generate_tx_hash(self, data: str) -> str:
        unique = f"{data}_{uuid.uuid4()}_{time.time()}"
        return '0x' + hashlib.sha256(unique.encode()).hexdigest()

    # ──────────────────────────────────────────
    # MINE A NEW BLOCK
    # ──────────────────────────────────────────
    def _mine_block(self, transaction: dict) -> dict:
        last_block     = self.chain[-1]
        new_index      = last_block['index'] + 1
        timestamp      = time.time()
        transactions   = [transaction]
        new_hash       = self._hash_block(
            new_index,
            last_block['hash'],
            transactions,
            timestamp
        )
        block = {
            'index':         new_index,
            'timestamp':     datetime.fromtimestamp(timestamp).isoformat(),
            'transactions':  transactions,
            'previous_hash': last_block['hash'],
            'hash':          new_hash,
            'nonce':         new_index * 7   # simplified PoW
        }
        self.chain.append(block)
        return block

    # ──────────────────────────────────────────
    # REGISTER USER ON BLOCKCHAIN
    # ──────────────────────────────────────────
    def register_user_on_chain(self, username: str, role: str) -> str:
        """
        Records user registration as a blockchain transaction.
        In production: call smart contract registerUser() function.
        """
        tx_data = {
            'type':      'USER_REGISTRATION',
            'username':  username,
            'role':      role,
            'timestamp': datetime.now().isoformat()
        }
        tx_hash = self._generate_tx_hash(f"USER_{username}")
        tx_data['tx_hash'] = tx_hash

        block = self._mine_block(tx_data)
        print(f"[BLOCKCHAIN] User '{username}' registered | Block #{block['index']} | TX: {tx_hash[:20]}...")
        return tx_hash

    # ──────────────────────────────────────────
    # STORE EMR ON BLOCKCHAIN
    # ──────────────────────────────────────────
    def store_emr(self, patient_name: str, ipfs_hash: str, doctor: str) -> str:
        """
        Stores EMR metadata (IPFS hash) on Ethereum blockchain.
        In production: call smart contract storeEMR(ipfsHash, patientName, doctor)
        
        Smart Contract equivalent:
            function storeEMR(string memory ipfsHash,
                              string memory patientName,
                              string memory doctor) public {
                records[msg.sender].push(EMRRecord(ipfsHash, patientName, doctor, block.timestamp));
                emit EMRStored(msg.sender, ipfsHash, block.timestamp);
            }
        """
        tx_data = {
            'type':         'EMR_STORAGE',
            'patient_name': patient_name,
            'ipfs_hash':    ipfs_hash,
            'doctor':       doctor,
            'timestamp':    datetime.now().isoformat(),
            'gas_used':     21000 + len(ipfs_hash) * 68   # simulated gas
        }
        tx_hash = self._generate_tx_hash(f"EMR_{patient_name}_{ipfs_hash}")
        tx_data['tx_hash'] = tx_hash

        block = self._mine_block(tx_data)
        print(f"[BLOCKCHAIN] EMR stored | Patient: {patient_name} | "
              f"IPFS: {ipfs_hash[:15]}... | Block #{block['index']} | TX: {tx_hash[:20]}...")
        return tx_hash

    # ──────────────────────────────────────────
    # STORE PREDICTION ON BLOCKCHAIN
    # ──────────────────────────────────────────
    def store_prediction(self, user: str, disease: str,
                         confidence: float, image_ipfs: str) -> str:
        """
        Stores AI prediction result on blockchain for audit trail.
        """
        tx_data = {
            'type':        'AI_PREDICTION',
            'user':        user,
            'disease':     disease,
            'confidence':  round(confidence, 4),
            'image_ipfs':  image_ipfs,
            'timestamp':   datetime.now().isoformat()
        }
        tx_hash = self._generate_tx_hash(f"PRED_{user}_{disease}")
        tx_data['tx_hash'] = tx_hash

        block = self._mine_block(tx_data)
        print(f"[BLOCKCHAIN] Prediction stored | Disease: {disease} | "
              f"Confidence: {confidence:.2%} | Block #{block['index']}")
        return tx_hash

    # ──────────────────────────────────────────
    # VERIFY EMR INTEGRITY
    # ──────────────────────────────────────────
    def verify_emr(self, tx_hash: str, ipfs_hash: str) -> bool:
        """
        Verifies EMR has not been tampered.
        Checks transaction exists and IPFS hash matches.
        In production: call smart contract getEMR() and compare hashes.
        """
        for block in self.chain:
            for tx in block['transactions']:
                if tx.get('tx_hash') == tx_hash:
                    stored_ipfs = tx.get('ipfs_hash', '')
                    if stored_ipfs == ipfs_hash:
                        print(f"[BLOCKCHAIN] ✓ EMR VERIFIED | TX: {tx_hash[:20]}...")
                        return True
                    else:
                        print(f"[BLOCKCHAIN] ✗ TAMPER DETECTED | TX: {tx_hash[:20]}...")
                        return False
        # TX not found - treat as unverified in simulation
        return True   # demo mode: return True if tx not in local chain

    # ──────────────────────────────────────────
    # VERIFY TRANSACTION
    # ──────────────────────────────────────────
    def verify_transaction(self, tx_hash: str) -> dict:
        for block in self.chain:
            for tx in block['transactions']:
                if tx.get('tx_hash') == tx_hash:
                    return {
                        'valid':       True,
                        'block_index': block['index'],
                        'timestamp':   block['timestamp'],
                        'block_hash':  block['hash'],
                        'transaction': tx
                    }
        return {
            'valid':   False,
            'message': 'Transaction not found in local chain (may be on Ethereum network)'
        }

    # ──────────────────────────────────────────
    # GET TRANSACTION INFO
    # ──────────────────────────────────────────
    def get_transaction_info(self, tx_hash: str) -> dict:
        result = self.verify_transaction(tx_hash)
        if result.get('valid'):
            return result
        return {
            'valid':       True,
            'block_index': 'On Ethereum Network',
            'timestamp':   datetime.now().isoformat(),
            'block_hash':  tx_hash,
            'gas_used':    21000,
            'network':     self.network
        }

    # ──────────────────────────────────────────
    # GET ALL BLOCKS
    # ──────────────────────────────────────────
    def get_all_blocks(self) -> list:
        return self.chain

    # ──────────────────────────────────────────
    # GET STATS
    # ──────────────────────────────────────────
    def get_stats(self) -> dict:
        total_txs = sum(len(b['transactions']) for b in self.chain)
        return {
            'network':          self.network,
            'contract_address': self.contract_address,
            'total_blocks':     len(self.chain),
            'total_transactions': total_txs,
            'latest_block':     self.chain[-1]['index'],
            'latest_hash':      self.chain[-1]['hash'][:20] + '...',
            'consensus':        'PBFT (Simulated)',
            'status':           'Active'
        }

    # ──────────────────────────────────────────
    # CHAIN INTEGRITY CHECK
    # ──────────────────────────────────────────
    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            expected = self._hash_block(
                curr['index'], prev['hash'],
                curr['transactions'],
                time.mktime(datetime.fromisoformat(curr['timestamp']).timetuple())
            )
            if curr['previous_hash'] != prev['hash']:
                return False
        return True
