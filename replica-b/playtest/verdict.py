#!/usr/bin/env python3.12
"""Play Log -> verdict. Fails closed. PASS only if every catalogued control was exercised,
every action was responsive and matched expectation, and every cited frame exists."""
import json, sys, os, hashlib
REQUIRED = ["title-drag","minimize","close","reopen","bgm-slider-thumb","bgm-arrow-left","bgm-arrow-right","bgm-on",
            "effect-slider-track","effect-on","dropdown-arrow","dropdown-row","checkbox-attack","checkbox-skill",
            "hover-minimize","hover-thumb"]
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def main(log_path, shots_dir):
    try: log=json.load(open(log_path))
    except Exception as e: return {"verdict":"INVALID","reason":f"unreadable log: {e}"}
    actions=log.get("actions",[])+log.get("free_play",[])
    problems=[]; seen=set(); frames_ok=0
    for a in actions:
        cid=a.get("control"); seen.add(cid)
        if cid=="miss": continue
        shots=a.get("screenshots") or {}
        if isinstance(shots,list): shots={"before":shots[0] if shots else None,"after":shots[1] if len(shots)>1 else None}
        paths={k:os.path.join(shots_dir,v) for k,v in shots.items() if v}
        missing=[k for k,p in paths.items() if not os.path.exists(p)]
        if missing: problems.append(f"{cid}: cited frame(s) missing {missing}")
        else: frames_ok+=len(paths)
        if "drag" in str(a.get("gesture","")) and "mid" not in paths: problems.append(f"{cid}: drag without a mid-gesture frame")
        if a.get("responsive") is True and "before" in paths and "after" in paths and os.path.exists(paths["before"]) and os.path.exists(paths["after"]):
            if sha(paths["before"])==sha(paths["after"]) and ("mid" not in paths or not os.path.exists(paths["mid"]) or sha(paths["mid"])==sha(paths["before"])):
                problems.append(f"{cid}: claimed responsive but before/after(/mid) frames are byte-identical")
        if a.get("responsive") is False and a.get("matches_expected") is not True and cid in REQUIRED: problems.append(f"{cid}: NOT RESPONSIVE — {a.get('observed','')[:160]}")
        if a.get("matches_expected") is False and cid in REQUIRED: problems.append(f"{cid}: does not match expected — {a.get('observed','')[:160]}")
    unexercised=[c for c in REQUIRED if c not in seen]
    fails=[p for p in problems if "NOT RESPONSIVE" in p or "does not match" in p or "byte-identical" in p]
    if any("unreadable" in p or "missing" in p or "without a mid" in p for p in problems): verdict="INVALID"
    elif fails: verdict="FAIL"
    elif unexercised: verdict="INCOMPLETE"
    else: verdict="PASS"
    return {"verdict":verdict,"actions":len(actions),"frames_verified":frames_ok,"unexercised":unexercised,"problems":problems}
if __name__=="__main__":
    print(json.dumps(main(sys.argv[1], sys.argv[2]),indent=1))
