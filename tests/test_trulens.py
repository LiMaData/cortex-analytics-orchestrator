"""Test TruLens installation"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_imports():
    """Test if TruLens imports work"""
    try:
        from trulens_eval import Tru, Feedback
        from trulens_eval.feedback.provider import OpenAI
        print("✅ TruLens imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_openai_key():
    """Test if OpenAI API key is configured"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env")
        return False
    
    if api_key.startswith('sk-'):
        print(f"✅ OpenAI API key found (starts with: {api_key[:10]}...)")
        return True
    else:
        print("⚠️ API key format looks wrong (should start with 'sk-')")
        return False

def test_trulens_init():
    """Test TruLens initialization"""
    try:
        from trulens_eval import Tru
        tru = Tru()
        print("✅ TruLens initialized successfully")
        return True
    except Exception as e:
        print(f"❌ TruLens init failed: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING TRULENS SETUP")
    print("="*60 + "\n")
    
    results = []
    
    print("1. Testing imports...")
    results.append(test_imports())
    
    print("\n2. Testing OpenAI API key...")
    results.append(test_openai_key())
    
    print("\n3. Testing TruLens initialization...")
    results.append(test_trulens_init())
    
    print("\n" + "="*60)
    if all(results):
        print("✅ ALL TESTS PASSED - TruLens is ready!")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
    print("="*60 + "\n")