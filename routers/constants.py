# База данных всех 127 героев Dota 2

# [Контроль, Стойкость, Инициация, Урон, Осада, Побег] (0-3)
HERO_TAGS = {
    "Abaddon": [1,3,1,1,1,1], "Alchemist": [1,2,1,2,3,1], "Ancient Apparition": [1,0,0,3,0,0], "Anti-Mage": [0,1,0,2,2,3],
    "Arc Warden": [1,1,0,3,3,1], "Axe": [3,3,3,1,0,0], "Bane": [3,1,0,2,0,1], "Batrider": [3,1,3,2,0,2],
    "Beastmaster": [2,2,3,1,3,0], "Bloodseeker": [2,1,2,2,1,1], "Bounty Hunter": [1,1,1,2,0,3], "Brewmaster": [2,3,3,2,1,2],
    "Bristleback": [0,3,1,2,1,0], "Broodmother": [1,2,1,2,3,2], "Centaur Warrunner": [3,3,3,1,1,1], "Chaos Knight": [2,3,2,3,1,1],
    "Chen": [1,1,1,1,3,0], "Clinkz": [0,1,1,3,3,2], "Clockwerk": [3,2,3,1,0,1], "Crystal Maiden": [3,0,1,2,0,0],
    "Dark Seer": [1,2,2,1,1,2], "Dark Willow": [3,1,1,3,0,2], "Dawnbreaker": [2,3,2,2,1,1], "Dazzle": [1,1,0,2,1,1],
    "Death Prophet": [1,2,1,2,3,1], "Disruptor": [3,0,1,2,0,0], "Doom": [2,3,2,2,0,1], "Dragon Knight": [3,3,2,2,2,0],
    "Drow Ranger": [1,0,0,3,2,1], "Earth Spirit": [3,2,3,1,0,2], "Earthshaker": [3,1,3,2,0,1], "Elder Titan": [2,2,2,2,1,0],
    "Ember Spirit": [1,1,2,2,0,3], "Enchantress": [1,1,1,2,2,1], "Enigma": [3,1,2,1,3,0], "Faceless Void": [3,2,3,2,1,2],
    "Grimstroke": [2,0,1,2,0,1], "Gyrocopter": [1,1,1,3,1,1], "Hoodwink": [2,0,1,3,0,2], "Huskar": [0,3,1,3,1,0],
    "Invoker": [2,1,2,3,1,2], "Io": [1,1,1,1,0,2], "Jakiro": [2,1,1,2,2,0], "Juggernaut": [0,1,1,2,3,2],
    "Keeper of the Light": [1,0,1,3,1,2], "Kez": [1,1,2,3,1,3], "Kunkka": [3,2,3,2,1,1], "Legion Commander": [2,3,2,2,1,1],
    "Leshrac": [1,1,1,3,3,1], "Lich": [2,0,1,3,0,0], "Lifestealer": [1,3,0,2,1,1], "Lina": [2,0,1,3,1,1],
    "Lion": [3,0,2,3,0,0], "Lone Druid": [1,2,1,2,3,1], "Luna": [1,1,1,2,3,1], "Lycan": [0,2,3,2,3,1],
    "Magnus": [3,2,3,1,0,1], "Marci": [2,2,2,2,0,2], "Mars": [3,3,3,1,1,1], "Medusa": [1,3,0,2,2,0],
    "Meepo": [2,2,1,3,2,2], "Mirana": [2,0,1,2,1,2], "Monkey King": [2,1,2,2,1,2], "Morphling": [1,1,1,3,1,3],
    "Muerta": [1,1,0,3,1,0], "Naga Siren": [2,2,1,1,3,2], "Nature's Prophet": [1,1,1,2,3,3], "Necrophos": [1,2,0,3,1,1],
    "Night Stalker": [2,2,3,2,0,2], "Nyx Assassin": [3,0,2,3,0,2], "Ogre Magi": [2,3,1,2,1,0], "Omniknight": [1,2,1,2,0,0],
    "Oracle": [2,0,0,2,0,1], "Outworld Destroyer": [2,1,1,3,1,1], "Pangolier": [2,1,3,2,0,3], "Phantom Assassin": [0,1,1,3,0,2],
    "Phantom Lancer": [1,1,1,2,1,3], "Phoenix": [2,2,2,3,0,2], "Primal Beast": [2,3,3,2,0,2], "Puck": [2,1,3,2,0,3],
    "Pudge": [2,3,2,2,0,1], "Pugna": [1,0,1,3,3,1], "Queen of Pain": [1,0,1,3,0,3], "Razor": [1,2,2,2,1,1],
    "Riki": [2,1,1,3,0,3], "Ringmaster": [3,1,1,2,0,1], "Rubick": [2,0,1,2,0,1], "Sand King": [3,2,3,2,1,2],
    "Shadow Demon": [2,0,1,1,0,1], "Shadow Fiend": [1,0,1,3,2,1], "Shadow Shaman": [3,1,1,2,3,0], "Silencer": [2,0,0,2,0,0],
    "Skywrath Mage": [1,0,0,3,0,0], "Slardar": [3,2,3,2,0,1], "Slark": [1,2,1,1,0,3], "Snapfire": [2,1,1,3,1,1],
    "Sniper": [1,0,0,3,2,1], "Spectre": [1,3,1,2,0,2], "Spirit Breaker": [3,2,3,1,0,2], "Storm Spirit": [1,1,3,3,0,3],
    "Sven": [2,2,2,3,2,1], "Techies": [2,1,1,3,1,2], "Templar Assassin": [1,1,1,3,2,2], "Terrorblade": [0,1,1,2,3,2],
    "Tidehunter": [3,3,3,1,1,0], "Timbersaw": [1,3,1,3,1,2], "Tinker": [1,1,2,3,0,2], "Tiny": [3,2,3,3,2,1],
    "Treant Protector": [3,2,2,1,1,1], "Troll Warlord": [1,2,1,2,3,1], "Tusk": [3,1,2,2,1,2], "Underlord": [2,3,1,1,2,0],
    "Undying": [2,3,1,1,0,0], "Ursa": [1,2,1,3,1,1], "Vengeful Spirit": [3,1,2,2,1,1], "Venomancer": [1,1,1,2,1,1],
    "Viper": [2,2,0,3,1,0], "Visage": [2,2,1,2,3,1], "Void Spirit": [2,1,3,2,0,3], "Warlock": [2,1,1,2,1,0],
    "Weaver": [1,1,1,2,1,3], "Windranger": [2,1,1,3,1,3], "Winter Wyvern": [3,1,1,2,1,2], "Witch Doctor": [2,1,1,3,0,0],
    "Wraith King": [2,3,1,2,2,1], "Zeus": [1,0,0,3,0,0], "Largo": [1,3,2,1,0,1]
}

HERO_POSITIONS = {
    "Anti-Mage": [1], "Arc Warden": [2], "Bloodseeker": [1], "Chaos Knight": [1, 3],
    "Clinkz": [1, 2], "Drow Ranger": [1], "Faceless Void": [1], "Gyrocopter": [1], "Juggernaut": [1],
    "Kez": [1, 2], "Lifestealer": [1], "Lone Druid": [1, 2], "Luna": [1], "Medusa": [1], "Meepo": [1, 2],
    "Morphling": [1, 2], "Muerta": [1], "Naga Siren": [1], "Nature's Prophet": [1, 2, 3, 4], "Phantom Assassin": [1],
    "Phantom Lancer": [1], "Razor": [1, 2, 3], "Riki": [1], "Slark": [1], "Sniper": [1, 2], "Spectre": [1],
    "Sven": [1], "Templar Assassin": [1, 2], "Terrorblade": [1], "Tiny": [2, 4], "Troll Warlord": [1],
    "Ursa": [1], "Weaver": [1, 4], "Wraith King": [1, 3], "Ember Spirit": [2], "Invoker": [2], 
    "Kunkka": [2, 3], "Leshrac": [2], "Lina": [2], "Necrophos": [2, 3], "Outworld Destroyer": [2],
    "Pangolier": [2, 3], "Puck": [2], "Queen of Pain": [2], "Shadow Fiend": [1, 2], "Storm Spirit": [2],
    "Tinker": [2], "Void Spirit": [2], "Zeus": [2, 4], "Batrider": [2, 3, 4], "Primal Beast": [2, 3],
    "Abaddon": [3, 4, 5], "Axe": [3], "Beastmaster": [3], "Brewmaster": [3], "Bristleback": [3],
    "Centaur Warrunner": [3], "Dark Seer": [3], "Dawnbreaker": [3, 4], "Doom": [3], "Dragon Knight": [2, 3],
    "Earthshaker": [3, 4], "Elder Titan": [3, 4, 5], "Enigma": [3, 4], "Largo": [3, 4, 5], "Legion Commander": [3],
    "Lycan": [3], "Magnus": [2, 3], "Marci": [3, 4], "Mars": [3], "Night Stalker": [3], "Omniknight": [3, 5],
    "Pudge": [3, 4], "Sand King": [3], "Slardar": [3], "Spirit Breaker": [3, 4], "Tidehunter": [3],
    "Timbersaw": [2, 3], "Underlord": [3], "Venomancer": [3, 4, 5], "Viper": [2, 3], "Visage": [2, 3],
    "Ancient Apparition": [4, 5], "Bane": [5], "Bounty Hunter": [4], "Chen": [5], "Clockwerk": [4],
    "Crystal Maiden": [5], "Dark Willow": [4, 5], "Dazzle": [5], "Disruptor": [5], "Earth Spirit": [4],
    "Enchantress": [4, 5], "Grimstroke": [4, 5], "Hoodwink": [4], "Io": [4, 5], "Jakiro": [5],
    "Keeper of the Light": [4], "Lich": [5], "Lion": [4, 5], "Mirana": [4], "Nyx Assassin": [4],
    "Ogre Magi": [5], "Oracle": [5], "Phoenix": [4, 5], "Pugna": [4, 5], "Ringmaster": [4, 5],
    "Rubick": [4], "Shadow Demon": [5], "Shadow Shaman": [5], "Silencer": [5], "Skywrath Mage": [4, 5],
    "Snapfire": [4, 5], "Techies": [4], "Treant Protector": [4, 5], "Tusk": [4], "Undying": [5],
    "Vengeful Spirit": [4, 5], "Warlock": [5], "Windranger": [4], "Winter Wyvern": [4, 5], "Witch Doctor": [5]
}

ILLUSION_HEROES = ["Naga Siren", "Phantom Lancer", "Terrorblade", "Chaos Knight", "Meepo"]
ILLUSION_KILLERS = ["Axe", "Earthshaker", "Sven", "Leshrac", "Legion Commander", "Sand King"]
