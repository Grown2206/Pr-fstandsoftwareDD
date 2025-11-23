"""
Electronic Signature System
Elektronische Signatur nach FDA 21 CFR Part 11
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import hashlib


@dataclass
class ElectronicSignature:
    """Elektronische Signatur"""
    id: Optional[int]
    user_id: int
    username: str
    full_name: str
    timestamp: datetime

    # Signierter Inhalt
    entity_type: str  # z.B. "TestRun", "Calibration", "TestProgram"
    entity_id: int
    action: str  # z.B. "APPROVE", "REJECT", "RELEASE"

    # Signatur-Daten
    reason: str  # Grund der Signatur
    password_hash: str  # Re-Authentifizierung

    # Integrität
    content_hash: str  # SHA-256 Hash des signierten Inhalts
    signature_hash: str  # SHA-256 Hash der gesamten Signatur

    # Metadaten
    ip_address: Optional[str] = None
    computer_name: Optional[str] = None

    # Compliance
    meaning: str = ""  # "Approved", "Reviewed", "Released"
    is_valid: bool = True


class SignatureManager:
    """Verwaltet elektronische Signaturen"""

    @staticmethod
    def create_signature(
        user_id: int,
        username: str,
        full_name: str,
        entity_type: str,
        entity_id: int,
        action: str,
        reason: str,
        password: str,
        content: str,
        ip_address: Optional[str] = None
    ) -> ElectronicSignature:
        """
        Erstellt elektronische Signatur

        Args:
            user_id: Benutzer-ID
            username: Benutzername
            full_name: Vollständiger Name
            entity_type: Typ des signierten Objekts
            entity_id: ID des signierten Objekts
            action: Aktion (APPROVE, REJECT, etc.)
            reason: Begründung
            password: Passwort zur Re-Authentifizierung
            content: Zu signierrender Inhalt (serialisiert)
            ip_address: IP-Adresse

        Returns:
            ElectronicSignature Objekt
        """
        timestamp = datetime.now()

        # Passwort hashen
        from ..models.user import User
        password_hash, _ = User.hash_password(password)

        # Content hashen (SHA-256)
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        # Signatur-String erstellen
        signature_string = (
            f"{user_id}|{username}|{timestamp.isoformat()}|"
            f"{entity_type}|{entity_id}|{action}|{content_hash}"
        )

        # Signatur hashen
        signature_hash = hashlib.sha256(signature_string.encode('utf-8')).hexdigest()

        # Meaning ermitteln
        meaning = {
            'APPROVE': 'Approved',
            'REJECT': 'Rejected',
            'RELEASE': 'Released',
            'REVIEW': 'Reviewed',
            'VERIFY': 'Verified'
        }.get(action, action)

        return ElectronicSignature(
            id=None,
            user_id=user_id,
            username=username,
            full_name=full_name,
            timestamp=timestamp,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason=reason,
            password_hash=password_hash,
            content_hash=content_hash,
            signature_hash=signature_hash,
            ip_address=ip_address,
            meaning=meaning,
            is_valid=True
        )

    @staticmethod
    def verify_signature(signature: ElectronicSignature, content: str) -> bool:
        """
        Verifiziert elektronische Signatur

        Args:
            signature: Zu verifizierende Signatur
            content: Original-Inhalt

        Returns:
            True wenn Signatur gültig
        """
        # Content-Hash neu berechnen
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        if content_hash != signature.content_hash:
            return False

        # Signatur-Hash neu berechnen
        signature_string = (
            f"{signature.user_id}|{signature.username}|{signature.timestamp.isoformat()}|"
            f"{signature.entity_type}|{signature.entity_id}|{signature.action}|{content_hash}"
        )

        signature_hash = hashlib.sha256(signature_string.encode('utf-8')).hexdigest()

        return signature_hash == signature.signature_hash and signature.is_valid

    @staticmethod
    def format_signature_text(signature: ElectronicSignature) -> str:
        """Formatiert Signatur als Text für Anzeige"""
        return (
            f"ELEKTRONISCHE SIGNATUR\n"
            f"{'=' * 50}\n"
            f"Signiert von: {signature.full_name} ({signature.username})\n"
            f"Zeitpunkt: {signature.timestamp.strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"Bedeutung: {signature.meaning}\n"
            f"Grund: {signature.reason}\n"
            f"{'=' * 50}\n"
            f"Signatur-Hash: {signature.signature_hash[:16]}...\n"
            f"Status: {'✓ Gültig' if signature.is_valid else '✗ Ungültig'}"
        )
