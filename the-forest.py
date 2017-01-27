import os
import time
import math
from termcolor.termcolor import colored
from random import randint, random
from abc import ABC, abstractmethod
from enum import Enum
import settings

# CLASSES
# ----------------------------------------------------------------------------------------------------

# Contains and manages a 2D map of objects
class World():

    def __init__(self, width = settings.world_width, height = settings.world_height):
        self.width = width
        self.height = height

        # Map is a 2D array of cells
        self.map = self.blank_map(self.width, self.height)
        for y in range(self.height):
            for x in range(self.width):
                self.map[x][y].link_adjacent_cells()

        self.trees = []
        self.lumberjacks = []
        self.bears = []

        self.month = 1

        self.generate_initial_state()

    # Returns the number of cells in the map
    def num_cells(self):
        return self.width * self.height

    # Returns a blank map (2D array of empty cells)
    def blank_map(self, width, height):
        return [[Cell(self, x, y) for x in range(width)] for y in range(height)]

    # Populates the map with a starting arrangment of objects
    def generate_initial_state(self):
        self.random_distribute_objs(
            Tree, math.floor(settings.starting_percentages.trees * self.num_cells()), self.create_tree,
            Tree.GrowthStage.tree
        )
        self.random_distribute_objs(
            Lumberjack, math.floor(settings.starting_percentages.lumberjacks * self.num_cells()), self.create_lumberjack
        )
        self.random_distribute_objs(
            Bear, math.floor(settings.starting_percentages.bears * self.num_cells()), self.create_bear
        )

    # Creates the specified number of objects and places them randomly around the map
    def random_distribute_objs(self, obj_class, num, create_func, *create_func_args):
        for i in range(num):
            while True:
                rand_x = randint(0, self.width - 1)
                rand_y = randint(0, self.height - 1)
                cell = self.get_cell(rand_x, rand_y)

                if not cell.get_object(obj_class):
                    create_func(cell, *create_func_args)
                    break

    # Creates a tree
    def create_tree(self, cell, growth_stage):
        tree = Tree(self, cell, growth_stage)
        self.trees.append(tree)
        cell.objects.append(tree)

    # Creates a lumberjack
    def create_lumberjack(self, cell):
        lumberjack = Lumberjack(self, cell)
        self.lumberjacks.append(lumberjack)
        cell.objects.append(lumberjack)

    # Creates a bear
    def create_bear(self, cell):
        bear = Bear(self, cell)
        self.bears.append(bear)
        cell.objects.append(bear)

    def remove_tree(self, tree):
        tree.cell.objects.remove(tree)
        self.trees.remove(tree)

    def remove_lumberjack(self, lumberjack):
        lumberjack.cell.objects.remove(lumberjack)
        self.lumberjacks.remove(lumberjack)

    def remove_bear(self, bear):
        bear.cell.objects.remove(bear)
        self.bears.remove(bear)

    # Returns the cell at the given coordinates
    def get_cell(self, x, y):
        return self.map[x][y]

    def simulate(self, sim_length = settings.sim_length, update_delay = settings.update_delay):
        while self.month < sim_length and len(self.trees) > 0:
            self.update()
            self.draw()
            self.month += 1

            time.sleep(update_delay)

    # Updates all objects in the world
    def update(self):
        for tree in self.trees:
            tree.update()

        for lumberjack in self.lumberjacks:
            lumberjack.update()

        for bear in self.bears:
            bear.update()

        if self.month % settings.lumberjack_inspection_interval == 0:
            lumber = self.get_total_lumber()

            if lumber >= len(self.lumberjacks):
                num_hires = math.floor((lumber - len(self.lumberjacks)) / 10) + 1
                self.random_distribute_objs(Lumberjack, num_hires, self.create_lumberjack)

            elif len(self.lumberjacks) > 1:
                num_removals = math.floor((len(self.lumberjacks) - lumber) / 1) + 1
                num_removals = min(num_removals, len(self.lumberjacks) - 1)

                for i in range(num_removals):
                    lumberjack = self.lumberjacks[randint(0, len(self.lumberjacks) - 1)]
                    self.remove_lumberjack(lumberjack)

            self.reset_lumber()

        if self.month % settings.bear_inspection_interval == 0:
            attacks = self.get_total_attacks()

            if attacks == 0:
                self.random_distribute_objs(Bear, 1, self.create_bear)
            else:
                bear = self.bears[randint(0, len(self.bears) - 1)]
                self.remove_bear(bear)

            self.reset_attacks()

    def get_total_lumber(self):
        total = 0
        for lumberjack in self.lumberjacks:
            total += lumberjack.lumber

        return total

    def reset_lumber(self):
        for lumberjack in self.lumberjacks:
            lumberjack.lumber = 0

    def get_total_attacks(self):
        total = 0
        for bear in self.bears:
            total += bear.attacks

        return total

    def reset_attacks(self):
        for bear in self.bears:
            bear.attacks = 0

    # Draws (prints) all objects in the world, as well as the rest of the interface
    def draw(self):
        clear()

        print("-" * 50)
        print("Simulated Ecology - The Forest")
        print("-" * 50)
        print("")
        print("Month: {} | Trees: {} | Lumberjacks: {} | Bears: {}".format(self.month, len(self.trees), len(self.lumberjacks), len(self.bears)))
        print("")
        print("+" + (" -" * self.width) + " +")

        for y in range(self.height):
            print("|", end="")

            for x in range(self.width):
                print(" ", end="")
                bear = self.get_cell(x, y).get_object(Bear)
                if bear is not None:
                    bear.draw()
                    continue

                lumberjack = self.get_cell(x, y).get_object(Lumberjack)
                if lumberjack is not None:
                    lumberjack.draw()
                    continue

                tree = self.get_cell(x, y).get_object(Tree)
                if tree is not None:
                    tree.draw()
                    continue

                print(settings.symbols.empty, end="")

            print(" |")

        print("+" + (" -" * self.width) + " +")

class Cell():

    def __init__(self, world, x, y):
        self.world = world
        self.x = x
        self.y = y

        self.objects = []
        self.adjacent_cells = []

    def get_object_list(self):
        return self.objects

    def get_object(self, obj_class):
        objs = [obj for obj in self.objects if isinstance(obj, obj_class)]
        if len(objs) > 0:
            return objs[0]
        else:
            return None

    def is_open(self):
        return len(self.objects) == 0

    # Returns a random cell adjacent to this cell
    def get_random_adjacent(self):
        return self.adjacent_cells[randint(0, len(self.adjacent_cells) - 1)]

    def get_random_open_adjacent(self):
        open_cells = [x for x in self.adjacent_cells if x.is_open()]
        if len(open_cells) > 0:
            return open_cells[randint(0, len(open_cells) - 1)]
        else:
            return None

    # Stores the adjacent cells in a list
    def link_adjacent_cells(self):
        self.adjacent_cells = []

        left_bound = -1 if self.x > 0 else 0
        right_bound = 1 if self.x < self.world.width - 1 else 0

        top_bound = -1 if self.y > 0 else 0
        bottom_bound = 1 if self.y < self.world.height - 1 else 0

        for x in range(left_bound, right_bound + 1):
            for y in range(top_bound, bottom_bound + 1):
                if not (x == 0 and y == 0):
                    self.adjacent_cells.append(self.world.get_cell(self.x + x, self.y + y))


# A world object has a location in the world, and can update and draw every tick
class WorldObject(ABC):

    def __init__(self, world, cell):
        self.world = world
        self.cell = cell

        self.symbol = " "
        self.colour = "white"

    @abstractmethod
    def update(self):
        pass

    def draw(self):
        print(colored(self.symbol, self.colour), end="")

    def move(self, destination_cell):
        self.cell.objects.remove(self)

        self.cell = destination_cell
        self.cell.objects.append(self)


class Tree(WorldObject):

    class GrowthStage(Enum):
        sapling = 0
        tree = 12
        elder_tree = 120

    def __init__(self, world, cell, growth_stage):
        super().__init__(world, cell)

        self.growth_stage = self.GrowthStage.sapling if growth_stage is None else growth_stage
        self.age = 0

        if self.growth_stage == self.GrowthStage.sapling:
            self.symbol = settings.symbols.sapling
        elif self.growth_stage == self.GrowthStage.tree:
            self.symbol = settings.symbols.tree
        else:
            self.symbol = settings.symbols.elder_tree

        self.colour = settings.symbol_colours.tree

    def update(self):
        if self.growth_stage == Tree.GrowthStage.tree or self.growth_stage == Tree.GrowthStage.elder_tree:
            if self.growth_stage == Tree.GrowthStage.tree:
                chance = settings.tree_sapling_spawn_chance
            else:
                chance = settings.elder_sapling_spawn_chance

            if(random() <= chance):
                open_cell = self.cell.get_random_open_adjacent()
                if open_cell is not None:
                    self.world.create_tree(open_cell, growth_stage = Tree.GrowthStage.sapling)

        self.age += 1
        if self.age >= Tree.GrowthStage.elder_tree.value:
            self.growth_stage = Tree.GrowthStage.elder_tree
            self.symbol = settings.symbols.elder_tree

        elif self.age >= Tree.GrowthStage.tree.value:
            self.growth_stage = Tree.GrowthStage.tree
            self.symbol = settings.symbols.tree

    def __repr__(self):
        return "Tree - {} ({}, {})".format(self.growth_stage.name, self.x, self.y)


class Lumberjack(WorldObject):

    def __init__(self, world, cell):
        super().__init__(world, cell)

        self.symbol = settings.symbols.lumberjack
        self.colour = settings.symbol_colours.lumberjack

        self.lumber = 0

    def update(self):
        move_count = 0

        while move_count < settings.lumberjack_moves:

            destination_cell = self.cell.get_random_adjacent()
            if destination_cell.get_object(Lumberjack) is not None:
                destination_cell = self.cell.get_random_adjacent()

                if destination_cell.get_object(Lumberjack) is not None:
                    break

            self.move(destination_cell)
            move_count += 1

            bear = self.cell.get_object(Bear)
            if bear is not None:
                world.remove_lumberjack(self)
                bear.attacks += 1

                if len(self.world.lumberjacks) == 0:
                    self.world.random_distribute_objs(Lumberjack, 1, self.world.create_lumberjack)

                break

            tree = self.cell.get_object(Tree)
            if tree is not None:
                if tree.growth_stage != Tree.GrowthStage.sapling:
                    world.remove_tree(tree)

                    if tree.growth_stage == Tree.GrowthStage.elder_tree:
                        self.lumber += settings.elder_tree_lumber
                    else:
                        self.lumber += settings.tree_lumber

                    break


    def __repr__(self):
        return "Lumberjack ({}, {})".format(self.x, self.y)


class Bear(WorldObject):

    def __init__(self, world, cell):
        super().__init__(world, cell)

        self.symbol = settings.symbols.bear
        self.colour = settings.symbol_colours.bear

        self.attacks = 0

    def update(self):
        move_count = 0

        while move_count < settings.bear_moves:

            destination_cell = self.cell.get_random_adjacent()
            if destination_cell.get_object(Bear) is not None:
                destination_cell = self.cell.get_random_adjacent()

                if destination_cell.get_object(Bear) is not None:
                    break

            self.move(destination_cell)
            move_count += 1

            lumberjack = self.cell.get_object(Lumberjack)
            if lumberjack is not None:
                world.remove_lumberjack(lumberjack)
                self.attacks += 1

                if len(self.world.lumberjacks) == 0:
                    self.world.random_distribute_objs(Lumberjack, 1, self.world.create_lumberjack)

                break

    def __repr__(self):
        return "Bear ({}, {})".format(self.x, self.y)


# FUNCTIONS
# ----------------------------------------------------------------------------------------------------


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


world = World()
world.simulate()