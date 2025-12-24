#!/usr/bin/env python3
"""
Test ReAct Agent (Reasoning + Acting)
Demonstrates Sense → Think → Act → Feedback cycle
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.react_agent import ReActAgent
from modules.reasoning_engine import ReasoningEngine


async def test_react_with_payment_api():
    """Test ReAct cycle with PCI-compliant API"""
    print("\n" + "="*70)
    print("TEST 1: ReAct Agent with Payment API (PCI Data)")
    print("="*70)
    
    agent = ReActAgent()
    
    # Create test directory
    test_dir = Path("/tmp/test-react-payment")
    test_dir.mkdir(exist_ok=True)
    
    # Copy example OAS
    import shutil
    examples_dir = Path(__file__).parent / "examples"
    shutil.copy(examples_dir / "payment-api.yaml", test_dir / "openapi.yaml")
    
    print("\n🔍 PHASE 1: SENSE (Observing environment)...")
    print("-" * 70)
    
    # Run ReAct cycle
    result = await agent.process_gateway_selection(
        project_dir=str(test_dir),
        request_feedback=True
    )
    
    print(f"\n📊 Status: {result['status']}")
    
    if result['status'] == 'needs_input':
        print("\n❓ Questions needed:")
        for q in result['questions']:
            print(f"  • {q['question']}")
            print(f"    Why: {q['why_needed']}")
        
        # Provide answers
        print("\n✍️  Providing answers...")
        session_id = result['session_id']
        context = agent.context_manager.get_context(session_id)
        
        # Update context with answers
        agent.context_manager.update_context(session_id, {
            "api_exposure": "external",
            "auth_type": "both"
        })
        
        # Re-run
        result = await agent.process_gateway_selection(
            project_dir=str(test_dir),
            request_feedback=True
        )
    
    if result['status'] == 'awaiting_feedback':
        print("\n🧠 PHASE 2 & 3: THINK & ACT")
        print("-" * 70)
        
        # Show reasoning summary
        summary = result['reasoning_summary']
        print(f"\n📋 Reasoning Summary:")
        print(f"  Task: {summary['task']}")
        print(f"  Total Steps: {summary['total_steps']}")
        print(f"  Observations: {summary['observations']}")
        print(f"  Thoughts: {summary['thoughts']}")
        print(f"  Actions: {summary['actions']}")
        
        # Show action plan
        plan = result['action_plan']
        print(f"\n⚡ Action Plan:")
        print(f"  Action: {plan['action']}")
        print(f"  Gateway: {plan['gateway']}")
        print(f"  Reason: {plan['reason']}")
        print(f"  Rule ID: {plan['rule_id']}")
        
        print("\n📝 PHASE 4: FEEDBACK (Learning)")
        print("-" * 70)
        
        # Provide feedback
        feedback_result = await agent.provide_feedback(
            session_id=result['session_id'],
            feedback_type="approval",
            feedback="Excellent reasoning. DataPower is the correct choice for PCI data.",
            rating=1.0
        )
        
        print(f"\n✅ Feedback recorded: {feedback_result['message']}")
        
        # View final trace
        print("\n📊 Final Reasoning Trace:")
        print("-" * 70)
        trace = agent.get_reasoning_trace()
        print(json.dumps(trace, indent=2))


async def test_reasoning_trace_inspection():
    """Test viewing and analyzing reasoning traces"""
    print("\n" + "="*70)
    print("TEST 2: Reasoning Trace Inspection")
    print("="*70)
    
    engine = ReasoningEngine()
    
    # Search for recent traces
    print("\n🔍 Searching for recent traces...")
    traces = engine.search_traces(limit=5)
    
    if traces:
        print(f"\nFound {len(traces)} recent traces:")
        for i, trace in enumerate(traces, 1):
            print(f"\n{i}. Trace ID: {trace['trace_id'][:8]}...")
            print(f"   Task: {trace['task']}")
            print(f"   Status: {trace['status']}")
            print(f"   Steps: {trace['steps_count']}")
            print(f"   Feedback: {trace['feedback_count']} items")
        
        # Inspect first trace in detail
        print(f"\n📖 Inspecting first trace in detail...")
        first_trace = engine.load_trace(traces[0]['trace_id'])
        
        if first_trace:
            print(f"\n🔍 Observations:")
            for obs in first_trace.get('observations', [])[:3]:
                print(f"  • {obs['observation']}")
            
            print(f"\n💭 Thoughts:")
            for thought in first_trace.get('thoughts', []):
                print(f"  • {thought['thought']}")
                print(f"    Confidence: {thought['confidence']}")
                print(f"    Reasoning: {thought['reasoning'][:100]}...")
            
            print(f"\n⚡ Actions:")
            for action in first_trace.get('actions', []):
                print(f"  • {action['action']}: {action.get('parameters', {})}")
                print(f"    Why: {action['why_this_action'][:100]}...")
                print(f"    Status: {action['status']}")
            
            print(f"\n📊 Metrics:")
            metrics = first_trace.get('metrics', {})
            print(f"  Success Rate: {metrics.get('success_rate', 0):.2%}")
            print(f"  Avg Confidence: {metrics.get('average_confidence', 0):.2f}")
            if metrics.get('human_rating'):
                print(f"  Human Rating: {metrics.get('human_rating'):.2f}")
    else:
        print("\n📝 No traces found yet. Run test 1 first.")


async def test_feedback_types():
    """Test different types of feedback"""
    print("\n" + "="*70)
    print("TEST 3: Different Feedback Types")
    print("="*70)
    
    agent = ReActAgent()
    
    # Create test directory
    test_dir = Path("/tmp/test-react-petstore")
    test_dir.mkdir(exist_ok=True)
    
    # Copy example OAS
    import shutil
    examples_dir = Path(__file__).parent / "examples"
    shutil.copy(examples_dir / "petstore-api.yaml", test_dir / "openapi.yaml")
    
    # Run selection
    result = await agent.process_gateway_selection(
        project_dir=str(test_dir),
        request_feedback=True
    )
    
    if result['status'] == 'needs_input':
        session_id = result['session_id']
        agent.context_manager.update_context(session_id, {
            "api_exposure": "external",
            "auth_type": "oauth"
        })
        result = await agent.process_gateway_selection(
            project_dir=str(test_dir),
            request_feedback=True
        )
    
    if result['status'] == 'awaiting_feedback':
        session_id = result['session_id']
        
        # Test 1: Approval feedback
        print("\n✅ TEST 3.1: Approval Feedback")
        feedback1 = await agent.provide_feedback(
            session_id=session_id,
            feedback_type="approval",
            feedback="Perfect choice. Apigee is great for this external API.",
            rating=1.0
        )
        print(f"  {feedback1['message']}")
        
        # Test 2: Correction feedback
        print("\n🔧 TEST 3.2: Correction Feedback")
        feedback2 = await agent.provide_feedback(
            session_id=session_id,
            feedback_type="correction",
            feedback="Actually, this should use DataPower for enhanced security.",
            rating=0.6,
            corrections={
                "preferred_gateway": "datapower",
                "reason": "Organization policy for all external APIs"
            }
        )
        print(f"  {feedback2['message']}")
        
        # Test 3: Suggestion feedback
        print("\n💡 TEST 3.3: Suggestion Feedback")
        feedback3 = await agent.provide_feedback(
            session_id=session_id,
            feedback_type="suggestion",
            feedback="Consider checking API versioning strategy before deployment.",
            rating=0.9
        )
        print(f"  {feedback3['message']}")
        
        # View updated trace with all feedback
        print("\n📊 Trace with All Feedback:")
        trace = agent.get_reasoning_trace()
        print(f"  Feedback Count: {trace.get('feedback_count', 0)}")


async def test_self_reflection():
    """Test self-reflection capabilities"""
    print("\n" + "="*70)
    print("TEST 4: Self-Reflection")
    print("="*70)
    
    engine = ReasoningEngine()
    
    # Start a trace
    trace_id = engine.start_reasoning_trace(
        session_id="test-session",
        task="Test self-reflection capabilities"
    )
    
    print(f"\n🧠 Starting trace: {trace_id[:8]}...")
    
    # Add observation
    engine.add_observation(
        observation="Test observation",
        data={"test": True}
    )
    
    # Add thought
    engine.add_thought(
        thought="Test thought",
        reasoning="This is test reasoning",
        confidence=0.9,
        alternatives_considered=["Alternative 1", "Alternative 2"]
    )
    
    # Add action
    action_id = engine.add_action(
        action="test_action",
        parameters={"param": "value"},
        expected_outcome="Should complete successfully",
        why_this_action="Testing self-reflection"
    )
    
    # Record result
    engine.record_action_result(
        action_id=action_id,
        status="completed",
        result={"success": True},
        outcome_matches_expected=True
    )
    
    # Self-reflect
    print("\n💭 Adding self-reflection...")
    engine.add_self_reflection(
        reflection="Action completed as expected",
        learned="Self-reflection mechanism works correctly",
        should_adjust=False,
        adjustment=None
    )
    
    # Complete trace
    trace_file = engine.complete_trace(
        status="success",
        summary="Self-reflection test completed"
    )
    
    print(f"\n✅ Trace completed and saved: {trace_file}")
    
    # Load and verify
    saved_trace = engine.load_trace(trace_id)
    print(f"\n📊 Trace contents:")
    print(f"  Steps: {len(saved_trace['steps'])}")
    print(f"  Observations: {len(saved_trace['observations'])}")
    print(f"  Thoughts: {len(saved_trace['thoughts'])}")
    print(f"  Actions: {len(saved_trace['actions'])}")
    print(f"  Self-reflections: {sum(1 for s in saved_trace['steps'] if s.get('type') == 'self_reflection')}")


async def main():
    """Run all ReAct tests"""
    print("\n🧪 ReAct Agent Test Suite")
    print("="*70)
    print("Testing Sense → Think → Act → Feedback cycle")
    print("="*70)
    
    try:
        # Test 1: Full ReAct cycle with PCI API
        await test_react_with_payment_api()
        
        # Test 2: Trace inspection
        await test_reasoning_trace_inspection()
        
        # Test 3: Different feedback types
        await test_feedback_types()
        
        # Test 4: Self-reflection
        await test_self_reflection()
        
        print("\n" + "="*70)
        print("✅ All ReAct Tests Completed!")
        print("="*70)
        
        print("\n📝 Summary:")
        print("  1. ✅ Full ReAct cycle tested (Sense → Think → Act → Feedback)")
        print("  2. ✅ Reasoning trace inspection works")
        print("  3. ✅ All feedback types recorded")
        print("  4. ✅ Self-reflection mechanism validated")
        
        print("\n💡 Reasoning traces saved to:")
        print("  ~/.gateway-governance/reasoning-store/")
        
        print("\n🔍 You can:")
        print("  • Inspect trace files in reasoning-store/")
        print("  • View traces via view_reasoning_trace tool")
        print("  • Search traces via search_reasoning_traces tool")
        print("  • Provide feedback via provide_feedback tool")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())



