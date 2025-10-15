import requests
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
from django.contrib.gis.geoip2 import GeoIP2
from .models import StoreVisit

def get_user_location(ip):
    try:
        g = GeoIP2()
        location = g.city(ip)
        return location.get("city", ""), location.get("region", ""), location.get("country_name", "")
    except:
        return "", "", ""

class StoreVisitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key  # Generate a session key if missing

        if not request.session.get("store_visited"):
            request.session["store_visited"] = True  # Prevent duplicate tracking
            
            ip = request.META.get("REMOTE_ADDR", "")
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            city, region, country = get_user_location(ip)

            StoreVisit.objects.create(
                session_id=session_key,
                ip_address=ip,
                user_agent=user_agent,
                city=city,
                region=region,
                country=country
            )

        request.session["visit_start_time"] = str(datetime.now())  # Store entry time
