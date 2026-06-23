import pytest
import time
from unittest.mock import patch, MagicMock

# Assuming the provided code is in a file named 'add_otp_verification_during_login.py'
from add_otp_verification_during_login import (
    OTP_LENGTH, OTP_EXPIRATION_SECONDS,
    _mock_user_db, _otp_store,
    UserNotFoundError, OTPGenerationError, OTPSendError,
    OTPNotFoundError, OTPExpiredError, InvalidOTPError,
    _generate_otp, _send_email_otp, register_user, _get_user_email,
    initiate_otp_login, verify_otp
)

# Fixture to reset mock databases before each test
@pytest.fixture(autouse=True)
def clean_databases():
    _mock_user_db.clear()
    _otp_store.clear()
    yield

# Fixture to mock time.time() for controlled time progression
@pytest.fixture
def mock_time(mocker):
    # Start time at a fixed point for consistency (e.g., Mar 15, 2023 12:00:00 PM UTC)
    mocked_time = 1678886400.0
    mocker.patch('time.time', return_value=mocked_time)
    return mocker.patch('time.time')

# Fixture to mock random.choices for predictable OTP generation
@pytest.fixture
def mock_random_choices(mocker):
    # Default to a predictable 6-digit OTP "123456"
    mocker.patch('random.choices', return_value=['1', '2', '3', '4', '5', '6'])
    return mocker.patch('random.choices')

# Fixture to mock _send_email_otp to prevent actual sleep and external calls
@pytest.fixture
def mock_send_email_otp(mocker):
    return mocker.patch('add_otp_verification_during_login._send_email_otp')

class TestHelperFunctions:

    # Tests _generate_otp with default valid length
    def test_generate_otp_success_default_length(self, mock_random_choices):
        otp = _generate_otp()
        assert len(otp) == OTP_LENGTH
        assert otp == "123456" # From mock_random_choices
        mock_random_choices.assert_called_once_with("0123456789", k=OTP_LENGTH)

    # Tests _generate_otp with a custom valid length
    def test_generate_otp_success_custom_length(self, mock_random_choices):
        mock_random_choices.return_value = ['7', '8', '9']
        otp = _generate_otp(length=3)
        assert len(otp) == 3
        assert otp == "789"
        mock_random_choices.assert_called_once_with("0123456789", k=3)

    # Tests _generate_otp with zero length (edge case)
    def test_generate_otp_failure_zero_length(self):
        with pytest.raises(OTPGenerationError, match="OTP length must be a positive integer."):
            _generate_otp(length=0)

    # Tests _generate_otp with negative length (edge case)
    def test_generate_otp_failure_negative_length(self):
        with pytest.raises(OTPGenerationError, match="OTP length must be a positive integer."):
            _generate_otp(length=-1)

    # Tests _generate_otp with non-integer length
    def test_generate_otp_failure_non_integer_length(self):
        with pytest.raises(OTPGenerationError, match="OTP length must be a positive integer."):
            _generate_otp(length="abc")

    # Tests _send_email_otp with valid inputs
    def test_send_email_otp_success(self, mocker):
        mock_sleep = mocker.patch('time.sleep')
        email = "test@example.com"
        otp = "123456"
        _send_email_otp(email, otp)
        mock_sleep.assert_called_once_with(0.1)

    # Tests _send_email_otp with empty email
    def test_send_email_otp_failure_empty_email(self):
        with pytest.raises(OTPSendError, match="Recipient email cannot be empty."):
            _send_email_otp("", "123456")

    # Tests _send_email_otp with None email
    def test_send_email_otp_failure_none_email(self):
        with pytest.raises(OTPSendError, match="Recipient email cannot be empty."):
            _send_email_otp(None, "123456")

    # Tests _send_email_otp with non-string email
    def test_send_email_otp_failure_non_string_email(self):
        with pytest.raises(OTPSendError, match="Recipient email cannot be empty."):
            _send_email_otp(123, "123456")

    # Tests _send_email_otp with OTP of incorrect length
    def test_send_email_otp_failure_invalid_otp_length(self):
        with pytest.raises(OTPSendError, match=f"OTP '123' is invalid for sending. Must be a {OTP_LENGTH}-digit string."):
            _send_email_otp("test@example.com", "123")

    # Tests _send_email_otp with non-digit OTP
    def test_send_email_otp_failure_non_digit_otp(self):
        with pytest.raises(OTPSendError, match=f"OTP 'abcde1' is invalid for sending. Must be a {OTP_LENGTH}-digit string."):
            _send_email_otp("test@example.com", "abcde1")

    # Tests _send_email_otp with empty OTP
    def test_send_email_otp_failure_empty_otp(self):
        with pytest.raises(OTPSendError, match=f"OTP '' is invalid for sending. Must be a {OTP_LENGTH}-digit string."):
            _send_email_otp("test@example.com", "")

    # Tests _send_email_otp with None OTP
    def test_send_email_otp_failure_none_otp(self):
        with pytest.raises(OTPSendError, match=f"OTP 'None' is invalid for sending. Must be a {OTP_LENGTH}-digit string."):
            _send_email_otp("test@example.com", None)

class TestUserManagement:

    # Tests registering a new user successfully
    def test_register_user_success_new_user(self):
        register_user("user1", "user1@example.com")
        assert _mock_user_db["user1"] == "user1@example.com"

    # Tests registering an existing user (should update email without error)
    def test_register_user_success_existing_user(self):
        register_user("user1", "old@example.com")
        register_user("user1", "new@example.com")
        assert _mock_user_db["user1"] == "new@example.com"

    # Tests registering with empty user_id
    def test_register_user_failure_empty_user_id(self):
        with pytest.raises(ValueError, match="User ID and email cannot be empty."):
            register_user("", "test@example.com")

    # Tests registering with empty email
    def test_register_user_failure_empty_email(self):
        with pytest.raises(ValueError, match="User ID and email cannot be empty."):
            register_user("user1", "")

    # Tests registering with None user_id
    def test_register_user_failure_none_user_id(self):
        with pytest.raises(ValueError, match="User ID and email cannot be empty."):
            register_user(None, "test@example.com")

    # Tests registering with None email
    def test_register_user_failure_none_email(self):
        with pytest.raises(ValueError, match="User ID and email cannot be empty."):
            register_user("user1", None)

    # Tests retrieving email for an existing user
    def test_get_user_email_success(self):
        _mock_user_db["user1"] = "user1@example.com"
        email = _get_user_email("user1")
        assert email == "user1@example.com"

    # Tests retrieving email for a non-existent user
    def test_get_user_email_failure_user_not_found(self):
        with pytest.raises(UserNotFoundError, match="User with ID 'nonexistent' not found."):
            _get_user_email("nonexistent")

class TestOTPFlow:

    # Tests successful initiation of OTP login
    def test_initiate_otp_login_success(self, mock_random_choices, mock_send_email_otp, mock_time):
        user_id = "user1"
        email = "user1@example.com"
        register_user(user_id, email)

        response = initiate_otp_login(user_id)

        assert f"OTP sent to {email}. Please verify within {OTP_EXPIRATION_SECONDS // 60} minutes." in response
        assert user_id in _otp_store
        assert _otp_store[user_id]["otp"] == "123456" # From mock_random_choices
        assert _otp_store[user_id]["timestamp"] == mock_time.return_value
        mock_send_email_otp.assert_called_once_with(email, "123456")

    # Tests initiating OTP for a non-existent user
    def test_initiate_otp_login_failure_user_not_found(self, mock_random_choices, mock_send_email_otp):
        with pytest.raises(UserNotFoundError, match="User with ID 'nonexistent' not found."):
            initiate_otp_login("nonexistent")
        assert "nonexistent" not in _otp_store
        mock_random_choices.assert_not_called()
        mock_send_email_otp.assert_not_called()

    # Tests that initiating OTP for the same user twice overwrites the previous OTP
    def test_initiate_otp_login_overwrites_previous_otp(self, mock_random_choices, mock_send_email_otp, mock_time):
        user_id = "user1"
        email = "user1@example.com"
        register_user(user_id, email)

        # First initiation
        initiate_otp_login(user_id)
        original_otp = _otp_store[user_id]["otp"]
        original_timestamp = _otp_store[user_id]["timestamp"]
        mock_send_email_otp.assert_called_once_with(email, original_otp)
        mock_send_email_otp.reset_mock() # Reset mock for second call

        # Advance time and change expected OTP
        mock_time.return_value += 10.0
        mock_random_choices.return_value = ['6', '5', '4', '3', '2', '1']

        # Second initiation
        initiate_otp_login(user_id)
        new_otp = _otp_store[user_id]["otp"]
        new_timestamp = _otp_store[user_id]["timestamp"]

        assert new_otp != original_otp
        assert new_otp == "654321"
        assert new_timestamp > original_timestamp
        assert new_timestamp == mock_time.return_value
        mock_send_email_otp.assert_called_once_with(email, new_otp)

    # Tests `initiate_otp_login` when `_generate_otp` fails
    def test_initiate_otp_login_failure_generate_otp(self, mocker, mock_send_email_otp):
        user_id = "user1"
        email = "user1@example.com"
        register_user(user_id, email)
        mocker.patch('add_otp_verification_during_login._generate_otp', side_effect=OTPGenerationError("Gen failed"))

        with pytest.raises(OTPGenerationError, match="Gen failed"):
            initiate_otp_login(user_id)
        assert user_id not in _otp_store # No OTP should be stored if generation fails
        mock_send_email_otp.assert_not_called()

    # Tests `initiate_otp_login` when `_send_email_otp` fails
    def test_initiate_otp_login_failure_send_email_otp(self, mocker, mock_random_choices):
        user_id = "user1"
        email = "user1@example.com"
        register_user(user_id, email)
        mocker.patch('add_otp_verification_during_login._send_email_otp', side_effect=OTPSendError("Send failed"))

        with pytest.raises(OTPSendError, match="Send failed"):
            initiate_otp_login(user_id)
        # OTP should still be stored even if email sending fails, as it was generated
        assert user_id in _otp_store
        assert _otp_store[user_id]["otp"] == "123456"

    # Tests successful OTP verification
    def test_verify_otp_success(self, mock_time, mock_random_choices):
        user_id = "user1"
        email = "user1@example.com"
        register_user(user_id, email)
        initiate_otp_login(user_id) # This populates _otp_store with "123456" and current time
        correct_otp = _otp_store[user_id]["otp"]

        # Ensure time hasn't expired
        mock_time.return_value += OTP_EXPIRATION_SECONDS - 10 # 10 seconds before expiry

        assert verify_otp(user_id, correct_otp) is True
        assert user_id not in _otp_store # OTP should be removed after successful verification

    # Tests OTP verification for an invalid format (non-digit or wrong length)
    @pytest.mark.parametrize("bad_otp", ["abcde1", "12345a", "", "123", "1234567"])
    def test_verify_otp_failure_invalid_format(self, bad_otp):
        with pytest.raises(ValueError, match=f"Submitted OTP '{bad_otp}' is invalid. Must be a {OTP_LENGTH}-digit string."):
            verify_otp("user1", bad_otp)

    # Tests OTP verification with None as submitted_otp
    def test_verify_otp_failure_none_submitted_otp(self):
        with pytest.raises(ValueError, match=f"Submitted OTP 'None' is invalid. Must be a {OTP_LENGTH}-digit string."):
            verify_otp("user1", None)

    # Tests OTP verification for a non-existent user
    def test_verify_otp_failure_user_not_found(self):
        with pytest.raises(UserNotFoundError, match="User with ID 'nonexistent' not found."):
            verify_otp("nonexistent", "123456")
        assert "nonexistent" not in _otp_store # No OTP should be stored or checked for non-existent users

    # Tests OTP verification when no OTP was ever initiated for the user
    def test_verify_otp_failure_no_otp_initiated(self):
        user_id = "user1"
        register_user(user_id, "user1@example.com") # User exists, but no OTP initiated
        with pytest.raises(OTPNotFoundError, match=f"No active OTP found for user '{user_id}'. Please initiate login again."):
            verify_otp(user_id, "123456")
        assert user_id not in _otp_store # Should remain empty

    # Tests OTP verification after OTP has expired
    def test_verify_otp_failure_expired_otp(self, mock_time, mock_random_choices):
        user_id = "user1"
        email = "user1@example.com"
        register_user(user_id, email)
        initiate_otp_login(user_id) # OTP generated and stored

        # Advance time past expiration
        mock_time.return_value += OTP_EXPIRATION_SECONDS + 1

        with pytest.raises(OTPExpiredError, match=f"OTP for user '{user_id}' has expired. Please request a new one."):
            verify_otp(user_id, "123456")
        assert user_id not in _otp_store # Expired OTP should be removed

    # Tests OTP verification with an incorrect OTP
    def test_verify_otp_failure_invalid_otp(self, mock_time, mock_random_choices):
        user_id = "user1"
        email = "user1@example.com"
        register_user(user_id, email)
        initiate_otp_login(user_id) # OTP stored as "123456"

        # Ensure time is within expiry
        mock_time.return_value += OTP_EXPIRATION_SECONDS - 10

        with pytest.raises(InvalidOTPError, match=f"Invalid OTP submitted for user '{user_id}'. Please try again."):
            verify_otp(user_id, "999999")
        assert user_id in _otp_store # Incorrect OTP should NOT be removed

    # Tests multiple incorrect OTP attempts within the expiration window
    def test_verify_otp_multiple_invalid_attempts(self, mock_time, mock_random_choices):
        user_id = "user1"
        email = "user1@example.com"
        register_user(user_id, email)
        initiate_otp_login(user_id)
        correct_otp = _otp_store[user_id]["otp"]

        # Ensure time is within expiry
        mock_time.return_value += 10 # A little time passed

        with pytest.raises(InvalidOTPError):
            verify_otp(user_id, "111111")
        assert user_id in _otp_store # Still in store

        with pytest.raises(InvalidOTPError):
            verify_otp(user_id, "222222")
        assert user_id in _otp_store # Still in store

        # Advance time but still within window
        mock_time.return_value += OTP_EXPIRATION_SECONDS - 30 # Just before expiry

        # Finally, correct OTP should work
        assert verify_otp(user_id, correct_otp) is True
        assert user_id not in _otp_store # OTP removed after success

    # Tests that OTP cannot be reused after successful verification
    def test_verify_otp_cannot_be_reused_after_success(self, mock_time, mock_random_choices):
        user_id = "user1"
        email = "user1@example.com"
        register_user(user_id, email)
        initiate_otp_login(user_id)
        correct_otp = _otp_store[user_id]["otp"]

        assert verify_otp(user_id, correct_otp) is True
        assert user_id not in _otp_store # OTP removed

        # Attempt to verify again with the same OTP
        with pytest.raises(OTPNotFoundError, match=f"No active OTP found for user '{user_id}'. Please initiate login again."):
            verify_otp(user_id, correct_otp)

    # Tests OTP verification after expiration, then immediately re-initiating and verifying successfully
    def test_verify_otp_flow_expired_then_new_otp(self, mock_time, mock_random_choices):
        user_id = "user1"
        register_user(user_id, "user1@example.com")

        # Initiate first OTP
        initiate_otp_login(user_id)
        old_otp = _otp_store[user_id]["otp"]
        mock_random_choices.reset_mock() # Reset for second generation

        # Advance time to expire the first OTP
        mock_time.return_value += OTP_EXPIRATION_SECONDS + 1
        with pytest.raises(OTPExpiredError):
            verify_otp(user_id, old_otp)
        assert user_id not in _otp_store # Old OTP removed

        # Re-initiate login, get a new OTP
        mock_time.return_value += 10 # A little more time
        mock_random_choices.return_value = ['7', '8', '9', '0', '1', '2']
        initiate_otp_login(user_id)
        new_otp = _otp_store[user_id]["otp"]
        assert new_otp == "789012"
        assert new_otp != old_otp

        # Verify new OTP
        mock_time.return_value += 10 # Still within new OTP's validity
        assert verify_otp(user_id, new_otp) is True
        assert user_id not in _otp_store # New OTP removed after success

    # Tests that `verify_otp` does not accidentally create or modify user_db
    def test_verify_otp_does_not_mutate_user_db(self):
        initial_user_db_state = _mock_user_db.copy()
        user_id = "nonexistent_user"
        with pytest.raises(UserNotFoundError):
            verify_otp(user_id, "123456")
        assert _mock_user_db == initial_user_db_state # Ensure user_db is unchanged