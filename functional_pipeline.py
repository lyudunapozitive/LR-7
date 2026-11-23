"""
Лабораторна робота № 7. Модуль 1 (Варіант 20).
Модуль діагностики кластера (*args, **kwargs), валідація параметрів
та багатокритеріальне сортування нод за [Кількість_збоїв (desc), Uptime (asc)].
Освітній компонент: Програмування на Python.
"""

import sys
import time
from typing import Any


def diagnose_cluster_nodes(*nodes: tuple, **options: Any) -> list[dict]:
    """
    Приймає варіативну кількість телеметричних записів вузлів кластера (*args)
    та параметри фільтрації (**kwargs).
    Формат кортежу вузла: (node_id: str, fault_count: int, uptime: float, cpu_load: float).
    """
    # Зчитування конфігураційних опцій зі значеннями за замовчуванням
    min_uptime = options.get("min_uptime", 0.0)
    max_faults = options.get("max_faults", 50)
    max_cpu_load = options.get("max_cpu_load", 95.0)
    only_unstable = options.get("only_unstable", False)

    validated_records = []

    for idx, raw_node in enumerate(nodes, start=1):
        # Валідація структури кортежу
        if not isinstance(raw_node, tuple) or len(raw_node) != 4:
            print(f"Попередження: Запис вузла #{idx} має некоректну структуру і проігнорований.")
            continue

        node_id, fault_count, uptime, cpu_load = raw_node

        # Валідація типів даних полів
        if not (
            isinstance(fault_count, int)
            and not isinstance(fault_count, bool)
            and isinstance(uptime, (int, float))
            and isinstance(cpu_load, (int, float))
        ):
            print(f"Помилка валідації: Запис вузла #{idx} містить некоректні числові типи.")
            continue

        # Перевірка фізичної коректності метрик кластера
        if fault_count < 0 or uptime < 0 or not (0.0 <= cpu_load <= 100.0):
            print(f"Помилка валідації: Запис вузла #{idx} має недопустимі значення метрик.")
            continue

        # Фільтрація за граничними інженерними умовами (**kwargs)
        if uptime < min_uptime:
            continue
        if fault_count > max_faults:
            continue
        if cpu_load > max_cpu_load:
            continue
        if only_unstable and fault_count == 0:
            continue

        # Формування структурованого словника
        record = {
            "node_id": str(node_id),
            "fault_count": int(fault_count),
            "uptime": float(uptime),
            "cpu_load": float(cpu_load),
        }
        validated_records.append(record)

    return validated_records


def main() -> None:
    """Головна функція демонстрації діагностики кластера та lambda-сортування."""
    print("=" * 80)
    print(f"{'ДІАГНОСТИКА ВУЗЛІВ КЛАСТЕРА ТА LAMBDA-СОРТУВАННЯ':^80}")
    print("=" * 80)

    # Сирий потік діагностичних пакетів від нод кластера
    raw_cluster_stream = (
        ("CL-NODE-03", 4, 142.5, 61.2),
        ("CL-NODE-01", 7, 310.0, 78.4),
        ("CL-NODE-02", 1, 520.8, 34.0),
        ("CL-NODE-04", 12, 18.0, 98.5),  # Буде відфільтровано за CPU load (> 95.0%)
        ("CL-NODE-05", 4, 89.2, 55.1),   # Однакова кількість збоїв із CL-NODE-03, але менший Uptime
        ("CL-NODE-06", 0, 740.0, 22.3),
        ("CL-NODE-07", 2, 12.4, 41.7),   # Буде відфільтровано за мінімальним Uptime (< 24.0 год)
    )

    # 1. Виклик функції з розпакуванням кортежу (*args) та передачею опцій (**kwargs)
    filtered_nodes = diagnose_cluster_nodes(
        *raw_cluster_stream,
        min_uptime=24.0,
        max_faults=20,
        max_cpu_load=95.0,
        only_unstable=False,
    )

    print(f"Вхідний потік: {len(raw_cluster_stream)} вузлів. Пройшли валідацію: {len(filtered_nodes)} вузлів.\n")

    # 2. Багатокритеріальне сортування за допомогою функції sorted та lambda
    # Критерій 1: Кількість збоїв за спаданням (-item['fault_count'])
    # Критерій 2: Час роботи Uptime за зростанням (item['uptime'])
    sorted_nodes = sorted(
        filtered_nodes,
        key=lambda item: (-item["fault_count"], item["uptime"])
    )

    # 3. Виведення результатів за допомогою f-strings
    print(f"| {'№':^4} | {'Вузол (Node ID)':^18} | {'Збої (шт.)':^12} | {'Uptime (год)':^16} | {'CPU (%)':^12} |")
    print("-" * 80)
    for idx, rec in enumerate(sorted_nodes, start=1):
        print(
            f"| {idx:^4d} | {rec['node_id']:<18} | {rec['fault_count']:^12d} | "
            f"{rec['uptime']:^16.1f} | {rec['cpu_load']:^12.1f} |"
        )
    print("=" * 80 + "\n")


if __name__ == "__main__":
    t_start = time.perf_counter()
    main()
    t_elapsed = time.perf_counter() - t_start
    print(f"Час виконання функціонального конвеєра: {t_elapsed * 1000:.3f} мс\n")