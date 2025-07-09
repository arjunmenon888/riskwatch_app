# constants.py

"""
Central location for storing application-wide constants to avoid "magic strings".
This improves maintainability and reduces the risk of typos.
"""

# User Permission Constants
PERM_OBSERVATION = "can_access_observation"
PERM_TRAINING = "can_access_training"
PERM_LF = "can_access_lost_and_found"
PERM_GATE_PASS = "can_access_gate_pass"
# --- FIX: Standardize on the shorter, correct column name ---
PERM_ASK_AI = "can_access_ask_ai"

# List of all allowed permission columns for validation
ALLOWED_PERMISSIONS = [
    PERM_OBSERVATION,
    PERM_TRAINING,
    PERM_LF,
    PERM_GATE_PASS,
    PERM_ASK_AI,
]