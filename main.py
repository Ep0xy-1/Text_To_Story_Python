import tkinter as tk
from tkinter import messagebox
import json
import os
from itertools import cycle
import threading
import random
import time
 
# Optional music
MUSIC_ENABLED = True
MUSIC_VOLUME = 0.35
ASSET_PATH = "assets"
MUSIC_FILE = os.path.join(ASSET_PATH, "background.mp3")

# Try to init pygame (non-fatal if missing)
try:
    import pygame
    pygame.mixer.init()
    PYGAME_OK = True
except Exception:
    PYGAME_OK = False
    MUSIC_ENABLED = False

# =================== WINDOW / THEME ===================
TITLE = "Even if the Stars Fall"
SAVE_FILE = "savefile.json"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 720

# CRT palette
BG_BASE = "#000000"
BG_PANEL = "#021702"        # deep green-black
FG_TEXT = "#00ff66"         # phosphor green
FG_DIM = "#1cff9e"          # softer highlight
FG_ACCENT = "#00ffa6"
BTN_BG = "#021c0a"
BTN_BG_ACTIVE = "#00ff66"
BTN_FG = "#00ff66"
BTN_FG_ACTIVE = "#001b0a"
FRAME_BORDER = "#013d1c"

# =================== GAME STATE ===================
game_state = {
    "current_scene": "intro_room",
    "inventory": [],
    "flags": {},
    "encountered": []
}

# =================== STORY: richer branching ===================
# Every scene text is written as multi-line (list) so the typewriter can line-break naturally.
# Each option: (label, next_scene)
# We include explicit "you are doing..." snippets in each scene to satisfy the request.

scenes = {
    "intro_room": {
        "text": [
            ">> EVEN IF THE STARS FALL <<",
            "",
            "Summer, 1987. The fan hums. Posters peel from the wall like tired constellations.",
            "Leah's note sits on your desk: 'Midnight. The cliff. I need to tell you something.'",
            "Your parents grounded you, but the window is cracked open—",
            "and your heart won't sit still.",
            "",
            "You grip your sneakers. The house ticks. You listen to your own courage."
        ],
        "options": [
            ("Climb out the window slowly, breathing with the creaks.", "yard_down_silent"),
            ("Take the hallway and front door—faster, riskier.", "hallway_start"),
            ("Text Leah from your brick of a phone: 'Running late.'", "phone_ping"),
        ]
    },

    # Hallway route
    "hallway_start": {
        "text": [
            "You inch into the hallway, feet grazing old wood. Every board is an informant.",
            "A strip of moonlight divides the floor like a promise. You follow it.",
            "Your breath becomes a metronome. Doorknobs glint. The front door waits."
        ],
        "options": [
            ("Pause to listen at your parents’ door.", "hallway_listen"),
            ("Risk it—unlatch the front door quickly.", "frontdoor_rush"),
            ("Detour through the kitchen for a flashlight.", "kitchen_flashlight"),
        ]
    },
    "hallway_listen": {
        "text": [
            "You lean to the door. Dad snores in triplets, Mom sighs on the off-beat.",
            "They're asleep. For now.",
            "Your pulse writes a drum solo in your wrists."
        ],
        "options": [
            ("Slowly unlatch the front door, counting to eight between each move.", "frontdoor_silent"),
            ("Backtrack to your room and try the window instead.", "yard_upback")
        ]
    },
    "frontdoor_silent": {
        "text": [
            "You count: one… two… three…",
            "Click. The latch yields like a secret shaking your hand.",
            "Night sweeps in—humid, sweet, electric.",
            "You slip outside; the porch light stays dead. Luck is with you."
        ],
        "options": [
            ("Cut across the neighbor’s hedges to the forest path.", "street_hedge_sneak"),
            ("Stick to the roadlights; stay visible, stay steady.", "street_lamps")
        ]
    },
    "frontdoor_rush": {
        "text": [
            "You yank the door. The hinge screams.",
            "A lamp flares behind you. Dad’s voice, a thunderclap:",
            "“Where do you think you’re going?”",
            "You bolt—down the porch steps, into the humid dark, regret snapping at your heels."
        ],
        "options": [
            ("Sprint through back alleys to shake him.", "alley_sprint"),
            ("Hide behind the trash bins and wait for silence.", "alley_hide")
        ]
    },
    "kitchen_flashlight": {
        "text": [
            "The fridge hum is an ocean. A flashlight waits in the junk drawer, like buried treasure.",
            "You take it and cradle its cold weight. A little cone of bravery.",
            "But the drawer thunks on the close. You freeze."
        ],
        "options": [
            ("Press on—front door silently this time.", "frontdoor_silent"),
            ("Back to your room; go for the window.", "yard_upback")
        ]
    },

    # Window route
    "yard_upback": {
        "text": [
            "You return to your room, window gaping like a portal.",
            "The night calls your name in moth-wing syllables.",
            "You plant a foot on the sill, tasting the fall."
        ],
        "options": [
            ("Lower yourself by the vines, slow as a prayer.", "yard_down_silent"),
            ("Drop to the grass and roll—fast and loud.", "yard_down_loud")
        ]
    },
    "yard_down_silent": {
        "text": [
            "Your fingers find ivy like a ladder stitched by the moon.",
            "You descend. Every inch bargains with gravity.",
            "Your sneakers kiss the grass. The dog doesn't bark. The world exhales."
        ],
        "options": [
            ("Cut through the fence gap into the forest shortcut.", "forest_edge"),
            ("Circle around to the street and keep a casual pace.", "street_lamps")
        ]
    },
    "yard_down_loud": {
        "text": [
            "You drop. The lawn coughs under you.",
            "A chain rattles—neighbor's dog erupts.",
            "Bedroom lights awake like angry stars."
        ],
        "options": [
            ("Dash through the side gate into the forest path.", "forest_edge_chased"),
            ("Hop fences through backyards until the road.", "alley_sprint")
        ]
    },

    # Street choices
    "street_lamps": {
        "text": [
            "Sodium lamps draw halos on wet asphalt.",
            "Your shadow paces you—taller, braver.",
            "You pass the closed diner; a jukebox mourns behind glass."
        ],
        "options": [
            ("Take the coastal road; longer, safer.", "coastal_walk"),
            ("Slip into the forest trail by the billboard; shorter, darker.", "forest_edge"),
            ("Call Leah from the payphone outside the diner.", "payphone_call")
        ]
    },
    "street_hedge_sneak": {
        "text": [
            "You slide along hedges, leaves brushing your jacket like whispered warnings.",
            "A sensor light yawns on. You freeze, one with the green.",
            "The light blinks off. You move again, a rumor crossing town."
        ],
        "options": [
            ("Cut into the forest trail gate.", "forest_edge"),
            ("Keep hedging until you hit the old rail crossing.", "rail_crossing")
        ]
    },

    # Forest
    "forest_edge": {
        "text": [
            "The forest swallows you with damp breath and resin dreams.",
            "Crickets keep time; your flashlight pries open the dark.",
            "Leah’s name sits on your tongue, a vow you chew to stay brave."
        ],
        "options": [
            ("Follow the creek by sound—water never lies.", "forest_creek"),
            ("Take the ridge trail; see the town lights from above.", "forest_ridge"),
            ("Pocket a smooth stone—lucky charm.", "forest_stone_take")
        ]
    },
    "forest_edge_chased": {
        "text": [
            "You crash into the trees, branches snatching at your sleeves.",
            "Behind you, distant shouting dissolves into the cricket-hum.",
            "You taste metal and adrenaline; the path forks."
        ],
        "options": [
            ("Duck underbrush and parallel the fence line.", "forest_fence"),
            ("Wade the shallow creek to cover your tracks.", "forest_creek")
        ]
    },
    "forest_stone_take": {
        "text": [
            "You crouch. Your palm finds a cool oval stone.",
            "It fits your hand like it was waiting.",
            "You pocket it. For luck. For her."
        ],
        "options": [
            ("Head up the ridge to move faster.", "forest_ridge"),
            ("Stick to the creek’s whispering path.", "forest_creek")
        ]
    },
    "forest_creek": {
        "text": [
            "Water threads the dark with silver noise.",
            "You hop stones, splash, and keep the cliff in your mind like a compass.",
            "A figure stands ahead—only a stump. Your laugh dies in your throat."
        ],
        "options": [
            ("Call softly: 'Leah?'", "forest_call"),
            ("Kill the flashlight and move by starlight.", "forest_starlight")
        ]
    },
    "forest_ridge": {
        "text": [
            "You climb until the town becomes a jewelry box below.",
            "A breeze combs your hair; the pines answer in barcode whispers.",
            "You see the coastline curve like a smile you haven't earned yet."
        ],
        "options": [
            ("Jog the ridge trail toward the cliff overlook.", "overlook_approach"),
            ("Take the deer path shortcut, risky but quick.", "deer_path")
        ]
    },
    "forest_fence": {
        "text": [
            "Chain-link gleams; you follow it like a silver river.",
            "An opening yawns where kids snuck through in brighter days.",
            "Beyond it: the service road to the cliffs."
        ],
        "options": [
            ("Slip through the gap and run the service road.", "service_road"),
            ("Double back to throw off anyone trailing you.", "forest_edge")
        ]
    },
    "forest_call": {
        "text": [
            "'Leah?' you breathe.",
            "Crickets pause—then resume, embarrassed.",
            "No answer. Only the creek clapping small hands around stones."
        ],
        "options": [
            ("Keep calling, louder this time.", "forest_call_loud"),
            ("Move, quietly—save the words for when she’s real.", "forest_starlight")
        ]
    },
    "forest_call_loud": {
        "text": [
            "'LEAH!' echoes and returns as a stranger.",
            "A porch in the distance spits a light on. A dog considers you.",
            "You duck, cheeks hot in the dark."
        ],
        "options": [
            ("Rush the trail; embarrassment is fuel.", "overlook_approach"),
            ("Hide and listen until the world forgets you.", "forest_listen_hide")
        ]
    },
    "forest_starlight": {
        "text": [
            "You click the light off. The dark blooms.",
            "Starlight drips through needles and paints your bones.",
            "Your feet learn the path by heart you didn’t know you had."
        ],
        "options": [
            ("Keep low and swift toward the overlook.", "overlook_approach"),
            ("Veer to the service road for speed.", "service_road")
        ]
    },
    "forest_listen_hide": {
        "text": [
            "You suck in the night and become furniture.",
            "An owl writes a circle in the air. The dog grows bored.",
            "Time loosens; you tighten your laces."
        ],
        "options": [
            ("Proceed, careful and cool.", "overlook_approach"),
            ("Text Leah: 'Almost there. Don’t go.'", "phone_ping_forest")
        ]
    },

    # Alternative paths to cliff
    "service_road": {
        "text": [
            "Gravel crunches—a sound you hope is smaller than it is.",
            "A maintenance sign leans like a drunk sentinel.",
            "Ahead, the cliff path breaks from the road like a vein to a heart."
        ],
        "options": [
            ("Take the cliff path. No more detours.", "cliff_gate"),
            ("Check your pockets—inventory matters tonight.", "inv_check_road")
        ]
    },
    "inv_check_road": {
        "text": [
            "You pat yourself down. Phone. Lucky stone. Keys (stolen back).",
            "Courage (in fragments).",
            "You nod to nobody. You are, improbably, enough."
        ],
        "options": [
            ("Step onto the cliff path.", "cliff_gate")
        ]
    },

    # Coastal and rail
    "coastal_walk": {
        "text": [
            "The ocean keeps a secret rhythm. You match it.",
            "Streetlights smear on the wet road like melted limes.",
            "Somewhere a radio begs, 'Don’t you (forget about me)'."
        ],
        "options": [
            ("Cut inland at the lifeguard station toward the cliff.", "cliff_gate"),
            ("Stop; send Leah a voice message.", "payphone_voice")
        ]
    },
    "rail_crossing": {
        "text": [
            "The rails hum with the memory of trains.",
            "You balance on a rail, arms out; night makes you a tightrope saint.",
            "A light in the distance—just a farmhouse changing its mind."
        ],
        "options": [
            ("Follow the tracks until the cliff trail.", "cliff_gate"),
            ("Head down to the beach stairs, climb up by the rocks.", "beach_rocks")
        ]
    },
    "beach_rocks": {
        "text": [
            "Waves flick coins of foam at your shoes.",
            "You climb, knuckles chalked by salt.",
            "The cliff is a dark shoulder, waiting to carry your future."
        ],
        "options": [
            ("Haul yourself up the last ledge.", "cliff_gate")
        ]
    },

    # Phone beats
    "phone_ping": {
        "text": [
            "You thumb a message: 'Running late. Please wait.'",
            "Three dots blink; then vanish; then a single line:",
            "'Hurry. I’m scared.'"
        ],
        "options": [
            ("No more delays—take the window.", "yard_upback"),
            ("Take the hallway, but slower this time.", "hallway_start")
        ]
    },
    "phone_ping_forest": {
        "text": [
            "You type in the dark. Your thumbs are fireflies.",
            "'Almost there. Don’t go.'",
            "No reply—only the creek's applause."
        ],
        "options": [
            ("Move. She’s either there or needs you more than your words do.", "overlook_approach")
        ]
    },
    "payphone_call": {
        "text": [
            "You feed a coin to the chrome throat.",
            "It rings—one, two, three—",
            "Her voice: 'Are you safe?' Breath caught in a paper cup."
        ],
        "options": [
            ("'I’m coming. Don’t hang up until I reach the forest gate.'", "payphone_walktalk"),
            ("'Meet me halfway by the overlook. Please.'", "overlook_early")
        ]
    },
    "payphone_walktalk": {
        "text": [
            "You walk and talk; your voices braid across the night.",
            "She’s quiet, which is another kind of loud.",
            "'I just need to say this while the stars are still listening,' she whispers."
        ],
        "options": [
            ("'Say it when I’m there. I want your eyes when you do.'", "overlook_approach"),
            ("'Say it now. I need a reason to run faster.'", "confess_phone_now")
        ]
    },
    "confess_phone_now": {
        "text": [
            "A pause. Then a soft meteor:",
            "'I love you.'",
            "The word burns a hole in every doubt you kept."
        ],
        "options": [
            ("'I love you too. Hold on.' (you run harder)", "overlook_approach"),
            ("Silence; let the word echo you forward.", "forest_starlight")
        ]
    },
    "payphone_voice": {
        "text": [
            "You record: 'Hey. I’m on my way. Don’t be scared. If the stars fall, I’ll hold them up.'",
            "You send it, pocket the phone, and face the wind as if it owes you answers."
        ],
        "options": [
            ("Go inland to the cliff path.", "cliff_gate")
        ]
    },

    # Alley outcomes
    "alley_sprint": {
        "text": [
            "You tear through alleys; windows are quicksilver eyes.",
            "Your lungs bargain with you. You don’t listen.",
            "A fence rises; you vault it and land in a hush of leaves."
        ],
        "options": [
            ("Cut into forest and keep low.", "forest_edge_chased"),
            ("Head for the service road; straight line, no poetry.", "service_road")
        ]
    },
    "alley_hide": {
        "text": [
            "You collapse behind bins scented with a thousand sins.",
            "Footsteps. Porch light. A question asked to no one.",
            "The night develops you like a photograph; you emerge."
        ],
        "options": [
            ("Backyards to the forest trail.", "forest_edge"),
            ("Side streets to the coastal walk.", "coastal_walk")
        ]
    },

    # Approaching the meeting
    "overlook_early": {
        "text": [
            "You reach the overlook early; the town glitters like a spilled cassette tape.",
            "A lone figure—just a drift of mist. You’re alone with your rehearsal."
        ],
        "options": [
            ("Wait, hands warming each other, counting satellites.", "wait_alone"),
            ("Leave a note wedged under the bench: 'I’m here.'", "leave_note")
        ]
    },
    "wait_alone": {
        "text": [
            "Minutes behave badly. Your breath fogs; hope doesn’t.",
            "Far below, the sea eats stars and asks for seconds.",
            "A crunch of gravel behind you—"
        ],
        "options": [
            ("Turn, smiling even if it's no one.", "meet_at_last"),
            ("Stay still; make them say your name first.", "meet_at_last_shy")
        ]
    },
    "leave_note": {
        "text": [
            "You write in shaky neon: 'I’m here. Don’t be afraid.'",
            "The note flutters as if trying to fly to her.",
            "You step back—foot on gravel—another pair of steps answer."
        ],
        "options": [
            ("Call softly: 'Leah?'", "meet_at_last"),
            ("Stay silent; offer your hand into the dark.", "meet_at_last_shy")
        ]
    },

    # Final approach common node
    "overlook_approach": {
        "text": [
            "Through trees that remember you as a child, you break into the clearing.",
            "The cliff is a black altar; the sea, a congregation that never sits.",
            "A silhouette stands at the edge, hair written by wind."
        ],
        "options": [
            ("Say her name like a secret that finally grew wings.", "meet_at_last"),
            ("Walk beside her and let the silence speak first.", "meet_at_last_shy")
        ]
    },
    "cliff_gate": {
        "text": [
            "A wire gate moans like an old song. You slip through.",
            "The path narrows, the world widens.",
            "Every step says: this is what choosing feels like."
        ],
        "options": [
            ("Jog the last bend; you need to see her now.", "overlook_approach"),
            ("Slow down; memorize the moment you’re walking into.", "overlook_approach")
        ]
    },

    # Meetings and endings
    "meet_at_last": {
        "text": [
            "'Leah.'",
            "She turns. Starlight builds a home in her eyes.",
            "'I thought you wouldn’t come,' she says, laughing like she just survived a storm.",
            "You’re close enough to count the brave freckles."
        ],
        "options": [
            ("Tell her the truth: 'I’d cross the town, the forest, the ocean—just to hear you say my name.'", "ending_starbound"),
            ("Ask what scared her tonight; listen like it’s a language.", "ending_listen"),
            ("Hold out the lucky stone. 'For you. For us.'", "ending_token")
        ]
    },
    "meet_at_last_shy": {
        "text": [
            "You stand beside her; the sea translates the sky.",
            "She threads her fingers with yours—no speech required.",
            "Some silences are symphonies."
        ],
        "options": [
            ("Whisper: 'If the stars fall, we’ll make wishes from the pieces.'", "ending_silent"),
            ("Finally look her in the eyes and say what you practiced.", "ending_starbound")
        ]
    },

    # Endings (multiple)
    "ending_starbound": {
        "text": [
            "Her smile is the exact temperature of tomorrow.",
            "You kiss. Time stops filing paperwork and takes the night off.",
            "",
            ">>> ENDING – Starbound Love",
            "Even if the stars fall, we'll wear them as crowns."
        ],
        "options": []
    },
    "ending_listen": {
        "text": [
            "She talks—about fear, about futures with missing maps.",
            "You listen until fear has fewer teeth.",
            "When she’s done, she leans on you like a doorway she can trust.",
            "",
            ">>> ENDING – The Listener",
            "Sometimes love is an ear offered to the dark."
        ],
        "options": []
    },
    "ending_token": {
        "text": [
            "You press the stone into her palm.",
            "'It’s warm,' she says. 'Must be from your heart.'",
            "You both laugh at how corny that is, which is how you know it’s true.",
            "",
            ">>> ENDING – Token Against Gravity",
            "Two small bodies, one enormous sky."
        ],
        "options": []
    },
    "ending_silent": {
        "text": [
            "No big speech. No fireworks.",
            "Just two hands and a night that finally forgives you.",
            "",
            ">>> ENDING – Silent Devotion",
            "The sea keeps your secret and calls it music."
        ],
        "options": []
    },

    # Failure / caught
    "caught_parent": {
        "text": [
            "A hand clamps your shoulder. The porch light is a confession booth.",
            "Dad’s disappointment is heavier than any door.",
            "You’re escorted back inside; the night keeps going without you."
        ],
        "options": []
    }
}

# ============== SAVE / LOAD ==============
def save_game():
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(game_state, f)
    except Exception as e:
        print("Save error:", e)

def load_game():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                game_state.update(data)
            return True
        except Exception as e:
            print("Load error:", e)
    return False

# ============== UI / ENGINE ==============
class App:
    def __init__(self, root):
        self.root = root
        self.root.title(TITLE)
        self.fullscreen = False

        # Base window
        self.root.configure(bg=BG_BASE)
        self.center_window()

        # Scanline canvas (on top)
        self.scan_canvas = tk.Canvas(self.root, bg=BG_BASE, highlightthickness=0)
        self.scan_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.scanlines = []
        self._build_scanlines()

        # Main layout: left text + right choices
        self.left = tk.Frame(self.root, bg=BG_PANEL, bd=6, relief="ridge", highlightbackground=FRAME_BORDER, highlightcolor=FRAME_BORDER, highlightthickness=2)
        self.left.place(relx=0.04, rely=0.16, width=680, height=480)

        self.right = tk.Frame(self.root, bg=BG_PANEL, bd=6, relief="ridge", highlightbackground=FRAME_BORDER, highlightcolor=FRAME_BORDER, highlightthickness=2)
        self.right.place(relx=0.66, rely=0.16, width=400, height=480)

        # Title / subtitle
        self.title_label = tk.Label(self.root, text=TITLE, font=("Courier New", 32, "bold"), fg=FG_ACCENT, bg=BG_BASE)
        self.title_label.place(relx=0.5, rely=0.07, anchor="center")

        self.subtitle = tk.Label(self.root, text="A late-night, cliff-edge, choice-driven tale.", font=("Courier New", 14), fg=FG_DIM, bg=BG_BASE)
        self.subtitle.place(relx=0.5, rely=0.12, anchor="center")

        # Left: centered multiline label with typewriter
        self.text_label = tk.Label(
            self.left,
            text="",
            wraplength=640,
            font=("Courier New", 14),
            fg=FG_TEXT,
            bg=BG_PANEL,
            justify="center",   # center the multi-line text
            anchor="center"
        )
        self.text_label.place(relx=0.5, rely=0.5, anchor="center")

        # Right: choices container
        self.choice_frame = tk.Frame(self.right, bg=BG_PANEL)
        self.choice_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Bottom bar (controls)
        self.bottom = tk.Frame(self.root, bg=BG_BASE)
        self.bottom.place(relx=0.04, rely=0.86, width=1020, height=60)

        self.btn_save = tk.Button(self.bottom, text="Save", command=save_game, font=("Courier New", 12),
                                  bg=BTN_BG, fg=BTN_FG, activebackground=BTN_BG_ACTIVE, activeforeground=BTN_FG_ACTIVE, width=10)
        self.btn_save.pack(side="left", padx=8)

        self.btn_load = tk.Button(self.bottom, text="Load", command=self.load_and_show, font=("Courier New", 12),
                                  bg=BTN_BG, fg=BTN_FG, activebackground=BTN_BG_ACTIVE, activeforeground=BTN_FG_ACTIVE, width=10)
        self.btn_load.pack(side="left", padx=8)

        self.btn_full = tk.Button(self.bottom, text="Fullscreen (Esc)", command=self.toggle_fullscreen, font=("Courier New", 12),
                                  bg=BTN_BG, fg=BTN_FG, activebackground=BTN_BG_ACTIVE, activeforeground=BTN_FG_ACTIVE, width=18)
        self.btn_full.pack(side="left", padx=8)

        self.music_on = MUSIC_ENABLED
        self.btn_music = tk.Button(self.bottom, text="Music: On" if self.music_on else "Music: Off",
                                   command=self.toggle_music, font=("Courier New", 12),
                                   bg=BTN_BG, fg=BTN_FG, activebackground=BTN_BG_ACTIVE, activeforeground=BTN_FG_ACTIVE, width=12)
        self.btn_music.pack(side="left", padx=8)

        self.btn_restart = tk.Button(self.bottom, text="Restart", command=self.restart_game, font=("Courier New", 12),
                                     bg=BTN_BG, fg=BTN_FG, activebackground=BTN_BG_ACTIVE, activeforeground=BTN_FG_ACTIVE, width=10)
        self.btn_restart.pack(side="left", padx=8)

        # Bindings
        self.root.bind("<Escape>", lambda e: self.toggle_fullscreen())

        # Typewriter state
        self.typing_thread = None
        self.typing_lock = threading.Lock()
        self.is_typing = False
        self.cursor_visible = True
        self.current_full_text = ""
        self.current_typed = ""
        self.cursor_job = None
        self.glitch_rate = 0.04  # chance of brief wrong char flash
        self.char_delay_range = (12, 35)  # ms per char

        # Start screen / music
        self.play_music()
        self.show_scene(game_state["current_scene"])

        # Animate CRT
        self.animate_scanlines()
        self.animate_flicker()

    # ---------- Window helpers ----------
    def center_window(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = int((sw - WINDOW_WIDTH) / 2)
        y = int((sh - WINDOW_HEIGHT) / 2)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def toggle_fullscreen(self):
        self.fullscreen = not getattr(self, "fullscreen", False)
        self.root.attributes("-fullscreen", self.fullscreen)

    def load_and_show(self):
        if load_game():
            self.show_scene(game_state["current_scene"])
        else:
            messagebox.showinfo("No Save Found", "No save file to load.")

    # ---------- Music ----------
    def toggle_music(self):
        self.music_on = not self.music_on
        self.btn_music.config(text="Music: On" if self.music_on else "Music: Off")
        if not PYGAME_OK:
            return
        if self.music_on:
            self.play_music()
        else:
            pygame.mixer.music.stop()

    def play_music(self):
        if not (self.music_on and PYGAME_OK):
            return
        try:
            if os.path.exists(MUSIC_FILE):
                pygame.mixer.music.load(MUSIC_FILE)
                pygame.mixer.music.set_volume(MUSIC_VOLUME)
                pygame.mixer.music.play(-1)
        except Exception as e:
            print("Music error:", e)

    def restart_game(self):
        game_state["current_scene"] = "intro_room"
        self.show_scene("intro_room")

    # ---------- Scanlines / Flicker ----------
    def _build_scanlines(self):
        self.scan_canvas.delete("all")
        h = self.root.winfo_height() or WINDOW_HEIGHT
        self.scanlines = []
        step = 4  # distance between lines
        for y in range(0, h, step):
            line = self.scan_canvas.create_rectangle(0, y, WINDOW_WIDTH, y+1, fill="#001400", outline="")
            self.scanlines.append(line)

    def animate_scanlines(self):
        # gentle vertical drift
        try:
            for line in self.scanlines:
                self.scan_canvas.move(line, 0, 1)
            # wrap-around
            to_move_top = []
            for line in self.scanlines:
                coords = self.scan_canvas.coords(line)
                if coords and coords[1] > WINDOW_HEIGHT:
                    to_move_top.append(line)
            for line in to_move_top:
                self.scan_canvas.move(line, 0, -WINDOW_HEIGHT)
        except Exception:
            pass
        self.root.after(33, self.animate_scanlines)  # ~30fps

    def animate_flicker(self):
        # subtle background brightness flicker
        shade = random.choice(["#000000", "#000100", "#000800", "#000300"])
        self.root.configure(bg=shade)
        # also flicker text slight color jitter
        jitter = random.choice([FG_TEXT, "#00f85f", "#1cff9e"])
        self.text_label.configure(fg=jitter)
        self.root.after(120, self.animate_flicker)

    # ---------- Choice buttons ----------
    def clear_choices(self):
        for w in self.choice_frame.winfo_children():
            w.destroy()

    def add_choice(self, text, target):
        b = tk.Button(self.choice_frame, text=text,
                      font=("Courier New", 12),
                      bg=BTN_BG, fg=BTN_FG,
                      activebackground=BTN_BG_ACTIVE, activeforeground=BTN_FG_ACTIVE,
                      bd=2, relief="ridge", wraplength=320, justify="center",
                      command=lambda t=target: self.show_scene(t))
        b.pack(pady=6, fill="x")

    # ---------- Typewriter with blinking '_' cursor ----------
    def stop_typing(self):
        with self.typing_lock:
            self.is_typing = False
        if self.cursor_job:
            self.root.after_cancel(self.cursor_job)
            self.cursor_job = None
        # final text without cursor
        self.text_label.config(text=self.current_full_text)

    def _cursor_blink(self):
        if not self.is_typing:
            return
        self.cursor_visible = not self.cursor_visible
        display = self.current_typed + ("_" if self.cursor_visible else " ")
        self.text_label.config(text=display)
        self.cursor_job = self.root.after(350, self._cursor_blink)

    def type_lines(self, lines):
        # Stop any current typing
        self.stop_typing()
        # Prepare new text
        self.current_full_text = "\n".join(lines)
        self.current_typed = ""
        with self.typing_lock:
            self.is_typing = True
        # Start cursor blink
        self.cursor_visible = True
        self._cursor_blink()

        def type_next(i=0):
            if not self.is_typing:
                return
            if i >= len(self.current_full_text):
                # done
                self.stop_typing()
                return
            ch = self.current_full_text[i]
            # brief glitch flash
            if ch not in ["\n", "\r"] and random.random() < self.glitch_rate:
                wrong = random.choice(["#", "%", "&", "$", "0", "1", "!", "?", "§"])
                self.current_typed += wrong
                self.text_label.config(text=self.current_typed + "_")
                self.root.after(20, lambda i=i, ch=ch: self._fix_glitch(i, ch))
            else:
                self.current_typed += ch
                # keep centered look by updating label text
                self.text_label.config(text=self.current_typed + "_")
                delay = random.randint(*self.char_delay_range)
                self.root.after(delay, lambda: type_next(i + 1))

        type_next()

    def _fix_glitch(self, i, real_char):
        if not self.is_typing:
            return
        # replace last char with the real one
        self.current_typed = self.current_typed[:-1] + real_char
        self.text_label.config(text=self.current_typed + "_")
        delay = random.randint(*self.char_delay_range)
        self.root.after(delay, lambda: self._continue_from(i + 1))

    def _continue_from(self, next_i):
        # continue typing from index
        def cont(i=next_i):
            if not self.is_typing:
                return
            if i >= len(self.current_full_text):
                self.stop_typing()
                return
            ch = self.current_full_text[i]
            if ch not in ["\n", "\r"] and random.random() < self.glitch_rate:
                wrong = random.choice(["#", "%", "&", "$", "0", "1", "!", "?", "§"])
                self.current_typed += wrong
                self.text_label.config(text=self.current_typed + "_")
                self.root.after(20, lambda i=i, ch=ch: self._fix_glitch(i, ch))
            else:
                self.current_typed += ch
                self.text_label.config(text=self.current_typed + "_")
                delay = random.randint(*self.char_delay_range)
                self.root.after(delay, lambda: cont(i + 1))
        cont()

    # ---------- Scene driver ----------
    def show_scene(self, scene_name):
        game_state["current_scene"] = scene_name
        save_game()

        scene = scenes.get(scene_name)
        if not scene:
            # fallback if missing
            scene = {"text": ["(Missing scene)"], "options": []}

        # Some implicit consequences (example: if you rushed and parents catch you)
        if scene_name == "frontdoor_rush":
            # small chance of instant caught (spice!)
            if random.random() < 0.12:
                scene = scenes["caught_parent"]

        # Type text
        self.type_lines(scene["text"])

        # Choices
        self.clear_choices()
        if not scene["options"]:
            # offer restart on endings or caught
            self.add_choice("Restart (Back to Bedroom)", "intro_room")
            return

        for label, target in scene["options"]:
            self.add_choice(label, target)

    # ---------- CRT maintenance ----------
    def resize_scanlines(self, event=None):
        self._build_scanlines()

# ---------- main ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.bind("<Configure>", app.resize_scanlines)
    root.mainloop()
