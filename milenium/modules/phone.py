import phonenumbers
from phonenumbers import geocoder, carrier, timezone

def check(number):
    out = {}
    try:
        p = phonenumbers.parse(number, None)
        out["valid"] = phonenumbers.is_valid_number(p)
        out["country"] = geocoder.description_for_number(p, "en")
        out["carrier"] = carrier.name_for_number(p, "en")
        out["timezone"] = list(timezone.time_zones_for_number(p))
        out["format_intl"] = phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except Exception as e:
        out["error"] = str(e)
    return out