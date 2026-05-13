import simpy


class BankModule:
    def __init__(self, n_tellers=2):
        self.env = simpy.Environment()
        self.tellers = [simpy.Resource(self.env, capacity=1) for _ in range(n_tellers)]
        self.n_tellers = n_tellers

    def service_process(self, agent, duration):
        accumulated_discomfort = 0

        teller_idx = agent.teller_id
        if teller_idx >= len(self.tellers):
            teller_idx = 0

        teller = self.tellers[teller_idx]

        with teller.request() as req:
            # ожидание в очереди
            while not req.triggered:
                yield req | self.env.timeout(1)

                # проверка терпения
                current_temp = agent.model.temperature
                if current_temp > 22:
                    heat_factor = 1 + (current_temp - 22) / 10
                else:
                    heat_factor = 0.5

                accumulated_discomfort += heat_factor

                if accumulated_discomfort >= agent.base_patience:
                    agent.status = "LEFT"
                    return

            # начали обслуживание
            agent.status = "BEING_SERVED"

            # Рассчет скорости обслуживания в зависимости от температуры
            temp = agent.model.temperature

            # Коэффициент замедления от температуры
            if temp <= 22:
                speed_factor = 1.0  # нормальный режим
            elif temp <= 28:
                # Лёгкий дискомфорт - небольшое замедление
                speed_factor = 1.1
            else:
                # Сильная жара - сильное замедление
                speed_factor = 1.5

            # Итоговое время обслуживания
            actual_duration = duration * speed_factor
            # Максимальное время обслуживания - 15 шагов
            actual_duration = min(actual_duration, 15)

            # Обслуживание с учётом замедления
            yield self.env.timeout(actual_duration)

            # Проверка на ошибку в зависимости от температуры
            error_occurred = False
            error_probability = (temp - 20) * 0.05
            error_probability = min(error_probability, 0.5)

            # Генерируем ошибку с заданной вероятностью
            import random
            if random.random() < error_probability:
                error_occurred = True
                agent.status = "LEFT_ERROR"  # Новый статус для ошибки
                # При ошибке агент возвращается в конец очереди

            if not error_occurred:
                # обслуживание завершено успешно
                agent.status = "SERVED"