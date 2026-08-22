"""
blockchain/ipfs_handler.py
──────────────────────────────────────────────────────────────
IPFS (InterPlanetary File System) Handler
- Uploads encrypted EMR data to IPFS
- Retrieves data via content-addressed hash (CID)
- Simulates IPFS in demo mode; use real IPFS node in production
──────────────────────────────────────────────────────────────
"""

import hashlib
import json
import base64
import os
from datetime import datetime


# ──────────────────────────────────────────────────────────────
# NOTE: For production IPFS integration, use:
#
#   import ipfshttpclient
#   client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
#   result = client.add_bytes(data)
#   ipfs_hash = result['Hash']
#
# Or use Pinata Cloud API:
#   import requests
#   headers = {"pinata_api_key": YOUR_KEY, "pinata_secret_api_key": SECRET}
#   response = requests.post("https://api.pinata.cloud/pinning/pinFileToIPFS", ...)
#   ipfs_hash = response.json()['IpfsHash']
# ──────────────────────────────────────────────────────────────

class IPFSHandler:
    """
    Handles IPFS storage operations for the Healthcare System.
    Stores encrypted EMR data in a decentralized, content-addressed way.
    Demo mode uses local simulation; replace with real IPFS in production.
    """

    def __init__(self):
        self._storage    = {}            # In-memory IPFS simulation
        self._file_store = {}            # For binary file storage
        self.node_url    = "http://127.0.0.1:5001"  # Local IPFS node
        self.gateway     = "https://ipfs.io/ipfs/"  # Public gateway
        self.is_demo     = True          # Set False for real IPFS

    # ──────────────────────────────────────────
    # GENERATE IPFS-STYLE CID
    # ──────────────────────────────────────────
    def _generate_cid(self, data: bytes) -> str:
        """Generates a SHA-256 based content identifier (simulates IPFS CID)."""
        raw_hash = hashlib.sha256(data).hexdigest()
        # Prefix with 'Qm' to mimic real IPFS CIDv0 format
        return 'Qm' + raw_hash[:44]

    # ──────────────────────────────────────────
    # UPLOAD STRING DATA
    # ──────────────────────────────────────────
    def upload_data(self, data: str) -> str:
        """
        Uploads encrypted string data (EMR) to IPFS.
        Returns IPFS content hash (CID).

        Production equivalent:
            result = client.add_str(data)
            return result  # Returns CID
        """
        if not data:
            raise ValueError("Cannot upload empty data to IPFS")

        encoded    = data.encode('utf-8')
        ipfs_hash  = self._generate_cid(encoded)
        metadata   = {
            'content':   data,
            'timestamp': datetime.now().isoformat(),
            'size':      len(encoded),
            'type':      'text/encrypted'
        }
        self._storage[ipfs_hash] = metadata
        print(f"[IPFS] ✓ Data uploaded | CID: {ipfs_hash[:20]}... | "
              f"Size: {len(encoded)} bytes")
        return ipfs_hash

    # ──────────────────────────────────────────
    # UPLOAD BYTES (for files: X-rays, reports)
    # ──────────────────────────────────────────
    def upload_bytes(self, data: bytes) -> str:
        """
        Uploads encrypted binary file (X-ray, scan, report) to IPFS.

        Production equivalent:
            result = client.add_bytes(data)
            return result
        """
        if not data:
            raise ValueError("Cannot upload empty bytes to IPFS")

        ipfs_hash = self._generate_cid(data)
        self._file_store[ipfs_hash] = {
            'content':   base64.b64encode(data).decode('utf-8'),
            'timestamp': datetime.now().isoformat(),
            'size':      len(data),
            'type':      'binary/encrypted'
        }
        print(f"[IPFS] ✓ File uploaded | CID: {ipfs_hash[:20]}... | "
              f"Size: {len(data)} bytes")
        return ipfs_hash

    # ──────────────────────────────────────────
    # UPLOAD FILE FROM DISK
    # ──────────────────────────────────────────
    def upload_file(self, filepath: str) -> str:
        """
        Reads a file from disk and uploads to IPFS.

        Production equivalent:
            result = client.add(filepath)
            return result['Hash']
        """
        if not os.path.exists(filepath):
            return self._generate_cid(filepath.encode())

        with open(filepath, 'rb') as f:
            data = f.read()
        return self.upload_bytes(data)

    # ──────────────────────────────────────────
    # RETRIEVE DATA
    # ──────────────────────────────────────────
    def retrieve_data(self, ipfs_hash: str) -> str:
        """
        Retrieves encrypted data from IPFS using content hash.

        Production equivalent:
            data = client.cat(ipfs_hash)
            return data.decode('utf-8')
        """
        if ipfs_hash in self._storage:
            content = self._storage[ipfs_hash]['content']
            print(f"[IPFS] ✓ Data retrieved | CID: {ipfs_hash[:20]}...")
            return content

        # If not in local simulation, return a placeholder
        print(f"[IPFS] ⚠ Data not in local store | CID: {ipfs_hash[:20]}... "
              f"(would fetch from IPFS network in production)")
        return f"[ENCRYPTED_EMR_DATA_FROM_IPFS:{ipfs_hash}]"

    # ──────────────────────────────────────────
    # RETRIEVE BYTES
    # ──────────────────────────────────────────
    def retrieve_bytes(self, ipfs_hash: str) -> bytes:
        """Retrieves binary file from IPFS."""
        if ipfs_hash in self._file_store:
            encoded = self._file_store[ipfs_hash]['content']
            return base64.b64decode(encoded.encode('utf-8'))
        return b''

    # ──────────────────────────────────────────
    # VERIFY HASH
    # ──────────────────────────────────────────
    def verify_hash(self, ipfs_hash: str, data: str) -> bool:
        """
        Verifies that given data matches stored IPFS hash.
        Used for tamper detection.
        """
        expected_hash = self._generate_cid(data.encode('utf-8'))
        is_valid      = (expected_hash == ipfs_hash)
        status        = "✓ VALID" if is_valid else "✗ TAMPERED"
        print(f"[IPFS] {status} | CID: {ipfs_hash[:20]}...")
        return is_valid

    # ──────────────────────────────────────────
    # GET PUBLIC GATEWAY URL
    # ──────────────────────────────────────────
    def get_gateway_url(self, ipfs_hash: str) -> str:
        return f"{self.gateway}{ipfs_hash}"

    # ──────────────────────────────────────────
    # IPFS STATUS
    # ──────────────────────────────────────────
    def get_status(self) -> dict:
        return {
            'mode':          'Demo Simulation' if self.is_demo else 'Live IPFS Node',
            'node_url':      self.node_url,
            'gateway':       self.gateway,
            'stored_items':  len(self._storage) + len(self._file_store),
            'total_size_kb': sum(v['size'] for v in self._storage.values()) // 1024,
            'status':        'Running'
        }

    # ──────────────────────────────────────────
    # PIN DATA (keep permanently on IPFS network)
    # ──────────────────────────────────────────
    def pin_data(self, ipfs_hash: str) -> bool:
        """
        Pins data to prevent garbage collection on IPFS node.
        Production: client.pin.add(ipfs_hash)
        """
        if ipfs_hash in self._storage or ipfs_hash in self._file_store:
            print(f"[IPFS] ✓ Pinned | CID: {ipfs_hash[:20]}...")
            return True
        return False
