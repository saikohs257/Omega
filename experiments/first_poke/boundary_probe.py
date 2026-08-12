from tiamat.engine import TiamatEngine

VALUES = [0.0, 1e-15, 1e-12, 1e-9, 1e-6, 1e-3]

def run(v):
    e = TiamatEngine()
    return e.diagnose(B=0.0, V=v, D=0.0)

for v in VALUES:
    d = run(v)
    print({"V": v, "mode": d.get("mode"), "pressure": d.get("pressure"), "momentum": d.get("momentum"), "hazard_raw": d.get("hazard_raw"), "guards": d.get("guards_triggered", [])})
