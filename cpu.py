import random
from dataclasses import dataclass

from data import CPUState, CommandType, Task


@dataclass
class CPU:
    pc: int = 0
    state: CPUState = CPUState.WAITING

    def execute_tick(self) -> None:
        self.pc += 1


def generate_command(task: Task, pc: int) -> CommandType:
    # Если достигнуто количество команд задания,
    # генерируется команда завершения.
    if pc >= task.command_count:
        return CommandType.EXIT

    # С вероятностью io_percent выбирается команда ввода-вывода.
    if random.randint(1, 100) <= task.io_percent:
        return CommandType.IO

    # В остальных случаях выполняется вычислительная команда.
    return CommandType.COMPUTE


def decode_command(command: CommandType) -> CommandType:
    # В текущей модели тип команды уже определяет операцию.
    return command


def read_operands() -> tuple[int, int]:
    # Заглушка чтения двух операндов из памяти.
    return 0, 0


def do_operation(
    command: CommandType,
    operand1: int,
    operand2: int,
) -> int | None:
    # Выполнить операцию вычислительной команды.
    if command == CommandType.COMPUTE:
        return operand1 + operand2

    return None


def write_result(result: int | None) -> None:
    # Запись результата в память пока не моделируется.
    # Механизм будет расширен на следующем этапе работы с памятью.
    return None

def execute_command(cpu: CPU, task: Task) -> CommandType:
    # 1. Получить текущую команду по адресу PC.
    command = generate_command(task, cpu.pc)

    # 2. Увеличить аппаратный счетчик команд.
    cpu.execute_tick()

    # 3. Распознать команду.
    command = decode_command(command)

    # Команды IO и EXIT пока передаются вызывающему коду
    # для выполнения соответствующих действий с процессом.
    if command in (CommandType.IO, CommandType.EXIT):
        return command

    # 4. Прочитать операнды.
    operand1, operand2 = read_operands()

    # 5. Выполнить операцию.
    result = do_operation(
        command,
        operand1,
        operand2,
    )

    # 6. Записать результат.
    write_result(result)

    return command
