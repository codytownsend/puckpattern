import requests
import sys

BASE_URL = "http://localhost:8000/api"

def test_endpoint(path, method="GET", expected_status=200, data=None):
    """Test an API endpoint and print the result."""
    url = f"{BASE_URL}{path}"
    print(f"Testing {method} {url}...")
    
    if method == "GET":
        response = requests.get(url)
    elif method == "POST":
        response = requests.post(url, json=data)
    
    if response.status_code == expected_status:
        print(f"✓ Success: {response.status_code}")
        return True
    else:
        print(f"✗ Failed: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return False

def run_tests():
    """Run all API endpoint tests."""
    failures = 0
    
    # Test root endpoint
    if not test_endpoint("/", "GET", 200):
        failures += 1
    
    # Test teams endpoints
    if not test_endpoint("/teams/", "GET", 200):
        failures += 1
    
    # Test players endpoints
    if not test_endpoint("/players/", "GET", 200):
        failures += 1
    
    # Test games endpoints
    if not test_endpoint("/games/", "GET", 200):
        failures += 1
    
    # Test metrics endpoint (requires data)
    if not test_endpoint("/metrics/", "GET", 200):
        failures += 1
    
    print(f"\nResults: {failures} failures")
    return failures == 0

if __name__ == "__main__":
    print("Starting API endpoint tests...")
    success = run_tests()
    sys.exit(0 if success else 1)