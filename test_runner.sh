#!/bin/bash

echo "Starting test run at $(date)" > test_run.log

# Check if servers are running
echo "Checking server status..." >> test_run.log

curl -s http://localhost:8007/api/v1/system/info > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API server is responding" >> test_run.log
else
    echo "❌ API server is not responding" >> test_run.log
fi

curl -s http://localhost:8006 > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Frontend server is responding" >> test_run.log
else
    echo "❌ Frontend server is not responding" >> test_run.log
fi

# Run the tests
echo "Running E2E tests..." >> test_run.log
cd frontend
npx playwright test multi-user.spec.js --project=chromium --reporter=line --timeout=30000 >> ../test_run.log 2>&1

echo "Test run completed at $(date)" >> ../test_run.log
