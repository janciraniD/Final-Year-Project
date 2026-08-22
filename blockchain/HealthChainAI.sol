// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * HealthChainAI.sol
 * ─────────────────────────────────────────────────────────────
 * Smart Contract for Intelligent Disease Prediction System
 * Using Deep Learning with Secure Blockchain Storage
 *
 * Achariya College of Engineering Technology
 * Pondicherry University – 2025
 *
 * Features:
 *  - Secure EMR storage (IPFS hash on-chain)
 *  - User role management (Doctor / Patient)
 *  - Access control via modifiers
 *  - AI prediction audit trail
 *  - Event logging for transparency
 * ─────────────────────────────────────────────────────────────
 */

contract HealthChainAI {

    // ─────────────────────────────────────────
    // STRUCTS
    // ─────────────────────────────────────────

    struct User {
        address wallet;
        string  username;
        string  role;         // "doctor" or "patient"
        bool    isRegistered;
        uint256 registeredAt;
    }

    struct EMRecord {
        uint256 id;
        string  patientName;
        string  ipfsHash;      // Encrypted EMR stored on IPFS
        string  fileIpfsHash;  // Attached file (X-ray, report)
        address doctor;
        address patient;
        uint256 timestamp;
        bool    isValid;
    }

    struct AIPrediction {
        uint256 id;
        address requestedBy;
        string  imageIpfsHash;
        string  diseasePredicted;
        uint256 confidenceScore;  // stored as percentage * 100 (e.g., 9250 = 92.50%)
        uint256 timestamp;
    }

    // ─────────────────────────────────────────
    // STATE VARIABLES
    // ─────────────────────────────────────────

    address public owner;
    uint256 public emrCount;
    uint256 public predictionCount;

    mapping(address => User)        public users;
    mapping(uint256 => EMRecord)    public emrRecords;
    mapping(uint256 => AIPrediction) public predictions;
    mapping(address => uint256[])   public userEMRs;      // user → emr IDs
    mapping(address => bool)        public authorizedDoctors;

    // ─────────────────────────────────────────
    // EVENTS
    // ─────────────────────────────────────────

    event UserRegistered(address indexed wallet, string username, string role, uint256 timestamp);
    event EMRStored(uint256 indexed emrId, string patientName, string ipfsHash, address indexed doctor, uint256 timestamp);
    event EMRAccessed(uint256 indexed emrId, address indexed accessor, uint256 timestamp);
    event EMRInvalidated(uint256 indexed emrId, address indexed by, uint256 timestamp);
    event PredictionStored(uint256 indexed predId, string disease, uint256 confidence, uint256 timestamp);
    event DoctorAuthorized(address indexed doctor, uint256 timestamp);

    // ─────────────────────────────────────────
    // MODIFIERS
    // ─────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "Only contract owner can perform this action");
        _;
    }

    modifier onlyRegistered() {
        require(users[msg.sender].isRegistered, "User not registered");
        _;
    }

    modifier onlyDoctor() {
        require(
            keccak256(bytes(users[msg.sender].role)) == keccak256(bytes("doctor")),
            "Only doctors can perform this action"
        );
        _;
    }

    modifier emrExists(uint256 emrId) {
        require(emrId > 0 && emrId <= emrCount, "EMR does not exist");
        require(emrRecords[emrId].isValid, "EMR has been invalidated");
        _;
    }

    // ─────────────────────────────────────────
    // CONSTRUCTOR
    // ─────────────────────────────────────────

    constructor() {
        owner = msg.sender;
        // Register owner as admin doctor
        users[msg.sender] = User({
            wallet:       msg.sender,
            username:     "admin",
            role:         "doctor",
            isRegistered: true,
            registeredAt: block.timestamp
        });
        authorizedDoctors[msg.sender] = true;
    }

    // ─────────────────────────────────────────
    // USER REGISTRATION
    // ─────────────────────────────────────────

    /**
     * @dev Register a new user (patient or doctor)
     * @param username Display name
     * @param role     "doctor" or "patient"
     */
    function registerUser(string memory username, string memory role) public {
        require(!users[msg.sender].isRegistered, "User already registered");
        require(bytes(username).length > 0, "Username cannot be empty");
        require(
            keccak256(bytes(role)) == keccak256(bytes("doctor")) ||
            keccak256(bytes(role)) == keccak256(bytes("patient")),
            "Role must be 'doctor' or 'patient'"
        );

        users[msg.sender] = User({
            wallet:       msg.sender,
            username:     username,
            role:         role,
            isRegistered: true,
            registeredAt: block.timestamp
        });

        if (keccak256(bytes(role)) == keccak256(bytes("doctor"))) {
            authorizedDoctors[msg.sender] = true;
        }

        emit UserRegistered(msg.sender, username, role, block.timestamp);
    }

    // ─────────────────────────────────────────
    // EMR STORAGE
    // ─────────────────────────────────────────

    /**
     * @dev Store encrypted EMR metadata on blockchain
     * @param patientName   Name of the patient
     * @param ipfsHash      IPFS CID of the encrypted EMR data
     * @param fileIpfsHash  IPFS CID of attached file (optional, pass "" if none)
     * @param patientWallet Patient's Ethereum wallet address
     */
    function storeEMR(
        string memory patientName,
        string memory ipfsHash,
        string memory fileIpfsHash,
        address       patientWallet
    ) public onlyRegistered onlyDoctor returns (uint256) {

        require(bytes(patientName).length > 0, "Patient name required");
        require(bytes(ipfsHash).length > 0,    "IPFS hash required");

        emrCount++;
        uint256 newId = emrCount;

        emrRecords[newId] = EMRecord({
            id:           newId,
            patientName:  patientName,
            ipfsHash:     ipfsHash,
            fileIpfsHash: fileIpfsHash,
            doctor:       msg.sender,
            patient:      patientWallet,
            timestamp:    block.timestamp,
            isValid:      true
        });

        userEMRs[msg.sender].push(newId);
        if (patientWallet != address(0)) {
            userEMRs[patientWallet].push(newId);
        }

        emit EMRStored(newId, patientName, ipfsHash, msg.sender, block.timestamp);
        return newId;
    }

    // ─────────────────────────────────────────
    // EMR RETRIEVAL
    // ─────────────────────────────────────────

    /**
     * @dev Retrieve EMR details (logs access for audit trail)
     */
    function getEMR(uint256 emrId)
        public
        onlyRegistered
        emrExists(emrId)
        returns (
            string memory patientName,
            string memory ipfsHash,
            string memory fileIpfsHash,
            address doctor,
            uint256 timestamp
        )
    {
        EMRecord storage record = emrRecords[emrId];

        // Access control: only doctor who created or the patient
        require(
            msg.sender == record.doctor ||
            msg.sender == record.patient ||
            msg.sender == owner,
            "Access denied: Not authorized to view this EMR"
        );

        emit EMRAccessed(emrId, msg.sender, block.timestamp);

        return (
            record.patientName,
            record.ipfsHash,
            record.fileIpfsHash,
            record.doctor,
            record.timestamp
        );
    }

    /**
     * @dev Verify EMR has not been tampered (check IPFS hash matches)
     */
    function verifyEMR(uint256 emrId, string memory ipfsHash)
        public
        view
        emrExists(emrId)
        returns (bool isValid)
    {
        return keccak256(bytes(emrRecords[emrId].ipfsHash)) ==
               keccak256(bytes(ipfsHash));
    }

    /**
     * @dev Get all EMR IDs for a user
     */
    function getUserEMRs(address userWallet)
        public
        view
        onlyRegistered
        returns (uint256[] memory)
    {
        return userEMRs[userWallet];
    }

    /**
     * @dev Invalidate (soft-delete) an EMR
     */
    function invalidateEMR(uint256 emrId)
        public
        onlyOwner
        emrExists(emrId)
    {
        emrRecords[emrId].isValid = false;
        emit EMRInvalidated(emrId, msg.sender, block.timestamp);
    }

    // ─────────────────────────────────────────
    // AI PREDICTION STORAGE
    // ─────────────────────────────────────────

    /**
     * @dev Store AI skin disease prediction on blockchain
     * @param imageIpfsHash     IPFS hash of the analyzed skin image
     * @param diseasePredicted  Predicted disease class name
     * @param confidenceScore   Confidence percentage × 100 (e.g., 9250 = 92.50%)
     */
    function storePrediction(
        string memory imageIpfsHash,
        string memory diseasePredicted,
        uint256       confidenceScore
    ) public onlyRegistered returns (uint256) {

        require(bytes(diseasePredicted).length > 0, "Disease name required");
        require(confidenceScore <= 10000, "Confidence must be <= 10000 (100.00%)");

        predictionCount++;
        uint256 newId = predictionCount;

        predictions[newId] = AIPrediction({
            id:               newId,
            requestedBy:      msg.sender,
            imageIpfsHash:    imageIpfsHash,
            diseasePredicted: diseasePredicted,
            confidenceScore:  confidenceScore,
            timestamp:        block.timestamp
        });

        emit PredictionStored(newId, diseasePredicted, confidenceScore, block.timestamp);
        return newId;
    }

    /**
     * @dev Retrieve a specific prediction
     */
    function getPrediction(uint256 predId)
        public
        view
        returns (
            address requestedBy,
            string memory imageIpfsHash,
            string memory diseasePredicted,
            uint256 confidenceScore,
            uint256 timestamp
        )
    {
        require(predId > 0 && predId <= predictionCount, "Prediction not found");
        AIPrediction storage p = predictions[predId];
        return (p.requestedBy, p.imageIpfsHash, p.diseasePredicted, p.confidenceScore, p.timestamp);
    }

    // ─────────────────────────────────────────
    // ADMIN FUNCTIONS
    // ─────────────────────────────────────────

    /**
     * @dev Authorize an additional doctor
     */
    function authorizeDoctor(address doctorWallet) public onlyOwner {
        authorizedDoctors[doctorWallet] = true;
        emit DoctorAuthorized(doctorWallet, block.timestamp);
    }

    /**
     * @dev Get contract statistics
     */
    function getStats()
        public
        view
        returns (uint256 totalEMRs, uint256 totalPredictions, address contractOwner)
    {
        return (emrCount, predictionCount, owner);
    }
}
