"""
Test the battery formula API endpoint
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_battery_api():
    print("=" * 70)
    print("Testing Battery Formula API Endpoint")
    print("=" * 70)
    
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        print(f"\n✅ Server is running: {health_response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: Server not running on {BASE_URL}")
        print("Please start the server first with: python app.py")
        return
    
    # Test cases
    test_cases = [
        {
            "name": "Test 1: Full payload (250 bullets)",
            "data": {
                "battery_percent": 100.0,
                "bullets": 250,
                "dt_seconds": 60.0
            }
        },
        {
            "name": "Test 2: Empty payload (0 bullets)",
            "data": {
                "battery_percent": 100.0,
                "bullets": 0,
                "dt_seconds": 60.0
            }
        },
        {
            "name": "Test 3: Half payload (125 bullets)",
            "data": {
                "battery_percent": 100.0,
                "bullets": 125,
                "dt_seconds": 60.0
            }
        },
        {
            "name": "Test 4: 10 minutes with full payload",
            "data": {
                "battery_percent": 100.0,
                "bullets": 250,
                "dt_seconds": 600.0
            }
        },
        {
            "name": "Test 5: Low battery with medium payload",
            "data": {
                "battery_percent": 25.0,
                "bullets": 150,
                "dt_seconds": 120.0
            }
        }
    ]
    
    print("\n" + "=" * 70)
    print("Running API Tests")
    print("=" * 70)
    
    for test in test_cases:
        print(f"\n{test['name']}")
        print("-" * 70)
        print(f"Request: {json.dumps(test['data'], indent=2)}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/formulas/battery",
                json=test['data'],
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Response (Status: {response.status_code}):")
                print(json.dumps(result, indent=2))
                
                # Verify calculations
                expected_drain = test['data']['battery_percent'] - result['final_battery']
                actual_drain = result['battery_drained']
                if abs(expected_drain - actual_drain) < 0.01:
                    print(f"\n✅ Calculation verified: {actual_drain:.2f}% drained")
                else:
                    print(f"\n⚠️ Calculation mismatch: expected {expected_drain:.2f}%, got {actual_drain:.2f}%")
            else:
                print(f"\n❌ Error (Status: {response.status_code}):")
                print(response.text)
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request failed: {e}")
        
        time.sleep(0.5)  # Small delay between tests
    
    # Test validation errors
    print("\n" + "=" * 70)
    print("Testing Validation Errors")
    print("=" * 70)
    
    validation_tests = [
        {
            "name": "Invalid battery percentage (> 100)",
            "data": {"battery_percent": 150.0, "bullets": 100, "dt_seconds": 60.0},
            "expected_error": "battery_percent must be between 0 and 100"
        },
        {
            "name": "Invalid bullet count (> 250)",
            "data": {"battery_percent": 100.0, "bullets": 300, "dt_seconds": 60.0},
            "expected_error": "bullets must be between 0 and 250"
        },
        {
            "name": "Invalid time (negative)",
            "data": {"battery_percent": 100.0, "bullets": 100, "dt_seconds": -10.0},
            "expected_error": "dt_seconds must be non-negative"
        }
    ]
    
    for test in validation_tests:
        print(f"\n{test['name']}")
        print("-" * 70)
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/formulas/battery",
                json=test['data'],
                timeout=5
            )
            
            if response.status_code == 400:
                result = response.json()
                print(f"✅ Validation error caught (Status: {response.status_code}):")
                print(f"   Error: {result.get('error')}")
                if result.get('error') == test['expected_error']:
                    print("✅ Correct error message")
                else:
                    print(f"⚠️ Expected: {test['expected_error']}")
            else:
                print(f"❌ Expected 400 error, got {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    print("\n" + "=" * 70)
    print("✅ All API tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    test_battery_api()
