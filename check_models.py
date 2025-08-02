#!/usr/bin/env python3
"""
Check available Gemini models
"""

import google.generativeai as genai

def check_available_models():
    """Check what models are available with the API key"""
    print("🔍 Checking Available Gemini Models")
    print("=" * 50)
    
    # Configure with API key
    api_key = "AIzaSyDkZgeLXhKJrjclXXv27YDv0U_2o8meE6c"
    genai.configure(api_key=api_key)
    
    try:
        # List all models
        print("📋 All available models:")
        models = list(genai.list_models())
        
        for model in models:
            print(f"\n🔹 Model: {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description}")
            print(f"   Generation Methods: {model.supported_generation_methods}")
            
            # Check if it supports generateContent
            if 'generateContent' in model.supported_generation_methods:
                print("   ✅ Supports generateContent")
            else:
                print("   ❌ Does not support generateContent")
        
        # Find the best model for our use case
        print("\n🎯 Recommended models for chatbot:")
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                if 'gemini' in model.name.lower():
                    print(f"   ✅ {model.name} - {model.display_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking models: {str(e)}")
        return False

def test_model(model_name):
    """Test a specific model"""
    print(f"\n🧪 Testing model: {model_name}")
    print("=" * 30)
    
    api_key = "AIzaSyDkZgeLXhKJrjclXXv27YDv0U_2o8meE6c"
    genai.configure(api_key=api_key)
    
    try:
        # Create model instance
        model = genai.GenerativeModel(model_name)
        
        # Test simple generation
        response = model.generate_content("Hello, are you working?")
        print(f"✅ Model works! Response: {response.text[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Model failed: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Gemini Model Checker")
    print("=" * 50)
    
    # Check available models
    success = check_available_models()
    
    if success:
        # Test common model names
        test_models = [
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            'gemini-pro',
            'gemini-pro-vision'
        ]
        
        print("\n🧪 Testing common model names:")
        for model_name in test_models:
            test_model(model_name)

if __name__ == "__main__":
    main() 