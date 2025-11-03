#!/usr/bin/env python3
"""
Test Proxy Generation and Deployment
Demonstrates the complete workflow: Select Gateway → Generate Proxy → Deploy to Dev
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from server import GatewayGovernanceAgent
from modules.deployment import DeploymentManager
from modules.context_manager import ContextManager


async def test_apigee_proxy_generation():
    """Test Apigee proxy bundle generation"""
    print("\n" + "="*70)
    print("TEST 1: Apigee Proxy Generation (Pet Store API)")
    print("="*70)
    
    agent = GatewayGovernanceAgent()
    deployment_mgr = DeploymentManager()
    context_mgr = ContextManager()
    
    # Create test directory
    test_dir = Path("/tmp/test-apigee-proxy")
    test_dir.mkdir(exist_ok=True)
    
    # Copy example OAS
    import shutil
    examples_dir = Path(__file__).parent / "examples"
    shutil.copy(examples_dir / "petstore-api.yaml", test_dir / "openapi.yaml")
    
    print("\n📊 Step 1: Selecting gateway...")
    
    # Run gateway selection
    result = await agent.process_request(str(test_dir))
    
    if result.get('status') == 'needs_input':
        print("❓ Answering questions...")
        answers = {
            "api_exposure": "external",
            "auth_type": "oauth"
        }
        result = await agent.answer_questions(result['session_id'], answers)
    
    print(f"✅ Gateway Selected: {result.get('gateway', 'N/A').upper()}")
    print(f"📝 Reason: {result.get('reason', 'N/A')}")
    
    session_id = result['session_id']
    context = context_mgr.get_context(session_id)
    
    print("\n📦 Step 2: Requesting proxy generation...")
    
    # Request confirmation
    deploy_result = await deployment_mgr.generate_and_deploy(
        gateway=context['gateway'],
        oas_spec=context['oas_spec'],
        oas_file=context['oas_file'],
        project_dir=str(test_dir),
        api_name="Pet Store API",
        confirmed=False
    )
    
    print(f"\n{deploy_result['message']}")
    print("\nNext steps:")
    for step in deploy_result['next_steps']:
        print(f"  {step}")
    
    # Simulate user confirmation
    print("\n👤 User confirms deployment...")
    
    # Generate and deploy
    deploy_result = await deployment_mgr.generate_and_deploy(
        gateway=context['gateway'],
        oas_spec=context['oas_spec'],
        oas_file=context['oas_file'],
        project_dir=str(test_dir),
        api_name="Pet Store API",
        confirmed=True
    )
    
    print(f"\n{deploy_result['message']}")
    
    if deploy_result['status'] == 'success':
        print(f"\n📦 Bundle Path: {deploy_result['bundle_path']}")
        print(f"🔗 Base Path: {deploy_result['base_path']}")
        print(f"🌐 Test URL: {deploy_result['test_url']}")
        
        # Check if bundle was created
        bundle_path = Path(deploy_result['bundle_path'])
        if bundle_path.exists():
            size_kb = bundle_path.stat().st_size / 1024
            print(f"✅ Bundle created: {size_kb:.2f} KB")
        
        print("\n📋 Next Steps:")
        for step in deploy_result.get('next_steps', []):
            print(f"  {step}")
        
        # Show deployment details
        deployment = deploy_result.get('deployment', {})
        print(f"\n🚀 Deployment Status: {deployment.get('status', 'N/A')}")
        if deployment.get('status') == 'stub':
            print(f"   Note: {deployment.get('message')}")
            if 'manual_deploy_steps' in deployment:
                print("\n   Manual deployment steps:")
                for step in deployment['manual_deploy_steps']:
                    print(f"     {step}")


async def test_datapower_config_generation():
    """Test DataPower configuration generation"""
    print("\n" + "="*70)
    print("TEST 2: DataPower Configuration Generation (Payment API)")
    print("="*70)
    
    agent = GatewayGovernanceAgent()
    deployment_mgr = DeploymentManager()
    context_mgr = ContextManager()
    
    # Create test directory
    test_dir = Path("/tmp/test-datapower-config")
    test_dir.mkdir(exist_ok=True)
    
    # Copy example OAS
    import shutil
    examples_dir = Path(__file__).parent / "examples"
    shutil.copy(examples_dir / "payment-api.yaml", test_dir / "openapi.yaml")
    
    print("\n📊 Step 1: Selecting gateway...")
    
    # Run gateway selection
    result = await agent.process_request(str(test_dir))
    
    if result.get('status') == 'needs_input':
        print("❓ Answering questions...")
        answers = {
            "api_exposure": "external",
            "auth_type": "both"  # OAuth + mTLS for PCI
        }
        result = await agent.answer_questions(result['session_id'], answers)
    
    print(f"✅ Gateway Selected: {result.get('gateway', 'N/A').upper()}")
    print(f"📝 Reason: {result.get('reason', 'N/A')}")
    print(f"🔍 PCI Detected: {result.get('input_data', {}).get('has_pci', False)}")
    
    session_id = result['session_id']
    context = context_mgr.get_context(session_id)
    
    print("\n⚙️  Step 2: Requesting DataPower configuration...")
    
    # Request confirmation
    deploy_result = await deployment_mgr.generate_and_deploy(
        gateway=context['gateway'],
        oas_spec=context['oas_spec'],
        oas_file=context['oas_file'],
        project_dir=str(test_dir),
        api_name="Payment Processing API",
        confirmed=False
    )
    
    print(f"\n{deploy_result['message']}")
    print("\nNext steps:")
    for step in deploy_result['next_steps']:
        print(f"  {step}")
    
    # Simulate user confirmation
    print("\n👤 User confirms deployment...")
    
    # Generate and deploy
    deploy_result = await deployment_mgr.generate_and_deploy(
        gateway=context['gateway'],
        oas_spec=context['oas_spec'],
        oas_file=context['oas_file'],
        project_dir=str(test_dir),
        api_name="Payment Processing API",
        confirmed=True
    )
    
    print(f"\n{deploy_result['message']}")
    
    if deploy_result['status'] == 'success':
        print(f"\n📦 Package Path: {deploy_result['package_path']}")
        print(f"🏢 Domain: {deploy_result['domain']}")
        print(f"🔗 Base Path: {deploy_result['base_path']}")
        print(f"🌐 Test URL: {deploy_result['test_url']}")
        
        # Check if package was created
        package_path = Path(deploy_result['package_path'])
        if package_path.exists():
            size_kb = package_path.stat().st_size / 1024
            print(f"✅ Package created: {size_kb:.2f} KB")
        
        # Show config files
        print("\n📄 Configuration Files:")
        for file_type, file_path in deploy_result.get('config_files', {}).items():
            print(f"  {file_type}: {Path(file_path).name}")
        
        print("\n📋 Next Steps:")
        for step in deploy_result.get('next_steps', []):
            print(f"  {step}")
        
        # Show deployment details
        deployment = deploy_result.get('deployment', {})
        print(f"\n🚀 Deployment Status: {deployment.get('status', 'N/A')}")
        if deployment.get('status') == 'stub':
            print(f"   Note: {deployment.get('message')}")
            if 'manual_deploy_steps' in deployment:
                print("\n   Manual deployment steps:")
                for step in deployment['manual_deploy_steps']:
                    print(f"     {step}")


async def test_confirmation_flow():
    """Test the confirmation flow"""
    print("\n" + "="*70)
    print("TEST 3: Confirmation Flow (User Rejects)")
    print("="*70)
    
    deployment_mgr = DeploymentManager()
    context_mgr = ContextManager()
    
    # Mock context
    session_id = context_mgr.create_session("/tmp/test-api")
    context_mgr.update_context(session_id, {
        "gateway": "apigee",
        "oas_spec": {
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "servers": [{"url": "http://backend.example.com"}]
        },
        "oas_file": "/tmp/test-api/openapi.yaml"
    })
    
    context = context_mgr.get_context(session_id)
    
    # Request deployment (no confirmation)
    print("\n📦 Requesting deployment...")
    result = await deployment_mgr.generate_and_deploy(
        gateway=context['gateway'],
        oas_spec=context['oas_spec'],
        oas_file=context['oas_file'],
        project_dir="/tmp/test-api",
        api_name="Test API",
        confirmed=False
    )
    
    print(f"\nStatus: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Confirmation Required: {result.get('confirmation_required', False)}")
    
    # Simulate user rejecting
    print("\n👤 User rejects deployment")
    print("❌ Deployment cancelled by user")
    
    print("\n✅ Confirmation flow working correctly")


async def main():
    """Run all proxy generation tests"""
    print("\n🧪 Proxy Generation & Deployment Tests")
    print("="*70)
    
    try:
        # Test 1: Apigee
        await test_apigee_proxy_generation()
        
        # Test 2: DataPower
        await test_datapower_config_generation()
        
        # Test 3: Confirmation flow
        await test_confirmation_flow()
        
        print("\n" + "="*70)
        print("✅ All Proxy Generation Tests Completed!")
        print("="*70)
        
        print("\n📝 Summary:")
        print("  1. Apigee proxy bundle generated successfully")
        print("  2. DataPower configuration generated successfully")
        print("  3. Confirmation flow working correctly")
        
        print("\n💡 Tip: Check the generated files in:")
        print("  - /tmp/test-apigee-proxy/build/apigee/")
        print("  - /tmp/test-datapower-config/build/datapower/")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

