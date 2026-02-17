import logging
import os
import sys
import subprocess

logger = logging.getLogger(__name__)

def main():
    blender_exe = os.environ.get("BLENDER_EXE")
    if not blender_exe:
        logger.error(
            "Environment variable BLENDER_EXE not set. "
            "Please set it to the path of your Blender executable."
        )
        return False

    logger.info(f"Using Blender executable: {blender_exe}")
    result = subprocess.run(
        [
            os.environ['BLENDER_EXE'],
            '--background',
            '--factory-startup',
            '--python',
            'tests/__init__.py'
        ],
        check=True
    )
    return result.returncode == 0
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = main()
    sys.exit(0 if result else 1)