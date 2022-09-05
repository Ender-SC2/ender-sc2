def family(mapname: str):
    mapfamily = ""
    for ch in mapname.replace("LE", "").replace("AIE", ""):
        if ("a" <= ch <= "z") or ("A" <= ch <= "Z"):
            mapfamily += ch.lower()
    return mapfamily
