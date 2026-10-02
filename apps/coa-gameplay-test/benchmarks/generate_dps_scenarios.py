import json,sys,os
SPECS=[
 (12,"Barbarian","Ancestral Strike",801576,3,1,False),
 (13,"Witch Doctor","Hex of Malice",501158,0,1,True),
 (14,"Felsworn","Ruin",801895,3,1,False),
 (15,"Witch Hunter","Shadowblast",680264,1,1,False),
 (17,"Knight of Xoroth","Hellmaw",806965,1,1,True),
 (20,"Bloodmage","Bloodfang Bite",572551,1,1,False),
 (21,"Ranger","Skullpiercer",802036,2,1,False),
 (23,"Necromancer","Lichfrost",801722,0,5,True),
 (26,"Starcaller","Celestial Strike",800496,3,1,False),
 (27,"Sun Cleric","Sunflare",800231,0,1,False),
 (29,"Venomancer","Venom Bolt",800869,0,1,False),
 (30,"Reaper","Soulrend",572342,0,10,True),
]
SAFE_POWER={1:500,2:100,3:100,6:500}
NCAST=8
GCD_MS=2500
MAX_PLAYERS=8
def power_steps(pid,power_type):
    if power_type==0: return []
    return [{"action":"set_power","actor":pid,"power":power_type,"value":SAFE_POWER.get(power_type,100)}]
def build(specs,name):
    players=[];creatures=[];steps=[{"action":"wait","label":"settle spawn and level scaling","ms":6000}]
    for c,title,ability,spell,power_type,race,hybrid in specs:
        pid="p%d"%c;did="d%d"%c
        players.append({"id":pid,"race":race,"class":c,"level":80})
        creatures.append({"id":did,"owner":pid,"entry":36,"health":100000000,"distance":5})
        steps.append({"action":"learn","actor":pid,"spell":spell})
        steps.extend(power_steps(pid,power_type))
        steps.append({"action":"snapshot","actor":pid,"metric":"spell_cast_time_ms","spell":spell,"save_as":"ct_%d"%c})
        steps.append({"action":"snapshot","actor":pid,"metric":"spell_damage_total","spell":spell,"target":did,"save_as":"d0_%d"%c})
        steps.append({"action":"snapshot","actor":pid,"metric":"spell_damage_count","spell":spell,"target":did,"save_as":"n0_%d"%c})
        for _ in range(NCAST):
            steps.extend(power_steps(pid,power_type))
            steps.append({"action":"cast","actor":pid,"spell":spell,"target":did})
            steps.append({"action":"wait","ms":GCD_MS})
        steps.append({"action":"assert","actor":pid,"metric":"spell_damage_total","spell":spell,"target":did,"relative_to":"d0_%d"%c,"min":0,"max":999999999,"label":"measure dmg %s"%title})
        steps.append({"action":"assert","actor":pid,"metric":"spell_damage_count","spell":spell,"target":did,"relative_to":"n0_%d"%c,"min":0,"max":100,"label":"measure cnt %s"%title})
        steps.append({"action":"assert","actor":pid,"metric":"spell_cast_time_ms","spell":spell,"min":0,"max":99999,"label":"measure ct %s"%title})
    return {"schema":1,"name":name,"contract":"Directional signature single-target ability throughput; L80 base stats no gear; NOT sustained-rotation DPS.","timeout_ms":600000,"players":players,"creatures":creatures,"steps":steps}
outdir=os.environ.get("OUT",".")
for i in range(0,len(SPECS),MAX_PLAYERS):
    batch=SPECS[i:i+MAX_PLAYERS]
    tag=chr(ord("a")+i//MAX_PLAYERS)
    path=os.path.join(outdir,"dps-sig-%s.json"%tag)
    open(path,"w",encoding="utf-8",newline="\n").write(json.dumps(build(batch,"DPS directional %s"%tag.upper()),indent=2))
    print("wrote %s (%d specs)"%(path,len(batch)))
