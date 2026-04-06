"""Entry point for: python -m marketbrief.mcp_server"""

import sys
import os

# Add project root to path so mcp_server package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp_server.server import main

if __name__ == "__main__":
    main()
