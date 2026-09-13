"""
SPARC-PM: Multi-Language Localization Engine
==================================================
Provides translation support for English, Hindi, Tamil, and French
to serve ISRO engineers across the mission control center.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "mission_control": "Mission Control",
        "severity_level": "Severity Level",
        "fsm_triage": "FSM Triage",
        "solar_proton_flux": "Solar Proton Flux",
        "solar_wind_speed": "Solar Wind Speed",
        "spacecraft_at_high_hazard": "Spacecraft at High Hazard",
        "gaganyaan_cabin_rate": "Gaganyaan Cabin Rate",
        "gaganyaan_crew_dosimetry": "Gaganyaan Crew Dosimetry",
        "3d_fleet_spatial_hazard": "3D Fleet Spatial Hazard",
        "predictive_maintenance": "Predictive Maintenance",
        "command_synthesizer": "Command Synthesizer",
        "incident_analytics": "Incident Analytics",
        "eva_cleared": "EVA Cleared",
        "eva_prohibited": "EVA Prohibited",
        "enter_storm_shelter": "Enter Storm Shelter",
        "nominal_operations": "Nominal Operations",
        "elevated_monitoring": "Elevated Monitoring",
        "suspend_eva": "Suspend EVA",
        "critical": "Critical",
        "warning": "Warning",
        "green": "Green",
        "yellow": "Yellow",
        "red": "Red",
        "normal": "Normal",
        "alert": "Alert",
        "status": "Status",
        "transmit_uplink": "Transmit & Uplink",
        "scheduled_telecommands": "Scheduled Telecommands",
        "allocated_power_budget": "Allocated Power Budget",
        "scheduler_latency": "Scheduler Latency",
        "fleet_operating": "Fleet Operating",
        "no_emergency": "Fleet operating in nominal regime",
        "hazard_ratio": "Hazard Ratio",
        "alert_level": "Alert Level",
        "distance_to_corridor": "Distance to Corridor",
        "altitude_km": "Altitude (km)",
        "satellite_id": "Satellite ID",
        "failure_risk": "Failure Risk",
        "health_status": "Health Status",
        "battery_voltage": "Battery Voltage",
        "subsystem_temperature": "Subsystem Temperature",
        "gyro_drift": "Gyro Drift",
        "dosimeter_count": "Dosimeter Count",
    },
    "hi": {
        "mission_control": "मिशन कंट्रोल",
        "severity_level": "गंभीरता स्तर",
        "fsm_triage": "FSM ट्राइज",
        "solar_proton_flux": "सौर प्रोटॉन फ्लक्स",
        "solar_wind_speed": "सौर हवा की गति",
        "spacecraft_at_high_hazard": "उच्च खतरे वाली अंतरिक्ष यान",
        "gaganyaan_cabin_rate": "गागन्यान केबिन दर",
        "gaganyaan_crew_dosimetry": "गागन्यान चाकू डॉसीमेट्री",
        "3d_fleet_spatial_hazard": "3D फ्लीट स्थानिक खतरा",
        "predictive_maintenance": "पूर्वानुमानित रखरखाव",
        "command_synthesizer": "कमांड संश्लेषक",
        "incident_analytics": "घटना विश्लेषण",
        "eva_cleared": "EVA मंजूर",
        "eva_prohibited": "EVA प्रतिबंधित",
        "enter_storm_shelter": "तूफान शेल्टर में प्रवेश करें",
        "nominal_operations": "सामान्य संचालन",
        "elevated_monitoring": "उन्नत निगरानी",
        "suspend_eva": "EVA निलंबित करें",
        "critical": "गंभीर",
        "warning": "चेतावनी",
        "green": "हरा",
        "yellow": "पीला",
        "red": "लाल",
        "normal": "सामान्य",
        "alert": "अलर्ट",
        "status": "स्थिति",
        "transmit_uplink": "प्रसारित करें और अपलिंक करें",
        "scheduled_telecommands": "शेड्यूल कमांड",
        "allocated_power_budget": "आवंटित बिजली बजट",
        "scheduler_latency": "शेड्यूलर विलंबता",
        "fleet_operating": "फ्लीट संचालित",
        "no_emergency": "फ्लीट सामान्य अवस्था में संचालित",
        "hazard_ratio": "खतरा अनुपात",
        "alert_level": "अलर्ट स्तर",
        "distance_to_corridor": "गले की दूरी",
        "altitude_km": "ऊंचाई (किमी)",
        "satellite_id": "उपग्रह आईडी",
        "failure_risk": "विफलता जोखिम",
        "health_status": "स्वास्थ्य स्थिति",
        "battery_voltage": "बैटरी वोल्टेज",
        "subsystem_temperature": "उप-प्रणाली तापमान",
        "gyro_drift": "जाय्रो ड्रिफ्ट",
        "dosimeter_count": "डोसीमीटर गिनती",
    },
    "ta": {
        "mission_control": "மிஷன் கண்காணிப்பு",
        "severity_level": "கவலைநிறைவு நிலை",
        "fsm_triage": "FSM வரிசைப்படுத்தல்",
        "solar_proton_flux": "சூரிய மூலக்குறி தினம்",
        "solar_wind_speed": "சூரிய காலா வேகம்",
        "spacecraft_at_high_hazard": "உயர்ந்த ஆபத்திலுள்ள விண்கலங்கள்",
        "gaganyaan_cabin_rate": "காகன்யான் கேபின் விகிடம்",
        "gaganyaan_crew_dosimetry": "காகன்யான் குடியேற்றுத் தொகுதி டாஸிமெட்ரி",
        "3d_fleet_spatial_hazard": "3D துணைத்தரங்கள் இடப்பொருள் ஆபத்து",
        "predictive_maintenance": "எதிர்கால பராமரிப்பு",
        "command_synthesizer": "கட்டளை ஒருங்கிணைப்பாளர்",
        "incident_analytics": "நிகழ்வுப் புள்ளியியல்",
        "eva_cleared": "EVA அனுமதிக்கப்பட்டது",
        "eva_prohibited": "EVA தடைசெய்யப்பட்டது",
        "enter_storm_shelter": "மழைத்தளத்தில் உள்நுழைக்கவும்",
        "nominal_operations": "வழக்கமான நடவடிக்கைகள்",
        "elevated_monitoring": "உயர்ந்த மீனியரிங்",
        "suspend_eva": "EVA நிறுத்தவும்",
        "critical": "சியாரியல்",
        "warning": "எச்சரிக்கை",
        "green": "பச்சை",
        "yellow": "மஞ்சள்",
        "red": "சிவப்பு",
        "normal": "சாதாரண",
        "alert": "எச்சரிக்கை",
        "status": "நிலை",
        "transmit_uplink": "அனுப்பவும் அப்லிங்க் செய்யவும்",
        "scheduled_telecommands": "ஷெடியுள்ள தொடர்புச் செயல்கள்",
        "allocated_power_budget": "ஒதுக்கப்பட்ட மின்சார பட்ஜெட்",
        "scheduler_latency": "ஷெட்யூலர் மின்னிறத்தன்மை",
        "fleet_operating": "துணைத்தரங்கள் செயல்படுகின்றன",
        "no_emergency": "துணைத்தரங்கள் சாதாரண நிலையில் செயல்படுகின்றன",
        "hazard_ratio": "ஆபத்து விகிதம்",
        "alert_level": "எச்சரிக்கை நிலை",
        "distance_to_corridor": "தொடர்பு தொலைவு",
        "altitude_km": "ஆழம் (கி.மீ)",
        "satellite_id": "விண்கலம் ஐடி",
        "failure_risk": "தோல்வி ஆபத்து",
        "health_status": "சுகத்து நிலை",
        "battery_voltage": "பேட்டரி வோல்டேஜ்",
        "subsystem_temperature": "துணை முறை வெப்பநிலை",
        "gyro_drift": "ஜைரோ தழல்",
        "dosimeter_count": "டாஸிமீட்டர் எண்ணிக்கை",
    },
    "fr": {
        "mission_control": "Centre de Mission",
        "severity_level": "Niveau de Gravité",
        "fsm_triage": "Triage FSM",
        "solar_proton_flux": "Flux de Protons Solaire",
        "solar_wind_speed": "Vitesse du Vent Solaire",
        "spacecraft_at_high_hazard": "Engins Spatiaux à Haut Risque",
        "gaganyaan_cabin_rate": "Taux d'habitacle Gaganyaan",
        "gaganyaan_crew_dosimetry": "Dosimétrie de l'Équipage Gaganyaan",
        "3d_fleet_spatial_hazard": "Risque Spatial 3D de la Flotte",
        "predictive_maintenance": "Maintenance Prédictive",
        "command_synthesizer": "Synthétiseur de Commandes",
        "incident_analytics": "Analyse d'Incident",
        "eva_cleared": "EVA Autorisé",
        "eva_prohibited": "EVA Interdit",
        "enter_storm_shelter": "Entrer à l'Abri Tempête",
        "nominal_operations": "Opérations Nominales",
        "elevated_monitoring": "Surveillance Élevée",
        "suspend_eva": "Suspendre l'EVA",
        "critical": "Critique",
        "warning": "Avertissement",
        "green": "Vert",
        "yellow": "Jaune",
        "red": "Rouge",
        "normal": "Normal",
        "alert": "Alerte",
        "status": "Statut",
        "transmit_uplink": "Transmettre et Téléverser",
        "scheduled_telecommands": "Télécommandes Programmées",
        "allocated_power_budget": "Budget Puissance Alloué",
        "scheduler_latency": "Latence du Planificateur",
        "fleet_operating": "Flotte en Service",
        "no_emergency": "Flotte en régime nominal",
        "hazard_ratio": "Ratio de Danger",
        "alert_level": "Niveau d'Alerte",
        "distance_to_corridor": "Distance au Couloir",
        "altitude_km": "Altitude (km)",
        "satellite_id": "ID Satellite",
        "failure_risk": "Risque de Défaillance",
        "health_status": "État de Santé",
        "battery_voltage": "Tension Batterie",
        "subsystem_temperature": "Température Sous-Système",
        "gyro_drift": "Dérive Gyro",
        "dosimeter_count": "Compteur Dosimètre",
    },
}

DEFAULT_LANGUAGE = "en"
_LANGUAGE_FILE = PROJECT_ROOT / ".language"


class I18nEngine:
    """
    Multi-language translation engine for SPARC-PM UI.
    Supports English, Hindi, Tamil, and French.
    """

    def __init__(self, language: str = DEFAULT_LANGUAGE):
        self._language = language if language in TRANSLATIONS else DEFAULT_LANGUAGE

    def set_language(self, language: str) -> bool:
        """
        Switches the current language.

        Args:
            language: Language code ('en', 'hi', 'ta', 'fr').

        Returns:
            True if language was set successfully.
        """
        if language in TRANSLATIONS:
            self._language = language
            self._save_language()
            return True
        return False

    def get_language(self) -> str:
        """Returns the current language code."""
        return self._language

    def get_available_languages(self) -> Dict[str, str]:
        """Returns available language codes and their display names."""
        return {
            "en": "English",
            "hi": "हिन्दी (Hindi)",
            "ta": "தமிழ் (Tamil)",
            "fr": "Français (French)",
        }

    def t(self, key: str, **kwargs: Any) -> str:
        """
        Translates a key to the current language.

        Args:
            key: Translation key (e.g., 'severity_level').
            **kwargs: Optional formatting arguments (not used currently).

        Returns:
            Translated string or key if not found.
        """
        lang_dict = TRANSLATIONS.get(self._language, TRANSLATIONS["en"])
        return lang_dict.get(key, key)

    def get_all_translations(self) -> Dict[str, str]:
        """Returns all translations for the current language."""
        return TRANSLATIONS.get(self._language, TRANSLATIONS["en"])

    def _save_language(self) -> None:
        """Persists language preference to file."""
        try:
            with open(_LANGUAGE_FILE, "w", encoding="utf-8") as f:
                f.write(self._language)
        except Exception:
            pass

    def _load_language(self) -> None:
        """Loads language preference from file."""
        if _LANGUAGE_FILE.exists():
            try:
                with open(_LANGUAGE_FILE, "r", encoding="utf-8") as f:
                    lang = f.read().strip()
                    if lang in TRANSLATIONS:
                        self._language = lang
            except Exception:
                pass


# Global singleton instance
_i18n_instance: Optional[I18nEngine] = None


def get_i18n(language: Optional[str] = None) -> I18nEngine:
    """Returns the global I18nEngine instance."""
    global _i18n_instance
    if _i18n_instance is None:
        lang = language or DEFAULT_LANGUAGE
        _i18n_instance = I18nEngine(lang)
        _i18n_instance._load_language()
    elif language:
        _i18n_instance.set_language(language)
    return _i18n_instance


# Convenience function for use in app.py
def _(key: str) -> str:
    """Translates a key using the global I18n instance."""
    return get_i18n().t(key)


if __name__ == "__main__":
    print("🌐 Initializing SPARC i18n Engine...")
    i18n = get_i18n("en")
    print(f"Languages: {list(i18n.get_available_languages().keys())}")
    print(f"Severity Level: {i18n.t('severity_level')}")
    print(f"Enter Storm Shelter: {i18n.t('enter_storm_shelter')}")

    # Test Hindi
    i18n.set_language("hi")
    print(f"HI - Severity Level: {i18n.t('severity_level')}")

    # Test Tamil
    i18n.set_language("ta")
    print(f"TA - Severity Level: {i18n.t('severity_level')}")

    # Test French
    i18n.set_language("fr")
    print(f"FR - Severity Level: {i18n.t('severity_level')}")
