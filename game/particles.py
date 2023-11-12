import random
from utils.patterns import *


class Particle:
    def __init__(self, x, y):
        self.position = np.array([x, y])
        self.radius = 0
        self.lifetime = 10  # in frames/game steps
        self.velocity = np.array([random.randint(-3, 3), random.randint(-3, 3)])

    def update(self):
        self.position += self.velocity
        self.lifetime -= 1

    def render(self, win):
        pygame.draw.circle(win, pygame.Color('White'), self.position, int(self.radius))


class ParticleGroup:
    def __init__(self):
        self.particles = []

    def emit(self, win):
        self.delete_particles()
        for particle in self.particles:
            particle.update()
            particle.render(win)

    def add_particle(self, x, y):
        particle = Particle(x, y)
        self.particles.append(particle)

    def delete_particles(self):  # deletes particles that have passed their lifetime
        self.particles = [particle for particle in self.particles if particle.lifetime >= 0]
