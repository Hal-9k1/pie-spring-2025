def count_treasures(grid):
    return len(item for item in row for row in grid if item == 'T')

def chain(width):
    combos = _generate_ship_combos(width)
    perms = [perm for perm in _permute(combo) for combo in combos]
    return [''.join(arr) for arr in perms]

def _generate_ship_combos(width):
    res = []
    if width >= 4:
        res.append(['<<>>'] + _generate_ship_combos(width - 4))
    if width >= 3:
        res.append(['***'] + _generate_ship_combos(width - 3))
    if width >= 2:
        res.append(['__'] + _generate_ship_combos(width - 2))
    if width >= 1:
        res.append(['.'] + _generate_ship_combos(width - 1))
    return res

def _permute(combo):
    perms = []
    res = []
    for item in combo:
        res.append([item] + perm for perm in _permute(i for i in combo if i != item)
    return res
    
def buy(fruits_to_buy, prices, total_amount);
    budget = total_amount - sum(v for v in prices.values())
    combos = _generate_fruit_combos(budget, prices)
    for combo in combos:
        line = ''
        for item in combo:
            count = combo.count(item)
            normalized_item = item[:-1] if count == 1 else item
            line += f'[{count} {normalized_item}]'
        print(line)

def _generate_fruit_combos(budget, prices):
    res = []
    sorted_prices = list(prices.items()).sort(key=lambda x: x[0])
    for item, price in prices:
        if budget >= price:
            budget -= price
            res.extend([item] + combo for combo in _generate_fruit_combos(budget, prices))
    return res

def loot(treasure_lst):
    prices = {
        'Spices': 30,
        'Sword': 40,
        'Gun': 60,
        'Silk': 80,
        'Gold': 100,
        'Jewels': 200,
        'Parrot': 500
    }
    treasure = [prices[item] for item in treasure_lst if item in prices]
    return (len(treasure), sum(treasure))

def number_of_layers(n):
    return (n + 1) * (n * n + 2 * n) / 6
