import pygame
import neat
import time
import os
import random
import math
import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
from statistics import mean

pygame.font.init()

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird2.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird3.png")))]
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 30)

##################################
generation = 0
##################################
DISCRETE_RECOMBINATION = True
INTERMEDIATE_RECOMBINATION = False
LINE_RECOMBINATION = False
USING_MEAN = False
##################################


class Bird:

    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5
    W1 = 0
    W2 = 0
    W3 = 0
    B = 0
    score = 0

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.img_count = 0
        self.jump_point = self.y
        self.img = self.IMGS[0]
        self.score = 0

    def set_nn_values(self, w1, w2, w3, b):
        self.W1 = w1
        self.W2 = w2
        self.W3 = w3
        self.B = b

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.jump_point = self.y

    def move(self):
        self.tick_count += 1
        d = self.vel*self.tick_count + 0.5 * 3 * self.tick_count ** 2  # g is 3 here

        if d >= 16:
            d = 16

        if d < 0:
            d -= 2

        self.y = self.y + d

        if d < 0 or self.y < self.jump_point + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self. img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4+1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

    def set_score(self, score):
        self.score = score

    def reset(self,x,y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.img_count = 0
        self.jump_point = self.y
        self.img = self.IMGS[0]


class Pipe:
    GAP = 180
    VEL = 5

    def __init__(self,x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        self.GAP = random.randint(160, 210)
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True

        return False


class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self,y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH <0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score):
    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)
    for bird in birds:
        bird.draw(win)
    base.draw(win)

    score_text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(score_text, (SCREEN_WIDTH - 10 - score_text.get_width(), 10))

    bird_text = STAT_FONT.render("Birds: " + str(len(birds)), 1, (255, 255, 255))
    win.blit(bird_text, (SCREEN_WIDTH - 10 - bird_text.get_width(), 10+score_text.get_height()))

    gen_text = STAT_FONT.render("Gen: " + str(generation), 1, (255, 255, 255))
    win.blit(gen_text, (SCREEN_WIDTH - 10 - gen_text.get_width(), 10 + score_text.get_height() + gen_text.get_height()))

    pygame.display.update()


def make_bird_jump(bird, pipes):
    """I assume that only two pipes in the screen at a given time"""
    index = 0
    if len(pipes) > 1 and bird.x > (pipes[index].x + pipes[index].PIPE_TOP.get_width()):
        index = 1
    value = bird.W1*(pipes[index].x - bird.x) + bird.W2*(pipes[index].bottom - bird.y) + bird.W3*(bird.y - pipes[index].height) + bird.B
    if math.tanh(value) > 0:
        bird.jump()


def evaluate_population(birds):

    dead_birds = []

    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    #clock = pygame.time.Clock()
    score = 0
    
    run = True
    while run:
        #clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        add_pipe = False
        rem = []
        for pipe in pipes:
            for bird in birds:
                if pipe.collide(bird):
                    bird.set_score(score)
                    dead_birds.append(bird)
                    birds.remove(bird)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for bird in birds:
            bird.move()
            if (bird.y + bird.img.get_height() >= 730) or (bird.y < 0):
                bird.set_score(score)
                dead_birds.append(bird)
                birds.remove(bird)
            make_bird_jump(bird, pipes)

        base.move()
        draw_window(win, birds, pipes, base, score)
        if len(birds) == 0 or score >= 100:
            run = False

    return dead_birds + birds


def create_new_generation(size):
    birds = []
    for i in range(size):
        bird = Bird(230, 350)
        bird.set_nn_values(random.randint(-100, 100), random.randint(-100, 100), random.randint(-100, 100), random.randint(-100, 100))
        birds.append(bird)
    return birds


def select_candidates(birds,size):
    birds.sort(key=lambda x: x.score, reverse=True)
    return birds[0:size]


def crossover(bird1,bird2):
    new_bird = Bird(230,350)
    values1 = [bird1.W1, bird1.W2, bird1.W3, bird1.B]
    values2 = [bird2.W1, bird2.W2, bird2.W3, bird2.B]

    if USING_MEAN:
        new_W1 = (values1[0] + values2[0])/2
        new_W2 = (values1[1] + values2[1])/2
        new_W3 = (values1[2] + values2[2])/2
        new_B = (values1[3] + values2[3])/2
        new_bird.set_nn_values(new_W1,new_W2,new_W3,new_B)
    elif LINE_RECOMBINATION:
        p_value = random.random()
        new_W1 = values1[0]*p_value + values2[0]*(1-p_value)
        new_W2 = values1[1]*p_value + values2[1]*(1-p_value)
        new_W3 = values1[2]*p_value + values2[2]*(1-p_value)
        new_B = values1[3]*p_value + values2[3]*(1-p_value)
        new_bird.set_nn_values(new_W1, new_W2, new_W3, new_B)
    elif INTERMEDIATE_RECOMBINATION:
        p_value = random.random()
        new_W1 = values1[0] * p_value + values2[0] * (1 - p_value)
        p_value = random.random()
        new_W2 = values1[1] * p_value + values2[1] * (1 - p_value)
        p_value = random.random()
        new_W3 = values1[2] * p_value + values2[2] * (1 - p_value)
        p_value = random.random()
        new_B = values1[3] * p_value + values2[3] * (1 - p_value)
        new_bird.set_nn_values(new_W1, new_W2, new_W3, new_B)
    elif DISCRETE_RECOMBINATION:
        p_value = random.random()
        new_W1 = values1[0] if p_value > 0.5 else values2[0]
        p_value = random.random()
        new_W2 = values1[1] if p_value > 0.5 else values2[1]
        p_value = random.random()
        new_W3 = values1[2] if p_value > 0.5 else values2[2]
        p_value = random.random()
        new_B = values1[3] if p_value > 0.5 else values2[3]
        new_bird.set_nn_values(new_W1, new_W2, new_W3, new_B)
    return new_bird


def mutation(bird):

    values = [bird.W1, bird.W2, bird.W3, bird.B]
    change_to = random.choice(range(4))
    values[change_to] = random.randint(-100, 100)
    bird.W1 = values[0]
    bird.W2 = values[1]
    bird.W3 = values[2]
    bird.B = values[3]
    return bird


def next_generation(parent_birds, size, mutation_p):
    new_population = parent_birds
    while len(new_population) < size:
        if random.randint(1, 100) > mutation_p:
            # do crossover
            member1 = random.choice(new_population)
            member2 = random.choice(new_population)
            new_member = crossover(member1, member2)
            new_population.append(new_member)
        else:
            # do mutation
            member = random.choice(new_population)
            new_member = mutation(member)
            new_population.append(new_member)
    for member in new_population:
        member.reset(230,350)
    return new_population


def controller():

    max_score = []
    average_score = []
    global generation
    birds = create_new_generation(100)

    for i in range(20):
        dead_birds = evaluate_population(birds)
        average_score.append(mean([i.score for i in dead_birds]))
        next_gen_parents = select_candidates(dead_birds, 50)
        print(next_gen_parents[0].W1, next_gen_parents[0].W2, next_gen_parents[0].W3, next_gen_parents[0].B)
        max_score.append(next_gen_parents[0].score)
        birds = next_generation(next_gen_parents, 100, 10)
        generation += 1

    plt.plot(max_score)
    # naming the x axis
    plt.xlabel("generation")
    # naming the y axis
    plt.ylabel("max_score")
    plt.title('Max score in each generation')
    plt.show()

    fig = plt.figure()

    plt.plot(average_score)
    # naming the x axis
    plt.xlabel("generation")
    # naming the y axis
    plt.ylabel("average score")
    plt.title('Average score in each generation')
    plt.show()

controller()
