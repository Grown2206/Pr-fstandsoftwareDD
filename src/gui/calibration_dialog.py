"""
Calibration Management Dialog
Kalibrierungsverwaltung
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QMessageBox,
    QGroupBox, QFormLayout, QDateEdit, QTextEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
from datetime import datetime, timedelta

from ..database.industrial_db_extension import IndustrialDatabaseManager
from ..models.calibration import CalibrationEquipment, CalibrationStatus, CalibrationRecord, CalibrationType


class CalibrationDialog(QDialog):
    """Dialog für Kalibrierungsverwaltung"""

    def __init__(self, db_manager: IndustrialDatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.init_ui()
        self.load_equipment()

    def init_ui(self):
        """Initialisiert UI"""
        self.setWindowTitle("Kalibrierungsverwaltung")
        self.setMinimumSize(1000, 700)

        layout = QVBoxLayout()

        # Header
        header = QLabel("🔧 Kalibrierungsverwaltung")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header)

        # Equipment Table
        self.equipment_table = QTableWidget()
        self.equipment_table.setColumnCount(7)
        self.equipment_table.setHorizontalHeaderLabels([
            "ID", "Prüfmittel-Nr.", "Bezeichnung", "Typ", "Status",
            "Nächste Kalibrierung", "Tage verbleibend"
        ])
        self.equipment_table.horizontalHeader().setStretchLastSection(True)
        self.equipment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.equipment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.equipment_table)

        # Buttons
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ Neues Prüfmittel")
        self.add_btn.clicked.connect(self.add_equipment)
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

        self.calibrate_btn = QPushButton("📋 Kalibrierung durchführen")
        self.calibrate_btn.clicked.connect(self.perform_calibration)
        self.calibrate_btn.setStyleSheet("""
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
        button_layout.addWidget(self.calibrate_btn)

        self.history_btn = QPushButton("📜 Kalibrierhistorie")
        self.history_btn.clicked.connect(self.show_history)
        button_layout.addWidget(self.history_btn)

        button_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Aktualisieren")
        self.refresh_btn.clicked.connect(self.load_equipment)
        button_layout.addWidget(self.refresh_btn)

        self.close_btn = QPushButton("Schließen")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_equipment(self):
        """Lädt Prüfmittel in Tabelle"""
        # Alle Equipment holen (in echter Implementation)
        # Hier als Beispiel mit get_calibration_due_soon
        equipment = self.db.get_calibration_due_soon(365)  # Alle im nächsten Jahr

        self.equipment_table.setRowCount(len(equipment))

        for row, eq in enumerate(equipment):
            self.equipment_table.setItem(row, 0, QTableWidgetItem(str(eq['id'])))
            self.equipment_table.setItem(row, 1, QTableWidgetItem(eq['equipment_id']))
            self.equipment_table.setItem(row, 2, QTableWidgetItem(eq['name']))
            self.equipment_table.setItem(row, 3, QTableWidgetItem(eq['equipment_type']))
            self.equipment_table.setItem(row, 4, QTableWidgetItem(eq['status']))

            # Nächste Kalibrierung
            next_cal = eq.get('next_calibration_date')
            if next_cal:
                if isinstance(next_cal, str):
                    next_cal_date = datetime.fromisoformat(next_cal)
                else:
                    next_cal_date = next_cal

                next_cal_str = next_cal_date.strftime('%d.%m.%Y')
                self.equipment_table.setItem(row, 5, QTableWidgetItem(next_cal_str))

                # Tage verbleibend
                days_left = (next_cal_date - datetime.now()).days
                days_item = QTableWidgetItem(str(days_left))

                # Farbcodierung
                if days_left < 0:
                    days_item.setBackground(QColor(231, 76, 60))  # Rot - überfällig
                    days_item.setForeground(QColor(255, 255, 255))
                elif days_left < 30:
                    days_item.setBackground(QColor(243, 156, 18))  # Orange - bald fällig
                    days_item.setForeground(QColor(255, 255, 255))
                elif days_left < 90:
                    days_item.setBackground(QColor(241, 196, 15))  # Gelb - demnächst
                else:
                    days_item.setBackground(QColor(39, 174, 96))  # Grün - i.O.
                    days_item.setForeground(QColor(255, 255, 255))

                self.equipment_table.setItem(row, 6, days_item)
            else:
                self.equipment_table.setItem(row, 5, QTableWidgetItem("Nicht festgelegt"))
                self.equipment_table.setItem(row, 6, QTableWidgetItem("N/A"))

    def add_equipment(self):
        """Fügt neues Prüfmittel hinzu"""
        dialog = EquipmentEditDialog(self.db, None, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_equipment()

    def perform_calibration(self):
        """Führt Kalibrierung durch"""
        selected_rows = self.equipment_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Prüfmittel aus!")
            return

        equipment_id = int(self.equipment_table.item(selected_rows[0].row(), 0).text())

        dialog = CalibrationRecordDialog(self.db, equipment_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_equipment()

    def show_history(self):
        """Zeigt Kalibrierhistorie"""
        selected_rows = self.equipment_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Prüfmittel aus!")
            return

        equipment_id = int(self.equipment_table.item(selected_rows[0].row(), 0).text())
        equipment_name = self.equipment_table.item(selected_rows[0].row(), 2).text()

        # Hier würde Historie geladen
        QMessageBox.information(
            self, "Kalibrierhistorie",
            f"Kalibrierhistorie für '{equipment_name}' wird angezeigt."
        )


class EquipmentEditDialog(QDialog):
    """Dialog zum Erstellen/Bearbeiten von Prüfmitteln"""

    def __init__(self, db_manager: IndustrialDatabaseManager, equipment: CalibrationEquipment = None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.equipment = equipment
        self.is_new = equipment is None
        self.init_ui()

    def init_ui(self):
        """Initialisiert UI"""
        self.setWindowTitle("Neues Prüfmittel" if self.is_new else "Prüfmittel bearbeiten")
        self.setMinimumWidth(600)

        layout = QVBoxLayout()

        # Form
        form_group = QGroupBox("Prüfmittel-Informationen")
        form_layout = QFormLayout()

        self.equipment_id_input = QLineEdit()
        self.equipment_id_input.setPlaceholderText("PM-001")
        form_layout.addRow("Prüfmittel-Nr.:", self.equipment_id_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Bezeichnung")
        form_layout.addRow("Bezeichnung:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Drucksensor",
            "Zeitmessgerät",
            "Temperatursensor",
            "Positionssensor",
            "Manometer",
            "Waage",
            "Messschieber"
        ])
        form_layout.addRow("Typ:", self.type_combo)

        self.manufacturer_input = QLineEdit()
        self.manufacturer_input.setPlaceholderText("Hersteller")
        form_layout.addRow("Hersteller:", self.manufacturer_input)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Modell")
        form_layout.addRow("Modell:", self.model_input)

        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Seriennummer")
        form_layout.addRow("Seriennummer:", self.serial_input)

        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText("365")
        self.interval_input.setText("365")
        form_layout.addRow("Kalibrierintervall (Tage):", self.interval_input)

        self.accuracy_input = QLineEdit()
        self.accuracy_input.setPlaceholderText("±0.5%")
        form_layout.addRow("Genauigkeitsklasse:", self.accuracy_input)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Labor, Raum 123")
        form_layout.addRow("Standort:", self.location_input)

        self.responsible_input = QLineEdit()
        self.responsible_input.setPlaceholderText("Name")
        form_layout.addRow("Verantwortlich:", self.responsible_input)

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
        """Speichert Prüfmittel"""
        equipment_id = self.equipment_id_input.text().strip()
        name = self.name_input.text().strip()

        if not equipment_id or not name:
            QMessageBox.warning(self, "Fehler", "Bitte mindestens Prüfmittel-Nr. und Bezeichnung eingeben!")
            return

        try:
            interval = int(self.interval_input.text())
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Kalibrierintervall muss eine Zahl sein!")
            return

        # Neues Equipment erstellen
        equipment = CalibrationEquipment(
            id=None,
            equipment_id=equipment_id,
            name=name,
            equipment_type=self.type_combo.currentText(),
            manufacturer=self.manufacturer_input.text().strip() or None,
            model=self.model_input.text().strip() or None,
            serial_number=self.serial_input.text().strip() or None,
            calibration_interval_days=interval,
            last_calibration_date=None,
            next_calibration_date=None,
            status=CalibrationStatus.GUELTIG,
            accuracy_class=self.accuracy_input.text().strip() or None,
            location=self.location_input.text().strip() or None,
            responsible_person=self.responsible_input.text().strip() or None
        )

        try:
            self.db.create_calibration_equipment(equipment)
            QMessageBox.information(self, "Erfolg", "Prüfmittel wurde erstellt!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Prüfmittel konnte nicht erstellt werden: {e}")


class CalibrationRecordDialog(QDialog):
    """Dialog zum Erstellen von Kalibrierprotokollen"""

    def __init__(self, db_manager: IndustrialDatabaseManager, equipment_id: int, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.equipment_id = equipment_id
        self.init_ui()

    def init_ui(self):
        """Initialisiert UI"""
        self.setWindowTitle("Kalibrierung durchführen")
        self.setMinimumWidth(600)

        layout = QVBoxLayout()

        # Form
        form_group = QGroupBox("Kalibrierprotokoll")
        form_layout = QFormLayout()

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        form_layout.addRow("Kalibrierungsdatum:", self.date_input)

        self.type_combo = QComboBox()
        for cal_type in CalibrationType:
            self.type_combo.addItem(cal_type.value, cal_type)
        form_layout.addRow("Kalibrierart:", self.type_combo)

        self.calibrated_by_input = QLineEdit()
        self.calibrated_by_input.setPlaceholderText("Name des Kalibrierers")
        form_layout.addRow("Kalibriert von:", self.calibrated_by_input)

        self.laboratory_input = QLineEdit()
        self.laboratory_input.setPlaceholderText("Labor / Einrichtung")
        form_layout.addRow("Labor:", self.laboratory_input)

        self.result_combo = QComboBox()
        self.result_combo.addItems(["Bestanden", "Bestanden mit Einschränkungen", "Nicht bestanden"])
        form_layout.addRow("Ergebnis:", self.result_combo)

        self.certificate_input = QLineEdit()
        self.certificate_input.setPlaceholderText("Zertifikatsnummer")
        form_layout.addRow("Zertifikatsnummer:", self.certificate_input)

        self.next_date_input = QDateEdit()
        self.next_date_input.setDate(QDate.currentDate().addYears(1))
        self.next_date_input.setCalendarPopup(True)
        form_layout.addRow("Nächste Kalibrierung:", self.next_date_input)

        self.remarks_input = QTextEdit()
        self.remarks_input.setPlaceholderText("Anmerkungen...")
        self.remarks_input.setMaximumHeight(100)
        form_layout.addRow("Anmerkungen:", self.remarks_input)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Kalibrierung speichern")
        save_btn.clicked.connect(self.save)
        save_btn.setStyleSheet("""
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
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def save(self):
        """Speichert Kalibrierprotokoll"""
        calibrated_by = self.calibrated_by_input.text().strip()

        if not calibrated_by:
            QMessageBox.warning(self, "Fehler", "Bitte 'Kalibriert von' eingeben!")
            return

        # Kalibrierprotokoll erstellen
        cal_date = self.date_input.date().toPyDate()
        next_date = self.next_date_input.date().toPyDate()

        record = CalibrationRecord(
            id=None,
            equipment_id=self.equipment_id,
            calibration_date=datetime.combine(cal_date, datetime.min.time()),
            calibration_type=self.type_combo.currentData(),
            calibrated_by=calibrated_by,
            laboratory=self.laboratory_input.text().strip() or None,
            result=self.result_combo.currentText(),
            certificate_number=self.certificate_input.text().strip() or None,
            next_calibration_date=datetime.combine(next_date, datetime.min.time()),
            remarks=self.remarks_input.toPlainText().strip() or None
        )

        try:
            self.db.create_calibration_record(record)
            QMessageBox.information(self, "Erfolg", "Kalibrierung wurde erfolgreich gespeichert!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Kalibrierung konnte nicht gespeichert werden: {e}")
