#!/bin/bash
# Start Django development server on port 6000 (avoiding port 8000 conflict)

echo ""
echo "============================================================"
echo "      Starting A92.2 Inspection App on port 6000"
echo "============================================================"
echo ""
echo "Server will be available at:"
echo "  http://localhost:6000"
echo "  http://127.0.0.1:6000"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

python3 manage.py runserver 6000
