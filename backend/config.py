"""
Application Configuration & Domain Name Settings for RailBlock AI
Allows dynamic customization of website domain name, system title, and branding
"""

import os
from pydantic import BaseModel


class SystemConfig(BaseModel):
    app_name: str = "RailBlock AI"
    app_short_code: str = "IR-ABPS"
    app_version: str = "v2.0"
    domain_name: str = "abps.indianrailways.gov.in"
    portal_url: str = "https://abps.indianrailways.gov.in"
    api_docs_url: str = "https://abps.indianrailways.gov.in/docs"
    organization: str = "Ministry of Railways, Government of India"
    zone_division: str = "North Central Railway (NCR) • Prayagraj Division"
    host: str = "127.0.0.1"
    port: int = 8000


# Singleton global configuration instance
CONFIG = SystemConfig()


def get_config() -> SystemConfig:
    return CONFIG


def update_domain(new_domain: str, new_app_name: str = None) -> SystemConfig:
    global CONFIG
    clean_domain = new_domain.strip().lower()
    if clean_domain.startswith("http://"):
        clean_domain = clean_domain[7:]
    elif clean_domain.startswith("https://"):
        clean_domain = clean_domain[8:]
        
    CONFIG.domain_name = clean_domain
    CONFIG.portal_url = f"https://{clean_domain}"
    CONFIG.api_docs_url = f"https://{clean_domain}/docs"
    
    if new_app_name:
        CONFIG.app_name = new_app_name.strip()
        
    return CONFIG
