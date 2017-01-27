world_width = 100
world_height = 100

class starting_percentages():
    trees = 0.5
    lumberjacks = 0.1
    bears = 0.02

class symbols():
    sapling = "."
    tree = "t"
    elder_tree = "T"
    lumberjack = "L"
    bear = "B"
    empty = " "

class symbol_colours():
    tree = "green"
    lumberjack = "cyan"
    bear = "red"

tree_sapling_spawn_chance = 0.1
elder_sapling_spawn_chance = 0.2

tree_lumber = 1
elder_tree_lumber = 2

lumberjack_moves = 3
bear_moves = 5

lumberjack_inspection_interval = 12
bear_inspection_interval = 12

sim_length = 4800
update_delay = 0.1