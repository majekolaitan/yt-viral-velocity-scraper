from datetime import timedelta
import re

class DataConverter:
    VIEW_MULTIPLIERS = {'k': 1e3, 'm': 1e6, 'b': 1e9, 't': 1e12}

    @staticmethod
    def parse_view_count(view_str: str) -> int:
        if not view_str or 'no' in view_str.lower():
            return 0
        
        clean_str = view_str.lower().replace(',', '').strip()
        match = re.search(r'([\d\.]+)\s*([kmbt]?)', clean_str)
        
        if not match:
            return 0
            
        num = float(match.group(1))
        multiplier = match.group(2)
        return int(num * DataConverter.VIEW_MULTIPLIERS.get(multiplier, 1))

    @staticmethod
    def parse_age_to_days(age_str: str) -> int:
        if not age_str:
            return 1
            
        # Normalize "a year ago" -> "1 year ago"
        age_str = age_str.lower()
        age_str = re.sub(r'\ba\b|\ban\b', '1', age_str)
        
        match = re.search(r'\d+', age_str)
        if not match:
            return 1
            
        num = int(match.group())
        
        if any(unit in age_str for unit in ['hour', 'minute', 'second']):
            return 1 
        if 'day' in age_str: return num
        if 'week' in age_str: return num * 7
        if 'month' in age_str: return num * 30
        if 'year' in age_str: return num * 365
        return 1
    
    # --- NEW FUNCTION TO PARSE DURATION ---
    @staticmethod
    def parse_duration_to_seconds(duration_str: str) -> int:
        """Converts MM:SS or HH:MM:SS to total seconds."""
        if not duration_str or not isinstance(duration_str, str):
            return 0
            
        parts = duration_str.split(':')
        try:
            # Safely convert parts to integers, defaulting to 0 if conversion fails
            time_parts = [int(p) for p in parts]
        except ValueError:
            return 0 # Handles cases like 'LIVE' or other non-numeric strings
        
        total_seconds = 0
        if len(time_parts) == 2: # MM:SS
            total_seconds = time_parts[0] * 60 + time_parts[1]
        elif len(time_parts) == 3: # HH:MM:SS
            total_seconds = time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2]
            
        return total_seconds

    # --- NEW FUNCTION TO FORMAT SECONDS ---
    @staticmethod
    def format_seconds_to_hhmmss(seconds: int) -> str:
        """Formats total seconds into a consistent HH:MM:SS string."""
        return str(timedelta(seconds=seconds))