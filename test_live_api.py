#!/usr/bin/env python3
"""
Test the live API to see exactly what the full-pipeline returns
"""
import requests
import json

API_URL = "http://localhost:8000"

# Minimal solicitation data
solicitation_data = {
    "raw_text": """
    MAGNITO CP NOFO
    
    The Department of Defense seeks cybersecurity solutions for data protection 
    and threat detection. We need companies with expertise in security technologies,
    threat monitoring, and incident response capabilities.
    
    Key requirements:
    - Cybersecurity expertise
    - Data protection solutions
    - Threat detection systems
    - Incident response capabilities
    
    NAICS: 541512
    Set-Aside: Small Business
    """,
    "title": "MAGNITO CP NOFO Test"
}

print("\n" + "="*80)
print("TESTING LIVE API: /api/full-pipeline")
print("="*80)

try:
    print("\n📤 Sending request to full-pipeline...")
    response = requests.post(
        f"{API_URL}/api/full-pipeline",
        json=solicitation_data,
        params={"top_k": 2}  # Just get 2 companies
    )
    
    print(f"✅ Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Got {len(data.get('results', []))} results")
        
        # Check first result
        if data.get('results'):
            result = data['results'][0]
            company_name = result.get('company_name', 'Unknown')
            
            print(f"\n{'='*80}")
            print(f"FIRST RESULT: {company_name}")
            print(f"{'='*80}")
            
            # Check confirmation_result
            conf = result.get('confirmation_result', {})
            if conf:
                alignment_summary = conf.get('alignment_summary', '')
                
                print(f"\n✓ Has confirmation_result: Yes")
                print(f"✓ Has alignment_summary: {bool(alignment_summary)}")
                print(f"✓ alignment_summary length: {len(alignment_summary)} chars")
                
                if alignment_summary:
                    paragraphs = [p.strip() for p in alignment_summary.split('\n\n') if p.strip()]
                    print(f"✓ Paragraph count: {len(paragraphs)}")
                    print(f"✓ Word count: {len(alignment_summary.split())}")
                    
                    print(f"\n--- ALIGNMENT SUMMARY (first 300 chars) ---")
                    print(alignment_summary[:300])
                    print("...")
                    print(f"--- END ---\n")
                    
                    if len(paragraphs) >= 2:
                        print("🎉 SUCCESS: 2-paragraph format detected!")
                    else:
                        print("❌ FAILED: Only 1 paragraph")
                else:
                    print("\n❌ CRITICAL: alignment_summary is EMPTY!")
                    print(f"decision_rationale: {result.get('decision_rationale', 'N/A')[:200]}")
            else:
                print("\n❌ No confirmation_result in response")
        else:
            print("\n⚠️  No results returned")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80 + "\n")

