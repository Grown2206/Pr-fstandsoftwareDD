"""
Barcode/QR-Code Scanner Integration
Für Chargen-Tracking und Komponenten-Identifikation
"""
from typing import Optional, Callable
from datetime import datetime
import re


class BarcodeScanner:
    """Barcode/QR-Code Scanner Wrapper"""

    def __init__(self):
        self.last_scan = None
        self.scan_callback: Optional[Callable] = None

    def set_scan_callback(self, callback: Callable):
        """Setzt Callback für gescannte Codes"""
        self.scan_callback = callback

    def process_scan(self, barcode: str) -> dict:
        """
        Verarbeitet gescannten Barcode

        Args:
            barcode: Gescannter Code

        Returns:
            Dictionary mit Scan-Informationen
        """
        self.last_scan = datetime.now()

        # Code-Typ erkennen
        code_type = self._detect_code_type(barcode)

        # Daten extrahieren
        data = self._extract_data(barcode, code_type)

        result = {
            'barcode': barcode,
            'code_type': code_type,
            'data': data,
            'timestamp': self.last_scan,
            'valid': data is not None
        }

        # Callback aufrufen
        if self.scan_callback:
            self.scan_callback(result)

        return result

    def _detect_code_type(self, barcode: str) -> str:
        """Erkennt Barcode-Typ"""
        # EAN-13 (13 Ziffern)
        if re.match(r'^\d{13}$', barcode):
            return 'EAN13'

        # EAN-8 (8 Ziffern)
        if re.match(r'^\d{8}$', barcode):
            return 'EAN8'

        # UPC-A (12 Ziffern)
        if re.match(r'^\d{12}$', barcode):
            return 'UPC-A'

        # Code 128 / Code 39 (alphanumerisch)
        if re.match(r'^[A-Z0-9\-]+$', barcode):
            return 'CODE128'

        # QR-Code (kann alles sein)
        if len(barcode) > 20:
            return 'QR'

        # Custom Format für Chargen
        if barcode.startswith('LOT-') or barcode.startswith('BATCH-'):
            return 'BATCH'

        # Custom Format für Komponenten
        if barcode.startswith('COMP-') or barcode.startswith('MAT-'):
            return 'COMPONENT'

        return 'UNKNOWN'

    def _extract_data(self, barcode: str, code_type: str) -> Optional[dict]:
        """Extrahiert Daten aus Barcode"""
        data = {}

        if code_type == 'BATCH':
            # Chargen-Format: LOT-YYYY-NNN
            match = re.match(r'(LOT|BATCH)-(\d{4})-(\d+)', barcode)
            if match:
                data['type'] = 'batch'
                data['year'] = match.group(2)
                data['number'] = match.group(3)
                data['batch_number'] = barcode

        elif code_type == 'COMPONENT':
            # Komponenten-Format: COMP-MATERIAL-SERIAL
            match = re.match(r'(COMP|MAT)-([A-Z0-9\-]+)-?(\d+)?', barcode)
            if match:
                data['type'] = 'component'
                data['material_number'] = match.group(2)
                if match.group(3):
                    data['serial_number'] = match.group(3)

        elif code_type == 'QR':
            # QR-Code kann JSON enthalten
            try:
                import json
                data = json.loads(barcode)
                data['type'] = 'qr'
            except:
                data['type'] = 'qr'
                data['raw'] = barcode

        elif code_type in ['EAN13', 'EAN8', 'UPC-A']:
            data['type'] = 'product'
            data['ean'] = barcode

        else:
            data['type'] = 'generic'
            data['raw'] = barcode

        return data if data else None

    @staticmethod
    def generate_batch_qr(batch_number: str, component_type: str, quantity: int) -> str:
        """Generiert QR-Code Daten für Charge"""
        import json
        qr_data = {
            'type': 'batch',
            'batch_number': batch_number,
            'component_type': component_type,
            'quantity': quantity,
            'created': datetime.now().isoformat()
        }
        return json.dumps(qr_data)

    @staticmethod
    def generate_component_qr(material_number: str, serial_number: str) -> str:
        """Generiert QR-Code Daten für Komponente"""
        import json
        qr_data = {
            'type': 'component',
            'material_number': material_number,
            'serial_number': serial_number,
            'scanned': datetime.now().isoformat()
        }
        return json.dumps(qr_data)

    @staticmethod
    def create_qr_image(data: str, filename: str = None) -> str:
        """
        Erstellt QR-Code Bild

        Args:
            data: Zu codierende Daten
            filename: Optionaler Dateiname

        Returns:
            Pfad zum generierten Bild
        """
        try:
            import qrcode
            from pathlib import Path

            # QR-Code generieren
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Speichern
            if not filename:
                filename = f"qr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            output_dir = Path("data/qrcodes")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / filename

            img.save(str(output_path))
            return str(output_path)

        except ImportError:
            print("qrcode library not installed. Run: pip install qrcode[pil]")
            return ""


class BarcodeValidator:
    """Validiert Barcodes"""

    @staticmethod
    def validate_ean13(ean: str) -> bool:
        """Validiert EAN-13 Prüfziffer"""
        if not re.match(r'^\d{13}$', ean):
            return False

        # Prüfziffer berechnen
        digits = [int(d) for d in ean[:12]]
        checksum = sum(digits[::2]) + sum(d * 3 for d in digits[1::2])
        checksum = (10 - (checksum % 10)) % 10

        return checksum == int(ean[12])

    @staticmethod
    def validate_batch_number(batch_number: str) -> bool:
        """Validiert Chargen-Nummer Format"""
        # LOT-YYYY-NNN oder BATCH-YYYY-NNN
        return bool(re.match(r'^(LOT|BATCH)-\d{4}-\d{3,6}$', batch_number))

    @staticmethod
    def validate_material_number(material_number: str) -> bool:
        """Validiert Materialnummer Format"""
        # Alphanumerisch mit Bindestrichen, 5-20 Zeichen
        return bool(re.match(r'^[A-Z0-9\-]{5,20}$', material_number))
