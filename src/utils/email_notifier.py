"""
Email Notification System
E-Mail-Benachrichtigungen für Ereignisse
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from datetime import datetime
from pathlib import Path


class EmailConfig:
    """E-Mail-Konfiguration"""
    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        username: str = "",
        password: str = "",
        from_address: str = "",
        use_tls: bool = True
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_address = from_address or username
        self.use_tls = use_tls


class EmailNotifier:
    """Sendet E-Mail-Benachrichtigungen"""

    def __init__(self, config: EmailConfig):
        self.config = config

    def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Sendet E-Mail

        Args:
            to_addresses: Empfänger-Adressen
            subject: Betreff
            body: Text-Inhalt
            html_body: Optional HTML-Inhalt
            attachments: Optional Liste von Dateipfaden

        Returns:
            True wenn erfolgreich
        """
        try:
            # Nachricht erstellen
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.from_address
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

            # Text-Teil
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # HTML-Teil
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            # Anhänge
            if attachments:
                for file_path in attachments:
                    self._attach_file(msg, file_path)

            # Senden
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()

                if self.config.username and self.config.password:
                    server.login(self.config.username, self.config.password)

                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Email error: {e}")
            return False

    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Fügt Datei als Anhang hinzu"""
        try:
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())

            encoders.encode_base64(part)

            filename = Path(file_path).name
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )

            msg.attach(part)

        except Exception as e:
            print(f"Attachment error: {e}")

    # ===== VORDEFINIERTE BENACHRICHTIGUNGEN =====

    def send_test_completed_notification(
        self,
        to_addresses: List[str],
        component_name: str,
        test_id: int,
        cycles: int,
        status: str,
        duration_minutes: float
    ) -> bool:
        """Sendet Benachrichtigung bei Test-Abschluss"""
        subject = f"Test abgeschlossen: {component_name}"

        body = f"""
Test-Benachrichtigung vom Pneumatik-Prüfstand

Komponente: {component_name}
Test-ID: {test_id}
Status: {status}
Zyklen: {cycles:,}
Dauer: {duration_minutes:.1f} Minuten

Zeitpunkt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

Dies ist eine automatische Benachrichtigung.
"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #2c3e50;">🔧 Test abgeschlossen</h2>
    <p>Der Test wurde erfolgreich abgeschlossen.</p>

    <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
        <tr style="background-color: #ecf0f1;">
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Komponente:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;">{component_name}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Test-ID:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;">{test_id}</td>
        </tr>
        <tr style="background-color: #ecf0f1;">
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Status:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><span style="color: #27ae60; font-weight: bold;">{status}</span></td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Zyklen:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;">{cycles:,}</td>
        </tr>
        <tr style="background-color: #ecf0f1;">
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Dauer:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;">{duration_minutes:.1f} Minuten</td>
        </tr>
    </table>

    <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
        Zeitpunkt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}<br>
        Dies ist eine automatische Benachrichtigung vom Pneumatik-Prüfstand.
    </p>
</body>
</html>
"""

        return self.send_email(to_addresses, subject, body, html_body)

    def send_calibration_due_notification(
        self,
        to_addresses: List[str],
        equipment_name: str,
        equipment_id: str,
        days_remaining: int
    ) -> bool:
        """Sendet Benachrichtigung für fällige Kalibrierung"""
        subject = f"⚠ Kalibrierung fällig: {equipment_name}"

        body = f"""
Kalibrierungs-Erinnerung

Prüfmittel: {equipment_name}
Prüfmittel-Nr.: {equipment_id}
Tage bis Fälligkeit: {days_remaining}

Bitte Kalibrierung zeitnah durchführen!

Dies ist eine automatische Erinnerung.
"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px;">
        <h2 style="color: #856404; margin-top: 0;">⚠ Kalibrierung fällig</h2>
        <p>Die Kalibrierung des folgenden Prüfmittels ist in {days_remaining} Tagen fällig.</p>
    </div>

    <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
        <tr style="background-color: #ecf0f1;">
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Prüfmittel:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;">{equipment_name}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Prüfmittel-Nr.:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;">{equipment_id}</td>
        </tr>
        <tr style="background-color: #ecf0f1;">
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Tage bis Fälligkeit:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>{days_remaining}</strong></td>
        </tr>
    </table>

    <p style="margin-top: 20px;">Bitte Kalibrierung zeitnah durchführen!</p>

    <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
        Dies ist eine automatische Erinnerung vom Kalibrierungs-Management-System.
    </p>
</body>
</html>
"""

        return self.send_email(to_addresses, subject, body, html_body)

    def send_test_failed_alert(
        self,
        to_addresses: List[str],
        component_name: str,
        test_id: int,
        error_message: str
    ) -> bool:
        """Sendet Alarm bei Test-Fehler"""
        subject = f"🚨 TEST FEHLGESCHLAGEN: {component_name}"

        body = f"""
ALARM: Test fehlgeschlagen!

Komponente: {component_name}
Test-ID: {test_id}
Fehler: {error_message}

Zeitpunkt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

Bitte umgehend prüfen!
"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <div style="background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin-bottom: 20px;">
        <h2 style="color: #721c24; margin-top: 0;">🚨 TEST FEHLGESCHLAGEN</h2>
        <p>Ein Test ist fehlgeschlagen und erfordert sofortige Aufmerksamkeit.</p>
    </div>

    <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
        <tr style="background-color: #ecf0f1;">
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Komponente:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;">{component_name}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Test-ID:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;">{test_id}</td>
        </tr>
        <tr style="background-color: #f8d7da;">
            <td style="padding: 10px; border: 1px solid #dc3545;"><strong>Fehler:</strong></td>
            <td style="padding: 10px; border: 1px solid #dc3545; color: #721c24;">{error_message}</td>
        </tr>
    </table>

    <p style="margin-top: 20px; color: #721c24; font-weight: bold;">Bitte umgehend prüfen!</p>

    <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
        Zeitpunkt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}<br>
        Dies ist eine automatische Alarm-Benachrichtigung.
    </p>
</body>
</html>
"""

        return self.send_email(to_addresses, subject, body, html_body)

    def send_report_notification(
        self,
        to_addresses: List[str],
        report_name: str,
        report_path: str
    ) -> bool:
        """Sendet Benachrichtigung mit Bericht als Anhang"""
        subject = f"Bericht verfügbar: {report_name}"

        body = f"""
Ihr Prüfbericht ist verfügbar.

Bericht: {report_name}
Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

Der Bericht ist im Anhang dieser E-Mail.
"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #2c3e50;">📊 Bericht verfügbar</h2>
    <p>Ihr angeforderter Prüfbericht wurde erstellt.</p>

    <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
        <tr style="background-color: #ecf0f1;">
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Bericht:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;">{report_name}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #bdc3c7;"><strong>Erstellt:</strong></td>
            <td style="padding: 10px; border: 1px solid #bdc3c7;">{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</td>
        </tr>
    </table>

    <p style="margin-top: 20px;">Der Bericht ist im Anhang dieser E-Mail.</p>

    <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
        Dies ist eine automatische Benachrichtigung vom Berichtssystem.
    </p>
</body>
</html>
"""

        attachments = [report_path] if Path(report_path).exists() else None
        return self.send_email(to_addresses, subject, body, html_body, attachments)
