#!/bin/bash

echo "=========================================="
echo "🧪 Queue System Test"
echo "=========================================="
echo ""

# Activate conda
source ~/miniconda3/etc/profile.d/conda.sh
conda activate mc

API_URL="http://localhost:8080"

echo "1️⃣ Checking server health..."
curl -s $API_URL/health | jq
echo ""

echo "2️⃣ Adding test request 1 to queue..."
curl -s -X POST $API_URL/predict \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://huggingface.co/blog/vlms-2025",
    "platforms": {"telegram": true, "twitter": false, "linkedin": false}
  }' | jq
echo ""

echo "3️⃣ Adding test request 2 to queue..."
curl -s -X POST $API_URL/predict \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/test-article",
    "platforms": {"telegram": false, "twitter": true, "linkedin": false}
  }' | jq
echo ""

echo "4️⃣ Adding test request 3 to queue..."
curl -s -X POST $API_URL/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Just testing the queue system!",
    "platforms": {"telegram": false, "twitter": false, "linkedin": true}
  }' | jq
echo ""

echo "5️⃣ Checking queue status..."
curl -s $API_URL/queue/status | jq
echo ""

echo "6️⃣ Viewing full queue..."
curl -s $API_URL/queue | jq
echo ""

echo "=========================================="
echo "✅ Test complete!"
echo ""
echo "To process queue NOW (don't wait for 23:00):"
echo "  python3 scripts/src/scheduler/processor.py --now"
echo ""
echo "To view queue:"
echo "  curl http://localhost:8080/queue"
echo "=========================================="