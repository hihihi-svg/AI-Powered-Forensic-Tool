
import uvicorn
import os
import sys

# Ensure backend dir is in path
sys.path.append(os.getcwd())

if __name__ == "__main__":
    print("Starting backend via run_backend.py...")
    try:
        # Removed pre-init to avoid storage lock conflict
        print("Starting uvicorn...")
        uvicorn.run("app.main:app", host="0.0.0.0", port=8086, reload=False, log_level="debug")
    except Exception as e:
        print(f"CRITICAL STARTUP ERROR: {e}")
        import traceback
        traceback.print_exc()
