"""
Privacy filtering and data protection utilities
"""

import json
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .database import User, UserPrivacySettings


class PrivacyFilter:
    """Advanced privacy filtering system"""

    def __init__(self, db: Session, user: Optional[User] = None):
        self.db = db
        self.user = user
        self.privacy_settings = None

        if user:
            self.privacy_settings = (
                db.query(UserPrivacySettings)
                .filter(UserPrivacySettings.user_id == user.id)
                .first()
            )

    def filter_data(
        self,
        data: Dict[str, Any],
        privacy_level: str = "public",
        is_authenticated: bool = False,
    ) -> Dict[str, Any]:
        """
        Main filtering method with multiple privacy levels

        Privacy levels:
        - business_card: Ultra-minimal (name, title, basic contact)
        - professional: Professional info only (no personal details)
        - public_full: Full public view (respects user privacy settings)
        - ai_safe: Safe for AI assistant consumption
        """
        # Even authenticated users can request privacy filtering
        # Only skip filtering if explicitly requested with privacy_level "none"
        if privacy_level == "none" and is_authenticated:
            return data  # Authenticated users with explicit "none" see everything

        if privacy_level == "business_card":
            return self.create_business_card_view(data)
        elif privacy_level == "ai_safe":
            return self.ai_safe_filter(data)
        elif privacy_level == "professional":
            return self.professional_filter(data)
        else:  # public_full or any other level
            return self.public_filter(data)

    def create_business_card_view(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only business card level information"""
        business_card = {}

        # Basic info
        if "name" in data:
            business_card["name"] = data["name"]
        if "title" in data:
            business_card["title"] = data["title"]

        # Current company (from most recent experience)
        if (
            "experience" in data
            and isinstance(data["experience"], list)
            and data["experience"]
        ):
            latest_job = data["experience"][0]
            if "company" in latest_job:
                business_card["company"] = latest_job["company"]
            if "position" in latest_job:
                business_card["position"] = latest_job["position"]

        # Essential contact info only
        if "contact" in data:
            contact = {}
            allowed_contact = ["email", "website", "linkedin", "github"]
            for field in allowed_contact:
                if field in data["contact"]:
                    contact[field] = data["contact"][field]
            if contact:
                business_card["contact"] = contact

        # Top 5 skills only
        if "skills" in data:
            skills = {}
            if isinstance(data["skills"], dict):
                if "technical" in data["skills"]:
                    skills["technical"] = data["skills"]["technical"][:5]
            elif isinstance(data["skills"], list):
                skills = {"technical": data["skills"][:5]}
            if skills:
                business_card["skills"] = skills

        return business_card

    def ai_safe_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter data specifically for AI assistant consumption"""
        # Start with professional filter
        filtered = self.professional_filter(data)

        # Remove anything that could be misused
        sensitive_for_ai = {
            "current_location",
            "home_address",
            "phone",
            "mobile",
            "personal_email",
            "family",
            "relationships",
            "medical",
            "financial",
            "legal",
            "private_notes",
            "internal_notes",
        }

        return self._recursive_filter_fields(filtered, sensitive_for_ai)

    def professional_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Show professional information, hide personal details"""
        # Apply user privacy settings if available
        if self.privacy_settings:
            return self._apply_user_privacy_settings(data)

        # Default professional filtering
        professional_data = self._apply_sensitive_patterns(data)

        # Additional professional-specific filtering
        professional_excludes = {
            "personal",
            "family",
            "relationships",
            "medical",
            "health",
            "financial",
            "salary",
            "compensation",
            "bank",
            "tax",
            "home_address",
            "personal_phone",
            "emergency_contact",
        }

        return self._recursive_filter_fields(professional_data, professional_excludes)

    def public_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Full public filtering with all safety measures"""
        return self._apply_sensitive_patterns(data)

    def _apply_user_privacy_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply user-specific privacy settings"""
        settings = self.privacy_settings
        filtered_data = dict(data)

        # Business card mode override
        if settings.business_card_mode:
            return self.create_business_card_view(data)

        # Contact info filtering
        if not settings.show_contact_info and "contact" in filtered_data:
            contact = filtered_data["contact"].copy()
            # Keep only essential business contact
            essential = {}
            if "email" in contact and not any(
                word in contact["email"].lower()
                for word in ["personal", "private", "home"]
            ):
                essential["email"] = contact["email"]
            if "website" in contact:
                essential["website"] = contact["website"]
            if "linkedin" in contact:
                essential["linkedin"] = contact["linkedin"]
            if "github" in contact:
                essential["github"] = contact["github"]
            filtered_data["contact"] = essential

        # Location filtering
        if not settings.show_location:
            filtered_data = self._recursive_filter_fields(
                filtered_data, {"location", "address", "city", "state", "country"}
            )

        # Company info filtering
        if not settings.show_current_company and "experience" in filtered_data:
            if (
                isinstance(filtered_data["experience"], list)
                and filtered_data["experience"]
            ):
                # Remove current company details but keep role/responsibilities
                for job in filtered_data["experience"]:
                    if job.get("end_date") in [None, "Present", "Current"]:
                        job.pop("company", None)

        # Salary/compensation filtering
        if not settings.show_salary_range:
            filtered_data = self._recursive_filter_fields(
                filtered_data, {"salary", "wage", "compensation", "pay", "income"}
            )

        # Education details filtering
        if not settings.show_education_details and "education" in filtered_data:
            if isinstance(filtered_data["education"], list):
                for edu in filtered_data["education"]:
                    edu.pop("gpa", None)
                    edu.pop("grades", None)
                    edu.pop("thesis", None)

        # Apply custom rules
        if settings.custom_privacy_rules:
            filtered_data = self._apply_custom_rules(
                filtered_data, settings.custom_privacy_rules
            )

        # Apply base sensitive pattern filtering
        return self._apply_sensitive_patterns(filtered_data)

    def _apply_sensitive_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply pattern-based sensitive data filtering"""
        sensitive_patterns = {
            # Personal contact info
            "phone",
            "mobile",
            "cell",
            "telephone",
            "personal_phone",
            "home_phone",
            "emergency_contact",
            "emergency_phone",
            "emergency",
            "personal_email",
            "private_email",
            "home_email",
            "address",
            "home_address",
            "street",
            "apartment",
            "apt",
            "suite",
            "zip",
            "zipcode",
            "postal_code",
            "postcode",
            # Financial info
            "salary",
            "wage",
            "compensation",
            "income",
            "pay",
            "earnings",
            "bank",
            "account",
            "routing",
            "iban",
            "swift",
            "credit_card",
            "tax_id",
            "ssn",
            "social_security",
            "ein",
            # Government IDs
            "passport",
            "drivers_license",
            "dl_number",
            "license_number",
            "visa",
            "green_card",
            "citizenship",
            # Sensitive flags
            "private",
            "confidential",
            "internal",
            "secret",
            "restricted",
            "intimate",
            "family_only",
            # Medical/Health
            "medical",
            "health",
            "diagnosis",
            "prescription",
            "allergy",
            "disability",
            "mental_health",
            # Security
            "password",
            "pin",
            "security_question",
            "recovery",
            "backup_codes",
            "api_key",
            "token",
            "secret_key",
            "auth",
        }

        def is_sensitive_value(value):
            if isinstance(value, str):
                # Phone patterns - more precise
                phone_cleaned = re.sub(r"[^\d]", "", value)  # Remove all non-digits
                if len(phone_cleaned) >= 10 and re.match(
                    r"^[\+]?[\d\s\-\(\)\.]{10,}$", value
                ):
                    return True
                # SSN pattern
                if re.match(r"\d{3}-?\d{2}-?\d{4}", value):
                    return True
                # Personal email indicators
                if "@" in value and any(
                    word in value.lower() for word in ["personal", "private", "home"]
                ):
                    return True
            return False

        def recursive_filter(obj, path=""):
            if isinstance(obj, dict):
                filtered = {}
                for key, value in obj.items():
                    # Check if field name is sensitive
                    if any(pattern in key.lower() for pattern in sensitive_patterns):
                        continue

                    # Check if value content is sensitive
                    if is_sensitive_value(value):
                        continue

                    # Recursively filter nested objects
                    filtered_value = recursive_filter(
                        value, f"{path}.{key}" if path else key
                    )
                    if filtered_value is not None:
                        filtered[key] = filtered_value

                return filtered

            elif isinstance(obj, list):
                return [
                    recursive_filter(item, f"{path}[{i}]")
                    for i, item in enumerate(obj)
                    if recursive_filter(item, f"{path}[{i}]") is not None
                ]

            else:
                return None if is_sensitive_value(obj) else obj

        return recursive_filter(data)

    def _recursive_filter_fields(
        self, data: Dict[str, Any], exclude_fields: set
    ) -> Dict[str, Any]:
        """Recursively filter out specific field names"""

        def filter_recursive(obj):
            if isinstance(obj, dict):
                return {
                    k: filter_recursive(v)
                    for k, v in obj.items()
                    if not any(excluded in k.lower() for excluded in exclude_fields)
                }
            elif isinstance(obj, list):
                return [filter_recursive(item) for item in obj]
            else:
                return obj

        return filter_recursive(data)

    def _apply_custom_rules(
        self, data: Dict[str, Any], custom_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply user-defined custom privacy rules"""
        # Custom rules format: {"field_path": "action"}
        # Example: {"contact.phone": "hide", "experience.0.salary": "redact"}

        def apply_rule_to_path(obj, path_parts, action):
            if not path_parts:
                return obj

            if isinstance(obj, dict):
                key = path_parts[0]
                if key in obj:
                    if len(path_parts) == 1:
                        # Apply action
                        if action == "hide":
                            obj.pop(key, None)
                        elif action == "redact":
                            obj[key] = "[REDACTED]"
                    else:
                        obj[key] = apply_rule_to_path(obj[key], path_parts[1:], action)

            return obj

        filtered_data = dict(data)
        for field_path, action in custom_rules.items():
            path_parts = field_path.split(".")
            filtered_data = apply_rule_to_path(filtered_data, path_parts, action)

        return filtered_data


def get_privacy_filter(db: Session, user: Optional[User] = None) -> PrivacyFilter:
    """Factory function to create privacy filter instance"""
    return PrivacyFilter(db, user)
