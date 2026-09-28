import msvcrt
import random
import sys
import time

from cpu import CPU, execute_command
from data import RSW, CommandType, CPUState, Memory, ProcessState, Task
from display import display, initialize_display, restore_display
from process import (
    check_io_interrupts,
    compact_process_table,
    execute_io_tick,
    find_free_process_slot,
    initialize_io,
    initialize_process_table,
    load_process,
    process,
    restore_state,
    save_state,
    set_state,
    terminate_process,
)
from scheduler import scheduler

MIN_SPEED = 0.1
MAX_SPEED = 1000.0
SPEED_STEP = 0.10

DEFAULT_MEMORY_SIZE = 1024

MIN_TASK_MEMORY = 100
MAX_TASK_MEMORY = 300

DEFAULT_TASK_COMMANDS = 100

MIN_PRIORITY = 1
MAX_PRIORITY = 10

DEFAULT_QUANTUM = 5

DEFAULT_IO_PERCENT = 5
DEFAULT_IO_DURATION = 10

def show_help() -> None:
    print("MODEL OS")
    print()
    print("Usage:")
    print("  python main.py       Start model")
    print("  python main.py /?    Show help")


def initialize_memory() -> Memory:
    return Memory(total=DEFAULT_MEMORY_SIZE)


def generate_task(task_id: int) -> Task:
    return Task(
        task_id=task_id,
        memory_size=random.randint(MIN_TASK_MEMORY, MAX_TASK_MEMORY),
        command_count=DEFAULT_TASK_COMMANDS,
        io_percent=DEFAULT_IO_PERCENT,
        io_duration=DEFAULT_IO_DURATION,
        priority=random.randint(MIN_PRIORITY, MAX_PRIORITY),
    )


def change_speed(speed: float, increase: bool) -> float:
    if increase:
        speed *= 1 + SPEED_STEP
    else:
        speed *= 1 - SPEED_STEP

    return max(MIN_SPEED, min(MAX_SPEED, speed))


def handle_input(speed: float) -> tuple[float, bool]:
    running = True

    if not msvcrt.kbhit():
        return speed, running

    key = msvcrt.getwch()

    if key == "\x1b":
        running = False

    elif key == "+":
        speed = change_speed(speed, increase=True)

    elif key == "-":
        speed = change_speed(speed, increase=False)

    return speed, running

def load_initial_processes(
    memory: Memory,
    process_table: list[RSW],
) -> tuple[dict[int, Task], int, int]:
    tasks: dict[int, Task] = {}

    task_id = 1
    next_process_id = 1

    while True:
        slot = find_free_process_slot(process_table)

        if slot is None:
            break

        task = generate_task(task_id)

        loaded = load_process(
            task=task,
            process_table=process_table,
            memory=memory,
            process_id=next_process_id,
        )

        if not loaded:
            break

        tasks[next_process_id] = task

        task_id += 1
        next_process_id += 1

    return tasks, task_id, next_process_id

def initialize_model() -> tuple[
    CPU,
    Memory,
    list[RSW],
    dict[int, Task],
    int,
    int,
]:
    cpu = CPU()
    memory = initialize_memory()
    process_table = initialize_process_table()

    tasks, next_task_id, next_process_id = load_initial_processes(
        memory=memory,
        process_table=process_table,
    )

    return (
        cpu,
        memory,
        process_table,
        tasks,
        next_task_id,
        next_process_id,
    )

def find_process(
    process_table: list[RSW],
    process_id: int,
) -> RSW | None:
    for rsw in process_table:
        if rsw.process_id == process_id:
            return rsw

    return None

def load_new_process(
    memory: Memory,
    process_table: list[RSW],
    tasks: dict[int, Task],
    task_id: int,
    process_id: int,
) -> tuple[int, int]:
    for _ in range(3):
        slot = find_free_process_slot(process_table)

        if slot is None:
            break

        task = generate_task(task_id)

        loaded = load_process(
            task=task,
            process_table=process_table,
            memory=memory,
            process_id=process_id,
        )

        task_id += 1

        if loaded:
            tasks[process_id] = task
            process_id += 1

    return task_id, process_id

def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "/?":
        show_help()
        return

    (
        cpu,
        memory,
        process_table,
        tasks,
        next_task_id,
        next_process_id,
    ) = initialize_model()

    speed = 10.0
    running = True

    current_process_id: int | None = None
    quantum_left = 0

    last_command = None

    # В начале работы CPU находится в состоянии ожидания.
    cpu.state = CPUState.WAITING

    # Выбрать первый процесс для выполнения.
    current_process_id = scheduler(process_table)

    if current_process_id is not None:
        current_rsw = find_process(process_table, current_process_id)

        if current_rsw is not None:
            set_state(current_rsw, ProcessState.ACTIVE)
            restore_state(cpu, current_rsw)

            quantum_left = DEFAULT_QUANTUM
            cpu.state = CPUState.WORKING

    initialize_display()

    try:
        while running:
            if cpu.state == CPUState.WORKING and current_process_id is not None:
                current_task = tasks[current_process_id]

                last_command = execute_command(
                    cpu=cpu,
                    task=current_task,
                )

                if last_command == CommandType.EXIT:
                    current_rsw = find_process(
                        process_table,
                        current_process_id,
                    )

                    if current_rsw is not None:
                        terminated_process_id = current_process_id

                        terminate_process(
                            current_rsw,
                            memory,
                        )

                        tasks.pop(terminated_process_id, None)

                        compact_process_table(process_table)

                    current_process_id = None
                    quantum_left = 0

                    # После освобождения памяти попробовать загрузить новое задание.
                    next_task_id, next_process_id = load_new_process(
                        memory=memory,
                        process_table=process_table,
                        tasks=tasks,
                        task_id=next_task_id,
                        process_id=next_process_id,
                    )

                    # Выбрать следующий готовый процесс.
                    selected_process_id = scheduler(process_table)

                    if selected_process_id is None:
                        cpu.state = CPUState.WAITING

                    else:
                        next_rsw = find_process(
                            process_table,
                            selected_process_id,
                        )

                        if next_rsw is not None:
                            current_process_id = selected_process_id

                            set_state(next_rsw, ProcessState.ACTIVE)
                            restore_state(cpu, next_rsw)

                            quantum_left = DEFAULT_QUANTUM
                            cpu.state = CPUState.WORKING

                elif last_command == CommandType.COMPUTE:
                    quantum_left -= 1

                    if quantum_left == 0:
                        current_rsw = find_process(
                            process_table,
                            current_process_id,
                        )

                        if current_rsw is not None:
                            save_state(cpu, current_rsw)
                            set_state(current_rsw, ProcessState.READY)

                        selected_process_id = scheduler(process_table)

                        if selected_process_id is None:
                            current_process_id = None
                            cpu.state = CPUState.WAITING

                        else:
                            next_rsw = find_process(
                                process_table,
                                selected_process_id,
                            )

                            if next_rsw is not None:
                                current_process_id = selected_process_id

                                set_state(next_rsw, ProcessState.ACTIVE)
                                restore_state(cpu, next_rsw)

                                quantum_left = DEFAULT_QUANTUM
                                cpu.state = CPUState.WORKING

                            else:
                                current_process_id = None
                                cpu.state = CPUState.WAITING

                elif last_command == CommandType.IO:
                    current_rsw = find_process(
                        process_table,
                        current_process_id,
                    )

                    if current_rsw is not None:
                        save_state(cpu, current_rsw)
                        initialize_io(current_rsw, current_task.io_duration)

                    selected_process_id = scheduler(process_table)

                    if selected_process_id is None:
                        current_process_id = None
                        cpu.state = CPUState.WAITING

                    else:
                        next_rsw = find_process(
                            process_table,
                            selected_process_id,
                        )

                        if next_rsw is not None:
                            current_process_id = selected_process_id

                            set_state(next_rsw, ProcessState.ACTIVE)
                            restore_state(cpu, next_rsw)

                            quantum_left = DEFAULT_QUANTUM
                            cpu.state = CPUState.WORKING

            # Моделировать один такт работы процессоров ввода-вывода.
            execute_io_tick(process_table)

            # Проверить завершившиеся операции ввода-вывода.
            completed_io = check_io_interrupts(process_table)

            # Обработать прерывания через регулировщик.
            for rsw in completed_io:
                process(rsw)

            # Проверить состояние системы.
            if cpu.state == CPUState.WAITING:
                selected_process_id = scheduler(process_table)

                if selected_process_id is not None:
                    next_rsw = find_process(
                        process_table,
                        selected_process_id,
                    )

                    if next_rsw is not None:
                        current_process_id = selected_process_id
                        set_state(next_rsw, ProcessState.ACTIVE)
                        restore_state(cpu, next_rsw)
                        quantum_left = DEFAULT_QUANTUM
                        cpu.state = CPUState.WORKING

            display(
                cpu_pc=cpu.pc,
                cpu_state=cpu.state,
                active_process_id=current_process_id,
                quantum_left=quantum_left,
                speed=speed,
                memory=memory,
                process_table=process_table,
                command=last_command,
            )

            speed, running = handle_input(speed)

            time.sleep(1 / speed)

    finally:
        restore_display()

if __name__ == "__main__":
    main()
