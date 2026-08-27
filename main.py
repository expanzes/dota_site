def get_role_data(role_key: str, candidate_stats: dict, heroes_map: dict):
    valid_heroes = ROLES_DB.get(role_key, set())
    role_candidates = []
    all_candidates = []

    for cid, data in candidate_stats.items():
        hero_info = heroes_map.get(cid)
        if not hero_info or data["games"] < 30:
            continue

        wr = (data["wins"] / data["games"]) * 100
        img_url = f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero_info['slug']}.png"
        item = {
            "name": hero_info["name"],
            "winrate": round(wr, 1),
            "games": data["games"],
            "img": img_url,
        }

        all_candidates.append(item)
        if hero_info["name"].lower() in valid_heroes:
            role_candidates.append(item)

    final_list = role_candidates if role_candidates else all_candidates
    if not final_list:
        return None

    by_winrate = sorted(final_list, key=lambda x: x["winrate"], reverse=True)
    by_games = sorted(final_list, key=lambda x: x["games"], reverse=True)

    top_wr = by_winrate[0]
    top_gm = by_games[0]

    # Исключаем из дополнительного списка героев, находящихся в главных карточках
    excluded_names = {top_wr["name"], top_gm["name"]}
    others = [h for h in by_winrate if h["name"] not in excluded_names][:3]

    return {
        "top_winrate": top_wr,
        "top_games": top_gm,
        "others": others,
    }
