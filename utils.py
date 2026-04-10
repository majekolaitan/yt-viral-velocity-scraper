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