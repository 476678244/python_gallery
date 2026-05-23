#!/usr/bin/env python3
"""
Flow Coding E2E Test: 基础对话功能
使用 Playwright 测试 SafeClaw API 的 chat/stream 端点

遵循 flow_coding.md 的 5 阶段算法:
1. Establish verification baseline
2. Intent expression & code generation  
3. Test spec adaptation
4. Self-healing loop
5. Final convergence
"""

import subprocess
import sys
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30  # seconds


def wait_for_server(url, max_retries=30, delay=1):
    """Wait for server to be ready"""
    print(f"⏳ Waiting for server at {url}...")
    for i in range(max_retries):
        try:
            req = urllib.request.Request(f"{url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    print(f"✅ Server is ready!")
                    return True
        except Exception as e:
            print(f"  Attempt {i+1}/{max_retries}: {e}")
            time.sleep(delay)
    return False


def test_health_endpoint():
    """Phase 1: Health check - verification baseline"""
    print("\n" + "="*60)
    print("Phase 1: Health Check (Verification Baseline)")
    print("="*60)
    
    try:
        req = urllib.request.Request(f"{BASE_URL}/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            body = response.read().decode('utf-8')
            data = json.loads(body)
            print(f"✅ Health check passed: {data}")
            return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_basic_chat_stream():
    """Test basic chat streaming endpoint"""
    print("\n" + "="*60)
    print("Phase 2: Basic Chat Stream Test")
    print("="*60)
    
    # Prepare request
    chat_request = {
        "messages": [
            {"role": "user", "content": "Hello, SafeClaw! What can you help me with?"}
        ],
        "session_id": "test-session-001",
        "model": "qwen3.5-9b-vlm",
        "temperature": 0.7,
        "stream": True
    }
    
    print(f"📤 Sending chat request: {json.dumps(chat_request, indent=2)}")
    
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/chat/stream",
            data=json.dumps(chat_request).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            method="POST"
        )
        
        print("\n📥 Receiving stream...")
        events_received = []
        
        with urllib.request.urlopen(req, timeout=60) as response:
            # Read SSE stream line by line
            for line in response:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    if data_str == '[DONE]':
                        break
                    try:
                        event = json.loads(data_str)
                        events_received.append(event)
                        
                        # Print different event types
                        if event.get('type') == 'execution_step':
                            step = event.get('step_id', 'unknown')
                            status = event.get('status', 'unknown')
                            print(f"  Step [{step}]: {status}")
                        elif event.get('type') == 'content':
                            content = event.get('content', '')[:50]
                            print(f"  Content: {content}...")
                        elif event.get('type') == 'done':
                            print(f"  ✅ Stream complete!")
                            msg_id = event.get('message_id', 'unknown')
                            total_tokens = event.get('usage', {}).get('total_tokens', 0)
                            print(f"  Message ID: {msg_id}")
                            print(f"  Total tokens: {total_tokens}")
                            
                            # Store message_id for LLM call logs test
                            global last_message_id
                            last_message_id = msg_id
                            
                    except json.JSONDecodeError:
                        print(f"  ⚠️  Could not parse: {data_str[:100]}")
        
        print(f"\n✅ Received {len(events_received)} events")
        return True
        
    except Exception as e:
        print(f"❌ Chat stream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_call_logs():
    """Test LLM call logs endpoint"""
    print("\n" + "="*60)
    print("Phase 3: LLM Call Logs Verification")
    print("="*60)
    
    if not last_message_id:
        print("❌ No message_id from previous test, skipping")
        return False
    
    print(f"🔍 Checking LLM call logs for: {last_message_id}")
    
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/llm-calls/{last_message_id}",
            method="GET"
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            body = response.read().decode('utf-8')
            data = json.loads(body)
            
            total_calls = data.get('total_calls', 0)
            calls = data.get('calls', [])
            
            print(f"✅ Found {total_calls} LLM call(s)")
            
            for i, call in enumerate(calls):
                print(f"\n  Call #{i+1}:")
                print(f"    - ID: {call.get('call_id', 'N/A')}")
                print(f"    - Duration: {call.get('duration_ms', 'N/A')}ms")
                print(f"    - Tokens: {call.get('prompt_tokens', 0)} in / {call.get('completion_tokens', 0)} out")
                print(f"    - Response preview: {call.get('response_preview', 'N/A')[:50]}...")
            
            return total_calls > 0
            
    except Exception as e:
        print(f"❌ LLM call logs test failed: {e}")
        return False


def main():
    """Main test runner - Flow Coding 5-phase process"""
    print("\n🚀 SafeClaw Basic Chat E2E Test (Flow Coding)")
    print("="*60)
    
    # Start API server
    print("\n🔧 Starting API server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "streamlit_ui.api.main:app", 
         "--host", "0.0.0.0", "--port", "8000", 
         "--reload", "False", "--log-level", "warning"],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    
    try:
        # Wait for server
        if not wait_for_server(BASE_URL):
            print("❌ Server failed to start")
            return 1
        
        # Run tests
        results = []
        
        # Phase 1: Health check
        results.append(("Health Check", test_health_endpoint()))
        
        # Phase 2: Basic chat
        results.append(("Basic Chat Stream", test_basic_chat_stream()))
        
        # Phase 3: LLM call logs
        results.append(("LLM Call Logs", test_llm_call_logs()))
        
        # Final report
        print("\n" + "="*60)
        print("Phase 5: Final Convergence & Confirmation")
        print("="*60)
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {name}")
        
        print(f"\n📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! Flow Coding complete.")
            return 0
        else:
            print("\n⚠️  Some tests failed. Entering self-healing loop...")
            return 1
            
    finally:
        # Cleanup
        print("\n🛑 Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()


if __name__ == "__main__":
    sys.exit(main())
