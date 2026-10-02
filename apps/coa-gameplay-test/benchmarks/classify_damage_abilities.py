import json,glob,collections,subprocess,os,sys
DBC=os.environ.get("DBC","env/dist/data/dbc")
SCEN=os.environ.get("SCENARIOS","apps/coa-gameplay-test/scenarios")
VIEWER=os.environ.get("VIEWER","apps/coa-dbc/coa-dbc-viewer")
DMG={2,30,31,121,122,123}
AOE_TARGETS={15,16,22,24,28,30,53,54}
SINGLE_ENEMY=6
cast=collections.defaultdict(collections.Counter)
for f in glob.glob(os.path.join(SCEN,"*.json")):
    try: d=json.load(open(f,encoding="utf-8"))
    except Exception: continue
    cls={p.get("class") for p in d.get("players",[]) if p.get("class")}
    if len(cls)!=1: continue
    c=cls.pop()
    if c<12: continue
    for s in d.get("steps",[]):
        if s.get("action")=="cast" and isinstance(s.get("spell"),int) and s.get("spell")>100000:
            cast[c][s["spell"]]+=1
def field(fields,name):
    for f in fields:
        if f.get("name")==name: return f.get("value")
    return None
cache={}
def classify(spell):
    if spell in cache: return cache[spell]
    try:
        out=subprocess.run([sys.executable,VIEWER,"record","--data",DBC,"--id",str(spell)],capture_output=True,text=True,timeout=30)
        d=json.loads(out.stdout); fl=d.get("fields",[]); nm=d.get("name","?")
    except Exception:
        cache[spell]=(None,"?","lookup-failed"); return cache[spell]
    effs=[field(fl,"Effect[%d]"%i) for i in range(3)]
    targets=[field(fl,"EffectImplicitTargetA[%d]"%i) for i in range(3)]
    recovery=field(fl,"RecoveryTime"); category=field(fl,"CategoryRecoveryTime")
    power=field(fl,"PowerType"); casting=field(fl,"CastingTimeIndex")
    damage_effects=[i for i,e in enumerate(effs) if e in DMG]
    single=any(targets[i]==SINGLE_ENEMY for i in damage_effects)
    aoe=any(t in AOE_TARGETS for t in targets)
    ok=bool(damage_effects) and single and not aoe and recovery in (0,None) and category in (0,None)
    detail="eff=%s tgt=%s rec=%s/%s cti=%s pt=%s"%(effs,targets,recovery,category,casting,power)
    cache[spell]=("INCLUDE" if ok else "EXCLUDE",nm,detail)
    return cache[spell]
picks={}
for c in sorted(cast):
    for spell,n in cast[c].most_common(6):
        verdict,nm,detail=classify(spell)
        if verdict=="INCLUDE" and c not in picks:
            picks[c]=(spell,nm,n,detail)
for c,(spell,nm,n,detail) in sorted(picks.items()):
    print("class %2d: %s %-24.24s (cast x%d) %s"%(c,spell,nm,n,detail))
print("COVERAGE: %d classes"%len(picks))
out=os.environ.get("OUT","dps-picks.json")
open(out,"w").write(json.dumps({str(c):{"spell":spell,"name":nm} for c,(spell,nm,n,detail) in picks.items()}))
