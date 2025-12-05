import pygame
from player import Player
import neat
import sys
import math
import time
from neat.genome import DefaultGenomeConfig

from concurrent.futures import ThreadPoolExecutor

config_path = "src/config.txt"
config = neat.config.Config(neat.DefaultGenome,neat.DefaultReproduction,neat.DefaultSpeciesSet,neat.DefaultStagnation,config_path)

stats_file = "stats.csv"

# Clearing the stats file
with open(stats_file, 'w') as f:
    f.write("")


# Setting up pygame and window
pygame.init()

clock = pygame.time.Clock()

running = True

playerGroup = pygame.sprite.Group()
Player.containers = playerGroup
#player = Player()

# Attributes of the Best Car at the time of Exit
file = open("src/Best_car.txt",'w')
file.write("Best_fitness: ")
Best_Fitness = 0


Maps = { "Oval" : ["src/assets/imgs/Oval_track.png","src/assets/imgs/Oval_track.png",pygame.Vector2(950,820)],
	  "Triangular" : ["src/assets/imgs/Triangular_track.png","src/assets/imgs/Triangular_track.png",pygame.Vector2(660,880)],
	  "Infinity" : ["src/assets/imgs/Infinity_track.png","src/assets/imgs/Infinity_track.png",pygame.Vector2(550,840)],
      "Endless" : ["src/assets/imgs/Desert_Track_brgd.jpg", "src/assets/imgs/Desert_Track.png", pygame.Vector2(1500, 3275)],
      "F100" : ["src/assets/imgs/F100.png", "src/assets/imgs/F100.png", pygame.Vector2(2000, 450)]
	}

Current_Track = "Oval"

WIDTH = 1280
HEIGHT = 720

CAR_SIZE_X = 60    
CAR_SIZE_Y = 60

BORDER_COLOR = (255, 255, 255, 255) # Color To Crash on Hit
screen = pygame.display.set_mode((WIDTH,HEIGHT))

current_generation = 0 # Generation counter

dt = 0.5

# Constants for training the model

BASE_TIME = 300
MAX_TIME = 3000

LAP_REWARD = 10


def run_simulation(genomes, config):
    
        # Empty Collections For Nets and Cars
        nets = []
        cars = []

        # Initialize PyGame And The Display

        # For All Genomes Passed Create A New Neural Network
        global current_generation
        global Current_Track
        global Best_Fitness

        # Calculating how long to run this generation
        generation_time = min(BASE_TIME + current_generation * 10, MAX_TIME)
        if Current_Track == "Endless" or Current_Track == "F100":
            generation_time = min(BASE_TIME + current_generation * 40, MAX_TIME)


        current_generation += 1

        track_border_path = Maps[Current_Track][1]
        track_image_path = Maps[Current_Track][0]
        start_pos = Maps[Current_Track][2]

        track_border = pygame.image.load(track_border_path)
        track_border_mask = pygame.mask.from_surface(track_border)

        start = pygame.image.load("src/assets/imgs/start.png")
        start_mask = pygame.mask.from_surface(start)

        start_rect = start.get_rect()
        start_rect.right = start_pos.x - 50
        start_rect.centery = start_pos.y


        # Creating cars for this generation
        for i, g in genomes:
            net = neat.nn.FeedForwardNetwork.create(g, config)
            nets.append(net)
            g.fitness = 0
	    	
            cars.append(Player(start_pos.x, start_pos.y, "src/assets/imgs/red-car.png"))

        # Font Settings & Loading Map
        clock = pygame.time.Clock()
        generation_font = pygame.font.SysFont("Arial", 30)
        alive_font = pygame.font.SysFont("Arial", 20)
        
        game_map = pygame.image.load(track_image_path).convert() # Convert Speeds Up A Lot

        if current_generation % 5 == 0:
            index = list(Maps.keys()).index(Current_Track)
            index = (index+1)%len(Maps)
            Current_Track = list(Maps.keys())[index]

        # Simple Counter To Roughly Limit Time
        counter = 0

        while True: 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    file.write(str(Best_Fitness))
                    for i in range(len(genomes)):
                        file.write(str(genomes[i][1]))
                    sys.exit(0)

            # Calculate the action taken by each car using multi-threading
            def calculate_output(net, car):
                 return net.activate(car.get_data())

            outputs = []
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(calculate_output, net, car) for net, car in zip(nets, cars)]
                outputs = [future.result() for future in futures]
            for i, output in enumerate(outputs):
                    cars[i].move(dt, output[0], output[1])
            
            # Check If Car Is Still Alive
            # Increase Fitness If Yes And Break Loop If Not
            still_alive = 0
            best_car : Player = cars[0]
            max_dist = 0.0
            for i, car in enumerate(cars):
                if car.is_alive(track_border_mask):
                    if max_dist < car.dist_travelled:
                        max_dist = car.dist_travelled
                        best_car = car
                        Best_Fitness = max(Best_Fitness,car.get_reward())
                    still_alive += 1
                    car.update(screen, dt, track_border, track_border_mask, start_mask, start_rect.topleft)
                    genomes[i][1].fitness += car.get_reward() + car.lap * LAP_REWARD - car.punish * 10

            counter += 1
            if still_alive == 0 or counter >= generation_time:
                with open(stats_file, 'a') as f:
                    f.write(f"{current_generation},{best_car.dist_travelled/100},{best_car.lap},{still_alive}\n")
                break

            # Drawing the background 
            offset : pygame.Vector2 = pygame.Vector2(0,0)
            offset.x = best_car.rect.centerx - WIDTH//2
            offset.y = best_car.rect.centery - HEIGHT//2

            screen.fill((0,0,0))

            # Draw the track
            screen.blit(game_map, -offset)

            # Draw the lap start marker
            screen.blit(start, start_rect.topleft - offset)

            # Draw All Cars That Are Alive
            for car in cars:
                if car.is_alive(track_border_mask):
                    car.draw(screen, offset)

            # Display Info
            pygame.draw.rect(screen, (255,255,255) ,(0,0,180,100))
            text = generation_font.render("Generation: " + str(current_generation), True, (0,0,0))
            text_rect = text.get_rect()
            text_rect.topleft = (10, 20)
            screen.blit(text, text_rect)

            text = alive_font.render("Still Alive: " + str(still_alive), True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = (60, 70)
            screen.blit(text, text_rect.topleft)

            clock.tick(60)
            pygame.display.flip()
            pygame.display.set_caption(f'Current FPS: {str(clock.get_fps())}')

def manual_play():
    """
    This function is to implement manually playing the game
    """

    # Initialize Pygame and the display
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    track_border_path = Maps[Current_Track][1]
    track_image_path = Maps[Current_Track][0]
    start_pos = Maps[Current_Track][2]
    track = pygame.image.load(track_image_path)
    game_map = pygame.image.load(track_image_path)
    track_border = pygame.image.load(track_border_path)
    track_border_mask = pygame.mask.from_surface(track_border)
    start = pygame.image.load("src/assets/imgs/start.png")
    start_mask = pygame.mask.from_surface(start)
    start_rect = start.get_rect()
    start_rect.right = start_pos.x + + 200
    start_rect.centery = start_pos.y

    # Create a player car object
    player_car = Player(start_pos.x, start_pos.y, "src/assets/imgs/red-car.png")

    # Game loop for human player control
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            accelerate = 0
            steering = 0

            if not player_car.alive:
                pygame.quit()

            # Handle keyboard input for controlling the car
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_w]:
                accelerate = 1
            elif pressed[pygame.K_s]:
                accelerate = -1

            if pressed[pygame.K_a]:
                steering = -1
            elif pressed[pygame.K_d]:
                steering = 1

        # Update the player car
        player_car.move(dt, steering, accelerate)
        player_car.update(screen, dt, track_border, track_border_mask, start_mask, start_rect.topleft)

        # Draw the background
        offset = pygame.Vector2(0, 0)
        offset.x = player_car.rect.centerx - WIDTH // 2
        offset.y = player_car.rect.centery - HEIGHT // 2
        screen.fill((0, 0, 0))
        screen.blit(game_map, -offset)
        screen.blit(start, start_rect.topleft - offset)

        # Draw the player car
        player_car.draw(screen, offset)

        # Display the screen
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    
    human = False

    if human:
        manual_play()
    else:
        # Load Config
        config_path = "src/config.txt"
        config = neat.config.Config(neat.DefaultGenome,
                                    neat.DefaultReproduction,
                                    neat.DefaultSpeciesSet,
                                    neat.DefaultStagnation,
                                    config_path)

        # Create Population And Add Reporters
        population = neat.Population(config)
        population.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        population.add_reporter(stats)
        
        # Run Simulation For A Maximum of 1000 Generations
        population.run(run_simulation, 100)

        # population.reporters.reporters[1].save_genome_fitness()
        population.reporters.reporters[1].save()

