# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

from copy import copy

from random import random, shuffle
from math import floor, ceil

import Core.Globals as g

import logging
logger = logging.getLogger("PostPro.TSP")

class TSPoptimize():
    """
    Optimize using the Travelling Salesman Problem (TSP) algorithim
    """
    def __init__(self, st_end_points=[], order=[]):

        self.shape_nrs = len(st_end_points)
        self.iterations = int(self.shape_nrs) * 10
        self.pop_nr = min(int(ceil(self.shape_nrs / 8.0) * 8.0),
                        g.config.vars.Route_Optimisation['max_population'])
        self.mutate_rate = g.config.vars.Route_Optimisation['mutation_rate']
        self.opt_route = []
        self.order = order
        self.st_end_points = st_end_points

        #Generate the Distance Matrix
        self.DistanceMatrix = DistanceMatrixClass(matrix=[])
        self.DistanceMatrix.generate_matrix(st_end_points)

        #Generation Population
        self.Population = PopulationClass(size=[self.shape_nrs, self.pop_nr],
                                         dmatrix=self.DistanceMatrix.matrix,
                                         pop=[])

        #Initialise the Result Class
        self.Fittness = FittnessClass(population=self.Population,
                                      cur_fittness=range(self.Population.size[1]))
        self.Fittness.calc_st_fittness(self.DistanceMatrix.matrix,
                                       range(self.shape_nrs))
        self.Fittness.order = self.order

        #Anfang der Reihenfolge immer auf den letzen Punkt legen
        #Beginning of the sequence always put the last point ???
        self.Fittness.set_startpoint()

        #Function to correct the order of the elements
        self.Fittness.correct_constrain_order()

        #logger.debug('Calculation of start fitness TSP: %s' %self)
        #logger.debug('Size Distance matrix: %s', len(self.DistanceMatrix.matrix))
        #Erstellen der ersten Ergebnisse
        #Create the first result
        self.Fittness.calc_cur_fittness(self.DistanceMatrix.matrix)
        self.Fittness.select_best_fittness()
        self.opt_route = self.Population.pop[self.Fittness.best_route]

        #ERstellen der 2 opt Optimierungs Klasse
        #Create the 2 opt optimization class ???
        #self.optmove=ClassOptMove(dmatrix=self.DistanceMatrix.matrix, nei_nr=int(round(self.shape_nrs/10)))

    def calc_next_iteration(self):
        """
        calc_next_iteration()
        """
        #Algorithmus ausfürhen
        # ? Algorithm ???
        self.Population.genetic_algorithm(Result=self.Fittness, mutate_rate=self.mutate_rate)
        #Für die Anzahl der Tours die Tours nach dem 2-opt Verfahren optimieren
        #Optimise the number of Tours de Tours to the 2-opt method ???
##        for pop_nr in range(len(self.Population.pop)):
##            #print ("Vorher: %0.2f" %self.calc_tour_length(tours[tour_nr]))
##            self.Population.pop[pop_nr]=self.optmove.do2optmove(self.Population.pop[pop_nr])
##            #print ("Nachher: %0.2f" %self.calc_tour_length(tours[tour_nr]))
        #Anfang der Reihenfolge immer auf den letzen Punkt legen
        #Always put the last point at the beginning of the sequence
        self.Fittness.set_startpoint()
        #Korrektur Funktion um die Reihenfolge der Elemente zu korrigieren
        #Function to correct the order of the elements
        self.Fittness.correct_constrain_order()
        #Fittness der jeweiligen Routen ausrechen
        #Calculate fitness of each route
        self.Fittness.calc_cur_fittness(self.DistanceMatrix.matrix)
        #Straffunktion falls die Route nicht der gewünschten Reihenfolge entspricht
        #Function if the route is not the desired sequence ???
        #Best route to choose
        self.Fittness.select_best_fittness()
        self.opt_route = self.Population.pop[self.Fittness.best_route]
        #logger.debug('Calculation next iteration of TSP: %s' %self)

    def __str__(self):
        #res = self.Population.pop
        return ("Iteration nrs:    %i" % (self.iterations * 10)) + \
               ("\nShape nrs:      %i" % self.shape_nrs) + \
               ("\nPopulation:     %i" % self.pop_nr) + \
               ("\nMutate rate:    %0.2f" % self.mutate_rate) + \
               ("\norder:          %s" % self.order) + \
               ("\nStart length:   %0.1f" % self.Fittness.best_fittness[0]) + \
               ("\nOpt. length:    %0.1f" % self.Fittness.best_fittness[-1]) + \
               ("\nOpt. route:     %s" % self.opt_route)

class PopulationClass:
    def __init__(self, size=[5, 8], mutate_rate=0.95,
                 dmatrix=[], pop=[], rot=[], order=[]):

        self.size = size
        self.mutate_rate = mutate_rate
        self.pop = pop
        self.rot = rot

        #logger.debug('The Population size is: %s' %self.size)

        for pop_nr in range(self.size[1]):
            #logger.debug("======= TSP initializing population nr %i =======" % pop_nr)

            if g.config.vars.Route_Optimisation['begin_art'] == 'ordered':
                self.pop.append(range(size[0]))
            elif g.config.vars.Route_Optimisation['begin_art'] == 'random':
                self.pop.append(self.random_begin(size[0]))
            elif g.config.vars.Route_Optimisation['begin_art'] == 'heuristic':
                self.pop.append(self.heuristic_begin(dmatrix[:]))
            else:
                logger.error(('Wrong begin art of TSP choosen'))

        for rot_nr in range(size[0]):
            self.rot.append(0)


    def random_begin(self, size):
        """
        random_begin for TSP
        """
        tour = range(size)
        shuffle(tour)
        return tour

    def heuristic_begin(self, dmatrix=[]):
        """
        heuristic_begin for TSP
        """
        tour = []
        possibilities = range(len(dmatrix[0]))
        start_nr = int(floor(random()*len(dmatrix[0])))

        #Hinzufügen der Nr und entfernen aus possibilies
        #Add and remove the number of possibilities ???
        tour.append(start_nr)
        possibilities.pop(possibilities.index(tour[-1]))
        counter = 0

        while len(possibilities):
            counter += 1
            tour.append(self.heuristic_find_next(tour[-1], possibilities, dmatrix))
            possibilities.pop(possibilities.index(tour[-1]))

            #if (counter % 10) == 0:
                #logger.debug("TSP heuristic searching nr %i" % counter)
        return tour

    def heuristic_find_next(self, start=1, possibilities=[], dmatrix=[]):
        """
        heuristic_find_next() for TSP
        """
        #Auswahl der Entfernungen des nächsten Punkts
        #The distances of the point selection ???
        min_dist = 1e99
        darray = dmatrix[start]

        for pnr in possibilities:
            if (darray[pnr] < min_dist):
                min_point = pnr
                min_dist = darray[pnr]
        return min_point

    def genetic_algorithm(self, Result=[], mutate_rate=0.95):
        """
        genetic_algorithm for TSP
        """
        self.mutate_rate = mutate_rate

        #Neue Population Matrix erstellen
        #Create new Population Matrix
        new_pop = []
        for p_nr in range(self.size[1]):
            new_pop.append([])

        #Tournament Selection 1 between Parents (2 Parents remaining)
        ts_r1 = range(self.size[1])
        shuffle(ts_r1)
        winners_r1 = []
        tmp_fittness = []
        for nr in range(self.size[1] / 2):
            if Result.cur_fittness[ts_r1[nr * 2]]\
               < Result.cur_fittness[ts_r1[(nr * 2) + 1]]:
                winners_r1.append(self.pop[ts_r1[nr * 2]])
                tmp_fittness.append(Result.cur_fittness[ts_r1[nr * 2]])
            else:
                winners_r1.append(self.pop[ts_r1[(nr * 2) + 1]])
                tmp_fittness.append(Result.cur_fittness[ts_r1[(nr * 2) + 1]])
        #print tmp_fittness

        #Tournament Selection 2 only one Parent remaining
        ts_r2 = range(self.size[1] / 2)
        shuffle(ts_r2)
        for nr in range(self.size[1] / 4):
            if tmp_fittness[ts_r2[nr * 2]]\
               < tmp_fittness[ts_r2[(nr * 2) + 1]]:
                winner = winners_r1[ts_r2[nr * 2]]
            else:
                winner = winners_r1[ts_r2[(nr * 2) + 1]]

            #Schreiben der Gewinner in die neue Population Matrix
            #print winner
            for pnr in range(2):
                new_pop[pnr * self.size[1] / 2 + nr] = winner[:]


        #Crossover Gens from 2 Parents
        crossover = range(self.size[1] / 2)
        shuffle(crossover)
        for nr in range(self.size[1] / 4):
            #child = parent2
            #Parents are the winners of the first round (Genetic Selection?)
            parent1 = winners_r1[crossover[nr * 2]][:]
            child = winners_r1[crossover[(nr * 2) + 1]][:]

            #The genetic line that is exchanged in the child parent1
            indx = [int(floor(random()*self.size[0])), int(floor(random()*self.size[0]))]
            indx.sort()
            while indx[0] == indx[1]:
                indx = [int(floor(random()*self.size[0])), int(floor(random()*self.size[0]))]
                indx.sort()
            gens = parent1[indx[0]:indx[1] + 1]

            #Remove the exchanged genes
            for gen in gens:
                child.pop(child.index(gen))

            #Insert the new genes at a random position
            ins_indx = int(floor(random()*self.size[0]))
            new_children = child[0:ins_indx] + gens + child[ins_indx:len(child)]

            #Write the new children in the new population matrix
            for pnr in range(2):
                new_pop[int((pnr + 0.5) * self.size[1] / 2 + nr)] = new_children[:]

        #Mutate the 2nd half of the population matrix
        mutate = range(self.size[1] / 2)
        shuffle(mutate)
        num_mutations = int(round(mutate_rate * self.size[1] / 2))
        for nr in range(num_mutations):
            #The genetic line that is exchanged in the child parent1 ???
            indx = [int(floor(random()*self.size[0])), int(floor(random()*self.size[0]))]
            indx.sort()
            while indx[0] == indx[1]:
                indx = [int(floor(random()*self.size[0])), int(floor(random()*self.size[0]))]
                indx.sort()

            #Zu mutierende Line
            #Line to be mutated ????
            mutline = new_pop[self.size[1] / 2 + mutate[nr]]
            if random() < 0.75: #Gen Abschnitt umdrehen / Turn gene segment
                cut = mutline[indx[0]:indx[1] + 1]
                cut.reverse()
                mutline = mutline[0:indx[0]] + cut + mutline[indx[1] + 1:len(mutline)]
            else: #2 Gene tauschen / 2 Gene exchange
                orgline = mutline[:]
                mutline[indx[0]] = orgline[indx[1]]
                mutline[indx[1]] = orgline[indx[0]]
            new_pop[self.size[1] / 2 + mutate[nr]] = mutline


        #Assign the new population matrix
        self.pop = new_pop

    def __str__(self):
        string = ("\nPopulation size: %i X %i \nMutate rate: %0.2f \nRotation Matrix:\n%s \nPop Matrix:" \
                % (self.size[0], self.size[1], self.mutate_rate, self.rot))

        for line in self.pop:
            string += '\n' + str(line)
        return string

class DistanceMatrixClass:
    """
    DistanceMatrixClass
    """
    def __init__(self, matrix=[]):
        self.matrix = matrix
        self.size = [0, 0]

    def generate_matrix(self, st_end_points):
        """
        generate_matrix()
        """
        x_vals = range(len(st_end_points))
        self.matrix = []
        for nr_y in range(len(st_end_points)):
            for nr_x in range(len(st_end_points)):
                x_vals[nr_x] = st_end_points[nr_y][1].distance(st_end_points[nr_x][0])
            self.matrix.append(copy(x_vals[:]))
        self.size = [len(st_end_points), len(st_end_points)]

    def __str__(self):
        string = ("Distance Matrix; size: %i X %i" % (self.size[0], self.size[1]))
        for line_x in self.matrix:
            string += "\n"
            for x_vals in line_x:
                string += ("%8.2f" % x_vals)
        return string

class FittnessClass:
    def __init__(self, population=[], cur_fittness=[], best_fittness=[], best_route=[]):
        self.population = population
        self.cur_fittness = cur_fittness
        self.best_fittness = best_fittness
        self.best_route = best_route

    def calc_st_fittness(self, matrix, st_pop):
        dis = matrix[st_pop[-1]][st_pop[0]]
        for nr in range(1, len(st_pop)):
            dis += matrix[st_pop[nr - 1]][st_pop[nr]]

        self.best_fittness.append(dis)

    def calc_cur_fittness(self, matrix):
        #logger.debug("Calculating current fittness len(self.population.pop): %s"
        #             %(len(self.population.pop)))
        #logger.debug("Length of self.cur_fittness: %s" %(len(self.cur_fittness)))

        for pop_nr in range(len(self.population.pop)):
            pop = self.population.pop[pop_nr]
            #logger.debug("pop_nr: %s" %pop_nr)
            dis = matrix[pop[-1]][pop[0]]
            for nr in range(1, len(pop)):
                dis += matrix[pop[nr - 1]][pop[nr]]
            self.cur_fittness[pop_nr] = dis

    #2te Möglichkeit die Reihenfolge festzulegen (Korrekturfunktion=Aktiv)
    #Second option set the order (correction function = Active) ???
    def correct_constrain_order(self):
        """FIXME: in order to change the correction to have all ordered shapes
        in begin this might be the best place to change it. Maybe we can also have
        an additional option in the config file?"""

        for pop_nr in range(len(self.population.pop)):
            #Search the current order
            order_index = self.get_pop_index_list(self.population.pop[pop_nr])
            #Momentane Reihenfolge der indexe sortieren
            #Current sort order of the index ???
            order_index.sort()
            #Indices according to correct order
            for ind_nr in range(len(order_index)):
                self.population.pop[pop_nr][order_index[ind_nr]] = self.order[ind_nr]

    def set_startpoint(self):
        """
        set_startpoint()
        """
        n_pts = len(self.population.pop[-1])
        for pop_nr in range(len(self.population.pop)):
            pop = self.population.pop[pop_nr]
            st_pt_nr = pop.index(n_pts - 1)
            #Contour is then in order with the starting point at the beginning
            self.population.pop[pop_nr] = pop[st_pt_nr:n_pts] + pop[0:st_pt_nr]

    def get_pop_index_list(self, pop):
        """
        get_pop_index_list
        """
        pop_index_list = []
        for val_nr in range(len(self.order)):
            pop_index_list.append(pop.index(self.order[val_nr]))
        return pop_index_list

    def select_best_fittness(self):
        """
        select_best_fittness
        """
        self.best_fittness.append(min(self.cur_fittness))
        self.best_route = self.cur_fittness.index(self.best_fittness[-1])


    def __str__(self):
        return ("\nBest Fittness: %s \nBest Route: %s \nBest Pop: %s" \
                % (self.best_fittness[-1], self.best_route, self.population.pop[self.best_route]))

