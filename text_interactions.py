# Класс для удобного создания взаимодействия с ботом при помощи текста.
class TextInteractions:
    # Конструктор.
    def __init__(self):
        self.interactions = {}
        
    
    # Присвоение флага.
    def set_interaction(self, name, value, callback):
        self.interactions[name] = (value, callback)
        
    # Вызов коллбека, ассоциируемого с флагом.
    async def call_interaction(self, name, *args, **kwargs):
        self.interactions[name] = (
            await self.interactions[name][1](self.interactions[name][0], *args, **kwargs),
            self.interactions[name][1]
        )
        
    # Вызов коллбека и присвоение вохврощаемого значения флагу.
    async def set_call_interaction(self, name, value, callback, *args, **kwargs):
        self.interactions[name] = (
            await callback(value, *args, **kwargs),
            callback
        )
    
    
    # Вызов коллбека, если флаг не имеет знаачение 0 или False.
    async def call_interactions(self, *args, **kwargs):
        for i in self.interactions:
            if (isinstance(self.interactions[i][0], int) and self.interactions[i][0] != 0) or \
               (isinstance(self.interactions[i][0], bool) and self.interactions[i][0]):
                await self.call_interaction(i, *args, **kwargs)
                return True
        return False
        
    
    # Возвращение всех флагов в обычное состояние.
    def reset(self):
        for i in self.interactions:
            if isinstance(self.interactions[i][0], int):
                self.interactions[i][0] = 0
            elif isinstance(self.interactions[i][0], bool):
                self.interactions[i][0] = False
