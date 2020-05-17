#Einfacherhalber ist aktuell es im Controller PY der Befehl
from src.uvis_controller import UltraVisController
from src.config import Configuration

if __name__ == "__main__":
    controller = UltraVisController(debug_mode=True)
    controller.run()
