# Smart-Map – one-shot dependency installer  (run in QGIS Python console)
import sys, subprocess, textwrap

def run_pip(*args):
    """
    Helper that calls pip using the very interpreter QGIS is running.
    Prints the exact command so you know what is happening.
    """
    cmd = [sys.executable, "-m", "pip", *args]
    print("\n>>>", " ".join(cmd), "\n")
    subprocess.check_call(cmd)

# 0.  Make sure pip itself is current (optional but avoids wheel issues)
run_pip("install", "--upgrade", "pip")

# 1.  Core scientific stack and Smart-Map extras
packages = [
    "numpy",          # base array library
    "pandas",         # DataFrame handling                       (Smart-Map docs)
    "scipy",          # stats / linear algebra                   (Smart-Map docs)
    "scikit-learn",   # SVM + utilities                          (Smart-Map docs)
    "scikit-fuzzy",   # clustering – bundled, but install anyway for updates
    "pykrige",        # ordinary kriging implementation
    "pysal"           # spatial analysis helpers
]

run_pip("install", *packages)

print(textwrap.dedent("""
    ------------------------------------------------------------
    All requested packages installed (assuming no red errors).
    Please restart QGIS so the new modules are visible to plugins.
    ------------------------------------------------------------
"""))
