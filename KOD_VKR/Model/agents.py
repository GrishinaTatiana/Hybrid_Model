from mesa import Agent
import random


class ClientAgent(Agent):
    # Инициализация агента клиента
    def __init__(self, model, bridge, client_type, teller_id):

        super().__init__(model)
        self.bridge = bridge  # мост для SimPy
        self.client_type = client_type  # тип клиента
        self.teller_id = teller_id  # ID целевой кассы
        self.direction = 'enter'  # направление движения ('enter' или 'exit')
        # Базовая терпеливость: 30 для жаростойких, 10 для чувствительных
        self.base_patience = 30 if client_type == "HEAT_RESISTANT" else 10
        self.status = "ENTERING"  # текущий статус агента

    # Возвращает Y-координату дорожки входа для кассы
    def get_enter_lane(self):
        return self.model.get_enter_lane(self.teller_id)

    # Возвращает Y-координату дорожки выхода для кассы
    def get_exit_lane(self):
        return self.model.get_exit_lane(self.teller_id)



    def step(self):
        try:
            # состояние 1: вход в систему
            if self.status == "ENTERING":
                # Проверка существования агента
                if self.pos is None:
                    self.remove_from_model()
                    return

                x, y = self.pos
                target_lane = self.get_enter_lane()

                # Если агент не на нужной дорожке - двигаемся к ней
                if y != target_lane:
                    new_pos = (x, target_lane)
                    if self.model.grid.is_cell_empty(new_pos):
                        self.model.grid.move_agent(self, new_pos)
                    return

                # Движение к кассе (влево по оси X)
                if x > 1:
                    new_pos = (x - 1, y)
                    if self.model.grid.is_cell_empty(new_pos):
                        self.model.grid.move_agent(self, new_pos)
                else:
                    # Достигли кассы (x=1), переходим в состояние ожидания
                    self.status = "WAITING"
                    self.bridge.start_service(self, duration=10)


            # состояние 2: обслуживание
            elif self.status == "BEING_SERVED":
                # Проверка существования агента
                if self.pos is None:
                    self.remove_from_model()
                    return

                x, y = self.pos
                # Перемещение на позицию обслуживания (x=0)
                if x != 0:
                    new_pos = (0, self.get_enter_lane())
                    if self.model.grid.is_cell_empty(new_pos):
                        self.model.grid.move_agent(self, new_pos)

            # состояние 3: обслужен, выход из системы
            elif self.status == "SERVED":
                # Проверка существования агента
                if self.pos is None:
                    self.remove_from_model()
                    return

                x, y = self.pos
                exit_lane = self.get_exit_lane()

                # Переход на дорожку выхода
                if y != exit_lane:
                    new_pos = (x, exit_lane)
                    if self.model.grid.is_cell_empty(new_pos):
                        self.model.grid.move_agent(self, new_pos)
                        self.direction = 'exit'  # меняем направление на выход
                    return

                # Движение к выходу (вправо по оси X)
                if x < self.model.grid.width - 1:
                    new_pos = (x + 1, y)
                    if self.model.grid.is_cell_empty(new_pos):
                        self.model.grid.move_agent(self, new_pos)
                else:
                    # Достигли края сетки - удаляем агента
                    self.remove_from_model()

            # состояние 4: ушел из за жары
            elif self.status == "LEFT":
                # Проверка существования агента
                if self.pos is None:
                    self.remove_from_model()
                    return

                x, y = self.pos
                exit_lane = self.get_exit_lane()

                # Переход на дорожку выхода
                if y != exit_lane:
                    new_pos = (x, exit_lane)
                    if self.model.grid.is_cell_empty(new_pos):
                        self.model.grid.move_agent(self, new_pos)
                        self.direction = 'exit'  # меняем направление на выход
                    return

                # Движение к выходу (вправо по оси X)
                if x < self.model.grid.width - 1:
                    new_pos = (x + 1, y)
                    if self.model.grid.is_cell_empty(new_pos):
                        self.model.grid.move_agent(self, new_pos)
                else:
                    # Достигли края сетки - удаляем агента
                    self.remove_from_model()

        except Exception as e:
            # Обработка любых ошибок в step()
            print(f"Ошибка в step() агента {self.unique_id}: {e}")
            self.remove_from_model()

    # Удаляет агента из модели и сетки
    def remove_from_model(self):
        try:
            # Удаляем агента из сетки, если он там есть
            if self.pos is not None:
                try:
                    self.model.grid.remove_agent(self)
                except:
                    pass  # Игнорируем ошибки при удалении
            # Устанавливаем статус "DELETED"
            self.status = "DELETED"
        except Exception as e:
            # Обработка ошибок при удалении
            print(f"Ошибка при удалении агента {self.unique_id}: {e}")
            self.status = "DELETED"