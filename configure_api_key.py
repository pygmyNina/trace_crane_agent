#!/usr/bin/env python3
"""
Interactive API key configuration for TRACE
"""

import os
import sys


def configure_api_key():
    """Interactive API key setup"""
    print("\n" + "="*60)
    print("  TRACE API Key Configuration")
    print("="*60 + "\n")

    # Check if .env already exists
    env_exists = os.path.exists('.env')

    if env_exists:
        print("⚠ .env file already exists")
        response = input("Do you want to update it? (y/n): ").lower()
        if response != 'y':
            print("\nSetup cancelled.")
            return

    print("\nPaste your Anthropic API key below.")
    print("(Get it from: https://console.anthropic.com/)\n")

    api_key = input("API Key: ").strip()

    if not api_key or api_key == "your-api-key-here":
        print("\n✗ Invalid API key. Setup cancelled.")
        return

    # Validate key format (should start with sk-)
    if not api_key.startswith('sk-'):
        print("\n⚠ Warning: API key should typically start with 'sk-'")
        response = input("Continue anyway? (y/n): ").lower()
        if response != 'y':
            print("\nSetup cancelled.")
            return

    # Write .env file
    with open('.env', 'w') as f:
        f.write(f"# TRACE Configuration\n")
        f.write(f"# Anthropic API Key for Vision features\n\n")
        f.write(f"ANTHROPIC_API_KEY={api_key}\n")

    print("\n✓ API key saved to .env")

    # Test the API key
    print("\n" + "="*60)
    print("Testing API connection...")
    print("="*60 + "\n")

    os.environ['ANTHROPIC_API_KEY'] = api_key

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        # Simple test call
        print("Sending test request to Claude API...")
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with just the word 'success' if you receive this."
                }
            ]
        )

        response_text = message.content[0].text.lower()

        if 'success' in response_text:
            print("\n✓ API key is valid and working!")
            print("\n" + "="*60)
            print("  Setup Complete!")
            print("="*60)
            print("\nYou can now use all Vision features:")
            print("  • load section <section> <pdf> --index")
            print("  • ask <question>")
            print("  • analyze <section> <pdf> <page>")
            print("  • trace <component>")
            print("\nStart TRACE:")
            print("  python trace_cli.py")
            print()
        else:
            print("\n⚠ Unexpected response from API")
            print(f"Response: {message.content[0].text}")

    except Exception as e:
        print(f"\n✗ Error testing API key: {e}")
        print("\nThe key was saved to .env, but the test failed.")
        print("Please verify your API key at: https://console.anthropic.com/")
        return

    # Update .gitignore if needed
    gitignore_path = '.gitignore'
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()

        if '.env' not in gitignore_content:
            with open(gitignore_path, 'a') as f:
                f.write('\n.env\n')
            print("✓ Added .env to .gitignore")


if __name__ == "__main__":
    try:
        configure_api_key()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
