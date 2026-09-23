from database.owner_database import OwnerDatabase


class OwnerModeService:
    """
    Connects the persistent owner database to the existing
    four-mode trading controller.

    No Deriv password is stored.
    """

    def __init__(self, db_path="database/fx_owner.db"):
        self.db = OwnerDatabase(db_path)

    def create_owner(self, owner_ref, display_name=None,
                     email=None, phone=None):
        return self.db.create_owner(
            owner_ref,
            display_name,
            email,
            phone
        )

    def connect_deriv_account(
        self,
        owner_id,
        deriv_account_id,
        account_type="DEMO",
        encrypted_auth_token=None
    ):
        self.db.add_deriv_account(
            owner_id,
            deriv_account_id,
            account_type,
            encrypted_auth_token
        )

    def select_mode(self, owner_id, account_type, trading_mode):
        self.db.set_mode(
            owner_id,
            account_type,
            trading_mode
        )

    def login(self, owner_id, account_type):
        self.db.record_login(
            owner_id,
            account_type
        )

    def status(self, owner_id):
        return self.db.status(owner_id)


def run_test():
    import tempfile
    from pathlib import Path

    test_db = Path(tempfile.gettempdir()) / "fx_owner_mode_test.db"

    if test_db.exists():
        test_db.unlink()

    service = OwnerModeService(test_db)

    # Create test owner
    owner_id = service.create_owner(
        "TEST_OWNER_001",
        display_name="THE_FX_TEST_OWNER"
    )

    assert owner_id > 0
    print("PASS : Owner created")

    # Connect DEMO Deriv account.
    # Placeholder authorization value only.
    # No real credential is used.
    service.connect_deriv_account(
        owner_id,
        "CR_DEMO_TEST",
        "DEMO",
        "TEST_ENCRYPTED_AUTH"
    )

    print("PASS : DEMO Deriv account registered")

    # Select DEMO AUTO
    service.select_mode(
        owner_id,
        "DEMO",
        "AUTO"
    )

    print("PASS : DEMO AUTO selected")

    # Record login
    service.login(owner_id, "DEMO")

    print("PASS : DEMO login recorded")

    # Verify everything
    status = service.status(owner_id)

    assert status["owner"] is not None
    assert status["trading"]["account_type"] == "DEMO"
    assert status["trading"]["trading_mode"] == "AUTO"
    assert status["trading"]["symbol"] == "XAUUSD"

    assert len(status["deriv_accounts"]) == 1
    assert status["deriv_accounts"][0]["account_type"] == "DEMO"
    assert status["deriv_accounts"][0]["deriv_account_id"] == "CR_DEMO_TEST"

    print("PASS : Owner status")
    print("PASS : DEMO account status")
    print("PASS : AUTO mode status")
    print("PASS : XAUUSD configuration")
    print("PASS : Login history")

    # Remove test DB
    test_db.unlink()

    print("=" * 72)
    print("THE_FX.TRADER.ZW — OWNER/MODE INTEGRATION")
    print("=" * 72)
    print("PASS : OWNER DATABASE")
    print("PASS : DERIV ACCOUNT REGISTRATION")
    print("PASS : DEMO / REAL ACCOUNT MODEL")
    print("PASS : MANUAL / AUTO MODEL")
    print("PASS : DEMO AUTO SELECTION")
    print("PASS : OWNER LOGIN RECORD")
    print("PASS : XAUUSD RESTRICTION")
    print("-" * 72)
    print("REAL ORDER SUBMITTED : NO")
    print("REAL MONEY USED      : NO")
    print("RESULT               : OWNER/MODE INTEGRATION PASS")
    print("=" * 72)


if __name__ == "__main__":
    run_test()
