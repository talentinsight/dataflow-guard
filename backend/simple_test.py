#!/usr/bin/env python3
"""
Basit Demo Test - Snowflake Bağlantısını Test Et
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_snowflake_config():
    """Snowflake konfigürasyonunu test et"""
    print("🔍 Snowflake Konfigürasyon Kontrolü")
    print("=" * 40)
    
    config = {
        "SNOWFLAKE_ACCOUNT": os.getenv("SNOWFLAKE_ACCOUNT"),
        "SNOWFLAKE_USER": os.getenv("SNOWFLAKE_USER"),
        "SNOWFLAKE_PASSWORD": os.getenv("SNOWFLAKE_PASSWORD"),
        "SNOWFLAKE_WAREHOUSE": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "SNOWFLAKE_DATABASE": os.getenv("SNOWFLAKE_DATABASE"),
        "SNOWFLAKE_SCHEMA": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    }
    
    for key, value in config.items():
        status = "✅" if value else "❌"
        display_value = value if key != "SNOWFLAKE_PASSWORD" else "***" if value else None
        print(f"{status} {key}: {display_value}")
    
    missing = [k for k, v in config.items() if not v]
    if missing:
        print(f"\n❌ Eksik konfigürasyon: {missing}")
        return False
    else:
        print(f"\n✅ Tüm konfigürasyon tamam!")
        return True

def test_compile_service():
    """Test compilation servisini test et"""
    print("\n🧪 Test Compilation Servisi")
    print("=" * 40)
    
    try:
        from dto_api.services.compile_service import compile_service
        
        # Basit test template'i
        test_templates = [
            {
                "name": "Row Count Test",
                "type": "row_count",
                "dataset": "PROD_DB.RAW.SAMPLE_TABLE",
                "expected_min": 0,
                "expected_max": None
            },
            {
                "name": "Schema Test", 
                "type": "schema",
                "dataset": "PROD_DB.RAW.SAMPLE_TABLE",
                "expected_columns": []
            }
        ]
        
        result = compile_service.compile_tests(test_templates)
        
        print(f"✅ Compilation başarılı!")
        print(f"📊 {len(result['tests'])} test derlendi")
        print(f"📝 SQL Preview:")
        print("-" * 30)
        print(result['sql'][:200] + "..." if len(result['sql']) > 200 else result['sql'])
        
        return True
        
    except Exception as e:
        print(f"❌ Compilation hatası: {str(e)}")
        return False

def test_database_init():
    """Database initialization test et"""
    print("\n💾 Database Initialization")
    print("=" * 40)
    
    try:
        from dto_api.db.models import init_database
        
        database_url = "sqlite:///./test_demo.db"
        init_database(database_url)
        
        print(f"✅ Database başarıyla initialize edildi: {database_url}")
        return True
        
    except Exception as e:
        print(f"❌ Database hatası: {str(e)}")
        return False

def main():
    print("🚀 DataFlowGuard Basit Test")
    print("=" * 50)
    
    results = []
    
    # Test 1: Snowflake Config
    results.append(test_snowflake_config())
    
    # Test 2: Database Init
    results.append(test_database_init())
    
    # Test 3: Compile Service
    results.append(test_compile_service())
    
    # Sonuçlar
    print("\n📊 TEST SONUÇLARI")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Geçen: {passed}/{total}")
    print(f"❌ Başarısız: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 Tüm testler başarılı! Demo için hazır!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test başarısız. Düzeltilmesi gerekiyor.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
