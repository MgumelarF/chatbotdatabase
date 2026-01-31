# email_service.py
import os
import resend
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_TEST_MODE = os.environ.get("EMAIL_TEST_MODE", "false").lower() == "true"
TESTING_EMAIL = os.environ.get("EMAIL_TEST_ADDRESS")  # email verified di Resend

resend.api_key = RESEND_API_KEY


def send_activation_email(to_email: str, username: str, activation_link: str):
    """
    Kirim email aktivasi akun admin
    - TEST MODE  : email dikirim ke email developer (verified)
    - PROD MODE  : email dikirim ke user asli
    """

    # =========================
    # VALIDATION
    # =========================
    if not RESEND_API_KEY:
        return {
            "success": False,
            "error": "RESEND_API_KEY not set"
        }

    if EMAIL_TEST_MODE and not TESTING_EMAIL:
        return {
            "success": False,
            "error": "EMAIL_TEST_ADDRESS not set while EMAIL_TEST_MODE is true"
        }

    # Tentukan penerima
    recipient_email = TESTING_EMAIL if EMAIL_TEST_MODE else to_email

    # =========================
    # EMAIL CONTENT
    # =========================
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #2f3e66; padding: 25px; color: white; text-align: center;">
            <h1 style="margin: 0;">Kelurahan Cipinang Melayu</h1>
            <p style="margin: 5px 0 0;">Sistem Administrasi Digital</p>
        </div>

        <div style="background: #ffffff; padding: 30px;">
            <h2 style="color: #2f3e66;">Aktivasi Akun Admin</h2>

            <p>Halo <strong>{username}</strong>,</p>

            <p>
                Akun admin Anda telah berhasil dibuat.
                Silakan klik tombol di bawah ini untuk mengaktifkan akun:
            </p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{activation_link}"
                   style="background: #4CAF50; color: white; padding: 14px 28px;
                          text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Aktivasi Akun
                </a>
            </div>

            <p style="font-size: 14px; color: #666;">
                Jika tombol tidak berfungsi, salin dan buka link berikut di browser:
            </p>

            <div style="background: #f5f5f5; padding: 12px; font-size: 13px;">
                <code>{activation_link}</code>
            </div>

            <p style="font-size: 12px; color: #999; margin-top: 30px;">
                Email ini dikirim secara otomatis. Mohon tidak membalas email ini.
            </p>
        </div>
    </div>
    """

    # =========================
    # SEND EMAIL
    # =========================
    try:
        resend.Emails.send({
            "from": "Kelurahan Cipinang Melayu <onboarding@resend.dev>",
            "to": recipient_email,
            "subject": "Aktivasi Akun Admin Kelurahan Cipinang Melayu",
            "html": html_content
        })

        return {
            "success": True,
            "mode": "TEST" if EMAIL_TEST_MODE else "PRODUCTION"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
