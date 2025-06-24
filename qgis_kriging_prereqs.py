# smartmap_installer_qgis340.py
# ------------------------------------------------------------
# Run from the QGIS script editor (not the >>> prompt).

import os, sys, subprocess, site, glob, shutil, textwrap, importlib.metadata

# ------------------------------------------------------------------
# 1. Locate the *real* Python that lives inside the QGIS bundle
# ------------------------------------------------------------------
CANDIDATES = [
    os.path.join(os.path.dirname(sys.executable), "bin", "python3"),
    os.path.join(os.path.dirname(sys.executable),
                 "../Frameworks/Python.framework/Versions/Current/bin/python3")
]
python_bin = next((p for p in CANDIDATES if os.path.exists(p)), None)
if not python_bin:
    raise RuntimeError("Cannot find the embedded python3 – adjust CANDIDATES.")

def run_pip(*args):
    cmd = [python_bin, "-m", "pip", *args]
    print("\n>>>", " ".join(cmd), "\n")
    subprocess.check_call(cmd)

# ------------------------------------------------------------------
# 2. Remove the distutils copy of scikit-learn 0.23.x (if present)
# ------------------------------------------------------------------
for root in site.getsitepackages():
    for pat in ("sklearn", "scikit_learn*"):
        for p in glob.glob(os.path.join(root, pat)):
            shutil.rmtree(p, ignore_errors=True)

# ------------------------------------------------------------------
# 3. Upgrade pip itself (avoids metadata quirks)
# ------------------------------------------------------------------
run_pip("install", "--upgrade", "pip")

# ------------------------------------------------------------------
# 4. Install wheels that *match* NumPy-2 ABI
#    (all are binary wheels for macOS x86_64 / Python 3.9)
# ------------------------------------------------------------------
run_pip(
    "install", "--only-binary", ":all:", "--upgrade",
    "numpy==2.0.2",
    "scipy==1.13.1",
    "pandas==2.2.2",
    "scikit-learn==1.5.0",
    "joblib==1.5.1",
    "threadpoolctl==3.6.0",
)

# optional pure-Python extras Smart-Map can use
run_pip("install", "--upgrade", "scikit-fuzzy", "pykrige")

# ------------------------------------------------------------------
# 5. Report final versions so the user can confirm
# ------------------------------------------------------------------
def v(pkg):
    try:
        return importlib.metadata.version(pkg)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"

print(textwrap.dedent(f"""
------------------------------------------------------------
Installer finished.

Detected library versions now visible to QGIS:
    NumPy         : {v('numpy')}
    pandas        : {v('pandas')}
    SciPy         : {v('scipy')}
    scikit-learn  : {v('scikit-learn')}
    scikit-fuzzy  : {v('scikit-fuzzy')}
    pykrige       : {v('pykrige')}

If NumPy shows 2.0.2 and the others match the list above,
restart QGIS and enable the Smart-Map plugin.
------------------------------------------------------------
"""))
