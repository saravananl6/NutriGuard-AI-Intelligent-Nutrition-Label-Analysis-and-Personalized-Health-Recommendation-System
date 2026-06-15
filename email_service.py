from flask_mail import Message, Mail
from flask import current_app, render_template_string
import json

mail = Mail()

def send_alert_email(user_email, check_data):
    """Send email alert for not recommended food products"""
    try:
        risk_factors = json.loads(check_data.risk_factors) if isinstance(check_data.risk_factors, str) else check_data.risk_factors
        safe_factors = json.loads(check_data.safe_factors) if isinstance(check_data.safe_factors, str) else check_data.safe_factors
        
        risk_factors_html = ''.join([f'<li style="color: #e74c3c; margin: 5px 0;">{factor}</li>' for factor in risk_factors])
        safe_factors_html = ''.join([f'<li style="color: #27ae60; margin: 5px 0;">{factor}</li>' for factor in safe_factors]) if safe_factors else '<li style="color: #7f8c8d;">None identified</li>'
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .alert-badge {{
                    background-color: #e74c3c;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    display: inline-block;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .section {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f9f9f9;
                    border-left: 4px solid #FF6B6B;
                    border-radius: 5px;
                }}
                .section h3 {{
                    margin-top: 0;
                    color: #2c3e50;
                }}
                ul {{
                    padding-left: 20px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 2px solid #eee;
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="alert-badge">⚠️ HEALTH ALERT</div>
                    <h1 style="margin: 10px 0;">Nutrition Check Warning</h1>
                </div>
                
                <p>Dear User,</p>
                
                <p>Our nutrition analysis system has identified potential health concerns with a food product you recently scanned.</p>
                
                <div class="section">
                    <h3>🔴 Risk Factors Identified:</h3>
                    <ul>
                        {risk_factors_html}
                    </ul>
                </div>
                
                <div class="section">
                    <h3>✅ Safe Factors:</h3>
                    <ul>
                        {safe_factors_html}
                    </ul>
                </div>
                
                <div class="section">
                    <h3>📋 Analysis Details:</h3>
                    <p><strong>Age Analyzed For:</strong> {check_data.age} years old</p>
                    <p><strong>Decision:</strong> <span style="color: #e74c3c; font-weight: bold;">{check_data.decision}</span></p>
                    <p><strong>Reason:</strong> {check_data.reason}</p>
                </div>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>⚕️ Recommendation:</strong> Consider consulting with a healthcare professional or nutritionist for personalized dietary advice.
                </div>
                
                <div class="footer">
                    <p><strong>Nutritrack</strong> - Your Health Nutrition Compliance Checker</p>
                    <p>This is an automated alert. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject='⚠️ Nutritrack Alert: Product Not Recommended',
            recipients=[user_email],
            html=html_body
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Email sending error: {str(e)}")
        return False