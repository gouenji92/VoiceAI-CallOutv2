"""
Comprehensive API Testing Script
Test tất cả các endpoints của VoiceAI API
"""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
TEST_PASSWORD = "TestPassword123!"

class APITester:
    """Class để test các API endpoints"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self.token: Optional[str] = None
        self.workflow_id: Optional[str] = None
        self.call_id: Optional[str] = None
        self.test_results = []
    
    def log_test(self, name: str, success: bool, message: str = "", data: Any = None):
        """Log kết quả test"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{status} - {name}")
        if message:
            print(f"   Message: {message}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_health_check(self):
        """Test endpoint health check"""
        try:
            response = await self.client.get("/")
            self.log_test(
                "Health Check",
                response.status_code == 200,
                f"Status: {response.status_code}",
                response.json()
            )
            return response.status_code == 200
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False
    
    async def test_register(self):
        """Test đăng ký user mới"""
        try:
            data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "role": "user"
            }
            response = await self.client.post("/api/auth/register", json=data)
            success = response.status_code in [200, 201]
            self.log_test(
                "User Registration",
                success,
                f"Status: {response.status_code}",
                response.json() if success else response.text
            )
            return success
        except Exception as e:
            self.log_test("User Registration", False, str(e))
            return False
    
    async def test_login(self):
        """Test đăng nhập"""
        try:
            data = {
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            response = await self.client.post(
                "/api/auth/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get("access_token")
                self.client.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                self.log_test(
                    "User Login",
                    True,
                    "Token received",
                    {"token_preview": self.token[:20] + "..."}
                )
                return True
            else:
                self.log_test(
                    "User Login",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False
    
    async def test_create_workflow(self):
        """Test tạo workflow"""
        try:
            data = {
                "name": f"Test Workflow {datetime.now().strftime('%H%M%S')}",
                "description": "Workflow created by automated test"
            }
            response = await self.client.post("/api/workflows/", json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.workflow_id = result.get("id")
                self.log_test(
                    "Create Workflow",
                    True,
                    f"Workflow ID: {self.workflow_id}",
                    result
                )
                return True
            else:
                self.log_test(
                    "Create Workflow",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
        except Exception as e:
            self.log_test("Create Workflow", False, str(e))
            return False
    
    async def test_get_workflows(self):
        """Test lấy danh sách workflows"""
        try:
            response = await self.client.get("/api/workflows/")
            success = response.status_code == 200
            
            if success:
                workflows = response.json()
                self.log_test(
                    "Get Workflows",
                    True,
                    f"Found {len(workflows)} workflows",
                    workflows[:2]  # Chỉ hiển thị 2 workflows đầu
                )
            else:
                self.log_test(
                    "Get Workflows",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            return success
        except Exception as e:
            self.log_test("Get Workflows", False, str(e))
            return False
    
    async def test_create_workflow_version(self):
        """Test tạo version cho workflow"""
        if not self.workflow_id:
            self.log_test("Create Workflow Version", False, "No workflow_id available")
            return False
        
        try:
            workflow_json = {
                "nodes": [
                    {
                        "id": "start",
                        "type": "greeting",
                        "message": "Xin chào, đây là test workflow"
                    }
                ],
                "edges": []
            }
            
            data = {
                "workflow_json": workflow_json,
                "change_description": "Initial version created by test"
            }
            
            response = await self.client.put(
                f"/api/workflows/{self.workflow_id}",
                json=data
            )
            
            success = response.status_code == 200
            self.log_test(
                "Create Workflow Version",
                success,
                f"Status: {response.status_code}",
                response.json() if success else response.text
            )
            return success
        except Exception as e:
            self.log_test("Create Workflow Version", False, str(e))
            return False
    
    async def test_nlp_processing(self):
        """Test NLP service thông qua webhook"""
        test_texts = [
            "Tôi muốn đặt lịch vào 9h sáng mai",
            "Số điện thoại của tôi là 0909123456",
            "Email tôi là test@example.com",
            "Hẹn gặp vào ngày 25 tháng 12"
        ]
        
        for text in test_texts:
            try:
                # Test entity extraction
                from app.services.entity_extractor import extract_entities
                entities = extract_entities(text)
                
                has_entities = any(entities.values())
                self.log_test(
                    f"NLP Entity Extraction: '{text[:30]}...'",
                    has_entities,
                    f"Found entities",
                    entities
                )
            except Exception as e:
                self.log_test(
                    f"NLP Entity Extraction: '{text[:30]}...'",
                    False,
                    str(e)
                )
    
    async def test_start_call(self):
        """Test khởi tạo cuộc gọi"""
        if not self.workflow_id:
            self.log_test("Start Call", False, "No workflow_id available")
            return False
        
        try:
            data = {
                "workflow_id": self.workflow_id,
                "customer_phone": "0909123456"
            }
            
            response = await self.client.post("/api/calls/start_call", json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.call_id = result.get("call_id")
                self.log_test(
                    "Start Call",
                    True,
                    f"Call ID: {self.call_id}",
                    result
                )
                return True
            else:
                self.log_test(
                    "Start Call",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
        except Exception as e:
            self.log_test("Start Call", False, str(e))
            return False
    
    async def test_webhook(self):
        """Test webhook xử lý speech input"""
        if not self.call_id:
            self.log_test("Webhook Processing", False, "No call_id available")
            return False
        
        test_inputs = [
            "Tôi muốn đặt lịch khám",
            "9 giờ sáng mai được không?",
            "Cảm ơn, tạm biệt"
        ]
        
        for text in test_inputs:
            try:
                data = {
                    "call_id": self.call_id,
                    "speech_to_text": text
                }
                
                response = await self.client.post("/api/calls/webhook", json=data)
                success = response.status_code == 200
                
                self.log_test(
                    f"Webhook: '{text}'",
                    success,
                    f"Status: {response.status_code}",
                    response.json() if success else response.text
                )
                
                # Delay giữa các request
                await asyncio.sleep(1)
            except Exception as e:
                self.log_test(f"Webhook: '{text}'", False, str(e))
    
    async def cleanup(self):
        """Đóng connection"""
        await self.client.aclose()
    
    def print_summary(self):
        """In tóm tắt kết quả test"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print("="*60)
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['name']}: {result['message']}")
    
    async def run_all_tests(self):
        """Chạy tất cả tests"""
        print("="*60)
        print("VOICEAI API COMPREHENSIVE TEST SUITE")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Test Email: {TEST_EMAIL}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test theo thứ tự
        await self.test_health_check()
        
        # Auth tests
        await self.test_register()
        await self.test_login()
        
        if self.token:
            # Workflow tests
            await self.test_create_workflow()
            await self.test_get_workflows()
            await self.test_create_workflow_version()
            
            # NLP tests
            await self.test_nlp_processing()
            
            # Call tests
            await self.test_start_call()
            await self.test_webhook()
        
        await self.cleanup()
        self.print_summary()


async def main():
    """Main function"""
    tester = APITester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        await tester.cleanup()
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        await tester.cleanup()


if __name__ == "__main__":
    print("\n⚠️  Lưu ý: Đảm bảo FastAPI server đang chạy ở http://localhost:8000")
    print("   Chạy server: uvicorn app.main:app --reload\n")
    
    asyncio.run(main())
