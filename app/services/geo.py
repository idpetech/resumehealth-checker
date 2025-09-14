"""
Geolocation Service

Built-in IP-based geolocation without external API dependencies.
Uses static IP ranges for major target markets.
"""
import json
import logging
from pathlib import Path
from ipaddress import ip_address, ip_network
from typing import Dict, Any, Optional

from ..core.config import config

logger = logging.getLogger(__name__)

class GeoService:
    """Service for IP-based country detection and regional pricing"""
    
    def __init__(self):
        """Initialize with IP ranges and pricing data"""
        self.ip_ranges = self._load_ip_ranges()
        self.pricing_data = self._load_pricing_data()
        logger.info("Geo service initialized")
    
    def _load_ip_ranges(self) -> Dict[str, list]:
        """Load IP ranges for country detection"""
        try:
            geo_file = Path(__file__).parent.parent / "data" / "geo.json"
            if geo_file.exists():
                with open(geo_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load geo.json: {e}")
        
        # Fallback: Built-in IP ranges for major markets
        return {
            "US": [
                "8.0.0.0/8", "4.0.0.0/6", "12.0.0.0/6", "16.0.0.0/4",
                "32.0.0.0/3", "64.0.0.0/2", "128.0.0.0/3", "160.0.0.0/5",
                "168.0.0.0/6", "172.0.0.0/12", "173.0.0.0/8", "174.0.0.0/7",
                "176.0.0.0/4", "192.0.0.0/9", "192.128.0.0/11"
            ],
            "PK": [
                "39.32.0.0/11", "103.26.0.0/16", "110.39.0.0/16", 
                "111.68.0.0/14", "116.71.0.0/16", "119.160.0.0/13",
                "121.52.0.0/14", "175.107.0.0/16", "202.83.160.0/19"
            ],
            "IN": [
                "106.51.0.0/16", "117.192.0.0/10", "122.160.0.0/12",
                "125.16.0.0/12", "144.48.0.0/12", "150.129.0.0/16",
                "157.119.0.0/16", "163.53.0.0/16", "180.149.0.0/16"
            ],
            "HK": [
                "113.252.0.0/14", "202.64.0.0/14", "202.80.0.0/13",
                "202.128.0.0/13", "203.80.0.0/12", "218.188.0.0/14"
            ],
            "AE": [
                "5.32.0.0/13", "31.25.0.0/17", "37.201.0.0/16",
                "78.88.0.0/13", "85.158.0.0/15", "188.65.0.0/16"
            ],
            "BD": [
                "27.112.0.0/12", "103.48.0.0/13", "114.130.0.0/16",
                "118.179.0.0/16", "119.40.64.0/18", "122.152.0.0/13"
            ]
        }
    
    def _load_pricing_data(self) -> Dict[str, Any]:
        """Load pricing data for regional calculations"""
        try:
            pricing_file = Path(__file__).parent.parent / "data" / "pricing.json"
            with open(pricing_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Could not load pricing data: {e}")
            # Return minimal fallback pricing
            return {
                "regions": {
                    "US": {
                        "currency": "USD",
                        "symbol": "$",
                        "products": {
                            "resume_analysis": {"price": 10, "display": "$10"},
                            "job_fit_analysis": {"price": 12, "display": "$12"},
                            "cover_letter": {"price": 8, "display": "$8"}
                        }
                    }
                },
                "default_region": "US"
            }
    
    def get_country_from_ip(self, ip_str: str) -> str:
        """
        Detect country from IP address
        
        Args:
            ip_str: IP address string
            
        Returns:
            Two-letter country code (e.g., "US", "PK")
        """
        if not ip_str or ip_str in ['127.0.0.1', 'localhost', '::1']:
            logger.info("Local IP detected, defaulting to US")
            return "US"
        
        try:
            user_ip = ip_address(ip_str)
            
            # Skip private IP ranges
            if user_ip.is_private:
                logger.info(f"Private IP {ip_str} detected, defaulting to US")
                return "US"
            
            # Check against known IP ranges
            for country, ranges in self.ip_ranges.items():
                for ip_range in ranges:
                    try:
                        if user_ip in ip_network(ip_range):
                            logger.info(f"IP {ip_str} detected as {country}")
                            return country
                    except ValueError:
                        # Invalid IP range format, skip
                        continue
            
            logger.info(f"IP {ip_str} not found in known ranges, defaulting to US")
            return "US"
            
        except ValueError:
            logger.warning(f"Invalid IP address format: {ip_str}")
            return "US"
    
    def get_pricing_for_region(self, country_code: str) -> Dict[str, Any]:
        """
        Get pricing information for a specific region
        
        Args:
            country_code: Two-letter country code
            
        Returns:
            Pricing data for the region
        """
        regions = self.pricing_data.get("regions", {})
        default_region = self.pricing_data.get("default_region", "US")
        
        # Get region data or fall back to default
        region_data = regions.get(country_code, regions.get(default_region, {}))
        
        if not region_data:
            logger.error(f"No pricing data for {country_code}, using minimal fallback")
            return {
                "currency": "USD",
                "symbol": "$",
                "products": {
                    "resume_analysis": {"price": 10, "display": "$10"},
                    "job_fit_analysis": {"price": 12, "display": "$12"},
                    "cover_letter": {"price": 8, "display": "$8"}
                }
            }
        
        logger.info(f"Pricing data retrieved for {country_code}")
        return region_data
    
    def detect_region_from_request(self, request) -> Dict[str, Any]:
        """
        Detect user region from HTTP request
        
        Args:
            request: FastAPI request object
            
        Returns:
            Region detection result with pricing
        """
        # Try to get real IP from headers (in case of proxy)
        forwarded_for = getattr(request.headers, 'x-forwarded-for', None) if hasattr(request, 'headers') else None
        real_ip = getattr(request.headers, 'x-real-ip', None) if hasattr(request, 'headers') else None
        client_ip = getattr(request.client, 'host', '127.0.0.1') if hasattr(request, 'client') else '127.0.0.1'
        
        # Use the most reliable IP source
        ip_to_check = forwarded_for or real_ip or client_ip
        if forwarded_for and ',' in forwarded_for:
            # Take the first IP if there are multiple
            ip_to_check = forwarded_for.split(',')[0].strip()
        
        # Detect country
        country = self.get_country_from_ip(ip_to_check)
        
        # Get pricing for country
        pricing = self.get_pricing_for_region(country)
        
        return {
            "detected_ip": ip_to_check,
            "country_code": country,
            "currency": pricing.get("currency", "USD"),
            "currency_symbol": pricing.get("symbol", "$"),
            "pricing": pricing
        }
    
    def get_currency_for_stripe(self, country_code: str) -> str:
        """
        Get Stripe-compatible currency code for country
        
        Args:
            country_code: Two-letter country code
            
        Returns:
            Lowercase currency code for Stripe (e.g., "usd", "inr")
        """
        region_data = self.get_pricing_for_region(country_code)
        currency = region_data.get("currency", "USD")
        
        # Convert to lowercase for Stripe compatibility
        return currency.lower()
    
    def convert_amount_for_stripe(self, country_code: str, product_type: str) -> int:
        """
        Get amount in cents/paise for Stripe
        
        Args:
            country_code: Two-letter country code
            product_type: Product type (resume_analysis, etc.)
            
        Returns:
            Amount in smallest currency unit (cents for USD, paise for INR, etc.)
        """
        pricing = self.get_pricing_for_region(country_code)
        products = pricing.get("products", {})
        product_info = products.get(product_type, {})
        
        base_amount = product_info.get("price", 10)  # Default to $10 equivalent
        currency = pricing.get("currency", "USD")
        
        # Most currencies use 2 decimal places (multiply by 100)
        # Some currencies like Japanese Yen don't use decimals
        if currency.upper() in ["JPY", "KRW"]:  # Zero-decimal currencies
            return base_amount
        else:  # Standard currencies
            return base_amount * 100

# Create geo data file if it doesn't exist
def create_geo_data_file():
    """Create geo.json file with IP ranges if it doesn't exist"""
    geo_file = Path(__file__).parent.parent / "data" / "geo.json"
    if not geo_file.exists():
        geo_service_instance = GeoService()
        try:
            with open(geo_file, 'w') as f:
                json.dump(geo_service_instance.ip_ranges, f, indent=2)
            logger.info("Created geo.json file with IP ranges")
        except Exception as e:
            logger.warning(f"Could not create geo.json: {e}")

# Singleton instance
geo_service = GeoService()

# Create data file on import
create_geo_data_file()