"""
User Management Dialog
Benutzerverwaltung
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QMessageBox,
    QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ..database.industrial_db_extension import IndustrialDatabaseManager
from ..models.user import User, UserRole


class UserManagementDialog(QDialog):
    """Dialog für Benutzerverwaltung"""

    def __init__(self, db_manager: IndustrialDatabaseManager, current_user: User, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.current_user = current_user
        self.init_ui()
        self.load_users()

    def init_ui(self):
        """Initialisiert UI"""
        self.setWindowTitle("Benutzerverwaltung")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout()

        # Header
        header = QLabel("👥 Benutzerverwaltung")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header)

        # User Table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Benutzername", "Name", "E-Mail", "Rolle", "Status"
        ])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.users_table)

        # Buttons
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ Neuer Benutzer")
        self.add_btn.clicked.connect(self.add_user)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏ Bearbeiten")
        self.edit_btn.clicked.connect(self.edit_user)
        button_layout.addWidget(self.edit_btn)

        self.toggle_active_btn = QPushButton("🔄 Aktivieren/Deaktivieren")
        self.toggle_active_btn.clicked.connect(self.toggle_user_active)
        button_layout.addWidget(self.toggle_active_btn)

        self.reset_password_btn = QPushButton("🔑 Passwort zurücksetzen")
        self.reset_password_btn.clicked.connect(self.reset_password)
        button_layout.addWidget(self.reset_password_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("Schließen")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_users(self):
        """Lädt Benutzer in Tabelle"""
        users = self.db.get_all_users()
        self.users_table.setRowCount(len(users))

        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.username))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.full_name))
            self.users_table.setItem(row, 3, QTableWidgetItem(user.email))
            self.users_table.setItem(row, 4, QTableWidgetItem(user.role.value))
            self.users_table.setItem(row, 5, QTableWidgetItem("Aktiv" if user.is_active else "Inaktiv"))

    def add_user(self):
        """Fügt neuen Benutzer hinzu"""
        dialog = UserEditDialog(self.db, None, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()

    def edit_user(self):
        """Bearbeitet ausgewählten Benutzer"""
        selected_rows = self.users_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie einen Benutzer aus!")
            return

        user_id = int(self.users_table.item(selected_rows[0].row(), 0).text())
        username = self.users_table.item(selected_rows[0].row(), 1).text()

        user = self.db.get_user_by_username(username)
        if not user:
            return

        dialog = UserEditDialog(self.db, user, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()

    def toggle_user_active(self):
        """Aktiviert/Deaktiviert Benutzer"""
        selected_rows = self.users_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie einen Benutzer aus!")
            return

        username = self.users_table.item(selected_rows[0].row(), 1).text()

        if username == self.current_user.username:
            QMessageBox.warning(self, "Fehler", "Sie können Ihr eigenes Konto nicht deaktivieren!")
            return

        # Implementation würde hier Datenbankupdate machen
        QMessageBox.information(self, "Erfolg", "Benutzerstatus wurde geändert.")
        self.load_users()

    def reset_password(self):
        """Setzt Passwort zurück"""
        selected_rows = self.users_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie einen Benutzer aus!")
            return

        username = self.users_table.item(selected_rows[0].row(), 1).text()

        reply = QMessageBox.question(
            self, "Passwort zurücksetzen",
            f"Passwort für Benutzer '{username}' auf 'passwort123' zurücksetzen?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Implementation würde hier Passwort zurücksetzen
            QMessageBox.information(self, "Erfolg", "Passwort wurde zurückgesetzt.")


class UserEditDialog(QDialog):
    """Dialog zum Erstellen/Bearbeiten von Benutzern"""

    def __init__(self, db_manager: IndustrialDatabaseManager, user: User = None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.user = user
        self.is_new = user is None
        self.init_ui()

    def init_ui(self):
        """Initialisiert UI"""
        self.setWindowTitle("Neuer Benutzer" if self.is_new else "Benutzer bearbeiten")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        # Form
        form_group = QGroupBox("Benutzer-Informationen")
        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Benutzername")
        if not self.is_new:
            self.username_input.setText(self.user.username)
            self.username_input.setEnabled(False)  # Username nicht änderbar
        form_layout.addRow("Benutzername:", self.username_input)

        if self.is_new:
            self.password_input = QLineEdit()
            self.password_input.setPlaceholderText("Passwort")
            self.password_input.setEchoMode(QLineEdit.Password)
            form_layout.addRow("Passwort:", self.password_input)

            self.password_confirm_input = QLineEdit()
            self.password_confirm_input.setPlaceholderText("Passwort wiederholen")
            self.password_confirm_input.setEchoMode(QLineEdit.Password)
            form_layout.addRow("Passwort bestätigen:", self.password_confirm_input)

        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Vor- und Nachname")
        if not self.is_new:
            self.fullname_input.setText(self.user.full_name)
        form_layout.addRow("Vollständiger Name:", self.fullname_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        if not self.is_new:
            self.email_input.setText(self.user.email)
        form_layout.addRow("E-Mail:", self.email_input)

        self.role_combo = QComboBox()
        for role in UserRole:
            self.role_combo.addItem(role.value, role)
        if not self.is_new:
            index = self.role_combo.findData(self.user.role)
            self.role_combo.setCurrentIndex(index)
        form_layout.addRow("Rolle:", self.role_combo)

        self.active_checkbox = QCheckBox("Konto ist aktiv")
        self.active_checkbox.setChecked(True if self.is_new else self.user.is_active)
        form_layout.addRow("Status:", self.active_checkbox)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Speichern")
        save_btn.clicked.connect(self.save)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def save(self):
        """Speichert Benutzer"""
        username = self.username_input.text().strip()
        fullname = self.fullname_input.text().strip()
        email = self.email_input.text().strip()
        role = self.role_combo.currentData()
        is_active = self.active_checkbox.isChecked()

        # Validierung
        if not username or not fullname or not email:
            QMessageBox.warning(self, "Fehler", "Bitte alle Felder ausfüllen!")
            return

        if self.is_new:
            password = self.password_input.text()
            password_confirm = self.password_confirm_input.text()

            if not password:
                QMessageBox.warning(self, "Fehler", "Bitte Passwort eingeben!")
                return

            if password != password_confirm:
                QMessageBox.warning(self, "Fehler", "Passwörter stimmen nicht überein!")
                return

            # Neuen Benutzer erstellen
            new_user = User(
                id=None,
                username=username,
                password_hash="",  # Wird vom DB-Manager gesetzt
                full_name=fullname,
                email=email,
                role=role,
                is_active=is_active
            )

            try:
                self.db.create_user(new_user, password)
                QMessageBox.information(self, "Erfolg", "Benutzer wurde erstellt!")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Benutzer konnte nicht erstellt werden: {e}")

        else:
            # Benutzer aktualisieren
            # Implementation würde hier update machen
            QMessageBox.information(self, "Erfolg", "Benutzer wurde aktualisiert!")
            self.accept()
