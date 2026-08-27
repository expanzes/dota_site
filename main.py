def get_recommendations_for_role(
    role_key: str, candidate_stats: dict, heroes_map: dict
) -> list[str]:
  valid_heroes_for_role = ROLES_DB.get(role_key, set())

  all_candidates = []
  role_candidates = []

  for cid, data in candidate_stats.items():
    hero_name = heroes_map.get(cid, "")

    # Игнорируем героев с выборкой меньше 30 матчей, чтобы убрать случайные 100% винрейты из 2-4 игр
    if not hero_name or data["games"] < 30:
      continue

    wr = (data["wins"] / data["games"]) * 100
    item = (hero_name, wr, data["games"])

    all_candidates.append(item)
    if hero_name.lower() in valid_heroes_for_role:
      role_candidates.append(item)

  role_candidates.sort(key=lambda x: x[1], reverse=True)
  all_candidates.sort(key=lambda x: x[1], reverse=True)

  # Если под роль с выборкой от 30 игр никто не подошел, снижаем планку до 10 игр
  if not role_candidates and not all_candidates:
    for cid, data in candidate_stats.items():
      hero_name = heroes_map.get(cid, "")
      if hero_name and data["games"] >= 10:
        wr = (data["wins"] / data["games"]) * 100
        item = (hero_name, wr, data["games"])
        all_candidates.append(item)
        if hero_name.lower() in valid_heroes_for_role:
          role_candidates.append(item)
    role_candidates.sort(key=lambda x: x[1], reverse=True)
    all_candidates.sort(key=lambda x: x[1], reverse=True)

  final_list = role_candidates if role_candidates else all_candidates

  formatted = []
  if final_list:
    best_hero, best_wr, best_games = final_list[0]
    formatted.append(
        f"  ★ САМЫЙ ЛУЧШИЙ ПИК: {best_hero} — {best_wr:.1f}% винрейт (матчей:"
        f" {best_games})"
    )

    if len(final_list) > 1:
      formatted.append("  Другие сильные варианты:")
      for h_name, wr, games in final_list[1:4]:
        formatted.append(f"    • {h_name}: {wr:.1f}% винрейт (матчей: {games})")
  else:
    formatted.append("  • Не удалось подобрать героя под эту роль")

  return formatted
