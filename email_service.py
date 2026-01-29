# email_service.py
import os
import resend
from datetime import datetime

# Setup Resend
resend.api_key = os.environ.get("RESEND_API_KEY")

def send_activation_email(to_email, username, activation_link):
    """Kirim email aktivasi menggunakan Resend"""
    
    if not resend.api_key:
        print("⚠️ RESEND_API_KEY not set, skipping email")
        return False
    
    try:
        # UNTUK TESTING: Kirim ke email verified kamu sendiri
        # Tapi dalam subject tunjukkan untuk siapa
        testing_email = "fajafi217@gmail.com"  # Email verified kamu di Resend
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #2f3e66 0%, #4c5f9e 100%); 
                       padding: 25px; border-radius: 10px 10px 0 0; color: white; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">Kelurahan Cipinang Melayu</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Sistem Administrasi Digital</p>
            </div>
            
            <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; 
                       box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                
                <div style="background: #fff8e1; padding: 15px; border-radius: 5px; 
                           margin-bottom: 20px; border-left: 4px solid #ffb300;">
                    <p style="margin: 0; color: #5d4037; font-size: 14px;">
                        <strong>⚠️ TEST MODE - DEMO ONLY</strong><br>
                        <strong>Actual recipient:</strong> {to_email}<br>
                        <strong>Username:</strong> {username}
                    </p>
                </div>
                
                <h2 style="color: #2f3e66; margin-top: 0;">🔐 Aktivasi Akun Admin</h2>
                
                <p>Halo <strong style="color: #2f3e66;">{username}</strong>,</p>
                <p>Akun admin Anda untuk <strong>Kelurahan Cipinang Melayu</strong> telah dibuat.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{activation_link}" 
                       style="background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%); 
                              color: white; 
                              padding: 15px 30px; 
                              text-decoration: none; 
                              border-radius: 8px; 
                              font-weight: bold;
                              font-size: 16px;
                              display: inline-block;
                              box-shadow: 0 4px 6px rgba(76, 175, 80, 0.3);
                              transition: transform 0.2s;">
                       🔓 Aktivasi Akun Sekarang
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    Atau copy link aktivasi berikut ke browser:
                </p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; 
                           border: 1px solid #e9ecef; margin: 15px 0;">
                    <code style="word-break: break-all; font-family: 'Courier New', monospace; 
                           font-size: 13px; color: #d63384;">
                        {activation_link}
                    </code>
                </div>
                
                <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; 
                           margin: 20px 0; border-left: 4px solid #4CAF50;">
                    <p style="margin: 0; color: #2e7d32; font-size: 14px;">
                        ⏰ <strong>Link berlaku 5 menit</strong><br>
                        Setelah klik link, Anda akan diminta membuat password untuk akun.
                    </p>
                </div>
                
                <div style="border-top: 1px solid #eee; margin-top: 30px; padding-top: 20px;">
                    <p style="color: #6c757d; font-size: 12px; text-align: center;">
                        Email ini dikirim otomatis. Jangan berikan link aktivasi kepada orang lain.<br>
                        © {datetime.now().year} Kelurahan Cipinang Melayu
                    </p>
                </div>
            </div>
        </div>
        """
        
        # Kirim ke email verified kamu sendiri (karena testing mode)
        r = resend.Emails.send({
            "from": "Kelurahan Cipinang Melayu <onboarding@resend.dev>",
            "to": testing_email,
            "subject": f"🔐 [TEST] Aktivasi Akun untuk {username} ({to_email})",
            "html": html_content
        })
        
        print(f"✅ [TEST MODE] Email sent to {testing_email}")
        print(f"   Intended for: {to_email} (username: {username})")
        print(f"   Activation link: {activation_link}")
        
        # Return dictionary bukan boolean
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