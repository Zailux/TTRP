from Observable import Observable

class UltraVisModel:
    def __init__(self):
        self.activeUser = Observable()

        self.tracking = Observable()

    def setActiveUser(self, activeUser):
        self.activeUser.set(activeUser)


    
  

   

    
    




