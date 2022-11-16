import config

print(type(config.CostAmount), config.CostAmount)
print(type(config.CostType), config.CostType)
# print(type(config.Cost), config.Cost)

for setting in config.all_setting:
    print(setting)