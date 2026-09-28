import sys

from data import RSW, CommandType, CPUState, Memory, ProcessState


def initialize_display() -> None:
    # Очистить экран, поставить курсор в начало, скрыть курсор
    sys.stdout.write("\033[2J\033[1;1H\033[?25l")
    sys.stdout.flush()


def clear_line(text: str = "") -> str:
    # Вывести текст и очистить остаток строки справа
    return text + "\033[K"


def get_state_code(state: ProcessState) -> int:
    if state == ProcessState.ABSENT:
        return 0

    if state == ProcessState.READY:
        return 1

    if state == ProcessState.ACTIVE:
        return 2

    if state == ProcessState.BLOCKED:
        return 3

    return -1


def display(
    cpu_pc: int,
    cpu_state: CPUState,
    active_process_id: int | None,
    quantum_left: int,
    speed: float,
    memory: Memory,
    process_table: list[RSW],
    command: CommandType | None = None,
) -> None:
    lines: list[str] = []

    lines.append("=" * 90)
    lines.append("                                       MODEL OS")
    lines.append("=" * 90)
    lines.append("")

    lines.append("CPU")
    lines.append("-" * 90)
    lines.append(f"PC:             {cpu_pc:<10}")
    lines.append(f"State:          {cpu_state.value:<15}")
    lines.append(
        f"Active process: "
        f"{active_process_id if active_process_id is not None else 'Нет':<10}"
    )
    lines.append(f"Quantum left:   {quantum_left:<10}")
    lines.append(
        f"Command:        "
        f"{command.value if command is not None else 'Нет':<15}"
    )
    lines.append(f"Speed:          {speed:<10.1f} ticks/sec")
    lines.append("")

    lines.append("MEMORY")
    lines.append("-" * 90)
    lines.append(f"Total:          {memory.total:<10}")
    lines.append(f"Used:           {memory.used:<10}")
    lines.append(f"Free:           {memory.free:<10}")
    lines.append("")

    lines.append("PROCESS TABLE (RSW)")
    lines.append("-" * 90)
    lines.append(
        f"{'№':<4}"
        f"{'Process ID':<13}"
        f"{'Task ID':<10}"
        f"{'Memory':<10}"
        f"{'Commands':<10}"
        f"{'PC':<8}"
        f"{'State':<14}"
        f"{'Code':<6}"
        f"{'IO left':<10}"
        f"{'Priority':<10}"
    )
    lines.append("-" * 90)

    for index, rsw in enumerate(process_table, start=1):
        state_code = get_state_code(rsw.state)

        displayed_io = (
            rsw.io_remaining
            if rsw.state == ProcessState.BLOCKED
            else "-"
        )

        # Для активного процесса показываем текущий PC процессора.
        # Для остальных процессов показываем сохранённый PC из RSW.
        displayed_pc = (
            cpu_pc
            if rsw.process_id == active_process_id
            and rsw.state == ProcessState.ACTIVE
            else rsw.pc
        )

        lines.append(
            f"{index:<4}"
            f"{rsw.process_id:<13}"
            f"{rsw.task_id:<10}"
            f"{rsw.memory_size:<10}"
            f"{rsw.command_count:<10}"
            f"{displayed_pc:<8}"
            f"{rsw.state.value:<14}"
            f"{state_code:<6}"
            f"{displayed_io:<10}"
            f"{rsw.priority:<10}"
        )

    lines.append("")
    lines.append("=" * 90)
    lines.append("Commands:")
    lines.append("[+] Increase speed")
    lines.append("[-] Decrease speed")
    lines.append("[Esc] Exit")
    lines.append("=" * 90)

    # Очищаем остаток каждой строки справа
    screen = "\n".join(clear_line(line) for line in lines)

    # Переходим в левый верхний угол и выводим новый кадр
    sys.stdout.write("\033[1;1H")
    sys.stdout.write(screen)
    sys.stdout.write("\033[J")
    sys.stdout.flush()


def restore_display() -> None:
    # Вернуть курсор
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()
