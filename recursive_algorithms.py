"""
Лабораторна робота № 7. Модуль 2 (Варіант 20).
Рекурсивний алгоритм швидкого перетворення Фур'є (FFT Кулі-Тьюкі)
із програмним контролем глибини стека та порівнянням з ітеративним аналогом.
Освітній компонент: Програмування на Python.
"""

import cmath
import math
import random
import sys
import time


class RecursionDepthTracker:
    """Клас моніторингу та захисту глибини рекурсивного стека."""
    def __init__(self, max_allowed_depth: int = 500):
        self.current_depth = 0
        self.max_observed_depth = 0
        self.max_allowed_depth = max_allowed_depth

    def enter(self) -> None:
        """Фіксує вхід у новий рекурсивний стековий кадр."""
        self.current_depth += 1
        if self.current_depth > self.max_observed_depth:
            self.max_observed_depth = self.current_depth
        if self.current_depth > self.max_allowed_depth:
            raise RecursionError(
                f"Перевищено безпечний ліміт глибини рекурсії: {self.current_depth} > {self.max_allowed_depth}"
            )

    def leave(self) -> None:
        """Фіксує вихід зі стекового кадру при поверненні значення."""
        self.current_depth -= 1


def fft_recursive_instrumented(signal: list[complex], tracker: RecursionDepthTracker) -> list[complex]:
    """
    Реалізує рекурсивне швидке перетворення Фур'є (алгоритм Кулі-Тьюкі)
    зі розбиттям сигналу на парні та непарні відліки та аудитом викликів.
    """
    tracker.enter()
    try:
        n = len(signal)

        # Базовий випадок рекурсії: сигнал довжиною 0 або 1
        if n <= 1:
            return [complex(val) for val in signal]

        # Перевірка кратності довжини сигналу степеню двійки (N = 2^k)
        if n & (n - 1) != 0:
            raise ValueError("Довжина вхідного сигналу для БПФ Кулі-Тьюкі має бути степенем двійки.")

        # Розбиття сигналу на парні та непарні відліки (метод Кулі-Тьюкі)
        even_fft = fft_recursive_instrumented(signal[0::2], tracker)
        odd_fft = fft_recursive_instrumented(signal[1::2], tracker)

        # Об'єднання спектрів за допомогою поворотних множників W_N^k
        half_n = n // 2
        spectrum = [0j] * n
        for k in range(half_n):
            twiddle = cmath.exp(-2j * cmath.pi * k / n) * odd_fft[k]
            spectrum[k] = even_fft[k] + twiddle
            spectrum[k + half_n] = even_fft[k] - twiddle

        return spectrum

    finally:
        tracker.leave()


def fft_iterative(signal: list[complex]) -> list[complex]:
    """
    Ітеративний аналог швидкого перетворення Фур'є (Кулі-Тьюкі)
    із біт-реверсивною перестановкою відліків.
    """
    n = len(signal)
    if n <= 1:
        return [complex(val) for val in signal]
    if n & (n - 1) != 0:
        raise ValueError("Довжина вхідного сигналу для БПФ Кулі-Тьюкі має бути степенем двійки.")

    data = [complex(val) for val in signal]

    # Біт-реверсивна перестановка індексів
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            data[i], data[j] = data[j], data[i]

    # Поетапне об'єднання підмасивів («метелики»)
    step = 2
    while step <= n:
        half_step = step // 2
        angle_step = -2j * cmath.pi / step
        for start in range(0, n, step):
            for k in range(half_step):
                twiddle = cmath.exp(angle_step * k) * data[start + k + half_step]
                u = data[start + k]
                data[start + k] = u + twiddle
                data[start + k + half_step] = u - twiddle
        step *= 2

    return data


def main() -> None:
    """Головна точка входу для демонстрації та профілювання БПФ Кулі-Тьюкі."""
    print("=" * 80)
    print(f"{'РЕКУРСИВНЕ ШВИДКЕ ПЕРЕТВОРЕННЯ ФУРʼЄ (FFT КУЛІ-ТЬЮКІ)':^80}")
    print("=" * 80)

    # Налаштування системного ліміту рекурсії
    system_limit = sys.getrecursionlimit()
    print(f"Системний ліміт глибини стека CPython: {system_limit} кадрів")

    # Генерація дискретного інженерного сигналу довжиною N = 256 (2^8)
    random.seed(2026)
    signal_size = 256
    test_signal = [
        complex(
            math.sin(2 * math.pi * 5 * n / signal_size)
            + 0.5 * math.cos(2 * math.pi * 12 * n / signal_size)
            + random.uniform(-0.05, 0.05),
            0.0,
        )
        for n in range(signal_size)
    ]

    print(f"Кількість відліків сигналу N:          {signal_size} відліків")
    print(f"Перші 4 відліки вхідного сигналу:      {[round(x.real, 3) for x in test_signal[:4]]}")
    print("-" * 80)

    # 1. Виконання рекурсивного БПФ із трекінгом глибини стека
    tracker = RecursionDepthTracker(max_allowed_depth=200)
    t_rec_start = time.perf_counter()
    fft_rec_result = fft_recursive_instrumented(test_signal, tracker)
    t_rec_elapsed = time.perf_counter() - t_rec_start

    # 2. Виконання ітеративного аналога БПФ
    t_iter_start = time.perf_counter()
    fft_iter_result = fft_iterative(test_signal)
    t_iter_elapsed = time.perf_counter() - t_iter_start

    # 3. Верифікація коректності (порівняння рекурсивного та ітеративного спектрів)
    is_correct = all(
        cmath.isclose(r, it, rel_tol=1e-9, abs_tol=1e-9)
        for r, it in zip(fft_rec_result, fft_iter_result)
    )

    # Знаходження пікової гармоніки (за модулем амплітуди)
    magnitudes = [abs(c) for c in fft_rec_result[: signal_size // 2]]
    peak_bin = magnitudes.index(max(magnitudes))

    print(f"{'РЕЗУЛЬТАТИ АНАЛІЗУ ТА ПОРІВНЯННЯ ШВИДКОДІЇ':^80}")
    print("-" * 80)
    print(f"Верифікація коректності (FFT_rec == FFT_iter): {str(is_correct).upper()}")
    print(f"Максимальна зафіксована глибина стека D:       {tracker.max_observed_depth} кадрів")
    print(f"Індекс основної гармоніки спектра:             k = {peak_bin} (|X[k]| = {magnitudes[peak_bin]:.2f})")
    print(f"Час виконання рекурсивного БПФ:                {t_rec_elapsed * 1000:.4f} мс")
    print(f"Час виконання ітеративного БПФ:                {t_iter_elapsed * 1000:.4f} мс")
    if t_iter_elapsed > 0:
        print(f"Відношення часу (Рекурсія / Ітерація):         {t_rec_elapsed / t_iter_elapsed:.2f}x")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()