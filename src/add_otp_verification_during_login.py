import random
import time
from typing import Any, Dict

# --- Constants ---
OTP_LENGTH: int = 6
OTP_EXPIRATION_SECONDS: int = 300  # 5 minutes

# --- Mock Databases (in-memory for this example) ---
# In a real application, these would be backed by a persistent database
# (e.g., PostgreSQL, MongoDB) or a fast key-value store (e.g., Redis).
_mock_user_db: Dict[str, str] = {}  # Stores user_id -> email
# Stores user_id -> {'otp': str, 'timestamp': float}
# This dict holds the temporary OTPs and their generation times.
_otp_store: Dict[str, Dict[str, Any]] = {}


# --- Custom Exceptions ---
class UserNotFoundError(Exception):
    """Raised when a user is not found in the system."""
    pass

class OTPGenerationError(Exception):
    """Raised when there's an issue generating the OTP."""
    pass

class OTPSendError(Exception):
    """Raised when there's an issue simulating the OTP email sending."""
    pass

class OTPVerificationError(Exception):
    """Base exception for OTP verification failures."""
    pass

class OTPNotFoundError(OTPVerificationError):
    """Raised when no OTP is found or initiated for the given user."""
    pass

class OTPExpiredError(OTPVerificationError):
    """Raised when the provided OTP has expired."""
    pass

class InvalidOTPError(OTPVerificationError):
    """Raised when the provided OTP does not match the stored OTP."""
    pass


# --- Helper Functions ---

def _generate_otp(length: int = OTP_LENGTH) -> str:
    """
    Generates a random numeric One-Time Password (OTP) of the specified length.

    Args:
        length: The desired length of the OTP.

    Returns:
        A string representation of the generated OTP.

    Raises:
        OTPGenerationError: If the length is not a positive integer.
    """
    if not isinstance(length, int) or length <= 0:
        raise OTPGenerationError("OTP length must be a positive integer.")
    try:
        # Generate random digits and join them into a string
        otp_code = "".join(random.choices("0123456789", k=length))
        return otp_code
    except Exception as e:
        # Catch any unexpected errors during OTP generation
        raise OTPGenerationError(f"Failed to generate OTP: {e}") from e

def _send_email_otp(email: str, otp: str) -> None:
    """
    Simulates sending a 6-digit OTP to the user's registered email address.

    In a real production environment, this function would integrate with an
    actual email service provider (e.g., SendGrid, Mailgun, AWS SES) via their APIs.

    Args:
        email: The recipient's email address.
        otp: The 6-digit OTP to send.

    Raises:
        OTPSendError: If there's an issue simulating the email sending process
                      or if input validation fails.
    """
    if not isinstance(email, str) or not email:
        raise OTPSendError("Recipient email cannot be empty.")
    if not isinstance(otp, str) or len(otp) != OTP_LENGTH or not otp.isdigit():
        raise OTPSendError(f"OTP '{otp}' is invalid for sending. Must be a {OTP_LENGTH}-digit string.")
    try:
        # Simulate network delay or interaction with an external email service
        time.sleep(0.1)
        print(f"DEBUG: Successfully simulated sending OTP '{otp}' to email: {email}")
        # Example of actual email sending (pseudo-code):
        # email_service.send_email(
        #     to=email,
        #     subject="Your Login OTP",
        #     body=f"Your One-Time Password is: {otp}. It is valid for 5 minutes."
        # )
    except Exception as e:
        # Catch any potential errors from the email service or during simulation
        raise OTPSendError(f"Failed to send OTP email to {email}: {e}") from e

# --- User Management (Mock) ---

def register_user(user_id: str, email: str) -> None:
    """
    Registers a new user in the mock user database or updates an existing one.

    Args:
        user_id: The unique identifier for the user.
        email: The registered email address for the user.

    Raises:
        ValueError: If user_id or email is empty.
    """
    if not user_id or not email:
        raise ValueError("User ID and email cannot be empty.")
    if user_id in _mock_user_db:
        print(f"WARNING: User '{user_id}' already registered. Updating email to {email}.")
    _mock_user_db[user_id] = email

def _get_user_email(user_id: str) -> str:
    """
    Retrieves the email address for a given user ID from the mock database.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The registered email address.

    Raises:
        UserNotFoundError: If the user ID is not found in the mock database.
    """
    email = _mock_user_db.get(user_id)
    if email is None:
        raise UserNotFoundError(f"User with ID '{user_id}' not found.")
    return email

# --- Feature Implementation ---

def initiate_otp_login(user_id: str) -> str:
    """
    Initiates the OTP verification process for a user login.

    This function is typically called after a user successfully provides their
    username and password. It generates a new 6-digit OTP, stores it
    with a timestamp, and simulates sending it to the user's registered email.

    Args:
        user_id: The unique identifier of the user attempting to log in.

    Returns:
        A message indicating that OTP verification is required.

    Raises:
        UserNotFoundError: If the user does not exist in the system.
        OTPGenerationError: If there's an issue generating the OTP.
        OTPSendError: If there's an issue sending the OTP email.
    """
    # 1. Retrieve user's email to ensure the user exists and for sending the OTP.
    email = _get_user_email(user_id)

    # 2. Generate a new OTP.
    otp_code = _generate_otp(OTP_LENGTH)

    # 3. Store the OTP along with its creation timestamp.
    # This design ensures that subsequent calls to initiate_otp_login for the same
    # user will overwrite any previous OTP, making only the latest one valid.
    _otp_store[user_id] = {
        "otp": otp_code,
        "timestamp": time.time()  # Store current Unix timestamp for expiration check
    }
    print(f"DEBUG: Stored OTP for {user_id}: {otp_code} (expires in {OTP_EXPIRATION_SECONDS // 60} mins)")

    # 4. Simulate sending the OTP to the user's registered email.
    _send_email_otp(email, otp_code)

    return f"OTP sent to {email}. Please verify within {OTP_EXPIRATION_SECONDS // 60} minutes."

def verify_otp(user_id: str, submitted_otp: str) -> bool:
    """
    Verifies the submitted OTP against the stored OTP for a given user.

    The OTP must be valid, not expired (within the `OTP_EXPIRATION_SECONDS` window),
    and must exactly match the stored code. Upon successful verification,
    the OTP is invalidated (removed from storage) to prevent reuse.

    Args:
        user_id: The unique identifier of the user.
        submitted_otp: The OTP code submitted by the user.

    Returns:
        True if the OTP is successfully verified.

    Raises:
        UserNotFoundError: If the user does not exist in the system.
        ValueError: If `submitted_otp` is not a string, empty, or not a {OTP_LENGTH}-digit number.
        OTPNotFoundError: If no OTP was initiated or found for the user.
        OTPExpiredError: If the OTP has expired.
        InvalidOTPError: If the submitted OTP does not match the stored OTP.
    """
    # 1. Basic input validation for the submitted OTP format.
    if not isinstance(submitted_otp, str) or not submitted_otp.isdigit() or len(submitted_otp) != OTP_LENGTH:
        raise ValueError(
            f"Submitted OTP '{submitted_otp}' is invalid. Must be a {OTP_LENGTH}-digit string."
        )

    # 2. Ensure the user exists. This also prevents leaking information about OTP status
    # for non-existent users.
    _ = _get_user_email(user_id) # This call will raise UserNotFoundError if applicable.

    # 3. Retrieve the stored OTP information for the user.
    stored_otp_data = _otp_store.get(user_id)

    if stored_otp_data is None:
        # No OTP was ever initiated for this user or it was already successfully verified and removed.
        raise OTPNotFoundError(f"No active OTP found for user '{user_id}'. Please initiate login again.")

    stored_otp = stored_otp_data["otp"]
    timestamp = stored_otp_data["timestamp"]

    # 4. Check if the OTP has expired.
    current_time = time.time()
    if (current_time - timestamp) > OTP_EXPIRATION_SECONDS:
        # OTP has expired. Remove it from the store to prevent future attempts with it.
        _otp_store.pop(user_id, None)
        raise OTPExpiredError(f"OTP for user '{user_id}' has expired. Please request a new one.")

    # 5. Check if the submitted OTP matches the stored OTP.
    if submitted_otp == stored_otp:
        # OTP is valid and not expired. Remove it from the store to ensure it's a single-use token.
        _otp_store.pop(user_id, None)
        print(f"DEBUG: OTP for {user_id} successfully verified and removed from store.")
        return True
    else:
        # The OTP is incorrect, but not necessarily expired.
        # We do NOT remove the OTP from the store on an incorrect attempt,
        # allowing the user to retry within the expiration window.
        raise InvalidOTPError(f"Invalid OTP submitted for user '{user_id}'. Please try again.")


# --- Main Guard and Usage Example ---
if __name__ == "__main__":
    print("--- OTP Login Verification Example ---")

    # 1. Register some mock users for testing purposes
    register_user("john.doe", "john.doe@example.com")
    register_user("jane.smith", "jane.smith@example.com")
    register_user("admin_user", "admin@company.com")

    # --- Scenario 1: Successful Login Flow ---
    print("\n--- Scenario 1: Successful Login ---")
    user_id_1 = "john.doe"
    try:
        print(f"\nAttempting login for '{user_id_1}'...")
        # Step 1: User provides valid username/password (simulated as success here).
        # Step 2: Initiate OTP verification.
        otp_init_message = initiate_otp_login(user_id_1)
        print(otp_init_message)

        # Simulate user receiving email and entering the OTP.
        # In a real system, the user would manually retrieve this.
        # For demonstration, we'll fetch it from our mock store.
        correct_otp_1 = _otp_store[user_id_1]["otp"]
        print(f"(Simulated) User '{user_id_1}' received OTP: {correct_otp_1}")

        # Step 3: User submits the received OTP.
        print(f"User '{user_id_1}' submitting OTP: {correct_otp_1}")
        if verify_otp(user_id_1, correct_otp_1):
            print(f"SUCCESS: Login completed for '{user_id_1}'! Welcome.")
        else:
            print(f"FAILURE: Login failed unexpectedly for '{user_id_1}'.")
    except (UserNotFoundError, OTPGenerationError, OTPSendError, OTPVerificationError, ValueError) as e:
        print(f"ERROR during login for '{user_id_1}': {e}")

    # --- Scenario 2: Invalid OTP Submitted ---
    print("\n--- Scenario 2: Invalid OTP ---")
    user_id_2 = "jane.smith"
    try:
        print(f"\nAttempting login for '{user_id_2}'...")
        initiate_otp_login(user_id_2)
        correct_otp_2 = _otp_store[user_id_2]["otp"]
        print(f"(Simulated) User '{user_id_2}' received OTP: {correct_otp_2}")

        # User submits an incorrect OTP
        invalid_otp = "999999" # Incorrect 6-digit code
        print(f"User '{user_id_2}' submitting invalid OTP: {invalid_otp}")
        if verify_otp(user_id_2, invalid_otp):
            print(f"SUCCESS: Login completed for '{user_id_2}'! (This should NOT happen)")
        else:
            print(f"FAILURE: Login failed unexpectedly for '{user_id_2}'.")
    except InvalidOTPError as e:
        print(f"EXPECTED FAILURE: Login failed for '{user_id_2}': {e}")
        # Let's try again with the correct OTP as the original was not removed
        print(f"User '{user_id_2}' retrying with correct OTP: {correct_otp_2}")
        try:
            if verify_otp(user_id_2, correct_otp_2):
                print(f"SUCCESS: Login completed for '{user_id_2}' after retry.")
        except OTPVerificationError as e:
            print(f"ERROR: Retry failed unexpectedly: {e}")
    except (UserNotFoundError, OTPGenerationError, OTPSendError, ValueError) as e:
        print(f"ERROR during login for '{user_id_2}': {e}")

    # --- Scenario 3: Expired OTP ---
    print("\n--- Scenario 3: Expired OTP ---")
    user_id_3 = "admin_user"
    try:
        print(f"\nAttempting login for '{user_id_3}'...")
        initiate_otp_login(user_id_3)
        correct_otp_3 = _otp_store[user_id_3]["otp"]
        print(f"(Simulated) User '{user_id_3}' received OTP: {correct_otp_3}")

        # Simulate time passing beyond expiration (5 minutes + 1 second)
        print(f"Simulating {OTP_EXPIRATION_SECONDS + 1} seconds passing for OTP to expire...")
        time.sleep(OTP_EXPIRATION_SECONDS + 1)

        print(f"User '{user_id_3}' submitting OTP: {correct_otp_3} AFTER expiration")
        if verify_otp(user_id_3, correct_otp_3):
            print(f"SUCCESS: Login completed for '{user_id_3}'! (This should NOT happen)")
        else:
            print(f"FAILURE: Login failed unexpectedly for '{user_id_3}'.")
    except OTPExpiredError as e:
        print(f"EXPECTED FAILURE: Login failed for '{user_id_3}': {e}")
    except (UserNotFoundError, OTPGenerationError, OTPSendError, ValueError) as e:
        print(f"ERROR during login for '{user_id_3}': {e}")

    # --- Scenario 4: User Not Found ---
    print("\n--- Scenario 4: User Not Found ---")
    user_id_nonexistent = "ghost_user"
    try:
        print(f"\nAttempting to initiate login for '{user_id_nonexistent}'...")
        initiate_otp_login(user_id_nonexistent)
    except UserNotFoundError as e:
        print(f"EXPECTED FAILURE: Login attempt failed for '{user_id_nonexistent}': {e}")
    except (OTPGenerationError, OTPSendError, OTPVerificationError, ValueError) as e:
        print(f"ERROR during login for '{user_id_nonexistent}': {e}")

    # --- Scenario 5: Re-verification attempt after successful login ---
    print("\n--- Scenario 5: Re-verification after successful login ---")
    user_id_1_again = "john.doe" # User1's OTP was already verified and removed from store
    try:
        print(f"\nAttempting to re-verify OTP for '{user_id_1_again}' without re-initiating...")
        # Since OTP was removed, this should result in OTPNotFoundError
        if verify_otp(user_id_1_again, "123456"): # Any valid-format OTP string
            print(f"SUCCESS: Login completed for '{user_id_1_again}'! (This should NOT happen)")
    except OTPNotFoundError as e:
        print(f"EXPECTED FAILURE: Login failed for '{user_id_1_again}': {e}")
    except (UserNotFoundError, OTPGenerationError, OTPSendError, OTPVerificationError, ValueError) as e:
        print(f"ERROR during login for '{user_id_1_again}': {e}")

    # --- Scenario 6: Invalid submitted OTP format ---
    print("\n--- Scenario 6: Invalid submitted OTP format ---")
    user_id_2_again = "jane.smith" # Initiate OTP first
    try:
        print(f"\nAttempting login for '{user_id_2_again}'...")
        initiate_otp_login(user_id_2_again)
        print(f"User '{user_id_2_again}' submitting malformed OTP: 'abc'")
        verify_otp(user_id_2_again, "abc")
    except ValueError as e:
        print(f"EXPECTED FAILURE: Login failed for '{user_id_2_again}': {e}")
    except (UserNotFoundError, OTPGenerationError, OTPSendError, OTPVerificationError) as e:
        print(f"ERROR during login for '{user_id_2_again}': {e}")
    finally:
        # Clean up the OTP for user2_again for future runs
        _otp_store.pop(user_id_2_again, None)
        print(f"DEBUG: Cleaned up OTP for '{user_id_2_again}'.")