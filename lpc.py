from os import walk, makedirs
from os.path import join, exists
from json import loads, dumps
import shutil
from itertools import groupby
from operator import itemgetter

import jsbeautifier



LPC_DIR = '../Universal-LPC-Spritesheet-Character-Generator/'
SHEET_DEFINITION_DIR = LPC_DIR + 'sheet_definitions'
SPRITESHEET_DIR = LPC_DIR + 'spritesheets'
COPY_DIR = './spritesheets/'



BODY_TYPES = ["male", "muscular", "female", "pregnant", "teen", "child"]

SPRITESHEET_TRES_TEMPLATE = '''[gd_resource type="Resource" script_class="LPCSpriteSheet" load_steps=3 format=3 uid="uid://%s"]

[ext_resource type="Script" path="res://addons/LPCAnimatedSprite/LPCSpriteSheet.gd" id="1"]
[ext_resource type="Texture2D" uid="uid://%s" path="res://spritesheets/%s" id="2"]

[resource]
script = ExtResource("1")
SpriteSheet = ExtResource("2")
Name = "%s"
SpriteType = 0
'''



def load_sheet_definitions():
  sheet_definitions = []

  for dir_path, dir_names, file_names in walk(SHEET_DEFINITION_DIR):
    for file_name in file_names:
      if file_name.endswith('.json'):
        with open(join(SHEET_DEFINITION_DIR, file_name), 'r', encoding='utf-8') as f:
          sheet_definition = loads(f.read())
          sheet_definitions.append(sheet_definition)

  return sheet_definitions

def stat_sheet_definitions(sheet_definitions):
  type_name_count = {}
  for sheet_definition in sheet_definitions:
    type_name = sheet_definition['type_name']
    type_name_count[type_name] = type_name_count.get(type_name, 0) + 1
  type_name_count = sorted(type_name_count.items(), key=lambda x:x[1])
  for entry in type_name_count:
    print(entry[0], entry[1])

def validate_spritesheet(sheet_definitions, show_error, is_missing_spritesheet_error):
  valid_sheet_definitions = []
  for sheet_definition in sheet_definitions:
    valid = True
    layer_count = 0
    key_count = {}
    for field in sheet_definition.keys():
      if field.startswith('layer_'):
        layer = sheet_definition[field]
        layer_count += 1
        for key in layer.keys():
          if 'zPos' != key and 'is_mask' != key and 'custom_animation' != key:
            key_count[key] = key_count.get(key, 0) + 1

    type_name = sheet_definition['type_name']
    if 0 == layer_count:
      raise Exception('no layers : %s, %s' % (sheet_definition['name'], type_name))

    key_count_items = list(key_count.items())
    for item in key_count_items:
      if item[0] not in BODY_TYPES:
        raise Exception('unknown body type : %s, %s, %s' % (sheet_definition['name'], type_name, item[0]))
    for item in key_count_items:
      if key_count_items[0][1] != item[1]:
        print(item)
        print(key_count_items)
        raise Exception('missing body type : %s, %s, %s' % (sheet_definition['name'], type_name, str(key_count_items)))

    variants = sheet_definition['variants']
    layer_dirs = []
    for item in key_count_items:
      body_type = item[0]
      for variant in variants:
        has_variant = None
        for layer_index in range(layer_count):
          layer_name = 'layer_' + str(layer_index + 1)
          layer_dir = sheet_definition[layer_name][body_type]
          if layer_dir not in layer_dirs:
            layer_dirs.append(layer_dir)
          spritesheet_path = SPRITESHEET_DIR + '/' + layer_dir + variant + '.png'
          if None == has_variant:
            has_variant = exists(spritesheet_path)
          elif has_variant != exists(spritesheet_path):
            if is_missing_spritesheet_error:
              valid = False
              if show_error:
                print('missing spritesheet : %s, %s, %s, %s' % (sheet_definition['name'], type_name, body_type, variant))
    for layer_dir in layer_dirs:
      is_missing = True
      for variant in variants:
        spritesheet_path = SPRITESHEET_DIR + '/' + layer_dir + variant + '.png'
        if exists(spritesheet_path):
          is_missing = False
      if is_missing:
        valid = False
        if show_error:
          print('missing layer dir : %s, %s, %s' % (sheet_definition['name'], type_name, layer_dir))

    if valid:
      valid_sheet_definitions.append(sheet_definition)

  return valid_sheet_definitions

def list_spritesheet(valid_sheet_definitions):
  spritesheet_list = []

  for sheet_definition in valid_sheet_definitions:
    name = sheet_definition['name']
    type_name = sheet_definition['type_name']
    layer_count = 0
    for field in sheet_definition.keys():
      if field.startswith('layer_'):
        layer_count += 1

    variants = sheet_definition['variants']
    for body_type in BODY_TYPES:
      first_layer = sheet_definition['layer_1']
      if body_type not in first_layer:
        continue
      for variant in variants:
        if not exists(SPRITESHEET_DIR + '/' + first_layer[body_type] + variant + '.png'):
          continue
        layers = []
        for layer_index in range(layer_count):
          layer = sheet_definition['layer_' + str(layer_index + 1)]
          layers.append((layer[body_type], layer['zPos']))
        spritesheet_list.append([body_type, type_name, name, variant, layers])

  return spritesheet_list

def stat_spritesheet_list(spritesheet_list):
  spritesheet_list = sorted(spritesheet_list, key=itemgetter(0))
  for body_type, spritesheet_by_body_type in groupby(spritesheet_list, key=itemgetter(0)):
    spritesheet_by_body_type = sorted(list(spritesheet_by_body_type), key=itemgetter(1))
    type_count = 0
    name_count = 0
    variant_count = 0
    print('body_type %s : %d' % (body_type, len(spritesheet_by_body_type)))
    for type_name, spritesheet_by_type_name in groupby(spritesheet_by_body_type, key=itemgetter(1)):
      spritesheet_by_type_name = sorted(list(spritesheet_by_type_name), key=itemgetter(2))
      type_count += 1
      #print('\ttype_name %s : %d' % (type_name, len(spritesheet_by_type_name)))
      for name, spritesheet_by_name in groupby(spritesheet_by_type_name, key=itemgetter(2)):
        spritesheet_by_name = sorted(list(spritesheet_by_name), key=itemgetter(3))
        name_count += 1
        variant_count += len(spritesheet_by_name)
        #print('\tname %s : %d' % (name, len(spritesheet_by_name)))
    print('\ttype_count %s : %d' % (body_type, type_count))
    print('\tname_count %s : %d' % (body_type, name_count))
    print('\tvariant_count %s : %d' % (body_type, variant_count))

def copy_spritesheet(spritesheet_list):
  for spritesheet in spritesheet_list:
    variant = spritesheet[3]
    layer_dirs = list(map(lambda x: x[0], spritesheet[4]))
    for layer_dir in layer_dirs:
      makedirs(COPY_DIR + layer_dir, exist_ok=True)
      file_name = layer_dir + variant
      file_path = file_name + '.png'
      spritesheet_path = SPRITESHEET_DIR + '/' + file_path
      copy_path = COPY_DIR + file_path
      if not exists(copy_path):
        shutil.copyfile(spritesheet_path, copy_path)

def generate_spritesheet_tres(spritesheet_list):
  for spritesheet in spritesheet_list:
    variant = spritesheet[3]
    layer_dirs = list(map(lambda x: x[0], spritesheet[4]))
    for layer_dir in layer_dirs:
      makedirs(COPY_DIR + layer_dir, exist_ok=True)
      file_name = layer_dir + variant
      file_path = file_name + '.png'
      copy_path = COPY_DIR + file_path
      import_path = copy_path + '.import'
      tres_path = COPY_DIR + file_name + '.tres'
      if exists(import_path) and not exists(tres_path):
        texture_uid = None
        text = open(import_path, 'r', encoding='utf-8').read()
        lines = text.strip().split('\n')
        for line in lines:
          if line.startswith('uid='):
            texture_uid = line[11:-1]
            break
        new_uid = texture_uid + 't'
        sprite_tres = SPRITESHEET_TRES_TEMPLATE % (new_uid, texture_uid, file_path, file_name)
        with open(tres_path, 'w', encoding='utf-8') as f:
          f.write(sprite_tres)

def generate_spritesheet_json(spritesheet_list):
  body_to_type_to_name_to_spritesheets = {}
  for spritesheet in spritesheet_list:
    body_type = spritesheet[0]
    type_name = spritesheet[1]
    name = spritesheet[2]
    if body_type not in body_to_type_to_name_to_spritesheets:
      body_to_type_to_name_to_spritesheets[body_type] = {}
    type_to_name_to_spritesheets = body_to_type_to_name_to_spritesheets[body_type]
    if type_name not in type_to_name_to_spritesheets:
      type_to_name_to_spritesheets[type_name] = {}
    name_to_spritesheets = type_to_name_to_spritesheets[type_name]
    if name not in name_to_spritesheets:
      name_to_spritesheets[name] = []
    spritesheets = name_to_spritesheets[name]
    spritesheets.append(spritesheet[3:])

  orders = {
    # Body
    'shadow': ['Shadow'],
    'body': ['Body color', 'Zombie', 'Skeleton'],
    'wound_arm': ['Arm'],
    'wound_brain': ['Brain'],
    'wound_ribs': ['Ribs'],
    'wound_eye': ['Eye'],
    'wound_mouth': ['Mouth'],
    'prosthesis_hand': ['Hook hand'],
    'prosthesis_leg': ['Peg leg'],
    'tail': ['Wolf Tail', 'Fluffy Wolf Tail', 'Cat Tail', 'Lizard tail', 'Lizard Tail (Alt Colors)'],
    'wings': [
      'Feathered Wings', 'Bat Wings', 'Monarch Wings', 'Pixie Wings', 'Transparent Pixie Wings',\
      'Lunar Wings', 'Dragonfly Wings', 'Transparent Dragonfly Wings',\
      'Lizard Wings', 'Batlike Lizard Wings', 'Lizard Wings (Alt Colors)'],
    'wings_edge': ['Monarch Wings Edge'],
    'wings_dots': ['Monarch Wings Dots'],
    # Head
    'head': [
      'Human female', 'Human male', 'Human female elderly', 'Human male elderly', 'Human male plump', 'Human male gaunt', 'Human child', 'Human male small', 'Human female small', 'Human elderly small',\
      'Boarman', 'Boarman child',\
      'Pig', 'Pig child',\
      'Sheep', 'Sheep child',\
      'Minotaur', 'Minotaur female', 'Minotaur child',\
      'Wartotaur',\
      'Wolf female', 'Wolf male', 'Wolf child',\
      'Rabbit', 'Rabbit child',\
      'Rat', 'Rat child',\
      'Mouse', 'Mouse child',\
      'Lizard female', 'Lizard male', 'Lizard child',\
      'Orc female', 'Orc male', 'Orc child',\
      'Goblin', 'Goblin child',\
      'Alien',\
      'Troll', 'Troll child',\
      'Skeleton', 'Zombie', 'Jack O Lantern', 'Vampire', 'Frankenstein'],
    'ears': ['Big ears', 'Elven ears', 'Long ears', 'Medium Elven Ears', 'Hanging Elven Ears', 'Downward Elven Ears', 'Dragon Ears', 'Side Wolf Ears', 'Side Cat Ears', 'Feather Ears'],
    'ears_inner': ['Side Wolf Ears Skintone', 'Side Cat Ears Skintone', 'Feather Ears Skintone'],
    'furry_ears': ['Cat Ears', 'Wolf Ears'],
    'furry_ears_skin': ['Cat Ears Skintone', 'Wolf Ears Skintone'],
    'nose': ['Big nose', 'Button nose', 'Straight nose', 'Elderly nose', 'Large nose'],
    'eyes': ['Eyes', 'Cyclops Eyes'],
    'eyebrows': ['Thick Eyebrows', 'Thin Eyebrows'],
    'wrinkes': ['Wrinkles'],
    'beard': ['Basic Beard', 'Winter Beard', '5 O\'clock Shadow', 'Trimmed Beard', 'Medium Beard'],
    'mustache': ['Big Mustache', 'Mustache', 'French Mustache', 'Walrus Mustache', 'Chevron Mustache', 'Handlebar Mustache', 'Lampshade Mustache', 'Horseshoe Mustache'],
    'hair': [
      # afro
      'Afro', 'Natural', 'Dreadlocks short', 'Twists fade', 'Twists straight', 'Dreadlocks long', 'Flat top straight', 'Flat top fade', 'Cornrows',\
      # curly
      'Jewfro', 'Curly short', 'Curly short 2', 'Curly long',\
      # bald/shaved
      'Balding', 'Longhawk', 'Shorthawk', 'High and tight', 'Buzzcut',\
      # short
      'Plain', 'Pixie', 'Page', 'Idol', 'Mop', 'Parted', 'Messy2', 'Messy3', 'Messy1', 'Bedhead', 'Unkempt', 'Bangsshort', 'Swoop', 'Side Swoop', 'Curtains', 'Page2', 'Bangs', 'Single', 'Cowlick', 'Cowlick tall',\
      # spiky
      'Spiked porcupine', 'Spiked liberty2', 'Spiked liberty', 'Spiked beehive', 'Spiked', 'Spiked2', 'Halfmessy',\
      # pigtails
      'Bunches', 'Pigtails', 'Pigtails bangs',\
      # bob
      'Bob', 'Lob', 'Bob side part',\
      # braids, ponytails, updos
      'Half up', 'Bangs bun', 'Ponytail', 'Ponytail2', 'High ponytail', 'Braid', 'Braid2', 'Shoulderl', 'Shoulderr', 'Long tied',\
      # long
      'Loose', 'Bangslong', 'Bangslong2', 'Long', 'Long messy', 'Long messy2', 'Curtains long', 'Wavy', 'Long center part', 'Long straight',\
      # very long
      'Princess', 'Sara', 'Long band', 'Xlong',
      # child
      'Messed',
      'Parted 2', 'Parted 3',
      'Relm w/Ponytail', 'Relm Short', 'Long Topknot', 'Long Topknot 2', 'Short Topknot', 'Short Topknot 2'
    ],
    'ponytail': ['Long Topknot', 'Short Topknot'],
    'horns': ['Backwards Horns', 'Curled Horns'],
    'fins': ['Fin', 'Short fin'],
    'bandana': ['Bandana', 'Bordered Bandana', 'Mail'],
    'bandana_overlay': ['Skull Bandana Overlay'],
    'headcover': ['Kerchief', 'Thick Headband', 'Tied Headband'],
    'headcover_rune': ['Thick Headband Rune'],
    'hat': [\
      'Formal Bowler Hat', 'Formal Tophat', 'Misc Magic Hats', 'Wizard Hat Base',\
      # Helmets
      'Armet', 'Simple Armet', 'Barbarian', 'Barbarian nasal', 'Barbarian Viking', 'Barbuta', 'Simple barbuta', 'Bascinet', 'Pigface bascinet', 'Pigface bascinet raised', 'Round bascinet', 'Round bascinet raised', 'Close helm', 'Flattop', 'Greathelm', 'Horned helmet', 'Kettle helm', 'Legion', 'Maximus', 'Morion', 'Nasal helm', 'Norman helm', 'Pointed helm', 'Spangenhelm', 'Viking spangenhelm', 'Sugarloaf greathelm', 'Simple sugarloaf helm', 'Xeon helmet',
      # Pirate hats'
      'Bonnie', 'Bonnie Alt Tilt',\
      'Cavalier', 'Tricorne', 'Bicorne foreaft',
      # Crowns
      'Crown', 'Tiara',
      # Special'
      'Feather Cap', 'Hijab', 'Christmas Hat',\
      'Bicorne Athwart', 'Bicorne Athwart Admiral', 'Bicorne Athwart Captain', 'Bicorne Athwart Commodore', 'Bicorne Foreaft Commodore',\
      'Tricorne Captain', 'Tricorne Lieutenant'
    ],
    'hat_accessory': ['Feather Alt Colors', 'Bonnie feather', 'Cavalier feather', 'Bicorne Athwart Admiral Cockade'],
    'hat_trim': [
      'Elf Trim', 'Santa Trim', 'Wizard Hat Belt', 'Bonnie Center Trim',\
      'Bicorne Athwart Admiral Trim', 'Bicorne Athwart Commodore Trim', 'Bicorne Foreaft Commodore Trim',\
      'Tricorne Captain Trim', 'Tricorne Lieutenant Trim', 'Tricorne Stitching', 'Tricorne Thatching'
    ],
    'hat_overlay': ['Bicorne Athwart Skull', 'Bicorne Athwart Captain Skull', 'Tricorne Captain Skull'],
    'hat_buckle': ['Wizard Hat Buckle'],
    'hairtie': ['Hair Tie'],
    'hairtie_rune': ['Hair Tie Rune'],
    'hairextl': ['Left Braid', 'Left XLong Braid', 'Left XLong Bang'],
    'hairextr': ['Right Braid', 'Right XLong Braid', 'Right XLong Bang'],
    'visor': ['Grated visor', 'Narrow grated visor', 'Horned visor', 'Pigface visor', 'Pigface visor raised', 'Round visor', 'Round visor raised', 'Slit visor', 'Narrow slit visor'],
    'accessory': ['Crest', 'Centurion Crest', 'Helmet wings', 'Short Horns', 'Upward Horns', 'Downward Horns', 'Plumage', 'Centurion Plumage', 'Legion Plumage'],
    # Accessories
    'facial_eyes': [
      # Glasses
      'Glasses', 'Halfmoon Glasses', 'Nerd Glasses', 'Shades', 'Secretary Glasses', 'Round Glasses', 'Sunglasses',\
      # Eyepatches
      'Eyepatch Left', 'Eyepatch Right', 'Eyepatch 2 Left', 'Eyepatch 2 Right', 'Small Eyepatch Left', 'Small Eyepatch Right', 'Eyepatch Ambidextrous'
    ],
    'facial_left': ['Left Monocle'],
    'facial_left_trim': ['Left Monocle Frame Color'],
    'facial_right': ['Right Monocle'],
    'facial_right_trim': ['Right Monocle Frame Color'],
    'facial_mask': ['Plain Mask'],
    'earring_left': ['Simple Earring Left'],
    'earring_right': ['Simple Earring Right'],
    'neck': ['Bowtie', 'Bowtie 2', 'Necktie', 'Scarf', 'Capeclip', 'Capetie', 'Jabot', 'Cravat'],
    'necklace': ['Necklace'],
    # Arms
    'shoulders': ['Legion', 'Plate', 'Leather', 'Epaulets', 'Mantal'],
    'arms': ['Armour'],
    'bauldron': ['Bauldron'],
    'bracers': ['Bracers'],
    'wrists': ['Cuffs', 'Lace Cuffs'],
    'gloves': ['Gloves'],
    # Torso
    'dress': ['Sash dress', 'Slit dress', 'Kimono', 'Split Kimono'],
    'dress_trim': ['Kimono Trim', 'Split Kimono Trim'],
    'dress_sleeves': ['Kimono Sleeves', 'Kimono Oversized Sleeves'],
    'dress_sleeves_trim': ['Kimono Sleeves Trim', 'Kimono Oversized Sleeves Trim'],
    'clothes': [
      # Longsleeve
      'Longsleeve', 'Collared/Formal Longsleeve', 'Striped Collared/Formal Longsleeve', 'Longsleeve laced', 'Longsleeve Polo',\
      'Longsleeve 2', 'Longsleeve 2 Buttoned', 'Longsleeve 2 Scoop', 'Longsleeve 2 VNeck', 'Cardigan',\
      # Shortsleeve
      'Shortsleeve', 'Shortsleeve Polo',\
      # Sleeveless
      'Sleeveless', 'Sleeveless laced', 'Sleeveless striped',\
      'Sleeveless 2', 'Sleeveless 2 Buttoned', 'Sleeveless 2 Polo', 'Sleeveless 2 Scoop', 'Sleeveless 2 VNeck',\
      'Blouse', 'Longsleeve blouse', 'Tunic', 'Sara Tunic', 'Robe', 'Scoop', 'Tanktop',\
      'Child shirts',\
      'TShirt', 'TShirt Buttoned', 'TShirt Scoop', 'TShirt VNeck'
    ],
    'apron': ['Overskirt', 'Apron', 'Apron half', 'Apron full'],
    'overalls': ['Overalls', 'Suspenders'],
    'bandages': ['Bandages'],
    'chainmail': ['Chainmail'],
    'jacket': ['Collared coat', 'Iverness cloak', 'Trench coat', 'Tabard', 'Frock coat', 'Santa coat'],
    'jacket_trim': ['Frock coat buttons', 'Frock coat lace', 'Frock coat lapel'],
    'jacket_collar': ['Frock collar'],
    'jacket_pockets': ['Jacket pockets'],
    'vest': ['Vest', 'Vest open', 'Bodice', 'Corset'],
    'armour': ['Plate', 'Leather', 'Legion'],
    'cape': ['Solid', 'Tattered'],
    'cape_trim': ['Cape Trim'],
    'backpack': ['Backpack', 'Square pack', 'Jetpack', 'Basket'],
    'backpack_straps': ['Straps'],
    'cargo': ['Wood', 'Ore', 'Jetpack fins'],
    'quiver': ['Quiver'],
    'buckles': ['Buckles'],
    'belt': ['Leather Belt', 'Double Belt', 'Loose Belt', 'Belly belt', 'Other belts'],
    'sash': ['Obi', 'Sash', 'Narrow sash', 'Waistband'],
    'sash_obi': ['Obi Sash'],
    'sash_tie': ['Obi Knot Left', 'Obi Knot Right'],
    # Legs
    'legs': [
      'Armour', 'Pants', 'Pants 2',\
      'Wide pants', 'Pregnancy pants', 'Child pants',\
      'Pantaloons', 'Plain skirt', 'Slit skirt', 'Legion skirt', 'Belle skirt', 'Straight skirt', 'Leggings', 'Leggings 2',\
      'Child skirts', 'Cuffed Pants', 'Hose', 'Shorts', 'Short Shorts'
    ],
    'socks': ['Tabi Socks', 'Ankle Socks', 'High Socks'],
    'shoes': [
      # Boots
      'Boots', 'Boots 2', 'Fold Boots', 'Rim Boots',\
      # Shoes
      'Armour', 'Slippers', 'Shoes', 'Shoes 2', 'Hoofs', 'Sandals', 'Ghillies',\
      'Sara'
    ],
    'shoes_plate': ['Boots Metal Plating'],
    # Tools
    'weapon': [
      # Tool
      'Rod', 'Smash', 'Thrust', 'Whip',\
      # Ranged
      'Crossbow', 'Slingshot', 'Boomerang', 'Normal', 'Great', 'Recurve',\
      # Sword
      'Dagger', 'Glowsword', 'Longsword', 'Rapier', 'Saber', 'Katana', 'Scimitar', 'Longsword alt', 'Arming Sword',\
      # Blunt'
      'Flail', 'Mace', 'Waraxe', 'Club',\
      # Polearm
      'Cane', 'Spear', 'Scythe', 'Halberd', 'Long spear', 'Dragon spear', 'Trident',\
      # Magic'
      'Simple staff', 'Loop staff', 'Diamond staff', 'Gnarled staff', 'S staff'
    ],
    'shield': [
      'Shield', 'Spartan shield',\
      # Two-engrailed Shield
      'Two engrailed shield', 'Crusader shield', 'Plus shield',
      # Scutum Shield'
      'Scutum shield',\
      # Heater Shield
      'Heater Shield Base', 'Revised Heater Shield Base'
    ],
    'shield_trim': ['Heater Shield Trim', 'Scutum shield trim', 'Revised Heater Shield Trim'],
    'shield_paint': ['Heater Shield Paint', 'Revised Heater Shield Paint'],
    'shield_pattern': [
      'Heater shield pattern',\
      'barry', 'bend', 'bend_sinister', 'bendy', 'bendy_sinister', 'bordure',\
      'chevron', 'chevron_inverted', 'chief', 'cross', 'fess', 'lozengy',\
      'pale', 'pall', 'paly', 'per_bend', 'per_bend_sinister',\
      'per_chevron', 'per_chevron_inverted', 'per_fess',\
      'per_pale', 'per_saltire', 'quarterly', 'saltire',\
      'revised_barry', 'revised_bend', 'revised_bend_sinister', 'revised_bendy', 'revised_bendy_sinister', 'revised_bordure',\
      'revised_chevron', 'revised_chevron_inverted', 'revised_chief', 'revised_cross', 'revised_fess', 'revised_lozengy',\
      'revised_pale', 'revised_pall', 'revised_paly', 'revised_per_bend', 'revised_per_bend_sinister',\
      'revised_per_chevron', 'revised_per_chevron_inverted', 'revised_per_fess',\
      'revised_per_pale', 'revised_per_saltire', 'revised_quarterly', 'revised_saltire'
    ],
    'ammo': ['Ammo'],
    'weapon_magic_crystal': ['Crystal'],
  }

  for body_type in BODY_TYPES:
    type_to_name_to_spritesheets = body_to_type_to_name_to_spritesheets[body_type]
    for type_name in type_to_name_to_spritesheets:
      name_to_spritesheets = type_to_name_to_spritesheets[type_name]
      if type_name in orders:
        for name in name_to_spritesheets:
          if name not in orders[type_name]:
            raise Exception('%s / %s / %s' % (body_type, type_name, name))
      else:
        raise Exception('%s / %s' % (body_type, type_name))

  order_count = {}
  for type_name in orders:
    for name in orders[type_name]:
      order_name = type_name + '__' + name
      order_count[order_name] = 0
  for body_type in BODY_TYPES:
    type_to_name_to_spritesheets = body_to_type_to_name_to_spritesheets[body_type]
    for type_name in type_to_name_to_spritesheets:
      name_to_spritesheets = type_to_name_to_spritesheets[type_name]
      for name in name_to_spritesheets:
        order_name = type_name + '__' + name
        order_count[order_name] = order_count.get(order_name, 0) + 1
  for item in order_count.items():
    if 0 == item[1]:
      raise Exception(item[0])

  for body_type in BODY_TYPES:
    output = {}
    type_to_name_to_spritesheets = body_to_type_to_name_to_spritesheets[body_type]
    for type_name in orders:
      if type_name not in type_to_name_to_spritesheets:
        continue
      output[type_name] = {}
      name_to_spritesheets = type_to_name_to_spritesheets[type_name]
      for name in orders[type_name]:
        if name not in name_to_spritesheets:
          continue
        output[type_name][name] = name_to_spritesheets[name]
    json_path = COPY_DIR + '/spritesheets-' + body_type + '.json'
    with open(json_path, 'w', encoding='utf-8') as f:
      options = jsbeautifier.default_options()
      options.indent_size = 1
      options.indent_char = '\t'
      output = jsbeautifier.beautify(dumps(output), options)
      f.write(output.replace(', ', ','))





sheet_definitions = load_sheet_definitions()
#stat_sheet_definitions(sheet_definitions)
valid_sheet_definitions = validate_spritesheet(sheet_definitions, False, False)
print(len(sheet_definitions))
print(len(valid_sheet_definitions))
spritesheet_list = list_spritesheet(valid_sheet_definitions)
print(len(spritesheet_list))
stat_spritesheet_list(spritesheet_list)

# copy_spritesheet(spritesheet_list)
# generate_spritesheet_tres(spritesheet_list)
generate_spritesheet_json(spritesheet_list)
