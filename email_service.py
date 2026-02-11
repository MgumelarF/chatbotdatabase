import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

def send_activation_email(to_email, username, activation_link):
    """Kirim email aktivasi menggunakan Resend"""

    if not os.getenv("RESEND_API_KEY"):
        print("⚠️ RESEND_API_KEY not set, skipping email")
        return {"success": False, "error": "API Key not set"}

    try:
        # Ambil email testing dari environment variable
        testing_email = os.getenv("TEST_EMAIL")
        if not testing_email:
            print("⚠️ TEST_EMAIL not set, skipping email")
            return {"success": False, "error": "Test email not set"}

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            ...
            <strong>Actual recipient:</strong> {to_email}<br>
            <strong>Username:</strong> {username}
            ...
            <a href="{activation_link}" style="...">🔓 Aktivasi Akun Sekarang</a>
            ...
        </div>
        """

        r = resend.Emails.send({
            "from": "Kelurahan Cipinang Melayu <onboarding@resend.dev>",
            "to": testing_email,
            "subject": f"🔐 [TEST] Aktivasi Akun untuk {username} ({to_email})",
            "html": html_content
        })

        print(f"✅ [TEST MODE] Email sent to {testing_email}")
        print(f"   Intended for: {to_email} (username: {username})")
        print(f"   Activation link: {activation_link}")

        return {
            "success": True,
            "testing_mode": True,
            "sent_to": testing_email,
            "intended_for": to_email,
            "activation_link": activation_link
        }

    except Exception as e:
        print(f"❌ Email failed: {e}")
        return {"success": False, "error": str(e)}