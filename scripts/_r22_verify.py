import re
import zipfile
from pathlib import Path

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
for name in ("Paper_EN_IEEE_v76.docx", "supplementary/supp_en.docx"):
    z = zipfile.ZipFile(D / name)
    xml = z.read("word/document.xml").decode("utf-8")
    text = re.sub(r"<[^>]+>", "", xml)
    print("==", name, "chars", len(text))
    for pat in ("text[[", "prove invites", "τ_*", "+3,2", "VI.CONCLUSION", "±d ", "|λ| ≤ 70°",
                "0/+2/+3/", "P_D(T_z ≤ τ)", "Table II."):
        n = text.count(pat)
        if n:
            print(f"   found {n:2d}x  {pat!r}")
    print("   eq3 present:", "P_D( late under" in text)
    for pat in ("A0", "A6 carries no measurements", "0.00", "κ"):
        print(f"   {pat!r}: {text.count(pat)}")
