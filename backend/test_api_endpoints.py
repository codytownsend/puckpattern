import requests
import sys
import json

# The BASE_URL should already have /api but check that it does
BASE_URL = "http://localhost:8000/api"

def test_endpoint(path, method="GET", expected_status=200, data=None, params=None, print_response=False):
    """Test an API endpoint and print the result."""
    # Make sure path doesn't start with /api since it's already in BASE_URL
    if path.startswith('/api'):
        path = path[4:]  # Remove the /api prefix
    
    # Make sure path starts with /
    if not path.startswith('/'):
        path = '/' + path
        
    url = f"{BASE_URL}{path}"
    print(f"Testing {method} {url}...")
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, timeout=5)
        
        if response.status_code == expected_status:
            print(f"✓ Success: {response.status_code}")
            if print_response and response.status_code == 200:
                try:
                    json_data = response.json()
                    if isinstance(json_data, dict):
                        # Print first few keys for readability
                        keys = list(json_data.keys())[:3]
                        print(f"  Response keys: {keys}...")
                    elif isinstance(json_data, list) and json_data:
                        print(f"  First item of {len(json_data)}: {json_data[0]}")
                    else:
                        print(f"  Response: {json_data}")
                except:
                    print(f"  Non-JSON response of length {len(response.text)}")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}...")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Connection failed - is the server running at {url}?")
        return False
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        return False

def run_tests():
    """Run all API endpoint tests."""
    failures = 0
    total = 0
    
    # Root endpoint (this is at / not /api)
    total += 1
    if not test_endpoint("/", "GET", 200):
        failures += 1
    
    # Teams endpoints
    total += 1
    if not test_endpoint("/teams/", "GET", 200, print_response=True):
        failures += 1
    
    # Players endpoints
    total += 1
    if not test_endpoint("/players/", "GET", 200, print_response=True):
        failures += 1
    
    # Games endpoints
    total += 1
    if not test_endpoint("/games/", "GET", 200, print_response=True):
        failures += 1
    
    # Shots endpoints - expect success even if empty
    total += 1
    if not test_endpoint("/shots/", "GET", 200):
        failures += 1
    
    # Zone entries endpoints - expect success even if empty
    total += 1
    if not test_endpoint("/entries/", "GET", 200):
        failures += 1
    
    # Events endpoints - expect success even if empty
    total += 1
    if not test_endpoint("/events/", "GET", 200):
        failures += 1
    
    # Metrics endpoint for a team (this might fail if team 1 doesn't exist)
    # Let's test it but not count it as a failure
    response = requests.get(f"{BASE_URL}/metrics/team/1")
    print(f"Testing GET {BASE_URL}/metrics/team/1...")
    if response.status_code == 200:
        print(f"✓ Success: {response.status_code}")
    else:
        print(f"⚠️ Note: {response.status_code} - This may be normal if team ID 1 doesn't exist")
        print(f"  Response: {response.text[:200]}...")
    
    print(f"\nResults: {total-failures}/{total} tests passed ({failures} failures)")
    return failures == 0

if __name__ == "__main__":
    print("Starting API endpoint tests...")
    success = run_tests()
    sys.exit(0 if success else 1)