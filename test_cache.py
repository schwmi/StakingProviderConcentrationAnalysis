"""
Test script to verify the caching functionality of the StakingRewards API client.
"""

import os
import time
from pathlib import Path
from Helper import StakingRewardsAPIClient

def test_caching():
    """Test that caching works correctly."""

    # Initialize client
    client = StakingRewardsAPIClient()

    print("Testing caching functionality...")
    print("-" * 50)

    # Test 1: First call should hit the API and create a cache file
    print("\n1. First call (should hit API and create cache):")
    start = time.time()
    result1 = client.get_assets(symbols=["ETH"], limit=1)
    duration1 = time.time() - start
    print(f"   Duration: {duration1:.3f} seconds")
    print(f"   Result: {result1}")

    # Check if cache file was created
    cache_files = list(Path("api_response_cache").glob("*.json"))
    print(f"   Cache files created: {len(cache_files)}")

    # Test 2: Second call with same parameters should use cache (much faster)
    print("\n2. Second call with same parameters (should use cache):")
    start = time.time()
    result2 = client.get_assets(symbols=["ETH"], limit=1)
    duration2 = time.time() - start
    print(f"   Duration: {duration2:.3f} seconds")
    print(f"   Results match: {result1 == result2}")
    print(f"   Speed improvement: {duration1 / duration2:.1f}x faster")

    # Test 3: Call with use_cache=False should bypass cache
    print("\n3. Third call with use_cache=False (should hit API):")
    start = time.time()
    result3 = client.get_assets(symbols=["ETH"], limit=1, use_cache=False)
    duration3 = time.time() - start
    print(f"   Duration: {duration3:.3f} seconds")
    print(f"   Results match: {result1 == result3}")

    # Test 4: Different query should create a new cache file
    print("\n4. Different query (should create new cache):")
    cache_count_before = len(list(Path("api_response_cache").glob("*.json")))
    result4 = client.get_assets(symbols=["BTC"], limit=1)
    cache_count_after = len(list(Path("api_response_cache").glob("*.json")))
    print(f"   Cache files before: {cache_count_before}")
    print(f"   Cache files after: {cache_count_after}")
    print(f"   New cache file created: {cache_count_after > cache_count_before}")

    print("\n" + "-" * 50)
    print("Caching test completed!")
    print(f"Total cache files: {cache_count_after}")

if __name__ == "__main__":
    test_caching()
