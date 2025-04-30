def buy(fruits_to_buy, prices, budget):
    prices_list = []
    for fruits in fruits_to_buy:
        if fruits in prices.keys():
            prices_list.append(prices[fruits])
            
    budget = budget - sum(prices_list)
    
    prices_list.sort()
    
    current = []
    
    result = []
    
    combination_sum(prices_list, budget, current, result, 0)
    
    temp = []
    for combinations in result:
        for elem in prices_list:
            for key, value in prices.items():
                if int(elem) == int(value):
                    temp.append(display(str(key), int(combinations.count(elem) + 1)))
        print(''.join(temp))
        temp.clear()

def display(fruit: str, count: int) -> str:
    assert count >= 1 and fruit[-1] == 's'
    if count == 1:
        fruit = fruit[:-1]  # get rid of the plural s
    return '[' + str(count) + ' ' + fruit + ']'
    
def combination_sum(arr, budget, current, result, index):
    if budget == 0:
        result.append(list(current))
        return
    
    if budget < 0 or index >= len(arr):
        return
    
    current.append(arr[index])
    
    combination_sum(arr, budget - arr[index], current, result, index)
    
    current.pop()
    
    combination_sum(arr, budget, current, result, index + 1)


buy(["apples", "bananas", "oranges"], {"bananas": 2,"apples": 1, "oranges": 3}, 20)