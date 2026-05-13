import random
import pysd
import os
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from simpy_core import BankModule
from bridge import BankBridge
from agents import ClientAgent


class BankModel(Model):
    def __init__(self, width=20, height=10, n_tellers=2, spawn_rate=0.1):
        super().__init__()

        # АГЕНТНОЕ МОДЕЛИРОВАНИЕ
        actual_height = n_tellers * 2
        self.grid = MultiGrid(width, actual_height, torus=False)

        # Агенты управляются через self.agents (AgentSet)

        self.n_tellers = n_tellers
        self.spawn_rate = spawn_rate

        # Счетчик шагов (заменяет self.schedule.steps)
        self.current_step = 0

        # ДИСКРЕТНО-СОБЫТИЙНОЕ МОДЕЛИРОВАНИЕ
        self.bank = BankModule(n_tellers)
        self.bridge = BankBridge(self.bank)

        # СИСТЕМНАЯ ДИНАМИКА
        # Параметры тепловой модели
        self.HEAT_PER_PERSON = 100.0
        self.INSULATION_FACTOR = 150.0
        self.OUTSIDE_TEMP = 15.0
        self.AIR_HEAT_CAPACITY = 50000.0
        self.INITIAL_TEMP = 22.0

        # Текущая температура (результат SD модели)
        self.temperature = self.INITIAL_TEMP
        self.sd_time = 0

        # Загрузка SD модели температуры помещения
        mdl_path = os.path.join(os.path.dirname(__file__), '!thermal_model.mdl')
        try:
            self.sd_model = pysd.read_vensim(mdl_path)
            print("SD модель (PySD) успешно загружена")

            # Установка постоянных параметров
            self.sd_model.set_components({
                'Heat per Person': self.HEAT_PER_PERSON,
                'Outside Temperature': self.OUTSIDE_TEMP,
                'Insulation Factor': self.INSULATION_FACTOR,
                'Air Heat Capacity': self.AIR_HEAT_CAPACITY,
                'Initial Temperature': self.INITIAL_TEMP
            })

        except Exception as e:
            print(f"Ошибка загрузки SD модели: {e}")
            print("Будет использована упрощенная модель температуры")
            self.sd_model = None

        # Счетчики статистики
        self.left_by_heat = 0
        self.left_by_error = 0
        self.served_count = 0
        self.total_spawned = 0
        self.heat_resistant_served = 0
        self.heat_sensitive_served = 0
        self.heat_resistant_left = 0
        self.heat_sensitive_left = 0
        self.heat_resistant_error = 0
        self.heat_sensitive_error = 0

        # Сбор данных со всех трех парадигм
        self.datacollector = DataCollector(
            model_reporters={
                "В очереди": lambda m: m.get_total_queue_length(),
                "На обслуживании": lambda m: m.get_total_being_served(),
                "Обслужены (всего)": lambda m: m.served_count,
                "Ушли от жары (всего)": lambda m: m.left_by_heat,
                "Ушли от ошибки (всего)": lambda m: m.left_by_error,  # Уникальный функционал
                "Температура (SD)": lambda m: m.temperature
            }
        )

    # Возвращает Y-координату дорожки входа для кассы
    def get_enter_lane(self, teller_id):
        return teller_id * 2  # 0, 2, 4, ...

    # Возвращает Y-координату дорожки выхода для кассы
    def get_exit_lane(self, teller_id):
        return teller_id * 2 + 1  # 1, 3, 5, ...

    # Возвращает длину очереди для конкретной кассы
    def get_queue_length_for_teller(self, teller_id):
        enter_lane = self.get_enter_lane(teller_id)
        queue_length = len([
            a for a in self.agents
            if hasattr(a, 'teller_id')
               and a.teller_id == teller_id
               and a.direction == 'enter'
               and a.status in ["ENTERING", "WAITING"]
        ])
        return queue_length

    # Возвращает количество агентов на обслуживании у кассы
    def get_being_served_for_teller(self, teller_id):
        being_served = len([
            a for a in self.agents
            if hasattr(a, 'teller_id')
               and a.teller_id == teller_id
               and a.status == "BEING_SERVED"
        ])
        return being_served

    # Общая длина очереди по всем кассам
    def get_total_queue_length(self):
        return sum(self.get_queue_length_for_teller(teller) for teller in range(self.n_tellers))

    # Общее количество агентов на обслуживании
    def get_total_being_served(self):
        return sum(self.get_being_served_for_teller(teller) for teller in range(self.n_tellers))

    # Текущее количество обслуженных агентов (которые выходят)
    def get_current_served_count(self):
        return len([a for a in self.agents if a.status == "SERVED"])

    # Текущее количество ушедших агентов (которые покидают систему)
    def get_current_left_count(self):
        return len([a for a in self.agents if a.status == "LEFT"])

    # Текущее количество ушедших из-за ошибки кассира агентов (которые покидают систему)
    def get_current_error_count(self):
        return len([a for a in self.agents if a.status == "LEFT_ERROR"])

    # Выбирает кассу с наименьшим количеством агентов в очереди
    def get_best_teller(self):
        teller_queues = []
        for teller in range(self.n_tellers):
            queue_length = self.get_queue_length_for_teller(teller)
            teller_queues.append((queue_length, teller))

        teller_queues.sort(key=lambda x: x[0])
        best_length = teller_queues[0][0]
        best_tellers = [teller for length, teller in teller_queues if length == best_length]

        return random.choice(best_tellers)

    # Обновление температуры с использованием системной динамики
    def update_temperature_sd(self, current_time):
        total_people = self.get_total_queue_length() + self.get_total_being_served()

        if self.sd_model is not None:
            try:
                self.sd_model.set_components({'people_count': total_people})
                result = self.sd_model.run(return_timestamps=[current_time])
                self.temperature = result['Room Temperature'].iloc[-1]
                self.temperature = max(15.0, min(40.0, self.temperature))
            except Exception as e:
                print(f"Ошибка SD модели: {e}")
                self._fallback_temperature_update(total_people)
        else:
            self._fallback_temperature_update(total_people)

    # Обновление температуры без использованием PySD
    def _fallback_temperature_update(self, total_people):
        heat_gain = total_people * self.HEAT_PER_PERSON
        heat_loss = (self.temperature - self.OUTSIDE_TEMP) * self.INSULATION_FACTOR
        dt_hours = 1.0 / 60.0
        dT = (heat_gain - heat_loss) / self.AIR_HEAT_CAPACITY
        self.temperature += dT * dt_hours * 60
        self.temperature = max(15.0, min(40.0, self.temperature))

    def step(self):
        # Увеличиваем счетчик шагов
        self.current_step += 1

        # ШАГ 1: Системная динамика - обновление температуры
        self.update_temperature_sd(self.current_step)

        # ШАГ 2: Агентное моделирование - создание новых агентов
        if random.random() < self.spawn_rate:
            best_teller = self.get_best_teller()
            ctype = random.choice(["HEAT_RESISTANT", "HEAT_SENSITIVE"])
            new_client = ClientAgent(self, self.bridge, ctype, best_teller)
            self.total_spawned += 1

            start_x = self.grid.width - 1
            start_y = self.get_enter_lane(best_teller)

            self.grid.place_agent(new_client, (start_x, start_y))

        # ШАГ 3: Агентное моделирование - все агенты делают шаг
        agents_to_remove = []

        # Перебираем агентов в случайном порядке
        for agent in random.sample(list(self.agents), len(self.agents)):
            if agent.status != "DELETED":
                old_status = agent.status
                agent.step()
                new_status = agent.status

                # Собираем статистику при изменении статуса
                # Обслуживание завершено (агент перешел в SERVED)
                if old_status != "SERVED" and new_status == "SERVED":
                    self.served_count += 1
                    if agent.client_type == "HEAT_RESISTANT":
                        self.heat_resistant_served += 1
                    else:
                        self.heat_sensitive_served += 1

                # Агент ушел из-за жары (перешел в LEFT)
                if old_status != "LEFT" and new_status == "LEFT":
                    self.left_by_heat += 1
                    if agent.client_type == "HEAT_RESISTANT":
                        self.heat_resistant_left += 1
                    else:
                        self.heat_sensitive_left += 1

                # Агент ушел из-за ошибки кассира
                if old_status != "LEFT_ERROR" and new_status == "LEFT_ERROR":
                    self.left_by_error += 1
                    if agent.client_type == "HEAT_RESISTANT":
                        self.heat_resistant_error += 1
                    else:
                        self.heat_sensitive_error += 1

                if new_status == "DELETED":
                    agents_to_remove.append(agent)

        # ШАГ 4: Удаление завершивших агентов
        for agent in agents_to_remove:
            try:
                if agent.pos is not None:
                    self.grid.remove_agent(agent)
                if agent in self.agents:
                    self.agents.remove(agent)
            except Exception as e:
                print(f"Не удалось удалить агента {agent.unique_id}: {e}")
                if agent in self.agents:
                    self.agents.remove(agent)

        # ШАГ 5: Синхронизация DES (SimPy) времени
        self.bridge.sync(self.current_step)

        # ШАГ 6: Сбор данных
        self.datacollector.collect(self)