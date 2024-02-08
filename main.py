import sys
import time
import random
import pygame
import cv2 as cv
import mediapipe as mp
from collections import deque

# Inicializuojami Mediapipe ir Pygame elementai
mp_face_mesh = mp.solutions.face_mesh
pygame.init()

# Inicializuojami kiti privalomi elementai/aplinka
VID_CAP = cv.VideoCapture(0)
window_size = (int(VID_CAP.get(cv.CAP_PROP_FRAME_WIDTH)), int(VID_CAP.get(cv.CAP_PROP_FRAME_HEIGHT)))
screen = pygame.display.set_mode(window_size)

# Paukščio inicializavimas
bird_img = pygame.image.load("bird_sprite.png")
bird_img = pygame.transform.scale(bird_img, (bird_img.get_width() // 6, bird_img.get_height() // 6))
bird_frame = bird_img.get_rect(center=(window_size[0] // 6, window_size[1] // 2))

# Vamzdžių inicializavimas
pipe_frames = deque()
pipe_surface = pygame.Surface((50, window_size[1] - 120), pygame.SRCALPHA)
pipe_surface.fill((0, 255, 0))  # Spalvos nustatymas
pipe_starting_template = pipe_surface.get_rect()
pipe_velocity = 5  # Greitis

# Initialize space variable outside the loop
space = 180  # Konstantinis horizontalus tarpas tarp vamzdžių

# Initialize space reset timer
reset_space_timer = time.time()

# Žaidimo ciklas
game_clock = time.time()
stage = 1
pipeSpawnTimer = 0
time_between_pipe_spawn = 40
level = 0
score = 0
didUpdateScore = False
game_is_running = True
s_init = False  # Inicializuojamas kintamasis s_init

# FaceMesh atpažinimas su Mediapipe
with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:
    while True:
        # Tikrinama, ar žaidimas vyksta
        if not game_is_running:
            # Užpildykite ekraną juodu fonu
            screen.fill((0, 0, 0))

            # Pirmos eilutės tekstas
            text_line1 = pygame.font.SysFont("Helvetica Bold.ttf", 64).render('Žaidimas baigtas!', True, (241, 1, 1))
            tr_line1 = text_line1.get_rect()
            tr_line1.center = (window_size[0] / 2, window_size[1] / 2 - 30)

            # Antros eilutės tekstas
            text_line2 = pygame.font.SysFont("Helvetica Bold.ttf", 64).render('Spausk "r" kad žaistum', True, (241, 1, 1))
            tr_line2 = text_line2.get_rect()
            tr_line2.center = (window_size[0] / 2, window_size[1] / 2 + 30)

            # Abi eilutės pridedamos prie ekrano
            screen.blit(text_line1, tr_line1)
            screen.blit(text_line2, tr_line2)

            pygame.display.update()

            # Laukiama, kol paspaudžiamas 'r' mygtukas norint žaisti iš naujo
            replay_wait = True
            while replay_wait:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                        # Nustatomos žaidimo parametrai
                        pipe_frames.clear()
                        pipe_velocity = 5
                        stage = 1
                        score = 0
                        didUpdateScore = False
                        game_is_running = True
                        replay_wait = False
                        reset_space_timer = time.time()  # Nustatomas tarpų reset laikmatis

                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                pygame.time.Clock().tick(30)

        # Gaunamas kadras iš vaizdo kameros
        ret, frame = VID_CAP.read()
        if not ret:
            print("Tuščias kadras, tęsiama...")
            continue

        # Išvalomas ekranas
        screen.fill((125, 220, 232))

        # Atpažįstama veido mesh
        frame.flags.writeable = False
        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = face_mesh.process(frame)
        frame.flags.writeable = True

        # Piešiamas mesh
        if results.multi_face_landmarks and len(results.multi_face_landmarks) > 0:
            marker = results.multi_face_landmarks[0].landmark[94].y
            bird_frame.centery = (marker - 0.5) * 1.5 * window_size[1] + window_size[1] / 2
            if bird_frame.top < 0:
                bird_frame.y = 0
            if bird_frame.bottom > window_size[1]:
                bird_frame.y = window_size[1] - bird_frame.height

        # Atšvęsdinamas kadras, keičiant ašis dėl to, kad OpenCV != Pygame
        frame = cv.flip(frame, 1).swapaxes(0, 1)

        # Atnaujinami vamzdžių padėtys
        for pf in pipe_frames:
            pf[0].x -= pipe_velocity
            pf[1].x -= pipe_velocity

        if len(pipe_frames) > 0 and pipe_frames[0][0].right < 0:
            pipe_frames.popleft()

        # Atnaujinamas ekranas
        pygame.surfarray.blit_array(screen, frame)
        screen.blit(bird_img, bird_frame)

        # Atnaujinami vamzdžiai ir tikrinama rezultatas
        checker = True
        for pf in pipe_frames:
            if pf[0].left <= bird_frame.x <= pf[0].right:
                checker = False
                if not didUpdateScore:
                    score += 1
                    didUpdateScore = True
            pygame.draw.rect(screen, (101, 188, 70), pf[1])  # Viršutinis vamzdis
            pygame.draw.rect(screen, (101, 188, 70), pf[0])  # Apatinis vamzdis
        if checker:
            didUpdateScore = False

        # Etapas, rezultato tekstas
        text = pygame.font.SysFont("Helvetica Bold.ttf", 50).render(f'Lygis: {stage}', True, (0, 0, 1))
        tr = text.get_rect()
        tr.center = (100, 50)
        screen.blit(text, tr)
        text = pygame.font.SysFont("Helvetica Bold.ttf", 50).render(f'Taškai: {score}', True, (0, 0, 1))
        tr = text.get_rect()
        tr.center = (100, 100)
        screen.blit(text, tr)

        # Atnaujinamas ekranas
        pygame.display.flip()

        # Tikrinama, ar paukštis liečiasi su vamzdžiu
        if any([bird_frame.colliderect(pf[0]) or bird_frame.colliderect(pf[1]) for pf in pipe_frames]):
            game_is_running = False

        # Laikas pridėti naujus vamzdžius
        if pipeSpawnTimer == 0:
            gap_height = 200  # Tinkamas tarpas tarp vamzdžių

            top = pipe_starting_template.copy()
            bottom = pipe_starting_template.copy()

            # Nustatomas viršaus vamzdžio pozicija ir aukštis
            top.x, top.y = window_size[0], 0
            top.height = random.randint(50, window_size[1] - gap_height - 50)  # Atsitiktinis vertikalus tarpas

            # Nustatomas apatinio vamzdžio pozicija ir aukštis
            bottom.x, bottom.y = window_size[0], top.height + space
            bottom.height = window_size[1] - bottom.y

            # Tikrinama, ar laikas sukurti naują vamzdį
            if (time.time() - reset_space_timer) >= 1.3:
                pipe_frames.append([top, bottom])
                reset_space_timer = time.time()  # Nustatomas tarpų reset laikmatis

        # Atnaujinamas vamzdžių sukūrimo laikmatis - tampa ciklišku
        pipeSpawnTimer += 1
        if pipeSpawnTimer >= time_between_pipe_spawn:
            pipeSpawnTimer = 0

        # Atnaujinamas etapas
        if score >= stage * 10 and didUpdateScore:
            pipe_velocity *= 1.6  # Padidinamas vamzdžių greitis keičiant lygį
            stage += 1
            didUpdateScore = True
