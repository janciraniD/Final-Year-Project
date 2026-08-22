from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'healthcare_secret_key_2025'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# ─────────────────────────────────────────────
# Import modules
# ─────────────────────────────────────────────
from blockchain.ethereum import BlockchainManager
from blockchain.ipfs_handler import IPFSHandler
from utils.crypto_chaos import CryptoChaosEncryption
from utils.auth import AuthManager
from models.database import DatabaseManager

# ─────────────────────────────────────────────
# Initialize components
# ─────────────────────────────────────────────
blockchain = BlockchainManager()
ipfs = IPFSHandler()
crypto = CryptoChaosEncryption()
auth = AuthManager()
db = DatabaseManager()

# ─────────────────────────────────────────────
# Login required decorator
# ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role     = request.form['role']       # doctor / patient
        email    = request.form['email']

        result = auth.register_user(username, password, email, role)
        if result['success']:
            # Register user on blockchain
            tx_hash = blockchain.register_user_on_chain(username, role)
            db.save_user_tx(username, tx_hash)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash(result['message'], 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        result = auth.verify_user(username, password)
        if result['success']:
            session['user_id']  = result['user']['id']
            session['username'] = result['user']['username']
            session['role']     = result['user']['role']
            flash(f"Welcome, {username}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    user_records = db.get_user_emrs(session['user_id'])
    blockchain_stats = blockchain.get_stats()
    return render_template('dashboard.html',
                           records=user_records,
                           stats=blockchain_stats,
                           username=session['username'],
                           role=session['role'])

# ─────────────────────────────────────────────
# EMR MANAGEMENT
# ─────────────────────────────────────────────
@app.route('/emr/add', methods=['GET', 'POST'])
@login_required
def add_emr():
    if request.method == 'POST':
        patient_name  = request.form['patient_name']
        diagnosis     = request.form['diagnosis']
        prescription  = request.form['prescription']
        doctor_name   = request.form['doctor_name']
        file          = request.files.get('medical_file')

        emr_data = {
            'patient_name': patient_name,
            'diagnosis':    diagnosis,
            'prescription': prescription,
            'doctor_name':  doctor_name,
            'created_by':   session['username']
        }

        # Step 1: Encrypt EMR with CryptoChaos
        encrypted_data, key = crypto.encrypt(str(emr_data))

        # Step 2: Upload encrypted data to IPFS
        ipfs_hash = ipfs.upload_data(encrypted_data)

        # Step 3: Store IPFS hash + metadata on Ethereum blockchain
        tx_hash = blockchain.store_emr(
            patient_name=patient_name,
            ipfs_hash=ipfs_hash,
            doctor=session['username']
        )

        # Step 4: Handle file upload (X-ray, reports)
        file_ipfs_hash = None
        if file and file.filename:
            file_data = file.read()
            encrypted_file, _ = crypto.encrypt_bytes(file_data, key)
            file_ipfs_hash = ipfs.upload_bytes(encrypted_file)

        # Step 5: Save to local DB
        db.save_emr(
            user_id      = session['user_id'],
            patient_name = patient_name,
            ipfs_hash    = ipfs_hash,
            tx_hash      = tx_hash,
            file_hash    = file_ipfs_hash,
            encryption_key = key
        )

        flash(f'EMR stored! IPFS: {ipfs_hash[:20]}... | TX: {tx_hash[:20]}...', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_emr.html', username=session['username'])

@app.route('/emr/view/<int:emr_id>')
@login_required
def view_emr(emr_id):
    emr = db.get_emr_by_id(emr_id)
    if not emr:
        flash('EMR not found.', 'danger')
        return redirect(url_for('dashboard'))

    # Verify blockchain integrity
    is_valid = blockchain.verify_emr(emr['tx_hash'], emr['ipfs_hash'])

    # Retrieve encrypted data from IPFS
    encrypted_data = ipfs.retrieve_data(emr['ipfs_hash'])

    # Decrypt using stored key
    decrypted_data = crypto.decrypt(encrypted_data, emr['encryption_key'])

    # Get blockchain transaction info
    tx_info = blockchain.get_transaction_info(emr['tx_hash'])

    return render_template('view_emr.html',
                           emr=emr,
                           decrypted=decrypted_data,
                           tx_info=tx_info,
                           is_valid=is_valid)

@app.route('/emr/all')
@login_required
def all_emrs():
    if session['role'] != 'doctor':
        flash('Access denied. Doctors only.', 'danger')
        return redirect(url_for('dashboard'))
    records = db.get_all_emrs()
    return render_template('all_emrs.html', records=records)

# ─────────────────────────────────────────────
# BLOCKCHAIN INFO
# ─────────────────────────────────────────────
@app.route('/blockchain/info')
@login_required
def blockchain_info():
    transactions = db.get_all_transactions()
    chain_data   = blockchain.get_all_blocks()
    return render_template('blockchain_info.html',
                           transactions=transactions,
                           chain_data=chain_data)

@app.route('/blockchain/verify/<tx_hash>')
@login_required
def verify_tx(tx_hash):
    result = blockchain.verify_transaction(tx_hash)
    return jsonify(result)

# ─────────────────────────────────────────────
# SKIN DISEASE PREDICTION (AI Module)
# ─────────────────────────────────────────────
@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    prediction = None
    confidence = None
    image_path = None
    result     = None

    if request.method == 'POST':
        file = request.files.get('skin_image')
        if file and file.filename:
            filename  = f"skin_{session['user_id']}_{file.filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            image_path = f"uploads/{filename}"

            try:
                from models.efficientnet_model import SkinDiseasePredictor
                predictor  = SkinDiseasePredictor()
                result     = predictor.predict(save_path)
                prediction = result['class']
                confidence = result['confidence']

                try:
                    tx_hash = blockchain.store_prediction(
                        user=session['username'],
                        disease=prediction,
                        confidence=confidence,
                        image_ipfs=ipfs.upload_file(save_path)
                    )
                    flash(f'Prediction stored on blockchain! TX: {tx_hash[:20]}...', 'info')
                except Exception:
                    flash('Prediction complete (blockchain offline — demo mode).', 'info')

            except Exception as e:
                flash(f'Prediction error: {str(e)}', 'warning')
                prediction = 'Analysis Error'
                confidence = 0.0
                result     = None

    return render_template('predict.html',
                           prediction=prediction,
                           confidence=confidence,
                           image_path=image_path,
                           result=result)

# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────
@app.route('/api/emr/<int:emr_id>', methods=['GET'])
@login_required
def api_get_emr(emr_id):
    emr = db.get_emr_by_id(emr_id)
    if emr:
        return jsonify({'success': True, 'data': emr})
    return jsonify({'success': False, 'message': 'Not found'}), 404

@app.route('/api/blockchain/stats', methods=['GET'])
@login_required
def api_blockchain_stats():
    return jsonify(blockchain.get_stats())

@app.route('/api/ipfs/status', methods=['GET'])
@login_required
def api_ipfs_status():
    return jsonify(ipfs.get_status())

# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db.init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
