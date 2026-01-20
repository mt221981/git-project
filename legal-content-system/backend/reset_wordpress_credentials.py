"""
Script to reset WordPress site credentials with proper encryption.

Usage:
    python reset_wordpress_credentials.py

This will prompt you to enter the WordPress credentials for each active site
and re-encrypt them with the current SECRET_KEY.
"""

from app.database import SessionLocal
from app.models.wordpress_site import WordPressSite
from app.utils.encryption import encrypt_text, decrypt_text


def main():
    db = SessionLocal()

    try:
        # Get all WordPress sites
        sites = db.query(WordPressSite).all()

        if not sites:
            print("No WordPress sites found in database.")
            return

        print(f"Found {len(sites)} WordPress site(s)")
        print("=" * 60)

        for site in sites:
            print(f"\nSite: {site.site_name}")
            print(f"URL: {site.site_url}")
            print(f"Active: {site.is_active}")
            print(f"Username: {site.api_username}")

            # Try to decrypt existing password
            try:
                current_password = decrypt_text(site.api_password_encrypted) if site.api_password_encrypted else None
                if current_password:
                    print(f"Current password can be decrypted successfully")
                else:
                    print("No password currently set")
            except Exception as e:
                print(f"WARNING: Cannot decrypt current password: {str(e)}")
                current_password = None

            # Ask if user wants to update this site
            update = input("\nUpdate credentials for this site? (y/n): ").strip().lower()

            if update == 'y':
                # Get new credentials
                username = input(f"Username (current: {site.api_username}): ").strip()
                if not username:
                    username = site.api_username

                password = input("Password (leave empty to skip): ").strip()

                if password:
                    # Encrypt and save
                    encrypted_password = encrypt_text(password)
                    site.api_username = username
                    site.api_password_encrypted = encrypted_password
                    db.commit()
                    print("✓ Credentials updated and encrypted successfully")
                else:
                    print("✗ Skipped - no password entered")
            else:
                print("Skipped")

        print("\n" + "=" * 60)
        print("Done!")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
