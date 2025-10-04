from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import smtplib
import os

load_dotenv()

class SendEmailVerification:
    def __init__(self) -> None:
        self.sender_email:str = os.getenv('sender_email')
        self.sender_password:str = os.getenv('sender_password')
        
    def send_verification_email(self, recipient_email: str, verification_code_or_link: str, type_email: str) -> None:
        match type_email:
            case 'create_account':
                subject = "🎉 Seu Código de Verificação Lectify"
                text = f"""Olá,

Seja bem-vindo(a) à Lectify!
Para concluir a criação da sua conta e começar a aproveitar todos os recursos, insira o código de verificação abaixo no campo indicado:

    {verification_code_or_link}

Este código é válido por 10 minutos.

Se você não realizou nenhuma tentativa de cadastro, basta ignorar este e-mail.

Atenciosamente,  
Equipe Lectify
"""
                
            case 'reset_password':
                subject = "🔒 Redefinição de Senha Lectify"
                text = f"""Olá,
Recebemos uma solicitação para redefinir a senha da sua conta Lectify Para prosseguir com a redefinição, clique no link abaixo:
    
    {verification_code_or_link}

Este código é válido por 10 minutos.

Se você não solicitou a redefinição de senha, por favor, ignore este e-mail. Sua senha permanecerá inalterada.

Atenciosamente,  
Equipe Lectify
"""
                
            case 'delete_account':
                subject = "⚠️ Confirmação de Exclusão de Conta Lectify"
                text = f"""Olá,
Recebemos uma solicitação para excluir sua conta Lectify. Para confirmar a exclusão, insira o código de verificação abaixo no campo indicado:

    {verification_code_or_link}

Este código é válido por 10 minutos.

Se você não solicitou a exclusão da conta, por favor, ignore este e-mail. Sua conta permanecerá ativa.

Atenciosamente,
Equipe Lectify
"""
                
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = recipient_email

        part = MIMEText(text, "plain")
        message.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, recipient_email, message.as_string())