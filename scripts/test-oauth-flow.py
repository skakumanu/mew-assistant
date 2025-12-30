#!/usr/bin/env python3
"""
Test OAuth flow to debug authentication issues
"""

import asyncio

import httpx

BASE_URL = "https://mew-assistant-dev.gentlehill-b3306295.westus2.azurecontainerapps.io"


async def test_oauth_flow():
    async with httpx.AsyncClient(follow_redirects=False) as client:
        # Step 1: Get authorization URL
        print("Step 1: Initiating OAuth flow...")
        response = await client.get(f"{BASE_URL}/auth/oauth/authorize/google")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 307:
            redirect_url = response.headers.get("location")
            print(f"\nRedirect URL: {redirect_url}")
            print(
                "\nPlease visit this URL in your browser and complete the Google sign-in."
            )
            print("After signing in, copy the full callback URL from your browser.")


if __name__ == "__main__":
    asyncio.run(test_oauth_flow())
