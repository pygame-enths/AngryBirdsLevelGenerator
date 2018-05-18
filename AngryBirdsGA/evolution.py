import math
import random
import os
from AngryBirdsGA import *
from AngryBirdsGA.BlockGene import BlockGene
from AngryBirdsGA.LevelIndividual import LevelIndividual
import AngryBirdsGA.SeparatingAxisTheorem as SAT
import AngryBirdsGA.XMLHelpers as xml
import numpy as np
from collections import Counter

class Evolution:

    def __init__(self):
        self.population = []
        self.initialization = None
        self.fitness = None
        self.selection = None
        self.cross = None
        self.mutation = None
        self.replacement = None

    def registerInitialization(self,initialization):
         self.initialization = initialization

    def registerFitness(self, fitness):
        self.fitness = fitness

    def registerSelection(self, selection):
        self.selection = selection

    def registerCross(self, cross):
        self.cross = cross

    def registerMutation(self, mutation):
        self.mutation = mutation

    def registerReplacement(self, replacement):
        self.replacement = replacement

    def initEvolution(self, population_size, fitness_params ):
        assert self.fitness is not None, "Fitness function required"
        assert self.initialization is not None, "Initialization function required"
        self.population = self.initialization(population_size)
        return self.fitness(self.population, *fitness_params)

    def runGeneration(self, fitness_params, selection_params, mutation_params, replacement_params):
        assert self.population is not [], "Before executing a generation you need to initialize the evolution"
        assert self.selection is not None, "Selection function required"
        assert self.mutation is not None, "Mutation function required"
        assert self.replacement is not None, "Replacement function required"
        assert self.cross is not None, "Cross function required"
        parents = self.selection(self.population, *selection_params)
        children = self.cross(parents)
        self.mutation(children,*mutation_params)
        fit_out = self.fitness(children, *fitness_params)
        self.population = self.replacement(children, self.population, *replacement_params)

        return self.population, fit_out


def initPopulation(number_of_individuals):
    population = []

    for i in range(number_of_individuals):
        population.append(LevelIndividual([]).initRandom(n_blocks=random.randint(MIN_B, MAX_B)))

    return population

def initPopulationCheckOverlapping(number_of_individuals):
    population = []

    for i in range(number_of_individuals):
        population.append(LevelIndividual([]).initNoOverlapping(n_blocks=random.randint(MIN_B, MAX_B)))

    return population

def initPopulationDiscretePos(number_of_individuals):
    population = []
    for i in range(number_of_individuals):
        population.append(LevelIndividual([]).initDiscrete(n_blocks = random.randint(MIN_B, MAX_B)))

    return population

def initPopulationCheckOverlappingDiscretePos(number_of_individuals):
    population = []

    print("Initializing population 0/" + str(number_of_individuals) + "\r", end="", flush=True)
    for i in range(number_of_individuals):
        print("Initializing population " + str(i) + "/" + str(number_of_individuals)+ "\r", end="", flush=True)
        population.append(LevelIndividual([]).initDiscreteNoOverlapping(n_blocks = random.randint(MIN_B, MAX_B)))

    print("Initializing population completed")
    return population


def fitnessPopulation(population, game_path, write_path, read_path):
    # generate all xml
    for i in range(len(population)):
        xml.writeXML(population[i], os.path.join(write_path, "level-"+str(i)+".xml"))

    # run game
    os.system(game_path)

    # parse all xml
    for i in range(len(population)):
        averageVelocity = xml.readXML(os.path.join(read_path,"level-"+str(i)+".xml"))
        # assign fitness
        population[i].calculateFitness(averageVelocity)

def fitnessPopulationSkip(population, game_path, write_path, read_path, max_evaluated):
    # generate all xml
    fill = len(str(len(population)))
    evaluated= []
    for i in range(len(population)):
        print("Calculating fitness of "+ str(i)+ "/"+str(len(population))+ " with size of " + str(len(population[i].blocks())) +"\r", end="")
        population[i].calculatePreFitness()
        if population[i].fitness == 0:
            xml.writeXML(population[i], os.path.join(write_path, "level-"+str(len(evaluated)).zfill(fill)+".xml"))
            evaluated.append(i)

    # run game
    if len(evaluated)>0:
        print( "Run Game" )
        os.system(game_path)


    # parse all xml
    for i in range(len(evaluated)):
        averageVelocity = xml.readXML(os.path.join(read_path,"level-"+str(i)+".xml"))
        # assign fitness
        population[evaluated[i]].calculateFitness(averageVelocity)
        max_evaluated = max(population[evaluated[i]].fitness, max_evaluated)

    # to make sure all levels not evaluated in game have worse fitness value
    for i in range(len(population)):
        if i not in evaluated:
            population[i].base_fitness = max_evaluated
            population[i].fitness+=max_evaluated

    return max_evaluated


def selectionTournament(population,n_tournaments):
    parents = []
    for i in range(n_tournaments):
        candidate_1 = population[random.randint(0,len(population)-1)]
        candidate_2 = population[random.randint(0,len(population)-1)]
        parents.append(min(candidate_1, candidate_2, key=lambda x: x.fitness))

        candidate_1 = population[random.randint(0,len(population)-1)]
        candidate_2 = population[random.randint(0,len(population)-1)]
        parents.append(min(candidate_1, candidate_2, key=lambda x: x.fitness))
    return parents

def selectionTournamentNoRepetition(population,n_tournaments):
    parents = []
    for i in range(n_tournaments):
        candidate_1, candidate_2  = random.sample(population,2)
        parents.append(min(candidate_1, candidate_2, key=lambda x: x.fitness))

        candidate_1, candidate_2  = random.sample(population,2)
        parents.append(min(candidate_1, candidate_2, key=lambda x: x.fitness))
    return parents


def crossSample(parents):
    children = []
    for i in range(0,len(parents), 2):
        child_n_blocks = min(len(parents[i].blocks()) + len(parents[i+1].blocks()) // 2, MAX_B)
        child_blocks = random.sample(parents[i].blocks()+parents[i+1].blocks(), child_n_blocks)
        children.append(LevelIndividual(child_blocks))
    return children

def crossSampleNoDuplicate(parents):
    children = []
    for i in range(0,len(parents), 2):
        common = []
        #fast way of have unique elements in a list of un-hashable objects. If x is not in common, append evaluates and returns None, which evaluates false
        merged = [x for x in parents[i].blocks()+parents[i+1].blocks() if x not in common and (common.append(x) or True)]
        child_n_blocks = min(len(merged),min(len(parents[i].blocks()) + len(parents[i+1].blocks()) // 2, MAX_B))
        assert len(merged)>=child_n_blocks, "Length is %r but the mean is %r" % (len(merged),child_n_blocks)
        child_blocks = random.sample(merged, child_n_blocks)
        children.append(LevelIndividual(child_blocks))
    return children


def mutationBlockNumber(population, n_mutations, max_difference):
    for a in range(n_mutations):
        n_blocks = random.randint(-max_difference, max_difference)
        indv_mut = population[random.randint(0, len(population)-1)]

        if(n_blocks>0):

            ny = math.floor((MAX_Y - MIN_Y) / SMALLEST_STEP)
            nx = math.floor((MAX_X - MIN_X) / SMALLEST_STEP)
            for b in range(n_blocks):
                x = random.randint(0, nx)
                y = random.randint(0, ny)
                block = BlockGene(type = random.randint(1, len(BLOCKS) - 1),
                                  pos = (MIN_X + SMALLEST_STEP * x, MIN_Y + SMALLEST_STEP * y),
                                  r = random.randint(0, len(ROTATION) - 1))
                indv_mut.appendBlock(block)
        else:
            for b in range(-n_blocks):
                indv_mut.removeBlock(random.randint(0,len(indv_mut.blocks())-1))

def mutationBlockProperties(population, n_mutations):
    sample = random.sample(population, len(population))
    for indv_mut in sample:
        block_i = random.randint(0, len(indv_mut.blocks()) - 1)
        block = BlockGene(type=indv_mut.blocks()[block_i].type,
                          pos=(indv_mut.blocks()[block_i].x, indv_mut.blocks()[block_i].x),
                          r=indv_mut.blocks()[block_i].rot)
        block.type = (block.type+random.randint(-1, 1))%len(BLOCKS)
        block.x = block.x+random.uniform(-1,1)
        block.y = block.y+random.uniform(-1,1)
        block.rot = (block.rot+random.randint(-1, 1))%len(ROTATION)

        indv_mut.updateBlock(block_i,block)


def elitistReplacement(old, new, n_new):
    return sorted((old + new), key=lambda a: a.fitness, reverse=False)[:n_new]

def cleanDirectory(path):
    for f in os.listdir(path):
        os.remove(os.path.join(path,f))

def informationEntropy(population, prec):
    c = Counter([round(p.fitness,prec) for p in population])
    k = 1
    for i in range(prec):
        k/=10
    #k = round((max(population, key=lambda x: x.fitness).fitness - min(population, key=lambda x: x.fitness).fitness)/k)
    k = len(population)
    h = - sum( [(f/k)*math.log(f/k,2) for e,f in c.most_common()])
    return h

def main1():
    #game_path = os.path.join(os.path.dirname(os.getcwd()), 'ablinux/ab_linux_build.x86_64')
    project_root = os.path.dirname(os.getcwd())
    game_path = os.path.join(os.path.dirname(project_root), 'abwin/win_build.exe')
    write_path = os.path.join(os.path.dirname(project_root),
                              'abwin/win_build_Data/StreamingAssets/Levels')
    #                          'ablinux/ab_linux_build_Data/StreamingAssets/Levels')
    read_path = os.path.join(os.path.dirname(project_root),
                             'abwin/win_build_Data/StreamingAssets/Output')
    #                         'ablinux/ab_linux_build_Data/StreamingAssets/Output')
    log_path = os.path.join(os.path.dirname(project_root), 'tfgLogs/log.txt')
    population_size = 100
    number_of_generations = 100
    number_of_parents = math.floor(0.5*population_size)
    number_of_mutations = math.floor((number_of_parents//2)*0.3)

    population = initPopulationCheckOverlappingDiscretePos(population_size)

    # clean directory (input and output)
    cleanDirectory(write_path)
    cleanDirectory(read_path)
    if os.path.isfile(log_path):
        os.remove(log_path)

    max_evaluated = fitnessPopulationSkip(population, game_path=game_path, write_path=write_path, read_path=read_path, max_evaluated=0)

    for generation in range(number_of_generations):
        print("Generation " + str(generation) + "/" + str(number_of_generations))
        # Select parents
        parents = selectionTournamentNoRepetition(population, number_of_parents)
        # generate children
        children = crossSampleNoDuplicate(parents)
        # mutate children
        mutationBlockProperties(children,number_of_mutations)

        cleanDirectory(write_path)
        cleanDirectory(read_path)
        # evaluate children
        max_evaluated = fitnessPopulationSkip(children, game_path=game_path, write_path=write_path, read_path=read_path, max_evaluated=max_evaluated)
        # replace generation
        for i in population+children:
            i.updateBaseFitness(max_evaluated)
        population = sorted((children+parents), key=lambda x: x.fitness, reverse = False)[:population_size]

        print("ENTROPY " + str(informationEntropy(population, 4)) + " best-> " + str(population[0].fitness) + " avg -> " + str(
            sum(map(lambda x: x.fitness, population)) / len(population)) + " worst -> " + str(
            max(population, key=lambda x: x.fitness).fitness))

        f = open(os.path.join(os.path.dirname(project_root), 'tfgLogs/log.txt'), 'a')
        f.write("----------------------------------------------Generation " + str(generation) + "/" + str(number_of_generations)+ "----------------------------------------------")
        for level in population:
            f.write(level.toString())
        f.close()

    best_individual = min(population, key=lambda x: x.fitness)

    print("DONE: best-> "+str(best_individual.fitness)+ " avg -> "+ str( sum(map(lambda x: x.fitness, population))/len(population) ) + " worst -> " + str(max(population, key=lambda x: x.fitness).fitness))

    xml.writeXML(best_individual, os.path.join(os.path.dirname(project_root),
                                               'abwin/level-0.xml'))

def main():
    population_size = 100
    number_of_generations = 100
    number_of_parents = math.floor(0.5 * population_size)
    number_of_mutations = math.floor((number_of_parents // 2) * 0.3)

    project_root = os.path.dirname(os.getcwd())
    game_path = os.path.join(os.path.dirname(project_root), 'abwin/win_build.exe')
    write_path = os.path.join(os.path.dirname(project_root),'abwin/win_build_Data/StreamingAssets/Levels')
    read_path = os.path.join(os.path.dirname(project_root),'abwin/win_build_Data/StreamingAssets/Output')
    log_path = os.path.join(os.path.dirname(project_root), 'tfgLogs/log.txt')



    evolution = Evolution()
    evolution.registerInitialization(initialization=initPopulationDiscretePos)
    evolution.registerFitness(fitness=fitnessPopulationSkip)
    evolution.registerCross(cross=crossSampleNoDuplicate)
    evolution.registerMutation(mutation=mutationBlockProperties)
    evolution.registerReplacement(replacement= elitistReplacement)
    evolution.registerSelection(selection=selectionTournamentNoRepetition)

    max_evaluated = evolution.initEvolution(population_size= population_size, fitness_params=[game_path, write_path, read_path, 0])

    cleanDirectory(write_path)
    cleanDirectory(read_path)
    if os.path.isfile(log_path):
        os.remove(log_path)

    for generation in range(number_of_generations):
        population, max_evaluated = evolution.runGeneration(fitness_params=[game_path, write_path, read_path, max_evaluated],
                                                            mutation_params=[number_of_mutations],
                                                            selection_params=[number_of_parents],
                                                            replacement_params=[population_size])
        cleanDirectory(write_path)
        cleanDirectory(read_path)
        print("G: " + str(generation) +\
              " ENTROPY " + str(informationEntropy(population, 4)) +\
              " best-> " + str(population[0].fitness) +\
              " avg -> " + str(sum(map(lambda x: x.fitness, population)) / len(population)) +\
              " worst -> " + str(max(population, key=lambda x: x.fitness).fitness))

        f = open(os.path.join(os.path.dirname(project_root), 'tfgLogs/log.txt'), 'a')
        f.write("----------------------------------------------Generation " + str(generation) + "/" + str(
            number_of_generations) + "----------------------------------------------")
        for level in population:
            f.write(level.toString())
        f.close()

    xml.writeXML(best_individual, os.path.join(os.path.dirname(project_root),
                                               'abwin/level-0.xml'))

if __name__ == "__main__":
    main()
