#!/usr/bin/env python3
"""
Backend API Tests for PicoGnize AI Image Recognition App
Tests all backend endpoints and core functionality
"""

import requests
import json
import base64
import time
from io import BytesIO
from PIL import Image
import os

# API Configuration
API_BASE_URL = "https://picognize.preview.emergentagent.com/api"

class PicoGnizeAPITester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.test_analysis_id = None
        
    def create_sample_image_base64(self):
        """Create a simple test image and convert to base64"""
        # Create a simple colored image with text
        img = Image.new('RGB', (200, 100), color='lightblue')
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return img_base64
    
    def test_health_check(self):
        """Test GET /api/ endpoint"""
        print("\n=== Testing Health Check Endpoint ===")
        try:
            response = self.session.get(f"{self.base_url}/")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "AI Image Recognition API is running!":
                    print("✅ Health check passed")
                    return True
                else:
                    print("❌ Health check failed - incorrect message")
                    return False
            else:
                print(f"❌ Health check failed - status code {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check failed with error: {str(e)}")
            return False
    
    def test_image_analysis(self):
        """Test POST /api/analyze-image endpoint"""
        print("\n=== Testing Image Analysis Endpoint ===")
        try:
            # Create test image
            test_image_base64 = self.create_sample_image_base64()
            
            payload = {
                "filename": "test_image.png",
                "image_base64": test_image_base64
            }
            
            print("Sending image analysis request...")
            response = self.session.post(
                f"{self.base_url}/analyze-image",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Image analysis request successful")
                
                # Store the analysis ID for later tests
                self.test_analysis_id = data.get("id")
                
                # Verify response structure
                required_fields = ["id", "filename", "analysis", "objects_detected", 
                                 "text_found", "emotions", "scene_description", 
                                 "confidence", "timestamp"]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    print(f"❌ Missing required fields: {missing_fields}")
                    return False
                
                print(f"Analysis ID: {data.get('id')}")
                print(f"Filename: {data.get('filename')}")
                print(f"Analysis: {data.get('analysis')[:100]}...")
                print(f"Objects Detected: {data.get('objects_detected')}")
                print(f"Text Found: {data.get('text_found')}")
                print(f"Emotions: {data.get('emotions')}")
                print(f"Scene: {data.get('scene_description')}")
                print(f"Confidence: {data.get('confidence')}")
                
                # Verify structured parsing worked
                if data.get('analysis'):
                    print("✅ AI analysis generated successfully")
                    return True
                else:
                    print("❌ AI analysis is empty")
                    return False
            else:
                print(f"❌ Image analysis failed - status code {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {error_detail}")
                except:
                    print(f"Error response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Image analysis failed with error: {str(e)}")
            return False
    
    def test_analysis_history(self):
        """Test GET /api/analysis-history endpoint"""
        print("\n=== Testing Analysis History Endpoint ===")
        try:
            response = self.session.get(f"{self.base_url}/analysis-history")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Analysis history retrieved successfully")
                print(f"Number of analyses: {len(data)}")
                
                if len(data) > 0:
                    # Verify structure of first item
                    first_analysis = data[0]
                    required_fields = ["id", "filename", "analysis", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in first_analysis]
                    
                    if missing_fields:
                        print(f"❌ Missing required fields in history item: {missing_fields}")
                        return False
                    
                    print(f"Latest analysis ID: {first_analysis.get('id')}")
                    print(f"Latest analysis filename: {first_analysis.get('filename')}")
                
                return True
            else:
                print(f"❌ Analysis history failed - status code {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Analysis history failed with error: {str(e)}")
            return False
    
    def test_get_specific_analysis(self):
        """Test GET /api/analysis/{analysis_id} endpoint"""
        print("\n=== Testing Get Specific Analysis Endpoint ===")
        
        if not self.test_analysis_id:
            print("❌ No test analysis ID available - skipping test")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/analysis/{self.test_analysis_id}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Specific analysis retrieved successfully")
                print(f"Analysis ID: {data.get('id')}")
                print(f"Filename: {data.get('filename')}")
                
                # Verify it's the same analysis we created
                if data.get('id') == self.test_analysis_id:
                    print("✅ Retrieved correct analysis")
                    return True
                else:
                    print("❌ Retrieved wrong analysis")
                    return False
            elif response.status_code == 404:
                print("❌ Analysis not found - database storage may have failed")
                return False
            else:
                print(f"❌ Get specific analysis failed - status code {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Get specific analysis failed with error: {str(e)}")
            return False
    
    def test_delete_analysis(self):
        """Test DELETE /api/analysis/{analysis_id} endpoint"""
        print("\n=== Testing Delete Analysis Endpoint ===")
        
        if not self.test_analysis_id:
            print("❌ No test analysis ID available - skipping test")
            return False
            
        try:
            response = self.session.delete(f"{self.base_url}/analysis/{self.test_analysis_id}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Analysis deleted successfully")
                print(f"Response: {data}")
                
                # Verify deletion by trying to get the analysis again
                verify_response = self.session.get(f"{self.base_url}/analysis/{self.test_analysis_id}")
                if verify_response.status_code == 404:
                    print("✅ Deletion verified - analysis no longer exists")
                    return True
                else:
                    print("❌ Deletion verification failed - analysis still exists")
                    return False
            elif response.status_code == 404:
                print("❌ Analysis not found for deletion")
                return False
            else:
                print(f"❌ Delete analysis failed - status code {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Delete analysis failed with error: {str(e)}")
            return False
    
    def test_cors_headers(self):
        """Test CORS configuration"""
        print("\n=== Testing CORS Configuration ===")
        try:
            # Make an OPTIONS request to check CORS headers
            response = self.session.options(f"{self.base_url}/")
            print(f"OPTIONS Status Code: {response.status_code}")
            
            # Check for CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            print("CORS Headers:")
            for header, value in cors_headers.items():
                print(f"  {header}: {value}")
            
            if cors_headers['Access-Control-Allow-Origin']:
                print("✅ CORS configured")
                return True
            else:
                print("❌ CORS not properly configured")
                return False
                
        except Exception as e:
            print(f"❌ CORS test failed with error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n=== Testing Error Handling ===")
        
        # Test invalid analysis ID
        print("Testing invalid analysis ID...")
        try:
            response = self.session.get(f"{self.base_url}/analysis/invalid-id")
            if response.status_code == 404:
                print("✅ Invalid analysis ID handled correctly")
                error_handling_score = 1
            else:
                print(f"❌ Invalid analysis ID not handled correctly - status: {response.status_code}")
                error_handling_score = 0
        except Exception as e:
            print(f"❌ Error testing invalid analysis ID: {str(e)}")
            error_handling_score = 0
        
        # Test malformed image analysis request
        print("Testing malformed image analysis request...")
        try:
            response = self.session.post(
                f"{self.base_url}/analyze-image",
                json={"invalid": "data"},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code in [400, 422]:  # Bad request or validation error
                print("✅ Malformed request handled correctly")
                error_handling_score += 1
            else:
                print(f"❌ Malformed request not handled correctly - status: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing malformed request: {str(e)}")
        
        return error_handling_score >= 1
    
    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting PicoGnize Backend API Tests")
        print(f"API Base URL: {self.base_url}")
        
        test_results = {}
        
        # Run tests in order
        test_results['health_check'] = self.test_health_check()
        test_results['image_analysis'] = self.test_image_analysis()
        test_results['analysis_history'] = self.test_analysis_history()
        test_results['get_specific_analysis'] = self.test_get_specific_analysis()
        test_results['delete_analysis'] = self.test_delete_analysis()
        test_results['cors_headers'] = self.test_cors_headers()
        test_results['error_handling'] = self.test_error_handling()
        
        # Summary
        print("\n" + "="*50)
        print("🏁 TEST SUMMARY")
        print("="*50)
        
        passed = sum(test_results.values())
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Backend API is working correctly.")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Backend needs attention.")
            return False

def main():
    """Main test execution"""
    tester = PicoGnizeAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Backend testing completed successfully!")
        exit(0)
    else:
        print("\n❌ Backend testing completed with failures!")
        exit(1)

if __name__ == "__main__":
    main()