"""
Login Dialog
Benutzer-Authentifizierung
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from ..database.industrial_db_extension import IndustrialDatabaseManager
from ..models.user import User


class LoginDialog(QDialog):
    """Login-Dialog für Benutzer-Authentifizierung"""

    def __init__(self, db_manager: IndustrialDatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.authenticated_user = None
        self.init_ui()

    def init_ui(self):
        """Initialisiert UI"""
        self.setWindowTitle("Pneumatik-Prüfstand - Anmeldung")
        self.setFixedSize(400, 300)
        self.setModal(True)

        # Layout
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Logo/Title
        title = QLabel("🔧 Pneumatik-Prüfstand")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 20px;")
        layout.addWidget(title)

        subtitle = QLabel("Benutzer-Anmeldung")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(subtitle)

        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Benutzername")
        self.username_input.setMinimumHeight(40)
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        layout.addWidget(self.username_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Passwort")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        self.password_input.returnPressed.connect(self.login)
        layout.addWidget(self.password_input)

        # Remember me
        self.remember_checkbox = QCheckBox("Angemeldet bleiben")
        layout.addWidget(self.remember_checkbox)

        # Buttons
        button_layout = QHBoxLayout()

        self.login_button = QPushButton("Anmelden")
        self.login_button.setMinimumHeight(40)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.login_button.clicked.connect(self.login)
        button_layout.addWidget(self.login_button)

        cancel_button = QPushButton("Abbrechen")
        cancel_button.setMinimumHeight(40)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        # Info
        info_label = QLabel("Standard-Login: admin / admin")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #95a5a6; font-size: 11px; padding-top: 10px;")
        layout.addWidget(info_label)

        self.setLayout(layout)

        # Focus auf Username
        self.username_input.setFocus()

    def login(self):
        """Führt Login durch"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Fehler", "Bitte Benutzername und Passwort eingeben!")
            return

        # Benutzer abrufen
        user = self.db.get_user_by_username(username)

        if not user:
            QMessageBox.critical(self, "Login fehlgeschlagen",
                               "Ungültiger Benutzername oder Passwort!")
            self.password_input.clear()
            return

        if not user.is_active:
            QMessageBox.critical(self, "Konto gesperrt",
                               "Ihr Benutzerkonto ist deaktiviert. Bitte kontaktieren Sie den Administrator.")
            return

        # Passwort prüfen
        salt = self.db.get_password_salt(username)
        if not user.verify_password(password, salt):
            QMessageBox.critical(self, "Login fehlgeschlagen",
                               "Ungültiger Benutzername oder Passwort!")
            self.password_input.clear()
            return

        # Login erfolgreich
        self.authenticated_user = user
        self.db.update_last_login(user.id)

        # Audit-Log
        from ..utils.audit_logger import AuditLogger
        audit = AuditLogger(self.db)
        audit.log_login(user.id, user.username, success=True)

        QMessageBox.information(self, "Anmeldung erfolgreich",
                              f"Willkommen, {user.full_name}!\n\nRolle: {user.role.value}")

        self.accept()

    def get_user(self) -> User:
        """Gibt authentifizierten Benutzer zurück"""
        return self.authenticated_user
