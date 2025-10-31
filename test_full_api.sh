#!/bin/bash
# Test the full API pipeline

echo "Testing /api/full-pipeline endpoint..."
echo ""

response=$(curl -s -X POST http://localhost:8000/api/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "THRIVE ISO - The agency seeks therapeutic development for RNA-based immunotherapies. Requirements include gene editing, CRISPR technology, vaccine development. NAICS: 541711",
    "title": "THRIVE ISO Test"
  }' \
  --max-time 120)

# Save to file for inspection
echo "$response" > /tmp/api_response.json

# Parse key fields
echo "$response" | python3 << 'ENDPYTHON'
import sys, json

try:
    data = json.load(sys.stdin)
    
    print(f"Status: Response received")
    print(f"Results count: {len(data.get('results', []))}")
    
    if data.get('results'):
        for i, result in enumerate(data['results'][:3], 1):
            print(f"\n--- RESULT {i}: {result.get('company_name')} ---")
            
            # Check confirmation_result
            conf = result.get('confirmation_result')
            if conf:
                alignment = conf.get('alignment_summary', '')
                print(f"  Has confirmation_result: Yes")
                print(f"  Has alignment_summary: {bool(alignment)}")
                print(f"  alignment_summary length: {len(alignment)} chars")
                
                if alignment:
                    paras = len([p for p in alignment.split('\n\n') if p.strip()])
                    print(f"  Paragraph count: {paras}")
                    print(f"  First 100 chars: {alignment[:100]}...")
                    
                    if paras >= 2:
                        print(f"  ✅ CORRECT FORMAT!")
                    else:
                        print(f"  ❌ WRONG FORMAT - only {paras} paragraph(s)")
                else:
                    print(f"  ❌ alignment_summary is EMPTY")
                    print(f"  decision_rationale: {result.get('decision_rationale', '')[:80]}...")
            else:
                print(f"  ❌ No confirmation_result")
    else:
        print("No results in response")
        print(f"Error: {data.get('detail', 'Unknown')}")
        
except Exception as e:
    print(f"Error parsing response: {e}")
    print("Raw response saved to /tmp/api_response.json")
ENDPYTHON

echo ""
echo "Full response saved to: /tmp/api_response.json"
echo "To inspect: cat /tmp/api_response.json | python3 -m json.tool"

