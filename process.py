from cpu import CPU
from data import RSW, Memory, ProcessState, Task

# Максимальное количество записей в таблице RSW.
MAX_PROCESSES = 16


def initialize_process_table() -> list[RSW]:
    # Создать и инициализировать таблицу RSW.
    # Все записи получают состояние «Отсутствует».
    return [RSW() for _ in range(MAX_PROCESSES)]


def create_rsw(task: Task, process_id: int) -> RSW:
    # Сформировать RSW на основе параметров нового задания.
    # Новый процесс получает начальное состояние «Готов».
    return RSW(
        process_id=process_id,
        task_id=task.task_id,
        memory_size=task.memory_size,
        command_count=task.command_count,
        pc=0,
        state=ProcessState.READY,
        priority=task.priority,
    )


def find_free_process_slot(process_table: list[RSW]) -> int | None:
    # Найти первую свободную запись таблицы RSW.
    # Свободной считается запись в состоянии «Отсутствует».
    for index, rsw in enumerate(process_table):
        if rsw.state == ProcessState.ABSENT:
            return index

    # Свободных записей нет.
    return None

def compact_process_table(process_table: list[RSW]) -> None:
    # Переместить все существующие процессы в начало таблицы,
    # сохранив их текущий порядок.
    occupied_processes = [
        rsw
        for rsw in process_table
        if rsw.state != ProcessState.ABSENT
    ]

    # Заполнить начало таблицы существующими процессами.
    for index, rsw in enumerate(occupied_processes):
        process_table[index] = rsw

    # Оставшиеся записи сделать свободными.
    for index in range(
        len(occupied_processes),
        len(process_table),
    ):
        process_table[index] = RSW()

def can_load_process(
    task: Task,
    memory: Memory,
    process_table: list[RSW],
) -> bool:
    # Проверить наличие всех ресурсов, необходимых для загрузки задания.
    has_memory = task.memory_size <= memory.free
    has_process_slot = find_free_process_slot(process_table) is not None

    return has_memory and has_process_slot


def load_process(
    task: Task,
    process_table: list[RSW],
    memory: Memory,
    process_id: int,
) -> bool:
    # Проверить возможность загрузки задания.
    if not can_load_process(task, memory, process_table):
        return False

    # Найти свободную запись в таблице RSW.
    slot = find_free_process_slot(process_table)

    if slot is None:
        return False

    # Создать RSW для нового задания.
    rsw = create_rsw(task, process_id)

    # Записать RSW в таблицу.
    process_table[slot] = rsw

    # Выделить память для загруженного задания.
    memory.used += task.memory_size

    return True


def set_state(rsw: RSW, state: ProcessState) -> None:
    # Установить новое состояние процесса.
    rsw.state = state

def save_state(cpu: CPU, rsw: RSW) -> None:
    # Сохранить текущее значение счетчика команд CPU в RSW процесса.
    rsw.pc = cpu.pc


def restore_state(cpu: CPU, rsw: RSW) -> None:
    # Восстановить счетчик команд CPU из RSW процесса.
    cpu.pc = rsw.pc

def initialize_io(rsw: RSW, io_duration: int) -> None:
    # Запустить операцию ввода-вывода.
    rsw.io_remaining = io_duration
    set_state(rsw, ProcessState.BLOCKED)

def execute_io_tick(process_table: list[RSW]) -> None:
    # Выполнить один такт работы процессоров ввода-вывода.
    for rsw in process_table:
        if (
            rsw.state == ProcessState.BLOCKED
            and rsw.io_remaining > 0
        ):
            rsw.io_remaining -= 1

def check_io_interrupts(process_table: list[RSW]) -> list[RSW]:
    # Найти процессы, у которых завершилась операция ввода-вывода.
    return [
        rsw
        for rsw in process_table
        if rsw.state == ProcessState.BLOCKED
        and rsw.io_remaining == 0
    ]

def process(rsw: RSW) -> None:
    # Регулировщик: обработать завершение операции ввода-вывода.
    if (
        rsw.state == ProcessState.BLOCKED
        and rsw.io_remaining == 0
    ):
        set_state(rsw, ProcessState.READY)

def terminate_process(rsw: RSW, memory: Memory) -> None:
    # Освободить память, занимаемую процессом.
    memory.used -= rsw.memory_size

    # Освободить запись RSW.
    rsw.process_id = 0
    rsw.task_id = 0
    rsw.memory_size = 0
    rsw.command_count = 0
    rsw.pc = 0
    rsw.priority = 0
    rsw.state = ProcessState.ABSENT
