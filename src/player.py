import pygame
from math import sin, radians, degrees, copysign
import math
from pygame.math import Vector2

CAR_SIZE_X = 60    
CAR_SIZE_Y = 60

class Player(pygame.sprite.Sprite):

    def __init__(self, x, y, image, angle=0.0, length=4, max_steering=1, max_acceleration=1):
        pygame.sprite.Sprite.__init__(self, self.containers)

        # Assigning all the player variable and initial setup
        self.image = pygame.image.load(image)
        self.image = pygame.transform.scale(self.image, (int(self.image.get_width() * 0.2), 
                                                        int(self.image.get_height() * 0.2)))
        self.position = Vector2(x, y)
        self.velocity = Vector2(0.0, 0.0)
        self.angle = angle
        self.length = length
        self.max_acceleration = max_acceleration
        self.max_steering = max_steering
        self.max_velocity = 30
        self.brake_deceleration = 10
        self.free_deceleration = 0.5
        self.acceleration = 0.0
        self.steering = 0.0                                                        
        self.speed = 5
        self.lap = 0
        self.rotate_speed = 0.1
        self.alive = True
        self.dist_travelled = 0 

        self.rotated_image = self.image

        self.bounce_force = 0.5

        self.rect = pygame.Rect(x, y, self.image.get_width(), self.image.get_height())

        # RayCast
        self.raycasts = []
        self.distance = []

        self.cooldown = 0

        self.last_steer = 0.0
        self.punish = 0

    def cast_rays(self, border : pygame.image, offset_angle = 0):
        length = 0

        x = int(self.rect.center[0] + math.cos(math.radians(360 - (self.angle + offset_angle))) * length)
        y = int(self.rect.center[1] + math.sin(math.radians(360 - (self.angle + offset_angle))) * length)

        # While We Don't Hit BORDER_COLOR AND length < 300 (just a max) -> go further and further
        while border.get_at((x, y)).a == 0 and length < 300:
            length = length + 1
            x = int(self.rect.center[0] + math.cos(math.radians(360 - (self.angle + offset_angle))) * length)
            y = int(self.rect.center[1] + math.sin(math.radians(360 - (self.angle + offset_angle))) * length)

        # Calculate Distance To Border And Append To Radars List
        dist = int(math.sqrt(math.pow(x - self.rect.center[0], 2) + math.pow(y - self.rect.center[1], 2)))
        self.raycasts.append(((x,y),dist))
        self.distance.append(dist)
        """if len(self.distance) == 5:
            self.final = self.distance
        else:
            self.final = []
        print(self.final)
        print("len is 5")"""
    
    def draw(self,screen, offset : Vector2):
        #self.draw_radar(screen, offset)                    #OPTIONAL TO DISPLAY SENSORS
        screen.blit(self.rotated_image, self.position - offset) # Draw Sprite
        

    def draw_radar(self, screen, offset):
        # Optionally Draw All Sensors / Radars
        for radar in self.raycasts:
            position = radar[0]
            pygame.draw.line(screen, (0, 0, 255), self.rect.center, position, 1)
            pygame.draw.circle(screen, (0, 0, 255), position, 5)

    def update(self, screen,dt, track_border : pygame.image, track_border_mask : pygame.mask, start_mask, offset : Vector2):
        # This function is called once a frame

        self.cooldown = max(0, self.cooldown - 1)

        self.raycasts.clear()
        self.distance.clear()

        for angle_offset in range(-90, 120, 45):
            self.cast_rays(track_border, offset_angle = angle_offset)
        

        self.velocity += (self.acceleration * dt, 0)
        self.velocity.x = max(-self.max_velocity, min(self.velocity.x, self.max_velocity))

        if self.steering:
            turning_radius = self.length / sin(radians(self.steering))
            angular_velocity = self.velocity.x / turning_radius
        else:
            angular_velocity = 0    
            
        # Calculate distance travelled
        self.dist_travelled += self.get_magnitude(self.velocity)
        # Drawing the player
        rotated = pygame.transform.rotate(self.image, self.angle)
        self.rotated_image = rotated
        rect = rotated.get_rect(center=self.image.get_rect(topleft = self.position).center)

        self.position += self.velocity.rotate(-self.angle) * dt
        self.angle += degrees(angular_velocity) * dt
        self.rect = rect
	
        if self.collide(track_border_mask):
            self.alive = False
        

        start_collide_poi = self.collide(start_mask, *offset)
        if start_collide_poi != None:
            if self.cooldown == 0:
                if start_collide_poi[0] == 0:
                    self.lap += 1
                    self.cooldown = 150
                else:
                    self.lap -= 1
                    self.cooldown = 150

    def move(self, dt, steering, accelerate):
        pressed = pygame.key.get_pressed()

        if accelerate > 0:
            if self.velocity.x < 0:
                self.acceleration = self.brake_deceleration
            else:
                self.acceleration += accelerate * dt
        elif accelerate < 0:
            if self.velocity.x > 0:
                self.acceleration = -self.brake_deceleration
            else:
                self.acceleration += accelerate * dt
                #self.acceleration = 0
        elif pressed[pygame.K_SPACE]:
            if abs(self.velocity.x) > dt * self.brake_deceleration:
                self.acceleration = -copysign(self.brake_deceleration, self.velocity.x)
            else:
                self.acceleration = -self.velocity.x / dt
        else:
            if abs(self.velocity.x) > dt * self.free_deceleration:
                self.acceleration = -copysign(self.free_deceleration, self.velocity.x)
            else:
                if dt != 0:
                    self.acceleration = -self.velocity.x / dt
        self.acceleration = max(-self.max_acceleration, min(self.acceleration, self.max_acceleration))
#loops
        # TODO: Replace with one equation
        if abs(self.last_steer - steering) > 0.2:
            self.punish = 1
        else:
            self.punish = 0

        if steering > 0:
            self.steering -= self.rotate_speed * dt * steering * 10
        elif steering < 0:
            self.steering += self.rotate_speed * dt * abs(steering) * 10
        else:
            self.steering = 0
        self.steering = max(-self.max_steering, min(self.steering, self.max_steering))    
        self.last_steer = steering


    def collide(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.rotated_image)
        offset = (int(self.position.x - x), int(self.position.y - y))
        poi = mask.overlap(car_mask, offset)
        return poi
    

    def reset(self):
        self.velocity = Vector2(0.0, 0.0)
        self.acceleration = 0.0
        self.steering = 0.0
        self.angle = 0.0

    def get_data(self):
        speed = self.get_magnitude(self.velocity)/self.max_velocity     # Divide by max vel to normalize the input from 0 to 1
        return_values = [0, 0, 0, 0, 0, speed]
        for i, radar in enumerate(self.distance):
            return_values[i] = int(self.distance[1] / 30)  # Divide by 30 to normalize

        return return_values
    
    
    def is_alive(self,track_border_mask : pygame.mask):
        if self.collide(track_border_mask):
            self.alive = False
        return self.alive
    

    def get_reward(self):
        return max(self.velocity.x, self.velocity.y) / 10
    

    def get_magnitude(self, vector : Vector2):
        return (vector.x**2 + vector.y**2)**0.5 
    




