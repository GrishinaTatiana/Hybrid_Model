class BankBridge:
    def __init__(self, bank):
        self.bank = bank

    def start_service(self, agent, duration):
        # запускаем процесс обслуживания
        self.bank.env.process(self.bank.service_process(agent, duration))

    def sync(self, until_time):
        # продвигаем SimPy время до указанного
        try:
            if self.bank.env.now < until_time:
                self.bank.env.run(until=until_time)
        except Exception as e:
            print(f"Ошибка синхронизации: {e}")