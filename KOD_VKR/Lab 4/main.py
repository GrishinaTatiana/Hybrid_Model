from bank_model import BankModel
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def run_simulation(steps=200, visualize=True):
    n_tellers = 3
    model = BankModel(width=20, height=n_tellers * 2, n_tellers=n_tellers, spawn_rate=0.7)

    if visualize:
        plt.ion()
        fig = plt.figure(figsize=(15, 12))  # Увеличил высоту
        gs = GridSpec(4, 1, height_ratios=[0.15, 0.15, 0.1, 0.6], hspace=0.5)  # Добавил еще один ряд

        ax_clients = fig.add_subplot(gs[0])
        ax_temp = fig.add_subplot(gs[1])
        ax_ac = fig.add_subplot(gs[2])
        ax_grid = fig.add_subplot(gs[3])

        ax_clients.set_xlabel('Шаг симуляции', fontsize=9)
        ax_clients.set_ylabel('Количество клиентов', fontsize=9)
        ax_clients.set_title('Количество клиентов, уходящих из банка', fontsize=11, fontweight='bold')
        ax_clients.grid(True, alpha=0.3)
        ax_clients.tick_params(labelsize=8)

        ax_temp.set_xlabel('Шаг симуляции', fontsize=9)
        ax_temp.set_ylabel('Температура (°C)', fontsize=9)
        ax_temp.set_title('Динамика температуры в помещении', fontsize=11, fontweight='bold')
        ax_temp.grid(True, alpha=0.3)
        ax_temp.tick_params(labelsize=8)

        # настройка графика кондиционера
        ax_ac.set_xlabel('Шаг симуляции', fontsize=9)
        ax_ac.set_ylabel('Статус AC', fontsize=9)
        ax_ac.set_title('Работа кондиционера (1 = ВКЛ, 0 = ВЫКЛ)', fontsize=11, fontweight='bold')
        ax_ac.set_ylim(-0.1, 1.1)
        ax_ac.set_yticks([0, 1])
        ax_ac.set_yticklabels(['ВЫКЛ', 'ВКЛ'])
        ax_ac.grid(True, alpha=0.3)
        ax_ac.tick_params(labelsize=8)

    # Массивы для хранения истории
    steps_history = []
    current_served_history = []
    current_left_history = []
    current_error_history = []
    temperature_history = []
    ac_status_history = []
    spawn_rate_history = []

    # Накопительные для информации
    total_served_history = []
    total_left_history = []

    if visualize:
        # Инициализируем линии для текущих значений
        line_served, = ax_clients.plot([], [], 'b-', linewidth=1.5, label='Обслуженные (выходят)')
        line_left, = ax_clients.plot([], [], 'r-', linewidth=1.5, label='Ушедшие от жары')
        line_error, = ax_clients.plot([], [], 'r--', linewidth=1.5, label='Ушедшие из-за ошибки')
        line_temp, = ax_temp.plot([], [], 'r-', linewidth=1.5, label='Температура')
        line_ac, = ax_ac.plot([], [], 'g-', linewidth=1.5, label='Кондиционер', drawstyle='steps-post')  # ДОБАВЛЯЕМ
        ax_clients.legend(loc='upper left', fontsize=7)
        ax_temp.legend(loc='upper left', fontsize=7)
        ax_ac.legend(loc='upper left', fontsize=7)

    print("Симуляция запущена...")

    for step in range(steps):
        model.step()

        # Сохраняем историю
        steps_history.append(step)
        current_served = model.get_current_served_count()
        current_left = model.get_current_left_count()
        current_error = model.get_current_error_count()
        current_served_history.append(current_served)
        current_left_history.append(current_left)
        current_error_history.append(current_error)
        temperature_history.append(model.temperature)
        ac_status_history.append(1 if model.ac_on else 0)
        spawn_rate_history.append(model.spawn_rate)

        # Накопительные для информации в тексте
        total_served_history.append(model.served_count)
        total_left_history.append(model.left_by_heat)

        if visualize and plt.fignum_exists(fig.number):
            # Обновляем данные линий
            line_served.set_data(steps_history, current_served_history)
            line_left.set_data(steps_history, current_left_history)
            line_error.set_data(steps_history, current_error_history)
            line_temp.set_data(steps_history, temperature_history)
            line_ac.set_data(steps_history, ac_status_history)

            # Настраиваем пределы осей для графика клиентов
            max_val = max(max(current_served_history + [1]), max(current_left_history + [1]))
            ax_clients.set_xlim(0, steps)
            ax_clients.set_ylim(0, max_val * 1.2 + 2)

            # Настраиваем пределы осей для графика температуры
            ax_temp.set_xlim(0, steps)
            ax_temp.set_ylim(15, max(max(temperature_history), 30) * 1.1)

            # Настраиваем пределы для графика кондиционера
            ax_ac.set_xlim(0, steps)

            # Обновляем текстовую информацию
            for text in ax_clients.texts:
                text.remove()
            for text in ax_temp.texts:
                text.remove()
            for text in ax_ac.texts:
                text.remove()

            # Обновляем зону дискомфорта
            for collection in ax_temp.collections[:]:
                collection.remove()

            if max(temperature_history) > 28:
                ax_temp.fill_between(steps_history, 28, max(temperature_history + [30]),
                                     alpha=0.15, color='red', label='Зона дискомфорта')

            # Добавляем пороговые линии для кондиционера
            ax_ac.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Порог включения/выключения')

            # График 4: основная сетка банка
            ax_grid.clear()
            ax_grid.set_xlim(-1, model.grid.width)
            ax_grid.set_ylim(-1, model.grid.height)
            ax_grid.set_aspect('equal')
            ax_grid.set_title('Визуализация банка', fontsize=10, fontweight='bold')
            ax_grid.tick_params(labelsize=7)

            # Рисуем кассы и дорожки
            for teller in range(model.n_tellers):
                enter_lane = model.get_enter_lane(teller)
                exit_lane = model.get_exit_lane(teller)

                # Дорожки
                ax_grid.axhspan(enter_lane - 0.5, enter_lane + 0.5,
                                xmin=0, xmax=1, alpha=0.1, color='blue')
                ax_grid.axhspan(exit_lane - 0.5, exit_lane + 0.5,
                                xmin=0, xmax=1, alpha=0.1, color='green')

                # Границы дорожек
                ax_grid.axhline(y=enter_lane - 0.5, color='gray', linestyle='--', alpha=0.3)
                ax_grid.axhline(y=enter_lane + 0.5, color='gray', linestyle='--', alpha=0.3)
                ax_grid.axhline(y=exit_lane - 0.5, color='gray', linestyle='--', alpha=0.3)
                ax_grid.axhline(y=exit_lane + 0.5, color='gray', linestyle='--', alpha=0.3)

                # Касса
                ax_grid.axvline(x=0.5, color='red', linestyle='-', alpha=0.5, linewidth=2)

                # Стрелки
                ax_grid.annotate('←', xy=(model.grid.width - 2, enter_lane),
                                 xytext=(model.grid.width - 2, enter_lane), fontsize=8)
                ax_grid.annotate('→', xy=(2, exit_lane),
                                 xytext=(2, exit_lane), fontsize=8)

                # Подпись кассы
                queue_len = model.get_queue_length_for_teller(teller)
                ax_grid.text(-0.6, (enter_lane + exit_lane) / 2,
                             f"Касса {teller + 1}\nОчередь: {queue_len}",
                             ha='right', va='center', fontsize=7,
                             bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))

                # Подписи дорожек
                ax_grid.text(model.grid.width - 1, enter_lane, "ВХОД",
                             ha='center', va='center', fontsize=6, alpha=0.5)
                ax_grid.text(model.grid.width - 1, exit_lane, "ВЫХОД",
                             ha='center', va='center', fontsize=6, alpha=0.5)

            # Отрисовка агентов
            for agent in model.agents:
                if agent.pos and agent.status != "DELETED":
                    x, y = agent.pos

                    if agent.status == "BEING_SERVED":
                        color = "orange"
                        size = 150
                        marker = 's'
                    elif agent.status == "SERVED":
                        color = "green"
                        size = 70
                        marker = '>'
                    elif agent.status == "LEFT":
                        color = "red"
                        size = 70
                        marker = 'v'
                    elif agent.status == "LEFT_ERROR":
                        color = "darkred"
                        size = 90
                        marker = 'X'
                    else:
                        color = "blue" if agent.client_type == "HEAT_RESISTANT" else "purple"
                        size = 70
                        marker = 'o'

                    alpha = 0.7 if agent.status in ["SERVED", "LEFT"] else 1.0

                    ax_grid.scatter(x, y, c=color, s=size, marker=marker,
                                    edgecolors='black', linewidths=0.5,
                                    zorder=3, alpha=alpha)

            # Отображение текущей температуры и статуса AC на графике банка
            temp_text = f"Температура: {model.temperature:.1f}°C"
            temp_color = 'red' if model.temperature > 28 else 'orange' if model.temperature > 24 else 'green'

            ac_text = f"AC: {'ВКЛЮЧЕН' if model.ac_on else 'ВЫКЛЮЧЕН'}"
            ac_color = 'blue' if model.ac_on else 'gray'

            spawn_text = f"Spawn rate: {model.spawn_rate:.2f}"

            ax_grid.text(model.grid.width - 2, model.grid.height,
                         f"{temp_text}\n{ac_text}\n{spawn_text}",
                         fontsize=9, fontweight='bold',
                         color=temp_color,
                         bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
                         ha='right', va='top')

            # Легенда для сетки
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=6,
                       label='Жаростойкий (вход)'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='purple', markersize=6,
                       label='Чувствительный (вход)'),
                Line2D([0], [0], marker='s', color='w', markerfacecolor='orange', markersize=6,
                       label='Обслуживание'),
                Line2D([0], [0], marker='>', color='w', markerfacecolor='green', markersize=6,
                       label='Обслужен (выход)'),
                Line2D([0], [0], marker='v', color='w', markerfacecolor='red', markersize=6,
                       label='Ушел от жары'),
                Line2D([0], [0], marker='X', color='w', markerfacecolor='darkred', markersize=8,
                       label='Ушел из-за ошибки'),
            ]
            ax_grid.legend(handles=legend_elements, loc='upper left', fontsize=6, ncol=3)

            ax_grid.grid(True, linestyle=':', alpha=0.2)

            fig.canvas.draw()
            fig.canvas.flush_events()
            plt.pause(0.15)

    if visualize:
        plt.ioff()
        plt.show()


if __name__ == "__main__":
    run_simulation(200)