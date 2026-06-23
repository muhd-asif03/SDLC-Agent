# OTP Verification During Login

## Overview
This document outlines the implementation of a Two-Factor Authentication (2FA) mechanism using One-Time Passwords (OTPs) for user login. This feature enhances security by requiring users to verify their identity with a 6-digit OTP sent to their registered email address, in addition to their primary login credentials. The OTP is time-sensitive, expiring after 5 minutes, and is designed for single use.

## Jira Ticket
**SCRUM-2 - Add OTP verification during login**
*   **Summary**: Implement a 6-digit OTP verification step during the user login process. The OTP is sent to the user's registered email and must be verified within 5 minutes for login to complete. Invalid or expired OTPs will be rejected.
*   **Priority**: Medium

## Requirements
*   Upon a successful primary login (username/password), a 6-digit OTP must be generated and sent to the user's registered email address.
*   The login process should remain incomplete until the user successfully verifies the OTP.
*   The generated OTP must be valid for a period of 5 minutes from its generation time.
*   If the submitted OTP is incorrect, the user should be prompted to retry.
*   If the submitted OTP has expired, it must be rejected, and the user should be prompted to request a new OTP.
*   The OTP should be a single-use token; once successfully verified, it cannot be used again.

## Installation / Dependencies
This feature is implemented in Python and primarily relies on standard library modules.

*   **Python Version**: 3.x
*   **Standard Libraries**:
    *   `random`: For generating random OTP codes.
    *   `time`: For managing OTP expiration timestamps.
    *   `typing`: For type hints.

**External Dependencies (for a production environment):**
While the provided code simulates email sending, a real-world implementation would require integration with an external email service provider (e.g., SendGrid, Mailgun, AWS SES). This would involve installing the respective SDKs or using an HTTP client to interact with their APIs.

## Usage
The OTP verification process integrates into the existing user login flow. After a user successfully authenticates with their primary credentials (e.g., username and password), the system initiates the OTP generation and sending, and then waits for the user to submit the OTP for verification.

### Workflow
1.  **User Registration**: Ensure the user is registered with a valid email address using `register_user()`.
2.  **Primary Login (Simulated)**: The user provides their username and password. Upon successful validation of these credentials (not covered in this module), the OTP flow is triggered.
3.  **Initiate OTP**: Call `initiate_otp_login()` for the user. This generates an OTP, stores it, and simulates sending it via email.
4.  **OTP Submission**: The user retrieves the OTP from their email and submits it.
5.  **OTP Verification**: Call `verify_otp()` with the user's ID and the submitted OTP.
6.  **Login Completion**: If `verify_otp()` returns `True`, the login is complete. Otherwise, an error is raised, and the user must retry or request a new OTP.

### Code Example

```python
import time

# Assume the provided code is in a file named `otp_service.py`
from otp_service import (
    register_user,
    initiate_otp_login,
    verify_otp,
    UserNotFoundError,
    OTPGenerationError,
    OTPSendError,
    OTPExpiredError,
    InvalidOTPError,
    OTPNotFoundError,
    # Internal for demonstration, normally not accessed directly
    _otp_store
)

print("--- OTP Login Demonstration ---")

# 1. Register a mock user
user_id = "testuser_123"
email = "test.user@example.com"
register_user(user_id, email)
print(f"Registered user: {user_id} with email: {email}")

# --- Scenario A: Successful OTP Verification ---
print("\n--- Scenario A: Successful Verification ---")
try:
    print(f"\nInitiating OTP login for {user_id}...")
    initiate_otp_login(user_id)
    
    # In a real app, the user would check their email.
    # Here, we'll retrieve the OTP from our mock store for demonstration.
    correct_otp = _otp_store[user_id]["otp"]
    print(f"DEBUG: User receives OTP: {correct_otp}")

    # Simulate user submitting the correct OTP
    print(f"Verifying OTP '{correct_otp}' for {user_id}...")
    if verify_otp(user_id, correct_otp):
        print(f"SUCCESS: Login for {user_id} completed successfully!")
except (UserNotFoundError, OTPGenerationError, OTPSendError, OTPExpiredError, InvalidOTPError, ValueError) as e:
    print(f"ERROR: {e}")

# --- Scenario B: Invalid OTP Submission ---
print("\n--- Scenario B: Invalid OTP ---")
user_id_2 = "testuser_456"
register_user(user_id_2, "test2@example.com")
try:
    print(f"\nInitiating OTP login for {user_id_2}...")
    initiate_otp_login(user_id_2)
    
    # User submits an incorrect OTP
    incorrect_otp = "000000"
    print(f"Verifying incorrect OTP '{incorrect_otp}' for {user_id_2}...")
    verify_otp(user_id_2, incorrect_otp)
    print(f"ERROR: This line should not be reached for incorrect OTP.")
except InvalidOTPError as e:
    print(f"EXPECTED ERROR: {e} (User can retry with correct OTP)")
    # Demonstrate retry with correct OTP (since invalid attempts don't remove the OTP)
    try:
        correct_otp_2 = _otp_store[user_id_2]["otp"]
        print(f"Retrying with correct OTP '{correct_otp_2}' for {user_id_2}...")
        if verify_otp(user_id_2, correct_otp_2):
            print(f"SUCCESS: Login for {user_id_2} completed after retry!")
    except Exception as e:
        print(f"ERROR during retry: {e}")
except Exception as e:
    print(f"ERROR: {e}")

# --- Scenario C: Expired OTP ---
print("\n--- Scenario C: Expired OTP ---")
user_id_3 = "testuser_789"
register_user(user_id_3, "test3@example.com")
try:
    print(f"\nInitiating OTP login for {user_id_3}...")
    initiate_otp_login(user_id_3)
    
    correct_otp_3 = _otp_store[user_id_3]["otp"]
    print(f"DEBUG: User receives OTP: {correct_otp_3}")

    # Simulate time passing beyond expiration (5 minutes + a little extra)
    print("Simulating 301 seconds (5 min + 1 sec) for OTP to expire...")
    time.sleep(301) 

    print(f"Verifying expired OTP '{correct_otp_3}' for {user_id_3}...")
    verify_otp(user_id_3, correct_otp_3)
    print(f"ERROR: This line should not be reached for expired OTP.")
except OTPExpiredError as e:
    print(f"EXPECTED ERROR: {e} (User needs to request a new OTP)")
except Exception as e:
    print(f"ERROR: {e}")

# --- Scenario D: No active OTP for user ---
print("\n--- Scenario D: No Active OTP ---")
user_id_4 = "testuser_000"
register_user(user_id_4, "test4@example.com")
try:
    print(f"\nAttempting to verify OTP for {user_id_4} WITHOUT initiating it first...")
    verify_otp(user_id_4, "123456") # Any valid-format OTP
except OTPNotFoundError as e:
    print(f"EXPECTED ERROR: {e} (User must initiate OTP login first)")
except Exception as e:
    print(f"ERROR: {e}")
```

## API Reference

### Constants
*   `OTP_LENGTH` (int): The fixed length of the OTP (default: 6).
*   `OTP_EXPIRATION_SECONDS` (int): The duration in seconds for which an OTP is valid (default: 300 seconds, or 5 minutes).

### Custom Exceptions
*   `UserNotFoundError`: Raised when a specified user ID is not found.
*   `OTPGenerationError`: Raised when there's an issue generating the OTP.
*   `OTPSendError`: Raised when there's an issue simulating the OTP email sending.
*   `OTPVerificationError`: Base exception for all OTP verification failures.
    *   `OTPNotFoundError`: Raised when no active OTP is found for a user (e.g., not initiated, already verified, or removed).
    *   `OTPExpiredError`: Raised when the submitted OTP has exceeded its validity period.
    *   `InvalidOTPError`: Raised when the submitted OTP does not match the stored OTP.

### Functions

#### `register_user(user_id: str, email: str) -> None`
Registers a new user or updates an existing user's email in the mock database.
*   **Args**:
    *   `user_id` (str): Unique identifier for the user.
    *   `email` (str): Registered email address for the user.
*   **Raises**:
    *   `ValueError`: If `user_id` or `email` is empty.

#### `initiate_otp_login(user_id: str) -> str`
Initiates the OTP verification process for a user. Generates a new 6-digit OTP, stores it with a timestamp, and simulates sending it to the user's registered email.
*   **Args**:
    *   `user_id` (str): The unique identifier of the user attempting to log in.
*   **Returns**:
    *   `str`: A message indicating that OTP verification is required and sent.
*   **Raises**:
    *   `UserNotFoundError`: If the user does not exist.
    *   `OTPGenerationError`: If there's an issue generating the OTP.
    *   `OTPSendError`: If there's an issue sending the OTP email.

#### `verify_otp(user_id: str, submitted_otp: str) -> bool`
Verifies the submitted OTP against the stored OTP for a given user. The OTP must be valid, not expired, and match the stored code. Successfully verified OTPs are invalidated (removed from storage).
*   **Args**:
    *   `user_id` (str): The unique identifier of the user.
    *   `submitted_otp` (str): The OTP code submitted by the user.
*   **Returns**:
    *   `bool`: `True` if the OTP is successfully verified.
*   **Raises**:
    *   `UserNotFoundError`: If the user does not exist.
    *   `ValueError`: If `submitted_otp` is not a string, empty, or not a `OTP_LENGTH`-digit number.
    *   `OTPNotFoundError`: If no OTP was initiated or found for the user.
    *   `OTPExpiredError`: If the OTP has expired.
    *   `InvalidOTPError`: If the submitted OTP does not match the stored OTP.

### Helper/Internal Functions (not intended for direct external use)

#### `_generate_otp(length: int = OTP_LENGTH) -> str`
Generates a random numeric OTP of the specified length.
*   **Args**:
    *   `length` (int): The desired length of the OTP.
*   **Returns**:
    *   `str`: The generated OTP.
*   **Raises**:
    *   `OTPGenerationError`: If the length is not a positive integer or other generation issues occur.

#### `_send_email_otp(email: str, otp: str) -> None`
Simulates sending an OTP to the user's registered email address. In a production environment, this would integrate with an actual email service provider.
*   **Args**:
    *   `email` (str): The recipient's email address.
    *   `otp` (str): The OTP to send.
*   **Raises**:
    *   `OTPSendError`: If there's an issue simulating the email sending process or input validation fails.

#### `_get_user_email(user_id: str) -> str`
Retrieves the email address for a given user ID from the mock database.
*   **Args**:
    *   `user_id` (str): The unique identifier for the user.
*   **Returns**:
    *   `str`: The registered email address.
*   **Raises**:
    *   `UserNotFoundError`: If the user ID is not found.

## Edge Cases & Error Handling
The implementation includes robust error handling to address various scenarios:

*   **User Not Found**: Attempts to initiate or verify OTP for a non-existent `user_id` will raise a `UserNotFoundError`.
*   **OTP Not Initiated**: If `verify_otp` is called without a preceding `initiate_otp_login` or after a successful verification, an `OTPNotFoundError` is raised. This also applies if an OTP was previously removed from the store for any reason.
*   **Expired OTP**: If `verify_otp` is called with an OTP that has exceeded `OTP_EXPIRATION_SECONDS`, an `OTPExpiredError` is raised. The expired OTP is automatically removed from storage.
*   **Invalid OTP**: If the `submitted_otp` does not match the stored OTP, an `InvalidOTPError` is raised. Importantly, the OTP is *not* removed from storage on an invalid attempt, allowing the user to retry within the expiration window.
*   **Malformed Input**:
    *   `register_user`: Raises `ValueError` if `user_id` or `email` is empty.
    *   `_send_email_otp`: Raises `OTPSendError` if `email` is empty or `otp` is not a `OTP_LENGTH`-digit string.
    *   `verify_otp`: Raises `ValueError` if `submitted_otp` is not a `OTP_LENGTH`-digit string.
*   **OTP Generation Failure**: Rare, but issues during OTP generation will raise an `OTPGenerationError`.
*   **OTP Sending Failure**: Issues during the simulated email sending process will raise an `OTPSendError`. In a real system, this could indicate problems with the email service provider.
*   **Single-Use Token**: Upon successful verification, the OTP is immediately removed from `_otp_store` to prevent replay attacks and ensure it's a single-use token.
*   **Multiple `initiate_otp_login` calls**: If `initiate_otp_login` is called multiple times for the same user, each new call overwrites the previous OTP in the store, ensuring only the latest OTP is valid.

## Testing
The `if __name__ == "__main__":` block in the provided code serves as a basic demonstration and test suite, covering several key scenarios:

*   **Successful Login Flow**: Demonstrates initiating OTP, retrieving the correct OTP, and successfully verifying it.
*   **Invalid OTP Submission**: Shows that submitting an incorrect OTP raises an `InvalidOTPError` but allows for a retry with the correct OTP within the expiration window.
*   **Expired OTP**: Simulates the passage of time to demonstrate that an expired OTP raises an `OTPExpiredError`.
*   **User Not Found**: Confirms that attempts to initiate login for a non-existent user raise a `UserNotFoundError`.
*   **Re-verification After Success**: Tests that attempting to verify an OTP that was already successfully used (and thus removed) raises an `OTPNotFoundError`.
*   **Invalid Submitted OTP Format**: Checks that `verify_otp` correctly validates the format of the submitted OTP and raises a `ValueError` for malformed inputs.

For a production-grade system, it is recommended to implement:
*   **Unit Tests**: Use a testing framework (e.g., `pytest`) to test each function and exception handling in isolation.
*   **Integration Tests**: Test the full flow involving `initiate_otp_login` and `verify_otp`, potentially integrating with a mock email service to verify email sending.
*   **Security Testing**: Conduct penetration testing to ensure the OTP mechanism is resilient against brute-force attacks, timing attacks, and other common vulnerabilities.
*   **Performance Testing**: Evaluate the performance of OTP generation and verification under load.

## Author & Date
*   **Author**: Technical Writer
*   **Date**: 2023-10-27