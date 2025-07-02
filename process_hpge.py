import zipfile
import re
import os
import pandas as pd
from typing import List, Tuple, Optional
from scipy.stats import norm
import math

def parse_identified(text: str) -> List[Tuple[float, str, float, float]]:
    """
    Parse the 'Identified Nuclides' table from a Genie‑2000 RPT file.

    Args:
        text: Content of an RPT file.

    Returns:
        List of tuples: (energy_keV, nuclide, activity_Bq, uncertainty_Bq).
    """
    records: List[Tuple[float, str, float, float]] = []
    current_nuc: Optional[str] = None
    sci_num = re.compile(r"^[+-]?\d+\.\d+E[+-]\d+$")
    num_re = re.compile(r"^[+-]?\d+\.\d+(?:[Ee][+-]?\d+)?\*?$")
    for line in text.splitlines():
        cols = line.strip().split()
        if not cols:
            continue
        if re.match(r"^[A-Za-z]", cols[0]):
            current_nuc = cols[0].upper()
            energy: Optional[float] = None
            for token in cols[1:]:
                if num_re.match(token):
                    try:
                        val = float(token.rstrip('*'))
                    except ValueError:
                        continue
                    energy = val
                    break
            if energy is not None and len(cols) >= 3 and sci_num.match(cols[-2]):
                records.append((energy, current_nuc, float(cols[-2]), float(cols[-1])))
        else:
            if current_nuc is None:
                continue
            if num_re.match(cols[0]):
                try:
                    energy = float(cols[0].rstrip('*'))
                except ValueError:
                    continue
                if len(cols) >= 3 and sci_num.match(cols[-2]):
                    records.append((energy, current_nuc, float(cols[-2]), float(cols[-1])))
    return records

def classify_chain(nuclide: str) -> Optional[str]:
    if nuclide in {"RA-226", "PB-214", "BI-214"}:
        return "U-238"
    if nuclide in {"AC-228", "PB-212", "TL-208", "BI-212"}:
        return "Th-232"
    if nuclide == "K-40":
        return "K-40"
    return None

def select_one_line(
    records: List[Tuple[float, str, float, float]],
    parent: str
) -> Tuple[Optional[float], Optional[str], float, float]:
    targets = {"U-238": (186.2, "RA-226"), "Th-232": (911.2, "AC-228")}  
    if parent == "K-40":
        # Override energy to the documented 1460.8 keV
        # pick record with highest activity but set energy_keV to 1460.8
        if not records:
            return None, None, float('nan'), float('nan')
        best = max(records, key=lambda x: x[2])
        return 1460.8, best[1], best[2], best[3]
    targ_e, targ_nuc = targets[parent]
    for e, nuc, act, unc in records:
        if nuc == targ_nuc and abs(e - targ_e) <= 2:
            return e, nuc, act, unc
    fallback = [(e, nuc, act, unc) for e, nuc, act, unc in records if e > 100.0]
    if fallback:
        best = max(fallback, key=lambda x: x[2])
        return best[0], best[1], best[2], best[3]
    return None, None, float('nan'), float('nan')

def process_samples(zip_path: str) -> pd.DataFrame:
    rows = []
    with zipfile.ZipFile(zip_path) as zf:
        for fname in sorted(zf.namelist()):
            if not fname.lower().endswith('.rpt'):
                continue
            text = zf.read(fname).decode('utf-8', 'ignore')
            recs = parse_identified(text)
            by_chain = {}
            for e, nuc, act, unc in recs:
                parent = classify_chain(nuc)
                if parent:
                    by_chain.setdefault(parent, []).append((e, nuc, act, unc))
            for parent in ['Th-232', 'U-238', 'K-40']:
                rec_list = by_chain.get(parent, [])
                e, nuc, act, unc = select_one_line(rec_list, parent)
                rows.append({
                    'sample': os.path.basename(fname),
                    'chain': parent,
                    'energy_keV': e,
                    'nuclide': nuc,
                    'activity_Bq': act,
                    'uncertainty_Bq': unc
                })
    return pd.DataFrame(rows)

def compute_significance(df: pd.DataFrame) -> pd.DataFrame:
    import re
    pairs = {}
    for _, row in df.iterrows():
        m = re.match(r"(.+?)([abAB])_NID\.RPT$", row['sample'])
        if not m:
            continue
        pref, suf = m.group(1), m.group(2).lower()
        pairs.setdefault(pref, {}).setdefault(suf, {})[row['chain']] = {
            'activity': row['activity_Bq'],
            'se': row['uncertainty_Bq']
        }
    records = []
    for pref, recs in pairs.items():
        if 'a' in recs and 'b' in recs:
            for chain in ['Th-232', 'U-238', 'K-40']:
                a = recs['a'].get(chain)
                b = recs['b'].get(chain)
                if a and b:
                    se_comb = math.hypot(a['se'], b['se'])
                    z = (a['activity'] - b['activity']) / se_comb if se_comb > 0 else float('nan')
                    p = 2 * (1 - norm.cdf(abs(z))) if se_comb > 0 else float('nan')
                    records.append({
                        'sample_pair': pref,
                        'chain': chain,
                        'activity_a': a['activity'],
                        'uncertainty_a': a['se'],
                        'activity_b': b['activity'],
                        'uncertainty_b': b['se'],
                        'z_stat': z,
                        'p_value': p
                    })
    return pd.DataFrame(records)

def main():
    df = process_samples('nids.zip')
    df.to_csv('sample_activities_one_line_updated.csv', index=False)
    sig = compute_significance(df)
    sig.to_csv('sample_ab_significance_one_line.csv', index=False)

if __name__ == '__main__':
    main()
