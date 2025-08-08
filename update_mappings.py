"""Script to update manufacturer and model mappings with real Yad2 data."""

import json
import os
from config import DATA_DIR, MANUFACTURERS_FILE, MODELS_FILE

# Your actual Yad2 API data
YAD2_DATA = {
    "data": {
        "manufacturer": [
            {"id": 1, "engTitle": "Audi", "title": "אאודי"},
            {"id": 53, "engTitle": "Abarth", "title": "אבארט"},
            {"id": 338, "engTitle": "Avatr", "title": "אווטאר"},
            {"id": 96, "engTitle": "Autobianchi", "title": "אוטוביאנקי"},
            {"id": 2, "engTitle": "Opel", "title": "אופל"},
            {"id": 224, "engTitle": "ORA", "title": "אורה"},
            {"id": 323, "engTitle": "EVeasy", "title": "אי.וי איזי "},
            {"id": 288, "engTitle": "Aiways", "title": "איוויס"},
            {"id": 85, "engTitle": "Iveco", "title": "איווקו"},
            {"id": 310, "engTitle": "INEOS", "title": "אינאוס"},
            {"id": 3, "engTitle": "Infiniti", "title": "אינפיניטי"},
            {"id": 4, "engTitle": "Isuzu", "title": "איסוזו"},
            {"id": 299, "engTitle": "LEVC", "title": "אל.אי.וי.סי"},
            {"id": 77, "engTitle": "LTI", "title": "אל.טי.איי"},
            {"id": 5, "engTitle": "Alfa Romeo", "title": "אלפא רומיאו"},
            {"id": 115, "engTitle": "Alpine", "title": "אלפין"},
            {"id": 6, "engTitle": "MG", "title": "אם ג'י"},
            {"id": 345, "engTitle": "SWM", "title": "אס דאבל יו אמ"},
            {"id": 54, "engTitle": "Aston Martin", "title": "אסטון מרטין"},
            {"id": 111, "engTitle": "Acura", "title": "אקורה"},
            {"id": 335, "engTitle": "XEV", "title": "אקס אי וי"},
            {"id": 290, "engTitle": "XPENG", "title": "אקספנג"},
            {"id": 117, "engTitle": "Arcfox", "title": "ארקפוקס"},
            {"id": 7, "engTitle": "BMW", "title": "ב מ וו"},
            {"id": 126, "engTitle": "BAIC Motor", "title": "באייק"},
            {"id": 193, "engTitle": "BAW", "title": "בי.איי.דאבליו"},
            {"id": 141, "engTitle": "BYD", "title": "בי.ווי.די"},
            {"id": 8, "engTitle": "Buick", "title": "ביואיק"},
            {"id": 55, "engTitle": "Bentley", "title": "בנטלי"},
            {"id": 355, "engTitle": "Jaecoo", "title": "ג'אקו"},
            {"id": 99, "engTitle": "GAC", "title": "ג'י.איי.סי"},
            {"id": 9, "engTitle": "GMC", "title": "ג'י.אם.סי"},
            {"id": 10, "engTitle": "Jeep", "title": "ג'יפ"},
            {"id": 93, "engTitle": "Genesis", "title": "ג'נסיס"},
            {"id": 319, "engTitle": "Goupil", "title": "גופיל"},
            {"id": 346, "engTitle": "Jiayuan", "title": "גיאיוואן"},
            {"id": 11, "engTitle": "Great Wall", "title": "גרייט וול"},
            {"id": 200, "engTitle": "JAC", "title": "ג׳יי.איי.סי"},
            {"id": 177, "engTitle": "Geely", "title": "ג׳ילי"},
            {"id": 329, "engTitle": "WM Motors", "title": "דאבל יו אם מוטורס"},
            {"id": 360, "engTitle": "Dayun", "title": "דאיון"},
            {"id": 12, "engTitle": "Dacia", "title": "דאצ'יה"},
            {"id": 13, "engTitle": "Dodge", "title": "דודג'"},
            {"id": 88, "engTitle": "DongFeng", "title": "דונגפנג"},
            {"id": 14, "engTitle": "DS", "title": "די.אס"},
            {"id": 60, "engTitle": "Daewoo", "title": "דייהו"},
            {"id": 15, "engTitle": "Daihatsu", "title": "דייהטסו"},
            {"id": 362, "engTitle": "Deepal", "title": "דיפאל"},
            {"id": 16, "engTitle": "Hummer", "title": "האמר"},
            {"id": 301, "engTitle": "HONGQI", "title": "הונגצ'י"},
            {"id": 17, "engTitle": "Honda", "title": "הונדה"},
            {"id": 322, "engTitle": "Voyah", "title": "וויה"},
            {"id": 18, "engTitle": "Volvo", "title": "וולוו"},
            {"id": 284, "engTitle": "WEY", "title": "ויי"},
            {"id": 333, "engTitle": "Zeekr", "title": "זיקר"},
            {"id": 87, "engTitle": "Tata", "title": "טאטא"},
            {"id": 19, "engTitle": "Toyota", "title": "טויוטה"},
            {"id": 62, "engTitle": "Tesla", "title": "טסלה"},
            {"id": 20, "engTitle": "Jaguar", "title": "יגואר"},
            {"id": 357, "engTitle": "Yudo", "title": "יודו"},
            {"id": 21, "engTitle": "Hyundai", "title": "יונדאי"},
            {"id": 80, "engTitle": "Lada", "title": "לאדה"},
            {"id": 22, "engTitle": "Lotus", "title": "לוטוס"},
            {"id": 321, "engTitle": "Lynk & Co", "title": "לינק אנד קו"},
            {"id": 23, "engTitle": "Lincoln", "title": "לינקולן"},
            {"id": 363, "engTitle": "Linxys", "title": "לינקסיס"},
            {"id": 320, "engTitle": "Leapmotor", "title": "ליפמוטור"},
            {"id": 63, "engTitle": "Lamborghini", "title": "למבורגיני"},
            {"id": 24, "engTitle": "Land Rover", "title": "לנד רובר"},
            {"id": 25, "engTitle": "Lancia", "title": "לנצ'יה"},
            {"id": 26, "engTitle": "Lexus", "title": "לקסוס"},
            {"id": 27, "engTitle": "Mazda", "title": "מאזדה"},
            {"id": 86, "engTitle": "MAN", "title": "מאן"},
            {"id": 219, "engTitle": "Morgan", "title": "מורגן"},
            {"id": 28, "engTitle": "Maserati", "title": "מזראטי"},
            {"id": 29, "engTitle": "Mini", "title": "מיני"},
            {"id": 30, "engTitle": "Mitsubishi", "title": "מיצובישי"},
            {"id": 73, "engTitle": "McLaren", "title": "מקלארן"},
            {"id": 89, "engTitle": "Maxus", "title": "מקסוס"},
            {"id": 31, "engTitle": "Mercedes-Benz", "title": "מרצדס-בנץ"},
            {"id": 348, "engTitle": "Neta", "title": "נטע"},
            {"id": 289, "engTitle": "NIO", "title": "ניאו"},
            {"id": 32, "engTitle": "Nissan", "title": "ניסאן"},
            {"id": 78, "engTitle": "Nanjing", "title": "ננג'ינג"},
            {"id": 33, "engTitle": "Saab", "title": "סאאב"},
            {"id": 34, "engTitle": "SsangYong", "title": "סאנגיונג"},
            {"id": 56, "engTitle": "Today Sunshine", "title": "סאנשיין"},
            {"id": 35, "engTitle": "Subaru", "title": "סובארו"},
            {"id": 36, "engTitle": "Suzuki", "title": "סוזוקי"},
            {"id": 37, "engTitle": "Seat", "title": "סיאט"},
            {"id": 38, "engTitle": "Citroen", "title": "סיטרואן"},
            {"id": 39, "engTitle": "Smart", "title": "סמארט"},
            {"id": 97, "engTitle": "Cenntro", "title": "סנטרו"},
            {"id": 40, "engTitle": "Skoda", "title": "סקודה"},
            {"id": 300, "engTitle": "Skywell", "title": "סקייוול"},
            {"id": 287, "engTitle": "Seres", "title": "סרס"},
            {"id": 364, "engTitle": "Farizon", "title": "פאריזון"},
            {"id": 352, "engTitle": "Foton", "title": "פוטון"},
            {"id": 231, "engTitle": "Polestar", "title": "פולסטאר"},
            {"id": 41, "engTitle": "Volkswagen", "title": "פולקסווגן"},
            {"id": 42, "engTitle": "Pontiac", "title": "פונטיאק"},
            {"id": 43, "engTitle": "Ford", "title": "פורד"},
            {"id": 44, "engTitle": "Porsche", "title": "פורשה"},
            {"id": 334, "engTitle": "Forthing", "title": "פורתינג"},
            {"id": 90, "engTitle": "Piaggio", "title": "פיאג'ו"},
            {"id": 45, "engTitle": "Fiat", "title": "פיאט"},
            {"id": 46, "engTitle": "Peugeot", "title": "פיג'ו"},
            {"id": 57, "engTitle": "Ferrari", "title": "פרארי"},
            {"id": 147, "engTitle": "Chery", "title": "צ׳רי"},
            {"id": 47, "engTitle": "Cadillac", "title": "קאדילק"},
            {"id": 203, "engTitle": "Karma", "title": "קארמה"},
            {"id": 92, "engTitle": "Cupra", "title": "קופרה"},
            {"id": 48, "engTitle": "Kia", "title": "קיה"},
            {"id": 344, "engTitle": "KGM", "title": "קיי גי אם "},
            {"id": 49, "engTitle": "Chrysler", "title": "קרייזלר"},
            {"id": 91, "engTitle": "RAM", "title": "ראם"},
            {"id": 50, "engTitle": "Rover", "title": "רובר"},
            {"id": 58, "engTitle": "Rolls-Royce", "title": "רולס רויס"},
            {"id": 361, "engTitle": "ReHigh", "title": "ריהיי"},
            {"id": 51, "engTitle": "Renault", "title": "רנו"},
            {"id": 52, "engTitle": "Chevrolet", "title": "שברולט"}
        ],
        "model": [
            {"id": 10001, "title": "100", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10002, "title": "80", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10003, "title": "A1", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10004, "title": "A3", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10005, "title": "A4", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10006, "title": "A5", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10007, "title": "A6", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10876, "title": "A6 e-tron", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10008, "title": "A7", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10009, "title": "A8", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10010, "title": "E-tron", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10879, "title": "E-tron GT", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10011, "title": "Q2", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10012, "title": "Q3", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10883, "title": "Q4 e-tron", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10013, "title": "Q5", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 13336, "title": "Q6 e-tron", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10014, "title": "Q7", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10015, "title": "Q8", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 13069, "title": "Q8 e-tron", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10016, "title": "R8", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10017, "title": "RS 3", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10886, "title": "RS 4", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10018, "title": "RS 5", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10019, "title": "RS 6", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10020, "title": "RS 7", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10887, "title": "RS E-tron GT", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10021, "title": "RS Q3", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10022, "title": "RS Q8", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10023, "title": "S1", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10024, "title": "S3", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10025, "title": "S4", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10026, "title": "S5", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10027, "title": "S6", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10028, "title": "S7", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10029, "title": "S8", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10030, "title": "SQ2", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10031, "title": "SQ5", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10032, "title": "SQ7", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10889, "title": "SQ8", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 13222, "title": "SQ8 e-tron", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10033, "title": "TT", "manufacturer": {"id": 1, "title": "אאודי"}},
            {"id": 10158, "title": "אוונג'ר", "manufacturer": {"id": 13, "title": "דודג'"}},
            {"id": 10164, "title": "ג'רני", "manufacturer": {"id": 13, "title": "דודג'"}},
            {"id": 10163, "title": "דורנגו", "manufacturer": {"id": 13, "title": "דודג'"}},
            {"id": 10165, "title": "ניטרו", "manufacturer": {"id": 13, "title": "דודג'"}},
            {"id": 10162, "title": "צ'ארג'ר", "manufacturer": {"id": 13, "title": "דודג'"}},
            {"id": 10161, "title": "צ'לנג'ר", "manufacturer": {"id": 13, "title": "דודג'"}},
            {"id": 10159, "title": "קאליבר", "manufacturer": {"id": 13, "title": "דודג'"}},
            {"id": 10160, "title": "קראוון", "manufacturer": {"id": 13, "title": "דודג'"}}
        ]
    }
}

def create_manufacturer_mappings():
    """Create manufacturer ID to name mappings."""
    manufacturers = {}
    
    for manufacturer in YAD2_DATA["data"]["manufacturer"]:
        manufacturer_id = str(manufacturer["id"])
        hebrew_name = manufacturer["title"]
        english_name = manufacturer["engTitle"]
        
        # Combine Hebrew and English names
        full_name = f"{hebrew_name} ({english_name})"
        manufacturers[manufacturer_id] = full_name
    
    return manufacturers

def create_model_mappings():
    """Create model ID to name mappings organized by manufacturer."""
    models = {}
    
    for model in YAD2_DATA["data"]["model"]:
        model_id = str(model["id"])
        model_title = model["title"]
        manufacturer_id = str(model["manufacturer"]["id"])
        
        if manufacturer_id not in models:
            models[manufacturer_id] = {}
        
        models[manufacturer_id][model_id] = model_title
    
    return models

def update_files():
    """Update the manufacturer and model mapping files."""
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Create mappings
    manufacturers = create_manufacturer_mappings()
    models = create_model_mappings()
    
    # Save manufacturers
    with open(MANUFACTURERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(manufacturers, f, indent=2, ensure_ascii=False)
    
    # Save models  
    with open(MODELS_FILE, 'w', encoding='utf-8') as f:
        json.dump(models, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Updated {len(manufacturers)} manufacturers")
    print(f"✅ Updated models for {len(models)} manufacturers")
    
    # Show some examples
    print("\n📋 Sample Manufacturers:")
    for mid, name in list(manufacturers.items())[:10]:
        print(f"  {mid}: {name}")
    
    print(f"\n📋 Sample Models for Seat (ID 37):")
    if "37" in models:
        for model_id, model_name in list(models["37"].items())[:10]:
            print(f"  {model_id}: {model_name}")
    
    print(f"\n📋 Sample Models for Nissan (ID 32):")
    if "32" in models:
        for model_id, model_name in list(models["32"].items())[:10]:
            print(f"  {model_id}: {model_name}")

if __name__ == "__main__":
    update_files()