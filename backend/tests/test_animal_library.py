from backend.libs.animal_library import AnimalLibrary

animal_lib = AnimalLibrary()
animal_lib.add_animal('pet_001', '大黄', '中华田园犬', 0)
animal = animal_lib.get_animal('pet_001')
print(f"查到动物: {animal}")