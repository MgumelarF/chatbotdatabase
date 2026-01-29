# email_service.py
import os
import resend

# Setup Resend
resend.api_key = os.environ.get("RESEND_API_KEY")

def send_activation_email(to_email, username, activation_link):
    """Kirim email aktivasi menggunakan Resend"""
    
    if not resend.api_key:
        print("⚠️ RESEND_API_KEY not set, skipping email")
        return False
    
    try:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Aktivasi Akun Admin - Kelurahan Cipinang Melayu</h2>
            <p>Halo <strong>{username}</strong>,</p>
            <p>Akun admin Anda telah dibuat.</p>
            <p>Klik tombol di bawah untuk mengatur password:</p>
            <p style="margin: 30px 0;">
                <a href="{activation_link}" 
                   style="background: #4CAF50; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 5px; font-weight: bold;">
                   Aktivasi Akun
                </a>
            </p>
            <p>Atau copy link ini:<br>
            <code style="background: #f5f5f5; padding: 8px; border-radius: 3px;">
                {activation_link}
            </code></p>
            <p><small>Link berlaku 5 menit</small></p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Email ini dikirim otomatis dari sistem Kelurahan Cipinang Melayu.
            </p>
        </div>
        """
        
        # Kirim email via Resend API
        r = resend.Emails.send({
            "from": "Kelurahan Cipinang Melayu <onboarding@resend.dev>",
            "to": to_email,
            "subject": "Aktivasi Akun Admin",
            "html": html_content
        })
        
        print(f"✅ Email sent to {to_email}, ID: {r.get('id', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"❌ Email failed for {to_email}: {e}")
        return False