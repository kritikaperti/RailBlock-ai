"""
RailBlock AI - Launcher & Server Runner
AI-Powered Automatic Block Planning to Maximize Asset Availability for Indian Railways
"""

import sys
import os
import webbrowser
import socket
import uvicorn

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def find_free_port(start_port=8000, max_tries=20):
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


def main():
    port = find_free_port(8000)
    url = f"http://127.0.0.1:{port}"
    
    banner = f"""
========================================================================================
   [IR]  RAILBLOCK AI - INDIAN RAILWAYS AUTOMATIC BLOCK PLANNING SYSTEM (IR-ABPS)  [IR]
========================================================================================
  Multi-Department Maintenance & Corridor Optimization for Fixed Infrastructure
  - Engineering (TMS) * Signalling (SMMS) * Traction (TDMS) * Control Office (COA)
----------------------------------------------------------------------------------------
  * Control Room Dashboard : {url}
  * Interactive API Docs   : {url}/docs
  * Corridor               : Ghaziabad (GZB) - Kanpur Central (CNB) - DDU (781 KM)
========================================================================================
    """
    print(banner)
    
    # Run uvicorn server
    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=False, log_level="info")


if __name__ == "__main__":
    main()
