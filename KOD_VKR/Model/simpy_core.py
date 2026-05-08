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
                    #print(f"  Агент {agent.unique_id} ушел из очереди (дискомфорт: {accumulated_discomfort:.1f}/{agent.base_patience})")
                    return

            # начали обслуживание
            agent.status = "BEING_SERVED"
            #print(f"  Агент {agent.unique_id} начал обслуживание у кассы {teller_idx + 1}")

            # время обслуживания
            yield self.env.timeout(duration)

            # обслуживание завершено
            agent.status = "SERVED"
            #print(f"  Агент {agent.unique_id} завершил обслуживание")