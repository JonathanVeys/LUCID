import json, logging
import country_converter as coco
logging.getLogger('country_converter').setLevel(logging.CRITICAL)

cc = coco.CountryConverter()
df = cc.data[['name_short', 'name_official', 'ISO2', 'ISO3', 'ISOnumeric', 'UNregion', 'continent']]

GEO = {}
skipped = []
for _, r in df.iterrows():
    try:
        iso_id = int(r['ISOnumeric'])
    except (TypeError, ValueError):
        skipped.append(r['name_short']); continue
    entry = {
        "id": iso_id,
        "name": r['name_short'],          # canonical label
        "region": r['UNregion'],          # UN M49 subregion
        "continent": r['continent'],
        "iso3": r['ISO3'],
    }
    # index under several spellings so lookups hit
    for key in {r['name_short'], r['name_official'], r['ISO3'], r['ISO2']}:
        if isinstance(key, str) and key.strip():
            GEO[key] = entry

with open('geo_lookup.json', 'w', encoding='utf-8') as f:
    json.dump(GEO, f, ensure_ascii=False, indent=2, sort_keys=True)



if __name__ == "__main__":
    ids = {e['id'] for e in GEO.values()}
    print(f"keys (incl. aliases): {len(GEO)}")
    print(f"distinct countries  : {len(ids)}")
    print(f"distinct regions    : {len(  {e['region'] for e in GEO.values()} )}")
    print(f"skipped (no numeric): {skipped}")

    print(json.dumps(GEO, indent=2))
