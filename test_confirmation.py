#!/usr/bin/env python3
"""
Test script to verify the alignment_summary format fix
Tests the confirmation engine with a sample company and solicitation
"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app import (
    analyze_solicitation_themes,
    confirm_single_company,
    data_source_manager,
    logger
)


async def test_confirmation():
    """Test the confirmation engine with sample data"""
    
    print("\n" + "="*80)
    print("Testing Alignment Summary Format Fix")
    print("="*80 + "\n")
    
    # Check if ChatGPT is available
    if "chatgpt" not in data_source_manager.sources:
        print("❌ ERROR: ChatGPT not configured. Please add API key to config.json")
        return False
    
    print("✅ ChatGPT source available\n")
    
    # Load sample solicitation
    solicitation_file = Path(__file__).parent / "test_poultry.txt"
    if not solicitation_file.exists():
        print(f"❌ ERROR: Sample solicitation not found: {solicitation_file}")
        return False
    
    solicitation_text = solicitation_file.read_text()
    print(f"✅ Loaded solicitation: {len(solicitation_text)} characters\n")
    
    # Extract themes
    print("Extracting themes from solicitation...")
    themes = analyze_solicitation_themes(solicitation_text)
    print(f"✅ Themes extracted:")
    print(f"   - Problem areas: {len(themes.get('problem_areas', []))}")
    print(f"   - Key priorities: {len(themes.get('key_priorities', []))}")
    print(f"   - Technical capabilities: {len(themes.get('technical_capabilities', []))}")
    print()
    
    # Test companies
    test_companies = [
        {
            "name": "Cytiva",
            "description": "Global provider of bioprocessing technologies and services for biopharmaceutical manufacturing, with expertise in biosensors and diagnostic systems"
        },
        {
            "name": "Thermo Fisher Scientific",
            "description": "Leading biotechnology company providing analytical instruments, reagents, and services for life sciences research and diagnostics"
        },
        {
            "name": "Zoetis",
            "description": "Animal health company focused on veterinary medicines, vaccines, and diagnostic products for livestock and companion animals"
        }
    ]
    
    chatgpt_source = data_source_manager.sources["chatgpt"]
    solicitation_title = "HPAI Poultry Innovation Grand Challenge"
    
    results = []
    
    for i, company in enumerate(test_companies, 1):
        print(f"\n{'-'*80}")
        print(f"Test {i}/{len(test_companies)}: {company['name']}")
        print(f"{'-'*80}\n")
        
        try:
            # Run confirmation
            result = await confirm_single_company(
                company_name=company['name'],
                solicitation_title=solicitation_title,
                themes=themes,
                chatgpt_source=chatgpt_source,
                company_description=company['description']
            )
            
            # Extract alignment_summary
            alignment_summary = result.get('alignment_summary', '')
            
            # Analyze the result
            print(f"Company: {result.get('company_name', 'Unknown')}")
            print(f"Confirmed: {result.get('is_confirmed', False)}")
            print(f"Confidence: {result.get('confidence_score', 0):.2%}")
            print(f"Recommendation: {result.get('recommendation', 'N/A')}")
            print()
            
            # Validate format
            print("ALIGNMENT SUMMARY VALIDATION:")
            print("-" * 40)
            
            # Count paragraphs
            paragraphs = [p.strip() for p in alignment_summary.split('\n\n') if p.strip()]
            if len(paragraphs) < 2:
                paragraphs = [p.strip() for p in alignment_summary.split('\n') if p.strip() and len(p.strip()) > 50]
            
            word_count = len(alignment_summary.split())
            paragraph_count = len(paragraphs)
            
            print(f"Paragraph count: {paragraph_count}")
            print(f"Word count: {word_count}")
            print(f"Expected: 2 paragraphs, 160-240 words")
            print()
            
            # Check structure
            checks = {
                "Has 2 paragraphs": paragraph_count >= 2,
                "Word count in range (160-240)": 160 <= word_count <= 240,
                "Starts with 'Our research indicates'": alignment_summary.startswith("Our research indicates"),
                "Contains 'Our analysts show'": "Our analysts show" in alignment_summary,
                "Not too short (>100 words)": word_count > 100
            }
            
            all_passed = True
            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"{status} {check}")
                if not passed:
                    all_passed = False
            
            print()
            
            if all_passed:
                print("🎉 VALIDATION PASSED - Format is correct!")
            else:
                print("⚠️  VALIDATION ISSUES DETECTED")
            
            print()
            print("ALIGNMENT SUMMARY CONTENT:")
            print("-" * 40)
            print(alignment_summary)
            print()
            
            results.append({
                "company": company['name'],
                "validation_passed": all_passed,
                "paragraph_count": paragraph_count,
                "word_count": word_count,
                "alignment_summary": alignment_summary
            })
            
        except Exception as e:
            print(f"❌ ERROR testing {company['name']}: {e}")
            results.append({
                "company": company['name'],
                "error": str(e)
            })
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")
    
    passed_count = sum(1 for r in results if r.get('validation_passed', False))
    total_count = len([r for r in results if 'error' not in r])
    
    print(f"Tests passed: {passed_count}/{total_count}")
    print()
    
    if passed_count == total_count:
        print("✅ ALL TESTS PASSED - Alignment summary format is working correctly!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - Review the output above")
        return False


if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(test_confirmation())
    sys.exit(0 if success else 1)

