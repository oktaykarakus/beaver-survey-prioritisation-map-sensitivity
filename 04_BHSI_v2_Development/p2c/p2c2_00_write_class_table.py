"""P2-C2: write the frozen class-treatment table from the frozen P2-B crosswalk (p2c_lc.class_table). The table used by the
8 Nov 2026 overlay was written by an inline call to this same function before the overlay; this script makes that step
reproducible. Usage: python -I p2c2_00_write_class_table.py <out_csv>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2c_lc as L
R = Path(__file__).resolve().parents[2]
L.class_table(R / '06_Results_Figures/BHSI_v2_P2B/P2B_ECOLOGICAL_CROSSWALK.csv').to_csv(sys.argv[1], index=False)
