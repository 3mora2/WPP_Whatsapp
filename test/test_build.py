"""
Test script to verify WPP_Whatsapp package build
"""

def test_imports():
    """Test basic imports"""
    print("Testing imports...")
    
    # Test main package import
    import WPP_Whatsapp
    print(f"✓ WPP_Whatsapp imported successfully")
    
    # Test Create class
    from WPP_Whatsapp import Create
    print(f"✓ Create class imported successfully")
    
    # Test API module
    from WPP_Whatsapp.api import Whatsapp
    print(f"✓ Whatsapp class imported successfully")
    
    # Test controllers
    from WPP_Whatsapp.controllers import initializer
    print(f"✓ initializer module imported successfully")
    
    # Test utils
    from WPP_Whatsapp.utils import ffmpeg
    print(f"✓ ffmpeg module imported successfully")
    
    print("\n✅ All imports passed!\n")


def test_package_metadata():
    """Test package metadata"""
    print("Testing package metadata...")
    
    import WPP_Whatsapp
    
    # Check if package has __init__
    assert hasattr(WPP_Whatsapp, '__name__')
    print(f"✓ Package name: {WPP_Whatsapp.__name__}")
    
    # Check Create class exists
    from WPP_Whatsapp import Create
    assert Create is not None
    print(f"✓ Create class available")
    
    print("\n✅ Package metadata passed!\n")


def test_api_layers():
    """Test API layers imports"""
    print("Testing API layers...")
    
    from WPP_Whatsapp.api.layers import (
        BusinessLayer,
        CatalogLayer,
        ControlsLayer,
        GroupLayer,
        HostLayer,
        LabelsLayer,
        ListenerLayer,
        ProfileLayer,
        RetrieverLayer,
        SenderLayer,
        StatusLayer,
        UILayer
    )
    print(f"✓ All API layers imported successfully")
    
    print("\n✅ API layers passed!\n")


def test_helpers():
    """Test helper modules"""
    print("Testing helper modules...")
    
    from WPP_Whatsapp.api.helpers import (
        decorators,
        download_file,
        function,
        jsFunction,
        wapi,
        wa_version
    )
    print(f"✓ All helper modules imported successfully")
    
    print("\n✅ Helper modules passed!\n")


def test_model():
    """Test model module"""
    print("Testing model module...")
    
    from WPP_Whatsapp.api.model import status_find
    print(f"✓ status_find module imported successfully")
    
    print("\n✅ Model module passed!\n")


def main():
    """Run all tests"""
    print("=" * 60)
    print("WPP_Whatsapp Build Test")
    print("=" * 60)
    print()
    
    try:
        test_imports()
        test_package_metadata()
        test_api_layers()
        test_helpers()
        test_model()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
