"""
Simple script to test if Anthropic API key works
"""
import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables from .env file
load_dotenv()

# Get API key
api_key = os.environ.get('ANTHROPIC_API_KEY')

if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not found in environment variables")
    print("\nPlease create a .env file with:")
    print("ANTHROPIC_API_KEY=your_api_key_here")
    exit(1)

print(f"[OK] API Key found: {api_key[:20]}...")

# Test the API
try:
    print("\nTesting Anthropic API connection...")
    client = Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": "Say 'API key is working!' in one sentence."
        }]
    )

    print("[OK] API Connection successful!")
    print(f"\nResponse: {message.content[0].text}")
    print("\n[SUCCESS] Your API key is working correctly!")

except Exception as e:
    print(f"ERROR: {str(e)}")
    print("\nYour API key may be invalid or there may be a connection issue.")
