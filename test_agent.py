#!/usr/bin/env python3
"""
Test script for Gateway Governance Agent
Demonstrates how to use the agent programmatically
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from server import GatewayGovernanceAgent


async def test_petstore_api():
    """Test with non-PCI API (Pet Store)"""
    print("\n" + "="*60)
    print("TEST 1: Pet Store API (Non-PCI)")
    print("="*60)
    
    agent = GatewayGovernanceAgent()
    
    # Create test directory
    test_dir = Path("/tmp/test-petstore")
    test_dir.mkdir(exist_ok=True)
    
    # Copy example OAS
    import shutil
    examples_dir = Path(__file__).parent / "examples"
    shutil.copy(examples_dir / "petstore-api.yaml", test_dir / "openapi.yaml")
    
    # Run gateway selection
    result = await agent.process_request(str(test_dir))
    
    print("\n📊 Result:")
    print(f"Status: {result.get('status')}")
    
    if result.get('status') == 'needs_input':
        print(f"\n❓ Questions needed:")
        for q in result.get('questions', []):
            print(f"  - {q['question']}")
            print(f"    Options: {q['options']}")
        
        # Answer questions
        print("\n✍️  Providing answers...")
        answers = {
            "api_exposure": "external",
            "auth_type": "oauth"
        }
        
        result = await agent.answer_questions(result['session_id'], answers)
    
    print(f"\n✅ Gateway Selected: {result.get('gateway', 'N/A').upper()}")
    print(f"📝 Reason: {result.get('reason', 'N/A')}")
    print(f"🔖 Rule: {result.get('rule_id', 'N/A')}")


async def test_payment_api():
    """Test with PCI API (Payment)"""
    print("\n" + "="*60)
    print("TEST 2: Payment API (PCI Data)")
    print("="*60)
    
    agent = GatewayGovernanceAgent()
    
    # Create test directory
    test_dir = Path("/tmp/test-payment")
    test_dir.mkdir(exist_ok=True)
    
    # Copy example OAS
    import shutil
    examples_dir = Path(__file__).parent / "examples"
    shutil.copy(examples_dir / "payment-api.yaml", test_dir / "openapi.yaml")
    
    # Run gateway selection
    result = await agent.process_request(str(test_dir))
    
    print("\n📊 Result:")
    print(f"Status: {result.get('status')}")
    
    if result.get('status') == 'needs_input':
        print(f"\n🔍 PCI Analysis:")
        analysis = result.get('current_analysis', {})
        print(f"  PCI Detected: {analysis.get('pci_detected', False)}")
        print(f"  PCI Fields: {analysis.get('pci_fields', [])}")
        
        print(f"\n❓ Questions needed:")
        for q in result.get('questions', []):
            print(f"  - {q['question']}")
            print(f"    Options: {q['options']}")
        
        # Answer questions
        print("\n✍️  Providing answers...")
        answers = {
            "api_exposure": "external",
            "auth_type": "both"  # OAuth + mTLS
        }
        
        result = await agent.answer_questions(result['session_id'], answers)
    
    print(f"\n✅ Gateway Selected: {result.get('gateway', 'N/A').upper()}")
    print(f"📝 Reason: {result.get('reason', 'N/A')}")
    print(f"🔖 Rule: {result.get('rule_id', 'N/A')}")


async def test_preconfigured():
    """Test with pre-configured gateway"""
    print("\n" + "="*60)
    print("TEST 3: Pre-configured Gateway")
    print("="*60)
    
    agent = GatewayGovernanceAgent()
    
    # Create test directory
    test_dir = Path("/tmp/test-preconfigured")
    test_dir.mkdir(exist_ok=True)
    
    # Copy pre-configured selection
    import shutil
    examples_dir = Path(__file__).parent / "examples"
    shutil.copy(examples_dir / "gateway-selection.json", test_dir)
    
    # Run gateway selection
    result = await agent.process_request(str(test_dir))
    
    print("\n📊 Result:")
    print(f"Status: {result.get('status')}")
    print(f"✅ Gateway: {result.get('gateway', 'N/A').upper()}")
    print(f"📝 Reason: {result.get('reason', 'N/A')}")
    print(f"📦 Source: {result.get('source', 'N/A')}")


async def view_audit_logs():
    """View recent audit logs"""
    print("\n" + "="*60)
    print("AUDIT LOGS")
    print("="*60)
    
    from modules.audit_logger import AuditLogger
    
    logger = AuditLogger()
    logs = await logger.get_recent_logs(limit=5)
    
    if not logs:
        print("\nℹ️  No audit logs found")
        return
    
    print(f"\n📋 Recent {len(logs)} decisions:")
    for i, log in enumerate(logs, 1):
        print(f"\n{i}. {log.get('timestamp', 'Unknown time')}")
        print(f"   Project: {log.get('project_dir', 'Unknown')}")
        decision = log.get('decision', {})
        print(f"   Gateway: {decision.get('gateway', 'N/A').upper()}")
        print(f"   Rule: {decision.get('rule_id', 'N/A')}")
        context = log.get('context', {})
        print(f"   PCI: {context.get('pci_detected', False)}")


async def main():
    """Run all tests"""
    print("\n🧪 Gateway Governance Agent - Test Suite")
    print("=========================================")
    
    try:
        # Test 1: Non-PCI API
        await test_petstore_api()
        
        # Test 2: PCI API
        await test_payment_api()
        
        # Test 3: Pre-configured
        await test_preconfigured()
        
        # View audit logs
        await view_audit_logs()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

